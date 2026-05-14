#!/usr/bin/python
# -*- coding: utf-8 -*-
import asyncio
import binascii
import json
import logging
import os
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast

import paho.mqtt.publish as publish
from bleak import BleakScanner

from scale_processing import (
    build_metrics_message,
    match_user,
    parse_v1_service_data,
    parse_v2_service_data,
    should_ignore_measurement,
)

DEFAULT_DEBUG_LEVEL = "INFO"
VERSION = "0.3.5"

if TYPE_CHECKING:
    from paho.mqtt.publish import TLSParameter


def custom_user_decoder(user_dict):
    return namedtuple("USER", user_dict.keys())(*user_dict.values())


@dataclass
class Config:
    miscale_mac: str = ""
    mqtt_host: str = ""
    mqtt_port: int = 1883
    mqtt_username: str = "username"
    mqtt_password: Optional[str] = None
    mqtt_prefix: str = "miscale"
    mqtt_retain: bool = True
    mqtt_tls: Optional["TLSParameter"] = None
    mqtt_discovery: bool = True
    mqtt_discovery_prefix: str = "homeassistant"
    hci_dev: str = "hci0"
    bluepy_passive_scan: bool = False
    debug_level: str = DEFAULT_DEBUG_LEVEL
    users: list = field(default_factory=list)


def load_config(config_path="/data/options.json"):
    """Load configuration from options.json and return a Config object."""
    config = Config()

    with open(config_path) as json_file:
        data = json.load(json_file)["options"]

    # Debug level
    debug_level = data.get("DEBUG_LEVEL", DEFAULT_DEBUG_LEVEL)
    if debug_level not in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"):
        logging.warning(
            f"Invalid logging level provided, defaulting to {DEFAULT_DEBUG_LEVEL}..."
        )
        debug_level = DEFAULT_DEBUG_LEVEL
    config.debug_level = debug_level

    # Required fields
    if "MISCALE_MAC" not in data:
        raise ValueError("MAC Address not provided in config")
    config.miscale_mac = data["MISCALE_MAC"]

    if "MQTT_HOST" not in data:
        raise ValueError("MQTT Host not provided in config")
    config.mqtt_host = data["MQTT_HOST"]

    # Optional MQTT fields
    config.mqtt_username = data.get("MQTT_USERNAME", "username")
    config.mqtt_password = data.get("MQTT_PASSWORD", None)
    config.mqtt_prefix = data.get("MQTT_PREFIX", "miscale")
    config.mqtt_retain = data.get("MQTT_RETAIN", True)
    config.mqtt_discovery = data.get("MQTT_DISCOVERY", True)
    config.mqtt_discovery_prefix = data.get("MQTT_DISCOVERY_PREFIX", "homeassistant")
    config.hci_dev = data.get("HCI_DEV", "hci0").lower()
    config.bluepy_passive_scan = data.get("BLUEPY_PASSIVE_SCAN", False)

    # Port
    mqtt_port = data.get("MQTT_PORT", 1883)
    if not isinstance(mqtt_port, int):
        mqtt_port = int(mqtt_port)
    config.mqtt_port = mqtt_port

    # TLS
    mqtt_tls_cacerts = data.get("MQTT_TLS_CACERTS", None)
    mqtt_tls_insecure = data.get("MQTT_TLS_INSECURE", None)
    if mqtt_tls_cacerts in [None, "", "Path to CA Cert File"]:
        config.mqtt_tls = None
    else:
        config.mqtt_tls = cast(
            "TLSParameter",
            {"ca_certs": mqtt_tls_cacerts, "insecure": mqtt_tls_insecure},
        )

    # Users
    config.users = []
    for user_data in data["USERS"]:
        user = json.loads(json.dumps(user_data), object_hook=custom_user_decoder)
        if user.GT > user.LT:
            raise ValueError(f"GT can not be larger than LT - user {user.NAME}")
        config.users.append(user)

    # Deprecated options (log warnings)
    if "MISCALE_VERSION" in data:
        logging.info(
            "MISCALE_VERSION option is deprecated and can safely be removed from config..."
        )
    if "TIME_INTERVAL" in data:
        logging.info(
            "TIME_INTERVAL option is deprecated and can safely be removed from config..."
        )

    return config


