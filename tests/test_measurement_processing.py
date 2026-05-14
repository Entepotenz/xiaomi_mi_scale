"""Integration tests for measurement processing logic.

Tests the full pipeline from raw BLE data through user matching,
weight conversion, metric computation, and message building.
"""

from collections import namedtuple
from datetime import datetime, timedelta

import pytest

from scale_processing import (
    build_metrics_message,
    check_weight,
    convert_weight_to_kg,
    get_age,
    match_user,
    parse_v1_service_data,
    parse_v2_service_data,
    should_ignore_measurement,
)


def make_user(name, gt, lt, sex, height, dob):
    User = namedtuple("User", ["NAME", "GT", "LT", "SEX", "HEIGHT", "DOB"])
    return User(NAME=name, GT=gt, LT=lt, SEX=sex, HEIGHT=height, DOB=dob)


@pytest.fixture
def users():
    return [
        make_user("Alice", 40, 70, "female", 165, "1994-05-15"),
        make_user("Bob", 70, 110, "male", 178, "1989-03-22"),
    ]


class TestCheckWeight:
    def test_weight_in_range(self):
        user = make_user("Test", 50, 90, "male", 170, "1990-01-01")
        assert check_weight(user, 75) is True

    def test_weight_below_range(self):
        user = make_user("Test", 50, 90, "male", 170, "1990-01-01")
        assert check_weight(user, 45) is False

    def test_weight_above_range(self):
        user = make_user("Test", 50, 90, "male", 170, "1990-01-01")
        assert check_weight(user, 95) is False

    def test_weight_at_lower_boundary(self):
        user = make_user("Test", 50, 90, "male", 170, "1990-01-01")
        # GT is exclusive (weight > user.GT)
        assert check_weight(user, 50) is False

    def test_weight_at_upper_boundary(self):
        user = make_user("Test", 50, 90, "male", 170, "1990-01-01")
        # LT is exclusive (weight < user.LT)
        assert check_weight(user, 90) is False

    def test_weight_just_inside_range(self):
        user = make_user("Test", 50, 90, "male", 170, "1990-01-01")
        assert check_weight(user, 50.1) is True
        assert check_weight(user, 89.9) is True


class TestGetAge:
    def test_age_calculation(self):
        # Use a fixed known date for deterministic testing
        age = get_age("1990-01-01")
        # Should be approximately 36 years old (test date is May 2026)
        assert 35 < age < 37

    def test_young_person(self):
        age = get_age("2010-01-01")
        assert 15 < age < 17

    def test_elderly_person(self):
        age = get_age("1940-01-01")
        assert 85 < age < 87


class TestMatchUser:
    def test_matches_first_user(self, users):
        matched = match_user(users, 55.0)
        assert matched.NAME == "Alice"

    def test_matches_second_user(self, users):
        matched = match_user(users, 85.0)
        assert matched.NAME == "Bob"

    def test_no_match(self, users):
        matched = match_user(users, 120.0)
        assert matched is None

    def test_matches_first_eligible(self, users):
        """If ranges overlap, returns first match."""
        # Create overlapping users
        overlapping = [
            make_user("First", 60, 90, "male", 175, "1990-01-01"),
            make_user("Second", 70, 100, "male", 180, "1985-01-01"),
        ]
        matched = match_user(overlapping, 80.0)
        assert matched.NAME == "First"


class TestConvertWeightToKg:
    def test_kg_passthrough(self):
        assert convert_weight_to_kg(75.0, "kg") == 75.0

    def test_lbs_conversion(self):
        result = convert_weight_to_kg(165.0, "lbs")
        assert abs(result - 74.84) < 0.01

    def test_jin_conversion(self):
        result = convert_weight_to_kg(150.0, "jin")
        assert result == 75.0


