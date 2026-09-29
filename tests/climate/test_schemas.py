"""
Unit tests for Climate Schemas and Pydantic validation contracts.
"""

import json
import unittest
from pydantic import ValidationError

from backend.climate.schemas import (
    ClimateMetrics,
    ClimateProfile,
    ClimateZone,
    CurrentWeather,
    DataConfidence,
    DataProvenance,
    DataQuality,
    DesignExtremes,
    HumidityData,
    Location,
    PassiveStrategy,
    PriorityLevel,
    SolarData,
    TemperatureProfile,
    WindData,
)


class TestClimateSchemas(unittest.TestCase):
    """Tests for Pydantic data schemas and field validators."""

    def test_valid_location(self):
        loc = Location(
            place_name="Leh, Ladakh",
            latitude=34.1526,
            longitude=77.5771,
            elevation=3524.0
        )
        self.assertEqual(loc.place_name, "Leh, Ladakh")
        self.assertAlmostEqual(loc.latitude, 34.1526)
        self.assertAlmostEqual(loc.longitude, 77.5771)
        self.assertEqual(loc.elevation, 3524.0)

    def test_invalid_latitude_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Location(place_name="Invalid", latitude=95.0, longitude=77.0)

        with self.assertRaises(ValidationError):
            Location(place_name="Invalid", latitude=-91.0, longitude=77.0)

    def test_invalid_longitude_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Location(place_name="Invalid", latitude=30.0, longitude=185.0)

        with self.assertRaises(ValidationError):
            Location(place_name="Invalid", latitude=30.0, longitude=-181.0)

    def test_wind_data_negative_speed_rejected(self):
        with self.assertRaises(ValidationError):
            WindData(average_speed=-1.5)

    def test_humidity_data_range_validation(self):
        valid = HumidityData(average_relative_humidity=55.0)
        self.assertEqual(valid.average_relative_humidity, 55.0)

        with self.assertRaises(ValidationError):
            HumidityData(average_relative_humidity=105.0)

        with self.assertRaises(ValidationError):
            HumidityData(average_relative_humidity=-5.0)

    def test_solar_data_negative_irradiance_rejected(self):
        with self.assertRaises(ValidationError):
            SolarData(GHI=-10.0)

    def test_climate_profile_roundtrip_serialization(self):
        loc = Location(place_name="Leh", latitude=34.15, longitude=77.58, elevation=3524.0)
        temp = ClimateMetrics(
            classification=ClimateZone.EXTREME_COLD,
            annual_mean_temperature=5.3,
            minimum_temperature=-28.3,
            maximum_temperature=34.8
        )
        solar = SolarData(GHI=239.7, annual_solar_ghi_kwh_m2=2100.0)
        wind = WindData(average_speed=3.8)
        humidity = HumidityData(average_relative_humidity=32.0)
        extremes = DesignExtremes(cold_extreme=-18.5, hot_extreme=26.0)
        quality = DataQuality(confidence=DataConfidence.HIGH, provenance=DataProvenance.HISTORICAL)

        profile = ClimateProfile(
            location=loc,
            climate=temp,
            solar=solar,
            wind=wind,
            humidity=humidity,
            design_extremes=extremes,
            data_quality=quality
        )

        dumped = profile.model_dump()
        self.assertIsInstance(dumped, dict)
        self.assertEqual(dumped["location"]["place_name"], "Leh")
        self.assertEqual(dumped["climate"]["classification"], "EXTREME COLD")

        # Reload from dumped
        reloaded = ClimateProfile.model_validate(dumped)
        self.assertEqual(reloaded.location.place_name, profile.location.place_name)
        self.assertEqual(reloaded.climate.classification, ClimateZone.EXTREME_COLD)

    def test_passive_strategy_contract(self):
        strat = PassiveStrategy(
            climate_mode=ClimateZone.EXTREME_COLD,
            primary_strategy="Solar heat capture",
            secondary_strategies=["Thermal mass", "Airlock"],
            solar_capture=PriorityLevel.HIGH,
            thermal_mass=PriorityLevel.HIGH,
            insulation_priority=PriorityLevel.HIGH,
            ventilation_strategy="CONTROLLED_MINIMAL",
            shading_strategy="MINIMAL",
            opening_strategy="MINIMIZED",
            airlock=True,
            thermal_buffer=True,
            explanation="Extreme cold test explanation"
        )
        self.assertTrue(strat.airlock)
        self.assertEqual(strat.solar_capture, PriorityLevel.HIGH)
        self.assertEqual(strat.insulation_priority, PriorityLevel.HIGH)


if __name__ == "__main__":
    unittest.main()