class MQTTPublisher:
    """Handles all MQTT publishing operations."""

    def __init__(self, config: Config):
        self.config = config

    def _get_auth(self):
        return {
            "username": self.config.mqtt_username,
            "password": self.config.mqtt_password,
        }

    def publish_discovery(self):
        """Publish MQTT Discovery information for Home Assistant."""
        for user in self.config.users:
            message = json.dumps(
                {
                    "name": f"{user.NAME} Weight",
                    "state_topic": f"{self.config.mqtt_prefix}/{user.NAME}/weight",
                    "value_template": "{{ value_json.weight }}",
                    "json_attributes_topic": f"{self.config.mqtt_prefix}/{user.NAME}/weight",
                    "icon": "mdi:scale-bathroom",
                    "state_class": "measurement",
                }
            )
            publish.single(
                f"{self.config.mqtt_discovery_prefix}/sensor/{self.config.mqtt_prefix}/{user.NAME}/config",
                message,
                retain=True,
                hostname=self.config.mqtt_host,
                port=self.config.mqtt_port,
                auth=self._get_auth(),
                tls=self.config.mqtt_tls,
            )
        logging.info("MQTT Discovery Setup Completed...")

    def publish_weight(self, weight, unit, mitdatetime, has_impedance, impedance):
        """Publish weight data for the matched user."""
        matched_user = match_user(self.config.users, weight)
        if matched_user is None:
            logging.debug(f"No user matched for weight {weight}")
            return

        message = build_metrics_message(
            weight, unit, mitdatetime, has_impedance, impedance, matched_user
        )
        message_json = json.dumps(message)
        topic = f"{self.config.mqtt_prefix}/{matched_user.NAME}/weight"

        try:
            logging.info(f"Publishing data to topic {topic}: {message_json}")
            publish.single(
                topic,
                message_json,
                retain=self.config.mqtt_retain,
                hostname=self.config.mqtt_host,
                port=self.config.mqtt_port,
                auth=self._get_auth(),
                tls=self.config.mqtt_tls,
            )
            logging.info("Data Published ...")
        except Exception as error:
            logging.error(f"Could not publish to MQTT: {error}")
            raise


def setup_logging(debug_level):
    """Configure logging for the application."""
    logging.basicConfig(
        format="%(asctime)s - (%(levelname)s) %(message)s",
        level=debug_level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Prevent bleak log flooding
    bleak_logger = logging.getLogger("bleak")
    bleak_logger.setLevel(logging.INFO)


async def main(config: Config, publisher: MQTTPublisher):
    stop_event = asyncio.Event()
    old_measure = None

    def callback(device, advertising_data):
        nonlocal old_measure
        if device.address.lower() != config.miscale_mac:
            return

        logging.debug(f"miscale found, with advertising_data: {advertising_data}")

        # Try Xiaomi V2 Scale
        try:
            raw_hex = binascii.b2a_hex(
                advertising_data.service_data["0000181b-0000-1000-8000-00805f9b34fb"]
            ).decode("ascii")
            logging.debug(
                "miscale v2 found (service data: 0000181b-0000-1000-8000-00805f9b34fb)"
            )
            parsed = parse_v2_service_data(raw_hex)
            if parsed:
                current_measure = {
                    "unit": parsed["unit"],
                    "timestamp": datetime.now(),
                    "impedance": parsed["impedance"],
                    "weight": parsed["weight"],
                }
                if should_ignore_measurement(current_measure, old_measure):
                    logging.debug(
                        "skipping sending value because it is too close to old measure"
                    )
                else:
                    publisher.publish_weight(
                        round(parsed["weight"], 2),
                        parsed["unit"],
                        datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        parsed["has_impedance"],
                        parsed["impedance"],
                    )
                    old_measure = current_measure
        except Exception as exception:
            logging.debug(exception)

        # Try Xiaomi V1 Scale
        try:
            raw_hex = binascii.b2a_hex(
                advertising_data.service_data["0000181d-0000-1000-8000-00805f9b34fb"]
            ).decode("ascii")
            logging.debug(
                "miscale v1 found (service data: 0000181d-0000-1000-8000-00805f9b34fb)"
            )
            parsed = parse_v1_service_data(raw_hex)
            if parsed:
                logging.debug(f"continue: unit detected {parsed['unit']}")
                current_measure = {
                    "unit": parsed["unit"],
                    "timestamp": datetime.now(),
                    "weight": parsed["weight"],
                }
                logging.debug(
                    f"current_measure: unit: {current_measure['unit']}, "
                    f"timestamp: {current_measure['timestamp'].isoformat()}, "
                    f"weight: {current_measure['weight']}"
                )
                if old_measure:
                    logging.debug(
                        f"OLD_MEASURE: unit: {old_measure['unit']}, "
                        f"timestamp: {old_measure['timestamp'].isoformat()}, "
                        f"weight: {old_measure['weight']}"
                    )
                else:
                    logging.debug("OLD_MEASURE is None")
                if should_ignore_measurement(current_measure, old_measure):
                    logging.debug(
                        "skipping sending value because it is too close to old measure"
                    )
                else:
                    publisher.publish_weight(
                        round(parsed["weight"], 2),
                        parsed["unit"],
                        datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        False,
                        "0",
                    )
                    old_measure = current_measure
            else:
                logging.debug("skipping: no unit detected")
        except Exception as exception:
            logging.debug(exception)

    async with BleakScanner(callback, device=config.hci_dev):
        await stop_event.wait()


if __name__ == "__main__":
    os.system("clear")
    try:
        logging.info("-------------------------------------")
        logging.info(f"Starting Xiaomi mi Scale v{VERSION}...")
        config = load_config()
        setup_logging(config.debug_level)
        logging.info(f"Logging Level Set to {config.debug_level}...")
        logging.info("Config Loaded...")
    except FileNotFoundError as error:
        setup_logging(DEFAULT_DEBUG_LEVEL)
        logging.error(f"options.json file missing... {error}")
        raise

    publisher = MQTTPublisher(config)

    if config.mqtt_discovery:
        publisher.publish_discovery()

    logging.info("-------------------------------------")
    logging.info("Initialization Completed, Waiting for Scale...")
    try:
        asyncio.run(main(config, publisher))
    except Exception as error:
        logging.error(f"Unable to connect to Bluetooth: {error}")
