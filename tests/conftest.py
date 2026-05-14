import pytest


@pytest.fixture
def male_profile():
    """Typical male user profile for testing."""
    return {
        "weight": 75.0,
        "height": 178,
        "age": 35,
        "sex": "male",
        "impedance": 500,
    }


@pytest.fixture
def female_profile():
    """Typical female user profile for testing."""
    return {
        "weight": 60.0,
        "height": 165,
        "age": 30,
        "sex": "female",
        "impedance": 450,
    }


@pytest.fixture
def elderly_male_profile():
    """Elderly male user profile for edge case testing."""
    return {
        "weight": 80.0,
        "height": 170,
        "age": 75,
        "sex": "male",
        "impedance": 550,
    }


@pytest.fixture
def young_female_profile():
    """Young female user profile for edge case testing."""
    return {
        "weight": 50.0,
        "height": 155,
        "age": 16,
        "sex": "female",
        "impedance": 400,
    }
