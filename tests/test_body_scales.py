"""Integration tests for bodyScales class.

Locks down the scale/threshold lookup behavior for all supported
age/height/weight/sex combinations.
"""

import pytest
from body_scales import bodyScales


class TestBMIScale:
    def test_xiaomi_bmi_scale(self):
        scales = bodyScales(30, 170, "male", 70)
        assert scales.getBMIScale() == [18.5, 25.0, 28.0, 32.0]

    def test_holtek_bmi_scale(self):
        scales = bodyScales(30, 170, "male", 70, scaleType="holtek")
        assert scales.getBMIScale() == [18.5, 25.0, 30.0]


class TestFatPercentageScale:
    @pytest.mark.parametrize(
        "age,expected_male,expected_female",
        [
            (10, [7.0, 16.0, 25.0, 30.0], [12.0, 21.0, 30.0, 34.0]),
            (13, [7.0, 16.0, 25.0, 30.0], [15.0, 24.0, 33.0, 37.0]),
            (15, [7.0, 16.0, 25.0, 30.0], [18.0, 27.0, 36.0, 40.0]),
            (17, [7.0, 16.0, 25.0, 30.0], [20.0, 28.0, 37.0, 41.0]),
            (30, [11.0, 17.0, 22.0, 27.0], [21.0, 28.0, 35.0, 40.0]),
            (50, [12.0, 18.0, 23.0, 28.0], [22.0, 29.0, 36.0, 41.0]),
            (70, [14.0, 20.0, 25.0, 30.0], [23.0, 30.0, 37.0, 42.0]),
        ],
    )
    def test_xiaomi_fat_scale_by_age(self, age, expected_male, expected_female):
        male_scales = bodyScales(age, 170, "male", 70)
        female_scales = bodyScales(age, 165, "female", 60)
        assert male_scales.getFatPercentageScale() == expected_male
        assert female_scales.getFatPercentageScale() == expected_female

    def test_holtek_fat_scale_young(self):
        scales = bodyScales(20, 170, "male", 70, scaleType="holtek")
        assert scales.getFatPercentageScale() == [8, 14, 21, 25]

    def test_holtek_fat_scale_middle(self):
        scales = bodyScales(35, 170, "male", 70, scaleType="holtek")
        assert scales.getFatPercentageScale() == [13, 17, 25, 28]


class TestMuscleMassScale:
    def test_xiaomi_tall_male(self):
        scales = bodyScales(30, 175, "male", 70)
        assert scales.getMuscleMassScale() == [49.4, 59.5]

    def test_xiaomi_medium_male(self):
        scales = bodyScales(30, 165, "male", 70)
        assert scales.getMuscleMassScale() == [44.0, 52.5]

    def test_xiaomi_short_male(self):
        scales = bodyScales(30, 155, "male", 70)
        assert scales.getMuscleMassScale() == [38.5, 46.6]

    def test_xiaomi_tall_female(self):
        scales = bodyScales(30, 165, "female", 60)
        assert scales.getMuscleMassScale() == [36.5, 42.6]

    def test_xiaomi_medium_female(self):
        scales = bodyScales(30, 155, "female", 60)
        assert scales.getMuscleMassScale() == [32.9, 37.6]

    def test_xiaomi_short_female(self):
        scales = bodyScales(30, 145, "female", 60)
        assert scales.getMuscleMassScale() == [29.1, 34.8]


class TestWaterPercentageScale:
    def test_xiaomi_male(self):
        scales = bodyScales(30, 170, "male", 70)
        assert scales.getWaterPercentageScale() == [55.0, 65.1]

    def test_xiaomi_female(self):
        scales = bodyScales(30, 165, "female", 60)
        assert scales.getWaterPercentageScale() == [45.0, 60.1]

    def test_holtek(self):
        scales = bodyScales(30, 170, "male", 70, scaleType="holtek")
        assert scales.getWaterPercentageScale() == [53, 67]


class TestVisceralFatScale:
    def test_scale_is_constant(self):
        scales = bodyScales(30, 170, "male", 70)
        assert scales.getVisceralFatScale() == [10.0, 15.0]


class TestBoneMassScale:
    def test_xiaomi_heavy_male(self):
        scales = bodyScales(30, 170, "male", 80)
        result = scales.getBoneMassScale()
        assert result == [2.0, 4.2]

    def test_xiaomi_medium_male(self):
        scales = bodyScales(30, 170, "male", 65)
        result = scales.getBoneMassScale()
        assert result == [1.9, 4.1]

    def test_xiaomi_light_male(self):
        scales = bodyScales(30, 170, "male", 50)
        result = scales.getBoneMassScale()
        assert result == [1.6, 3.9]

    def test_xiaomi_heavy_female(self):
        scales = bodyScales(30, 165, "female", 65)
        result = scales.getBoneMassScale()
        assert result == [1.8, 3.9]

    def test_xiaomi_medium_female(self):
        scales = bodyScales(30, 165, "female", 50)
        result = scales.getBoneMassScale()
        assert result == [1.5, 3.8]

    def test_xiaomi_light_female(self):
        scales = bodyScales(30, 165, "female", 40)
        result = scales.getBoneMassScale()
        assert result == [1.3, 3.6]


class TestBMRScale:
    def test_xiaomi_young_male(self):
        scales = bodyScales(25, 170, "male", 70)
        result = scales.getBMRScale()
        assert result == [70 * 21.6]

    def test_xiaomi_middle_male(self):
        scales = bodyScales(35, 170, "male", 70)
        result = scales.getBMRScale()
        assert result == [70 * 20.07]

    def test_xiaomi_older_male(self):
        scales = bodyScales(55, 170, "male", 70)
        result = scales.getBMRScale()
        assert result == [70 * 19.35]


class TestProteinPercentageScale:
    def test_constant(self):
        scales = bodyScales(30, 170, "male", 70)
        assert scales.getProteinPercentageScale() == [16, 20]


class TestIdealWeightScale:
    def test_xiaomi_male(self):
        scales = bodyScales(30, 170, "male", 70)
        bmi_scale = scales.getBMIScale()
        expected = [(bmi * 170) * 170 / 10000 for bmi in bmi_scale]
        assert scales.getIdealWeightScale() == expected


class TestBodyTypeScale:
    def test_returns_nine_types(self):
        scales = bodyScales(30, 170, "male", 70)
        result = scales.getBodyTypeScale()
        assert len(result) == 9
        assert "balanced" in result
        assert "obese" in result


class TestBodyScoreScale:
    def test_returns_four_thresholds(self):
        scales = bodyScales(30, 170, "male", 70)
        result = scales.getBodyScoreScale()
        assert result == [50.0, 60.0, 80.0, 90.0]
