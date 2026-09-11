"""
Unit tests for Weather Provider abstraction, local fallback, and caching.
"""

import unittest
from backend.climate.climate_cache import ClimateCache
from backend.climate.schemas import DataConfidence, DataProvenance
from backend.climate.weather_provider import (
    CompositeWeatherProvider,
    LocalFallbackWeatherProvider,
)


class TestWeatherProvider(unittest.TestCase):
    """Tests for offline weather provider, mock dataset retrieval, and caching."""

    def setUp(self):
        self.cache = ClimateCache(default_ttl_seconds=60.0)
        self.fallback = LocalFallbackWeatherProvider()
        self.composite = CompositeWeatherProvider(enable_online=False, cache=self.cache)

    def test_local_fallback_leh(self):
        temp, wind, hum, ext, qual = self.fallback.get_historical_climate(34.1526, 77.5771)
        self.assertAlmostEqual(temp.annual_mean_temperature, 5.3, places=1)
        self.assertAlmostEqual(ext.cold_extreme, -18.5, places=1)
        self.assertEqual(qual.provenance, DataProvenance.HISTORICAL)
        self.assertEqual(qual.confidence, DataConfidence.HIGH)

    def test_local_fallback_jaisalmer(self):
        temp, wind, hum, ext, qual = self.fallback.get_historical_climate(26.9157, 70.9083)
        self.assertAlmostEqual(temp.annual_mean_temperature, 27.2, places=1)
        self.assertAlmostEqual(ext.hot_extreme, 46.0, places=1)
        self.assertLess(hum.average_relative_humidity, 35.0)

    def test_local_fallback_chennai(self):
        temp, wind, hum, ext, qual = self.fallback.get_historical_climate(13.0827, 80.2707)
        self.assertAlmostEqual(temp.annual_mean_temperature, 28.6, places=1)
        self.assertGreater(hum.average_relative_humidity, 65.0)
        self.assertGreaterEqual(ext.cold_extreme, 18.0)

    def test_solar_data_retrieval(self):
        solar = self.fallback.get_solar_data(34.1526, 77.5771)
        self.assertGreater(solar.GHI, 200.0)
        self.assertGreater(solar.annual_solar_ghi_kwh_m2, 1900.0)
        self.assertEqual(solar.unit, "W/m²")

    def test_composite_provider_offline_caching(self):
        self.assertEqual(self.cache.size(), 0)

        # First call populates cache
        temp1, _, _, _, _ = self.composite.get_historical_climate(34.1526, 77.5771)
        self.assertGreater(self.cache.size(), 0)

        # Second call should serve from cache
        temp2, _, _, _, _ = self.composite.get_historical_climate(34.1526, 77.5771)
        self.assertEqual(temp1.annual_mean_temperature, temp2.annual_mean_temperature)

    def test_current_weather_fallback_distinct_from_design(self):
        cw = self.fallback.get_current_weather(34.1526, 77.5771)
        self.assertFalse(cw.is_observed)
        self.assertIn("Fallback", cw.source)


if __name__ == "__main__":
    unittest.main()
