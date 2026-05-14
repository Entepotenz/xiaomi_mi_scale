"""Tests for configuration loading and MQTT publisher."""

import json
import pytest
from unittest.mock import patch, MagicMock
from collections import namedtuple

from Xiaomi_Scale import Config, load_config, MQTTPublisher, custom_user_decoder


@pytest.fixture
def minimal_config_data():
    """Minimal valid config data."""
    return {
        "options": {
            "MISCALE_MAC": "AA:BB:CC:DD:EE:FF",
            "MQTT_HOST": "192.168.1.100",
            "USERS": [
                {
                    "NAME": "Bob",
                    "GT": 70,
                    "LT": 110,
                    "SEX": "male",
                    "HEIGHT": 178,
                    "DOB": "1989-03-22",
                }
            ],
        }
    }


@pytest.fixture
def full_config_data():
    """Full config data with all options."""
    return {
        "options": {
            "MISCALE_MAC": "AA:BB:CC:DD:EE:FF",
            "MQTT_HOST": "192.168.1.100",
            "MQTT_PORT": 1883,
            "MQTT_USERNAME": "admin",
            "MQTT_PASSWORD": "secret",
            "MQTT_PREFIX": "myscale",
            "MQTT_RETAIN": False,
            "MQTT_DISCOVERY": True,
            "MQTT_DISCOVERY_PREFIX": "homeassistant",
            "MQTT_TLS_CACERTS": None,
            "MQTT_TLS_INSECURE": None,
            "HCI_DEV": "hci1",
            "BLUEPY_PASSIVE_SCAN": True,
            "DEBUG_LEVEL": "DEBUG",
            "USERS": [
                {
                    "NAME": "Alice",
                    "GT": 40,
                    "LT": 70,
                    "SEX": "female",
                    "HEIGHT": 165,
                    "DOB": "1994-05-15",
                },
                {
                    "NAME": "Bob",
                    "GT": 70,
                    "LT": 110,
                    "SEX": "male",
                    "HEIGHT": 178,
                    "DOB": "1989-03-22",
                },
            ],
        }
    }


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.mqtt_port == 1883
        assert config.mqtt_username == "username"
        assert config.mqtt_password is None
        assert config.mqtt_prefix == "miscale"
        assert config.mqtt_retain is True
        assert config.mqtt_discovery is True
        assert config.hci_dev == "hci0"
        assert config.users == []


class TestLoadConfig:
    def test_minimal_config(self, tmp_path, minimal_config_data):
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))

        config = load_config(str(config_file))

        assert config.miscale_mac == "AA:BB:CC:DD:EE:FF"
        assert config.mqtt_host == "192.168.1.100"
        assert len(config.users) == 1
        assert config.users[0].NAME == "Bob"

    def test_full_config(self, tmp_path, full_config_data):
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(full_config_data))

        config = load_config(str(config_file))

        assert config.miscale_mac == "AA:BB:CC:DD:EE:FF"
        assert config.mqtt_host == "192.168.1.100"
        assert config.mqtt_port == 1883
        assert config.mqtt_username == "admin"
        assert config.mqtt_password == "secret"
        assert config.mqtt_prefix == "myscale"
        assert config.mqtt_retain is False
        assert config.mqtt_discovery is True
        assert config.hci_dev == "hci1"
        assert config.bluepy_passive_scan is True
        assert config.debug_level == "DEBUG"
        assert len(config.users) == 2

    def test_missing_mac_raises(self, tmp_path):
        config_file = tmp_path / "options.json"
        config_file.write_text(
            json.dumps({"options": {"MQTT_HOST": "localhost", "USERS": []}})
        )

        with pytest.raises(ValueError, match="MAC Address"):
            load_config(str(config_file))

    def test_missing_mqtt_host_raises(self, tmp_path):
        config_file = tmp_path / "options.json"
        config_file.write_text(
            json.dumps({"options": {"MISCALE_MAC": "AA:BB:CC:DD:EE:FF", "USERS": []}})
        )

        with pytest.raises(ValueError, match="MQTT Host"):
            load_config(str(config_file))

    def test_invalid_debug_level_defaults(self, tmp_path, minimal_config_data):
        minimal_config_data["options"]["DEBUG_LEVEL"] = "INVALID"
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))

        config = load_config(str(config_file))
        assert config.debug_level == "INFO"

    def test_port_converted_from_string(self, tmp_path, minimal_config_data):
        minimal_config_data["options"]["MQTT_PORT"] = "8883"
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))

        config = load_config(str(config_file))
        assert config.mqtt_port == 8883

    def test_tls_config_with_cacerts(self, tmp_path, minimal_config_data):
        minimal_config_data["options"]["MQTT_TLS_CACERTS"] = "/path/to/ca.crt"
        minimal_config_data["options"]["MQTT_TLS_INSECURE"] = True
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))

        config = load_config(str(config_file))
        assert config.mqtt_tls == {"ca_certs": "/path/to/ca.crt", "insecure": True}

    def test_tls_none_when_placeholder(self, tmp_path, minimal_config_data):
        minimal_config_data["options"]["MQTT_TLS_CACERTS"] = "Path to CA Cert File"
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))

        config = load_config(str(config_file))
        assert config.mqtt_tls is None

    def test_user_gt_greater_than_lt_raises(self, tmp_path):
        config_data = {
            "options": {
                "MISCALE_MAC": "AA:BB:CC:DD:EE:FF",
                "MQTT_HOST": "localhost",
                "USERS": [
                    {
                        "NAME": "Bad",
                        "GT": 100,
                        "LT": 50,
                        "SEX": "male",
                        "HEIGHT": 170,
                        "DOB": "1990-01-01",
                    }
                ],
            }
        }
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError, match="GT can not be larger than LT"):
            load_config(str(config_file))

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path.json")


class TestMQTTPublisher:
    def test_publish_weight_no_match(self, minimal_config_data, tmp_path):
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))
        config = load_config(str(config_file))
        publisher = MQTTPublisher(config)

        with patch("Xiaomi_Scale.publish") as mock_publish:
            # Weight 50 doesn't match Bob's range (70-110)
            publisher.publish_weight(
                50.0, "kg", "2026-01-01T00:00:00+00:00", False, "0"
            )
            mock_publish.single.assert_not_called()

    def test_publish_weight_with_match(self, minimal_config_data, tmp_path):
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))
        config = load_config(str(config_file))
        publisher = MQTTPublisher(config)

        with patch("Xiaomi_Scale.publish") as mock_publish:
            publisher.publish_weight(
                80.0, "kg", "2026-01-01T00:00:00+00:00", False, "0"
            )
            mock_publish.single.assert_called_once()
            call_args = mock_publish.single.call_args
            assert call_args[0][0] == "miscale/Bob/weight"
            # Verify the message is valid JSON
            msg = json.loads(call_args[0][1])
            assert msg["weight"] == 80.0
            assert msg["weight_unit"] == "kg"
            assert "bmi" in msg

    def test_publish_discovery(self, minimal_config_data, tmp_path):
        config_file = tmp_path / "options.json"
        config_file.write_text(json.dumps(minimal_config_data))
        config = load_config(str(config_file))
        publisher = MQTTPublisher(config)

        with patch("Xiaomi_Scale.publish") as mock_publish:
            publisher.publish_discovery()
            mock_publish.single.assert_called_once()
            call_args = mock_publish.single.call_args
            assert "Bob" in call_args[0][0]
            msg = json.loads(call_args[0][1])
            assert msg["name"] == "Bob Weight"
