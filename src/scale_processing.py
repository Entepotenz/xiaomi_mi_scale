"""Pure business logic extracted from Xiaomi_Scale.py for testability.

This module contains functions that process scale measurements without
any dependency on MQTT, BLE, or configuration globals.
"""

from datetime import datetime, timedelta

import Xiaomi_Scale_Body_Metrics


def check_weight(user, weight):
    """Check if a weight measurement falls within a user's configured range."""
    return weight > user.GT and weight < user.LT


def get_age(dob_string):
    """Calculate age in years from a date-of-birth string (YYYY-MM-DD)."""
    d1 = datetime.strptime(dob_string, "%Y-%m-%d")
    d2 = datetime.strptime(datetime.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
    return abs((d2 - d1).days) / 365


def match_user(users, weight):
    """Find the first user whose weight range contains the given weight."""
    for user in users:
        if check_weight(user, weight):
            return user
    return None


def convert_weight_to_kg(weight, unit):
    """Convert weight from the given unit to kilograms."""
    if unit == "lbs":
        return round(weight * 0.4536, 2)
    if unit == "jin":
        return round(weight * 0.5, 2)
    return weight


def build_metrics_message(weight, unit, mitdatetime, has_impedance, impedance, user):
    """Build the MQTT message payload as a dict from a scale measurement.

    Returns the message dict or None if no user matched.
    """
    calcweight = convert_weight_to_kg(weight, unit)
    height = user.HEIGHT
    age = get_age(user.DOB)
    sex = user.SEX.lower()

    lib = Xiaomi_Scale_Body_Metrics.bodyMetrics(calcweight, height, age, sex, 0)
    message = {
        "weight": round(weight, 2),
        "weight_unit": unit,
        "bmi": round(lib.getBMI(), 2),
        "basal_metabolism": round(lib.getBMR(), 2),
        "visceral_fat": round(lib.getVisceralFat(), 2),
    }

    if has_impedance:
        lib = Xiaomi_Scale_Body_Metrics.bodyMetrics(
            calcweight, height, age, sex, int(impedance)
        )
        bodyscale = [
            "Obese",
            "Overweight",
            "Thick-set",
            "Lack-exercise",
            "Balanced",
            "Balanced-muscular",
            "Skinny",
            "Balanced-skinny",
            "Skinny-muscular",
        ]
        message["lean_body_mass"] = round(lib.getLBMCoefficient(), 2)
        message["body_fat"] = round(lib.getFatPercentage(), 2)
        message["water"] = round(lib.getWaterPercentage(), 2)
        message["bone_mass"] = round(lib.getBoneMass(), 2)
        message["muscle_mass"] = round(lib.getMuscleMass(), 2)
        message["protein"] = round(lib.getProteinPercentage(), 2)
        message["body_type"] = bodyscale[lib.getBodyType()]
        message["metabolic_age"] = round(lib.getMetabolicAge())
        message["impedance"] = int(impedance)

    message["timestamp"] = mitdatetime
    return message


def should_ignore_measurement(
    current_measurement, previous_measurement, max_timedelta=timedelta(hours=1)
):
    """Determine if a measurement should be ignored as a duplicate.

    Returns True if the measurement is too close to the previous one
    (same unit, within time window, and no significant data change).
    """
    if not previous_measurement:
        return False

    is_unit_equals = current_measurement["unit"] == previous_measurement["unit"]
    is_timedelta_exceeded = (
        previous_measurement["timestamp"] - current_measurement["timestamp"]
    ) >= max_timedelta

    is_measured_data_delta_significant = False
    if "impedance" in current_measurement.keys():
        is_measured_data_delta_significant = (
            round(current_measurement["weight"], 2)
            + int(current_measurement["impedance"])
        ) != (
            round(previous_measurement["weight"], 2)
            + int(previous_measurement["impedance"])
        )
    else:
        is_measured_data_delta_significant = round(
            current_measurement["weight"], 2
        ) != round(previous_measurement["weight"], 2)

    if not is_unit_equals:
        return False
    elif is_timedelta_exceeded:
        return False
    elif is_measured_data_delta_significant:
        return False
    else:
        return True


def parse_v2_service_data(raw_hex):
    """Parse Xiaomi V2 scale service data from hex string.

    Returns a dict with keys: unit, weight, impedance, has_impedance, is_stabilized
    or None if data cannot be parsed.
    """
    data = "1b18" + raw_hex
    data2 = bytes.fromhex(data[4:])
    ctrl_byte1 = data2[1]
    is_stabilized = bool(ctrl_byte1 & (1 << 5))
    has_impedance = bool(ctrl_byte1 & (1 << 1))

    measunit = data[4:6]
    measured = int((data[28:30] + data[26:28]), 16) * 0.01
    unit = ""
    if measunit == "03":
        unit = "lbs"
    if measunit == "02":
        unit = "kg"
        measured = measured / 2
    impedance = str(int((data[24:26] + data[22:24]), 16))

    if not unit or not is_stabilized:
        return None

    return {
        "unit": unit,
        "weight": measured,
        "impedance": impedance,
        "has_impedance": has_impedance,
        "is_stabilized": is_stabilized,
    }


def parse_v1_service_data(raw_hex):
    """Parse Xiaomi V1 scale service data from hex string.

    Returns a dict with keys: unit, weight
    or None if data cannot be parsed.
    """
    data = "1d18" + raw_hex
    measunit = data[4:6]
    measured = int((data[8:10] + data[6:8]), 16) * 0.01
    unit = ""
    if measunit.startswith(("03", "a3")):
        unit = "lbs"
    if measunit.startswith(("12", "b2")):
        unit = "jin"
    if measunit.startswith(("22", "a2", "02")):
        unit = "kg"
        measured = measured / 2

    if not unit:
        return None

    return {
        "unit": unit,
        "weight": measured,
    }