class TestBuildMetricsMessage:
    def test_basic_message_without_impedance(self, users):
        user = users[1]  # Bob
        msg = build_metrics_message(
            weight=80.0,
            unit="kg",
            mitdatetime="2026-01-15T10:30:00+00:00",
            has_impedance=False,
            impedance="0",
            user=user,
        )

        assert msg["weight"] == 80.0
        assert msg["weight_unit"] == "kg"
        assert "bmi" in msg
        assert "basal_metabolism" in msg
        assert "visceral_fat" in msg
        assert msg["timestamp"] == "2026-01-15T10:30:00+00:00"
        # Should NOT have impedance-dependent fields
        assert "body_fat" not in msg
        assert "muscle_mass" not in msg

    def test_message_with_impedance(self, users):
        user = users[1]  # Bob
        msg = build_metrics_message(
            weight=80.0,
            unit="kg",
            mitdatetime="2026-01-15T10:30:00+00:00",
            has_impedance=True,
            impedance="500",
            user=user,
        )

        assert msg["weight"] == 80.0
        assert "body_fat" in msg
        assert "muscle_mass" in msg
        assert "water" in msg
        assert "bone_mass" in msg
        assert "protein" in msg
        assert "body_type" in msg
        assert "metabolic_age" in msg
        assert msg["impedance"] == 500
        assert msg["lean_body_mass"] > 0

    def test_message_lbs_conversion(self, users):
        user = users[1]  # Bob
        msg = build_metrics_message(
            weight=176.0,
            unit="lbs",
            mitdatetime="2026-01-15T10:30:00+00:00",
            has_impedance=False,
            impedance="0",
            user=user,
        )

        assert msg["weight"] == 176.0
        assert msg["weight_unit"] == "lbs"
        # BMI should be calculated from kg-converted weight
        assert msg["bmi"] > 0

    def test_body_type_is_valid_string(self, users):
        user = users[1]  # Bob
        msg = build_metrics_message(
            weight=80.0,
            unit="kg",
            mitdatetime="2026-01-15T10:30:00+00:00",
            has_impedance=True,
            impedance="500",
            user=user,
        )

        valid_types = [
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
        assert msg["body_type"] in valid_types


class TestShouldIgnoreMeasurement:
    def test_no_previous_measurement(self):
        current = {"unit": "kg", "timestamp": datetime.now(), "weight": 75.0}
        assert should_ignore_measurement(current, None) is False

    def test_same_measurement_within_window(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0}
        previous = {
            "unit": "kg",
            "timestamp": now + timedelta(minutes=30),
            "weight": 75.0,
        }
        assert should_ignore_measurement(current, previous) is True

    def test_different_weight_not_ignored(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0}
        previous = {
            "unit": "kg",
            "timestamp": now + timedelta(minutes=5),
            "weight": 76.0,
        }
        assert should_ignore_measurement(current, previous) is False

    def test_different_unit_not_ignored(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0}
        previous = {
            "unit": "lbs",
            "timestamp": now + timedelta(minutes=5),
            "weight": 75.0,
        }
        assert should_ignore_measurement(current, previous) is False

    def test_exceeded_time_window_not_ignored(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0}
        previous = {"unit": "kg", "timestamp": now + timedelta(hours=2), "weight": 75.0}
        assert should_ignore_measurement(current, previous) is False

    def test_with_impedance_same_values_ignored(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0, "impedance": "500"}
        previous = {
            "unit": "kg",
            "timestamp": now + timedelta(minutes=5),
            "weight": 75.0,
            "impedance": "500",
        }
        assert should_ignore_measurement(current, previous) is True

    def test_with_impedance_different_values_not_ignored(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0, "impedance": "500"}
        previous = {
            "unit": "kg",
            "timestamp": now + timedelta(minutes=5),
            "weight": 75.0,
            "impedance": "510",
        }
        assert should_ignore_measurement(current, previous) is False

    def test_custom_time_window(self):
        now = datetime.now()
        current = {"unit": "kg", "timestamp": now, "weight": 75.0}
        previous = {
            "unit": "kg",
            "timestamp": now + timedelta(minutes=20),
            "weight": 75.0,
        }
        # With 15 minute window, should NOT be ignored (timedelta exceeded)
        assert (
            should_ignore_measurement(
                current, previous, max_timedelta=timedelta(minutes=15)
            )
            is False
        )


class TestParseV2ServiceData:
    def test_valid_kg_stabilized_data(self):
        # Construct a valid V2 payload:
        # After "1b18" prefix is stripped by function, we need raw_hex that when
        # prepended with "1b18" gives valid structure.
        # data[4:6] = measunit, needs to be "02" for kg
        # data2[1] = ctrlByte1, needs bit 5 set (stabilized) = 0x20
        # Let's build: "1b18" + raw_hex -> data
        # raw_hex starts at data[4:]
        # data2 = bytes.fromhex(data[4:]) -> data2 = bytes.fromhex(raw_hex)
        # data2[1] = ctrlByte1 -> raw_hex[2:4] should be "22" (bit 5 set = 0x20, bit 1 set = 0x02 for impedance)
        # measunit = data[4:6] = raw_hex[0:2] = "02" for kg
        # impedance at data[22:26] -> raw_hex[18:22]
        # weight at data[26:30] -> raw_hex[22:26]

        # Build a minimal 13-byte (26 hex chars) raw_hex:
        # [0:2] = "02" (measunit kg)
        # [2:4] = "22" (ctrlByte1: stabilized + impedance)
        # [4:18] = "00000000000000" (padding)
        # [18:22] = "f401" (impedance: 0x01f4 = 500, little-endian)
        # [22:26] = "204e" (weight: 0x4e20 = 20000 -> 200.00 * 0.01 / 2 = 100.0 kg... let's use different)
        # weight = int(data[28:30] + data[26:28], 16) * 0.01
        # data[26:28] = raw_hex[22:24], data[28:30] = raw_hex[24:26]
        # For 75 kg: need raw value 15000 (75*2/0.01=15000) = 0x3A98
        # raw_hex[24:26] + raw_hex[22:24] in little-endian = "983a" -> raw_hex[22:26] = "3a98" NO
        # Actually: int((data[28:30] + data[26:28]), 16) = int(raw_hex[24:26] + raw_hex[22:24], 16)
        # We want int("XX" + "YY", 16) * 0.01 / 2 = 75
        # So int("XXYY", 16) = 15000 = 0x3A98
        # raw_hex[24:26] = "3a", raw_hex[22:24] = "98"
        # So raw_hex[22:26] = "983a"

        raw_hex = "02" + "22" + "00000000000000" + "f4" + "01" + "98" + "3a"
        result = parse_v2_service_data(raw_hex)

        assert result is not None
        assert result["unit"] == "kg"
        assert result["is_stabilized"] is True
        assert result["has_impedance"] is True
        assert abs(result["weight"] - 75.0) < 0.01
        assert result["impedance"] == "500"

    def test_unstabilized_returns_none(self):
        # ctrlByte1 without bit 5 = 0x00
        raw_hex = "02" + "00" + "00000000000000" + "f4" + "01" + "98" + "3a"
        result = parse_v2_service_data(raw_hex)
        assert result is None

    def test_lbs_unit(self):
        # measunit = "03" for lbs, stabilized bit set
        raw_hex = "03" + "20" + "00000000000000" + "00" + "00" + "e8" + "03"
        result = parse_v2_service_data(raw_hex)
        assert result is not None
        assert result["unit"] == "lbs"


class TestParseV1ServiceData:
    def test_valid_kg_data(self):
        # data = "1d18" + raw_hex
        # measunit = data[4:6] = raw_hex[0:2]
        # measured = int((data[8:10] + data[6:8]), 16) * 0.01
        # data[6:8] = raw_hex[2:4], data[8:10] = raw_hex[4:6]
        # For kg: measunit starts with "22"
        # For 75 kg: int(raw_hex[4:6] + raw_hex[2:4], 16) * 0.01 / 2 = 75
        # int("XXYY", 16) = 15000 = 0x3A98
        # raw_hex[4:6] = "3a", raw_hex[2:4] = "98"
        raw_hex = "22" + "98" + "3a" + "0000000000"
        result = parse_v1_service_data(raw_hex)

        assert result is not None
        assert result["unit"] == "kg"
        assert abs(result["weight"] - 75.0) < 0.01

    def test_lbs_unit(self):
        # measunit starts with "03" for lbs
        # 165 lbs: int("XXYY", 16) * 0.01 = 165 -> 16500 = 0x4074
        # raw_hex[4:6] = "40", raw_hex[2:4] = "74"
        raw_hex = "03" + "74" + "40" + "0000000000"
        result = parse_v1_service_data(raw_hex)

        assert result is not None
        assert result["unit"] == "lbs"
        assert abs(result["weight"] - 165.0) < 0.01

    def test_jin_unit(self):
        # measunit starts with "12" for jin
        raw_hex = "12" + "dc" + "05" + "0000000000"
        result = parse_v1_service_data(raw_hex)

        assert result is not None
        assert result["unit"] == "jin"

    def test_unknown_unit_returns_none(self):
        raw_hex = "ff" + "98" + "3a" + "0000000000"
        result = parse_v1_service_data(raw_hex)
        assert result is None


class TestEndToEndMeasurementFlow:
    """Full integration test: parse BLE data -> match user -> build message."""

    def test_full_v2_flow(self):
        users = [
            make_user("Alice", 40, 70, "female", 165, "1994-05-15"),
            make_user("Bob", 70, 110, "male", 178, "1989-03-22"),
        ]

        # Simulate V2 scale data for ~80kg
        # weight = int(data[28:30] + data[26:28], 16) * 0.01 / 2
        # Want 80kg: value = 16000 = 0x3E80
        # raw_hex[24:26] = "3e", raw_hex[22:24] = "80"
        raw_hex = "02" + "22" + "00000000000000" + "f4" + "01" + "80" + "3e"
        parsed = parse_v2_service_data(raw_hex)
        assert parsed is not None

        user = match_user(users, parsed["weight"])
        assert user is not None
        assert user.NAME == "Bob"

        msg = build_metrics_message(
            weight=round(parsed["weight"], 2),
            unit=parsed["unit"],
            mitdatetime="2026-01-15T10:30:00+00:00",
            has_impedance=parsed["has_impedance"],
            impedance=parsed["impedance"],
            user=user,
        )

        assert msg["weight_unit"] == "kg"
        assert msg["bmi"] > 0
        assert "body_fat" in msg  # impedance was set
        assert "muscle_mass" in msg

    def test_full_v1_flow_no_impedance(self):
        users = [
            make_user("Alice", 40, 70, "female", 165, "1994-05-15"),
        ]

        # 60kg V1 data: int(raw_hex[4:6] + raw_hex[2:4], 16) * 0.01 / 2 = 60
        # value = 12000 = 0x2EE0
        # raw_hex[4:6] = "2e", raw_hex[2:4] = "e0"
        raw_hex = "22" + "e0" + "2e" + "0000000000"
        parsed = parse_v1_service_data(raw_hex)
        assert parsed is not None

        user = match_user(users, parsed["weight"])
        assert user is not None
        assert user.NAME == "Alice"

        msg = build_metrics_message(
            weight=round(parsed["weight"], 2),
            unit=parsed["unit"],
            mitdatetime="2026-01-15T10:30:00+00:00",
            has_impedance=False,
            impedance="0",
            user=user,
        )

        assert msg["weight_unit"] == "kg"
        assert "body_fat" not in msg  # no impedance
        assert msg["bmi"] > 0
