"""Integration tests for bodyMetrics class.

These tests lock down the current calculation behavior so that refactoring
doesn't introduce regressions. They test the full computation pipeline from
inputs through to final metric values.
"""

import pytest
from Xiaomi_Scale_Body_Metrics import bodyMetrics, MeasurementError


class TestBodyMetricsInitialization:
    def test_valid_inputs(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        assert lib.weight == 75.0
        assert lib.height == 178
        assert lib.age == 35
        assert lib.sex == "male"
        assert lib.impedance == 500

    def test_rejects_height_over_220(self):
        with pytest.raises(MeasurementError):
            bodyMetrics(70, 221, 30, "male", 500)

    def test_rejects_weight_under_10(self):
        with pytest.raises(MeasurementError):
            bodyMetrics(9, 170, 30, "male", 500)

    def test_rejects_weight_over_200(self):
        with pytest.raises(MeasurementError):
            bodyMetrics(201, 170, 30, "male", 500)

    def test_rejects_age_over_99(self):
        with pytest.raises(MeasurementError):
            bodyMetrics(70, 170, 100, "male", 500)

    def test_rejects_impedance_over_3000(self):
        with pytest.raises(MeasurementError):
            bodyMetrics(70, 170, 30, "male", 3001)

    def test_zero_impedance_accepted(self):
        lib = bodyMetrics(70, 170, 30, "male", 0)
        assert lib.impedance == 0


class TestBMI:
    def test_normal_bmi_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        bmi = lib.getBMI()
        # 75 / (1.78 * 1.78) ≈ 23.67
        assert 23.0 < bmi < 24.5

    def test_normal_bmi_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        bmi = lib.getBMI()
        # 60 / (1.65 * 1.65) ≈ 22.04
        assert 21.5 < bmi < 22.5

    def test_bmi_capped_at_minimum(self):
        # Very low weight relative to height
        lib = bodyMetrics(10, 220, 30, "male", 500)
        bmi = lib.getBMI()
        assert bmi >= 10

    def test_bmi_capped_at_maximum(self):
        # Very high weight relative to height
        lib = bodyMetrics(200, 90, 30, "male", 500)
        bmi = lib.getBMI()
        assert bmi <= 90


class TestBMR:
    def test_bmr_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        bmr = lib.getBMR()
        assert 500 <= bmr <= 10000
        # Male formula: 877.8 + 75*14.916 - 178*0.726 - 35*8.976
        expected = 877.8 + 75 * 14.916 - 178 * 0.726 - 35 * 8.976
        assert abs(bmr - expected) < 0.01

    def test_bmr_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        bmr = lib.getBMR()
        assert 500 <= bmr <= 10000
        # Female formula: 864.6 + 60*10.2036 - 165*0.39336 - 30*6.204
        expected = 864.6 + 60 * 10.2036 - 165 * 0.39336 - 30 * 6.204
        assert abs(bmr - expected) < 0.01

    def test_bmr_capped_minimum(self):
        # Very low weight
        lib = bodyMetrics(10, 220, 99, "male", 0)
        bmr = lib.getBMR()
        assert bmr >= 500


class TestFatPercentage:
    def test_fat_percentage_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        fat = lib.getFatPercentage()
        assert 5 <= fat <= 75

    def test_fat_percentage_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        fat = lib.getFatPercentage()
        assert 5 <= fat <= 75

    def test_fat_percentage_young_female(self, young_female_profile):
        lib = bodyMetrics(
            young_female_profile["weight"],
            young_female_profile["height"],
            young_female_profile["age"],
            young_female_profile["sex"],
            young_female_profile["impedance"],
        )
        fat = lib.getFatPercentage()
        assert 5 <= fat <= 75


class TestWaterPercentage:
    def test_water_percentage_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        water = lib.getWaterPercentage()
        assert 35 <= water <= 75

    def test_water_percentage_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        water = lib.getWaterPercentage()
        assert 35 <= water <= 75


class TestBoneMass:
    def test_bone_mass_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        bone = lib.getBoneMass()
        assert 0.5 <= bone <= 8

    def test_bone_mass_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        bone = lib.getBoneMass()
        assert 0.5 <= bone <= 8


class TestMuscleMass:
    def test_muscle_mass_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        muscle = lib.getMuscleMass()
        assert 10 <= muscle <= 120

    def test_muscle_mass_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        muscle = lib.getMuscleMass()
        assert 10 <= muscle <= 120


class TestVisceralFat:
    def test_visceral_fat_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        vfat = lib.getVisceralFat()
        assert 1 <= vfat <= 50

    def test_visceral_fat_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        vfat = lib.getVisceralFat()
        assert 1 <= vfat <= 50


class TestProteinPercentage:
    def test_protein_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        protein = lib.getProteinPercentage()
        assert 5 <= protein <= 32

    def test_protein_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        protein = lib.getProteinPercentage()
        assert 5 <= protein <= 32


class TestLBMCoefficient:
    def test_lbm_coefficient_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        lbm = lib.getLBMCoefficient()
        # Should be a positive value representing lean body mass
        assert lbm > 0

    def test_lbm_coefficient_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        lbm = lib.getLBMCoefficient()
        assert lbm > 0


class TestBodyType:
    def test_body_type_returns_valid_index(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        body_type = lib.getBodyType()
        assert 0 <= body_type <= 8

    def test_body_type_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        body_type = lib.getBodyType()
        assert 0 <= body_type <= 8


class TestMetabolicAge:
    def test_metabolic_age_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        met_age = lib.getMetabolicAge()
        assert 15 <= met_age <= 80

    def test_metabolic_age_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        met_age = lib.getMetabolicAge()
        assert 15 <= met_age <= 80


class TestIdealWeight:
    def test_ideal_weight_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        ideal = lib.getIdealWeight()
        # Male: (178 - 80) * 0.7 = 68.6
        assert abs(ideal - 68.6) < 0.01

    def test_ideal_weight_female(self, female_profile):
        lib = bodyMetrics(
            female_profile["weight"],
            female_profile["height"],
            female_profile["age"],
            female_profile["sex"],
            female_profile["impedance"],
        )
        ideal = lib.getIdealWeight()
        # Female: (165 - 70) * 0.6 = 57.0
        assert abs(ideal - 57.0) < 0.01


class TestFatMassToIdeal:
    def test_fat_mass_to_ideal_male(self, male_profile):
        lib = bodyMetrics(
            male_profile["weight"],
            male_profile["height"],
            male_profile["age"],
            male_profile["sex"],
            male_profile["impedance"],
        )
        result = lib.getFatMassToIdeal()
        assert result["type"] in ("to_gain", "to_lose")
        assert result["mass"] >= 0


class TestFullMetricsIntegration:
    """Integration tests that exercise the full metrics pipeline."""

    @pytest.mark.parametrize(
        "weight,height,age,sex,impedance",
        [
            (75, 178, 35, "male", 500),
            (60, 165, 30, "female", 450),
            (90, 180, 50, "male", 600),
            (55, 160, 25, "female", 400),
            (100, 185, 45, "male", 700),
            (45, 155, 20, "female", 380),
        ],
    )
    def test_all_metrics_computable(self, weight, height, age, sex, impedance):
        """Verifies that all metrics can be computed without errors for various inputs."""
        lib = bodyMetrics(weight, height, age, sex, impedance)

        # All these should return without error
        bmi = lib.getBMI()
        bmr = lib.getBMR()
        fat = lib.getFatPercentage()
        water = lib.getWaterPercentage()
        bone = lib.getBoneMass()
        muscle = lib.getMuscleMass()
        vfat = lib.getVisceralFat()
        protein = lib.getProteinPercentage()
        body_type = lib.getBodyType()
        met_age = lib.getMetabolicAge()
        lbm = lib.getLBMCoefficient()
        ideal = lib.getIdealWeight()
        fat_ideal = lib.getFatMassToIdeal()

        # Basic sanity assertions
        assert 10 <= bmi <= 90
        assert 500 <= bmr <= 10000
        assert 5 <= fat <= 75
        assert 35 <= water <= 75
        assert 0.5 <= bone <= 8
        assert 10 <= muscle <= 120
        assert 1 <= vfat <= 50
        assert 5 <= protein <= 32
        assert 0 <= body_type <= 8
        assert 15 <= met_age <= 80
        assert lbm > 0
        assert ideal > 0
        assert fat_ideal["type"] in ("to_gain", "to_lose")

    @pytest.mark.parametrize(
        "weight,height,age,sex,impedance",
        [
            (10, 90, 18, "male", 0),  # Minimum boundaries
            (200, 220, 99, "female", 3000),  # Maximum boundaries
        ],
    )
    def test_boundary_inputs(self, weight, height, age, sex, impedance):
        """Tests that boundary values don't crash."""
        lib = bodyMetrics(weight, height, age, sex, impedance)
        # Should not raise
        lib.getBMI()
        lib.getBMR()
        lib.getVisceralFat()
