"""
Unit tests for ClimateNormalizer and assemble_climate_profile.
"""

import unittest
from backend.climate.climate_resolver import ClimateNormalizer, assemble_climate_profile
from backend.climate.schemas import (
    ClimateZone,
    DataConfidence,
    DataProvenance,
    DataQuality,
    DesignExtremes,
    HumidityData,
    Location,
    SolarData,
    TemperatureProfile,
    WindData,
)


class TestClimateResolver(unittest.TestCase):
    """Tests for unit conversion, bounds validation, and profile assembly."""

    def test_temperature_fahrenheit_conversion(self):
        c = ClimateNormalizer.normalize_temperature(32.0, "F")
        self.assertAlmostEqual(c, 0.0)

        # 104°F = 40.0°C (realistic extreme summer heat)
        c2 = ClimateNormalizer.normalize_temperature(104.0, "F")
        self.assertAlmostEqual(c2, 40.0)

        # 212°F = 100°C exceeds terrestrial ambient limits (-80°C to 70°C)
        with self.assertRaises(ValueError):
            ClimateNormalizer.normalize_temperature(212.0, "F")

    def test_temperature_kelvin_conversion(self):
        c = ClimateNormalizer.normalize_temperature(273.15, "K")
        self.assertAlmostEqual(c, 0.0)

    def test_temperature_bounds_violation_raises(self):
        with self.assertRaises(ValueError):
            ClimateNormalizer.normalize_temperature(-95.0, "C")

        with self.assertRaises(ValueError):
            ClimateNormalizer.normalize_temperature(85.0, "C")

    def test_wind_speed_unit_conversions(self):
        # 36 km/h = 10 m/s
        speed = ClimateNormalizer.normalize_wind_speed(36.0, "km/h")
        self.assertAlmostEqual(speed, 10.0, places=1)

        # 22.3694 mph ~ 10 m/s
        speed_mph = ClimateNormalizer.normalize_wind_speed(22.3694, "mph")
        self.assertAlmostEqual(speed_mph, 10.0, places=1)

    def test_wind_speed_negative_raises(self):
        with self.assertRaises(ValueError):
            ClimateNormalizer.normalize_wind_speed(-5.0, "m/s")

    def test_humidity_fraction_conversion(self):
        # 0.42 fraction should convert to 42.0%
        rh = ClimateNormalizer.normalize_relative_humidity(0.42)
        self.assertEqual(rh, 42.0)

    def test_humidity_bounds(self):
        with self.assertRaises(ValueError):
            ClimateNormalizer.normalize_relative_humidity(105.0)

        with self.assertRaises(ValueError):
            ClimateNormalizer.normalize_relative_humidity(-2.0)

    def test_solar_insolation_conversions(self):
        # 5.0 kWh/m2/day = 1825 kWh/m2/year
        annual, flux = ClimateNormalizer.convert_daily_insolation_to_annual_and_flux(5.0)
        self.assertEqual(annual, 1825.0)
        # 1825 * 1000 / 8760 = 208.33 W/m2
        self.assertAlmostEqual(flux, 208.3, places=1)

    def test_assemble_climate_profile(self):
        loc = Location(place_name="Test City", latitude=20.0, longitude=75.0)
        temp = TemperatureProfile(
            annual_mean_temperature=22.0,
            minimum_temperature=5.0,
            maximum_temperature=38.0
        )
        solar = SolarData(GHI=210.0, annual_solar_ghi_kwh_m2=1850.0)
        wind = WindData(average_speed=3.2)
        humidity = HumidityData(average_relative_humidity=52.0)
        extremes = DesignExtremes(cold_extreme=3.0, hot_extreme=40.0)
        quality = DataQuality(confidence=DataConfidence.HIGH, provenance=DataProvenance.HISTORICAL)

        profile = assemble_climate_profile(
            location=loc,
            temperature=temp,
            solar=solar,
            wind=wind,
            humidity=humidity,
            design_extremes=extremes,
            data_quality=quality,
            classification=ClimateZone.TEMPERATE
        )

        self.assertEqual(profile.location.place_name, "Test City")
        self.assertEqual(profile.climate.classification, ClimateZone.TEMPERATE)
        self.assertEqual(profile.climate.annual_mean_temperature, 22.0)


if __name__ == "__main__":
    unittest.main()
