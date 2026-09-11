"""
Unit tests for ThermoShelter AI Data Validation Suite.
"""

from scripts.validate_data import DataValidator

def test_data_validator_locations():
    validator = DataValidator()
    assert validator.validate_locations() is True
    assert len(validator.errors) == 0
    assert validator.stats.get("locations_count", 0) >= 7

def test_data_validator_weather():
    validator = DataValidator()
    assert validator.validate_weather() is True
    assert len(validator.errors) == 0
    assert validator.stats.get("weather_rows", 0) >= 1000

def test_data_validator_materials():
    validator = DataValidator()
    assert validator.validate_materials() is True
    assert len(validator.errors) == 0
    assert validator.stats.get("materials_count", 0) >= 15

def test_data_validator_glazing():
    validator = DataValidator()
    assert validator.validate_glazing() is True
    assert len(validator.errors) == 0
    assert validator.stats.get("glazing_count", 0) >= 5

def test_data_validator_shelters():
    validator = DataValidator()
    assert validator.validate_shelters() is True
    assert len(validator.errors) == 0
    assert validator.stats.get("shelters_count", 0) >= 4

def test_data_validator_run_all():
    validator = DataValidator()
    assert validator.run_all() is True
    assert len(validator.errors) == 0
