"""
Unit tests for ClimateClassifier across all 6 project climate zones.
"""

import unittest
from backend.climate.climate_classifier import ClimateClassifier
from backend.climate.schemas import (
    ClimateZone,
    DesignExtremes,
    HumidityData,
    SolarData,
    TemperatureProfile,
    WindData,
)


class TestClimateClassifier(unittest.TestCase):
    """Tests that physical climate attributes correctly map to the 6 canonical climate zones."""

    def test_extreme_cold_classification(self):
        temp = TemperatureProfile(annual_mean_temperature=5.3, minimum_temperature=-28.3, maximum_temperature=34.8)
        hum = HumidityData(average_relative_humidity=32.0)
        ext = DesignExtremes(cold_extreme=-18.5, hot_extreme=26.0, heating_degree_days_18c=4850.0)
        res = ClimateClassifier.classify(temp, hum, ext)

        self.assertEqual(res.zone, ClimateZone.EXTREME_COLD)
        self.assertIn("severe alpine/high-altitude cold", res.explanation)
        self.assertGreater(len(res.primary_criteria), 0)

    def test_cold_classification(self):
        temp = TemperatureProfile(annual_mean_temperature=13.5, minimum_temperature=-7.0, maximum_temperature=33.0)
        hum = HumidityData(average_relative_humidity=65.0)
        ext = DesignExtremes(cold_extreme=-4.0, hot_extreme=31.0, heating_degree_days_18c=2650.0)
        res = ClimateClassifier.classify(temp, hum, ext)

        self.assertEqual(res.zone, ClimateZone.COLD)
        self.assertIn("cold mountain or valley", res.explanation)

    def test_hot_dry_classification(self):
        temp = TemperatureProfile(annual_mean_temperature=27.2, minimum_temperature=2.5, maximum_temperature=49.0, diurnal_range_mean=15.4)
        hum = HumidityData(average_relative_humidity=28.5)
        ext = DesignExtremes(cold_extreme=7.0, hot_extreme=46.0, cooling_degree_days_18c=3400.0)
        res = ClimateClassifier.classify(temp, hum, ext)

        self.assertEqual(res.zone, ClimateZone.HOT_DRY)
        self.assertIn("arid desert", res.explanation)

    def test_hot_humid_classification(self):
        temp = TemperatureProfile(annual_mean_temperature=28.6, minimum_temperature=18.2, maximum_temperature=42.8, diurnal_range_mean=7.8)
        hum = HumidityData(average_relative_humidity=74.0)
        ext = DesignExtremes(cold_extreme=20.0, hot_extreme=39.0, cooling_degree_days_18c=3600.0)
        res = ClimateClassifier.classify(temp, hum, ext)

        self.assertEqual(res.zone, ClimateZone.HOT_HUMID)
        self.assertIn("tropical warm-humid", res.explanation)

    def test_variable_classification(self):
        # Delhi: severe winter cold waves (5°C) and extreme hot summers (43.5°C) -> swing 38.5°C
        temp = TemperatureProfile(annual_mean_temperature=25.0, minimum_temperature=3.0, maximum_temperature=45.0)
        hum = HumidityData(average_relative_humidity=58.0)
        ext = DesignExtremes(cold_extreme=5.0, hot_extreme=43.5, heating_degree_days_18c=450.0, cooling_degree_days_18c=2850.0)
        res = ClimateClassifier.classify(temp, hum, ext)

        self.assertEqual(res.zone, ClimateZone.VARIABLE)
        self.assertIn("bi-modal seasonal swings", res.explanation)

    def test_temperate_classification(self):
        # Bengaluru: mild year-round
        temp = TemperatureProfile(annual_mean_temperature=23.8, minimum_temperature=12.0, maximum_temperature=34.0, diurnal_range_mean=9.5)
        hum = HumidityData(average_relative_humidity=62.0)
        ext = DesignExtremes(cold_extreme=14.0, hot_extreme=33.5, heating_degree_days_18c=50.0, cooling_degree_days_18c=1200.0)
        res = ClimateClassifier.classify(temp, hum, ext)

        self.assertEqual(res.zone, ClimateZone.TEMPERATE)
        self.assertIn("moderate, temperate", res.explanation)


if __name__ == "__main__":
    unittest.main()
