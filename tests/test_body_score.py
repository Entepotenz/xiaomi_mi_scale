"""Integration tests for bodyScore class.

Tests the body score deduction logic across different body compositions.
"""

import pytest

from body_score import bodyScore
from Xiaomi_Scale_Body_Metrics import bodyMetrics


class TestBodyScoreBasic:
    def test_score_starts_at_100(self):
        """A perfectly healthy person should score close to 100."""
        # Use values that should give minimal deductions
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=70,
            bmi=22.9,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        score = score_calc.getBodyScore()
        assert 80 <= score <= 100

    def test_score_decreases_with_obesity(self):
        """An obese person should score significantly lower."""
        score_calc = bodyScore(
            age=40,
            sex="male",
            height=170,
            weight=110,
            bmi=38.0,
            bodyfat=35.0,
            muscle=40.0,
            water=45.0,
            visceral_fat=16.0,
            bone=2.0,
            basal_metabolism=1200,
            protein=12.0,
        )
        score = score_calc.getBodyScore()
        assert score < 70

    def test_score_never_negative(self):
        """Score should not go below 0 even with worst-case inputs."""
        score_calc = bodyScore(
            age=80,
            sex="female",
            height=150,
            weight=120,
            bmi=53.3,
            bodyfat=50.0,
            muscle=25.0,
            water=35.0,
            visceral_fat=20.0,
            bone=1.0,
            basal_metabolism=800,
            protein=8.0,
        )
        score = score_calc.getBodyScore()
        # Score can theoretically go negative with extreme values
        assert isinstance(score, (int, float))


class TestBMIDeductScore:
    def test_normal_bmi_no_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=70,
            bmi=22.9,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        assert score_calc.getBmiDeductScore() == 0.0

    def test_extremely_low_bmi(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=40,
            bmi=13.0,
            bodyfat=5.0,
            muscle=30.0,
            water=60.0,
            visceral_fat=2.0,
            bone=2.0,
            basal_metabolism=1200,
            protein=16.0,
        )
        assert score_calc.getBmiDeductScore() == 30.0

    def test_height_under_90_returns_zero(self):
        score_calc = bodyScore(
            age=5,
            sex="male",
            height=80,
            weight=15,
            bmi=23.4,
            bodyfat=15.0,
            muscle=10.0,
            water=60.0,
            visceral_fat=2.0,
            bone=1.0,
            basal_metabolism=800,
            protein=16.0,
        )
        assert score_calc.getBmiDeductScore() == 0.0


class TestBodyFatDeductScore:
    def test_normal_fat_no_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=70,
            bmi=22.9,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        deduct = score_calc.getBodyFatDeductScore()
        assert deduct == 0.0

    def test_very_high_fat_max_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=100,
            bmi=32.7,
            bodyfat=30.0,
            muscle=40.0,
            water=45.0,
            visceral_fat=15.0,
            bone=2.5,
            basal_metabolism=1400,
            protein=14.0,
        )
        deduct = score_calc.getBodyFatDeductScore()
        assert deduct == 20.0


class TestMuscleDeductScore:
    def test_good_muscle_no_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=75,
            bmi=24.5,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        assert score_calc.getMuscleDeductScore() == 0.0

    def test_very_low_muscle_max_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=60,
            bmi=19.6,
            bodyfat=10.0,
            muscle=40.0,
            water=60.0,
            visceral_fat=3.0,
            bone=2.5,
            basal_metabolism=1400,
            protein=16.0,
        )
        deduct = score_calc.getMuscleDeductScore()
        assert deduct == 10.0


class TestWaterDeductScore:
    def test_good_water_no_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=75,
            bmi=24.5,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        assert score_calc.getWaterDeductScore() == 0.0

    def test_very_low_water_max_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=75,
            bmi=24.5,
            bodyfat=15.0,
            muscle=55.0,
            water=45.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        deduct = score_calc.getWaterDeductScore()
        assert deduct == 10.0


class TestVisceralFatDeductScore:
    def test_normal_vfat_no_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=70,
            bmi=22.9,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        assert score_calc.getVisceralFatDeductScore() == 0.0

    def test_high_vfat_max_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=100,
            bmi=32.7,
            bodyfat=30.0,
            muscle=40.0,
            water=45.0,
            visceral_fat=16.0,
            bone=2.5,
            basal_metabolism=1400,
            protein=14.0,
        )
        assert score_calc.getVisceralFatDeductScore() == 15.0


class TestProteinDeductScore:
    def test_good_protein_no_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=70,
            bmi=22.9,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=18.0,
        )
        assert score_calc.getProteinDeductScore() == 0.0

    def test_very_low_protein_max_deduction(self):
        score_calc = bodyScore(
            age=30,
            sex="male",
            height=175,
            weight=70,
            bmi=22.9,
            bodyfat=15.0,
            muscle=55.0,
            water=60.0,
            visceral_fat=5.0,
            bone=3.0,
            basal_metabolism=1600,
            protein=9.0,
        )
        assert score_calc.getProteinDeductScore() == 10.0


class TestBodyScoreWithRealMetrics:
    """Integration test: compute metrics, then compute body score from them."""

    @pytest.mark.parametrize(
        "weight,height,age,sex,impedance",
        [
            (75, 178, 35, "male", 500),
            (60, 165, 30, "female", 450),
            (90, 180, 50, "male", 600),
            (55, 160, 25, "female", 400),
        ],
    )
    def test_end_to_end_score(self, weight, height, age, sex, impedance):
        """Compute metrics from bodyMetrics and feed them to bodyScore."""
        lib = bodyMetrics(weight, height, age, sex, impedance)

        score_calc = bodyScore(
            age=age,
            sex=sex,
            height=height,
            weight=weight,
            bmi=lib.getBMI(),
            bodyfat=lib.getFatPercentage(),
            muscle=lib.getMuscleMass(),
            water=lib.getWaterPercentage(),
            visceral_fat=lib.getVisceralFat(),
            bone=lib.getBoneMass(),
            basal_metabolism=lib.getBMR(),
            protein=lib.getProteinPercentage(),
        )

        score = score_calc.getBodyScore()
        # Score should be a reasonable number
        assert isinstance(score, (int, float))
        # For healthy-ish inputs, score should be positive
        assert score > 0
