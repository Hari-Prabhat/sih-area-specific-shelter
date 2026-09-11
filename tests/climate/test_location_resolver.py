"""
Unit tests for LocationResolver.
"""

import unittest
from backend.climate.location_resolver import LocationResolver
from backend.climate.schemas import Location


class TestLocationResolver(unittest.TestCase):
    """Tests for coordinate validation, place-name lookup, and offline fallback."""

    def setUp(self):
        self.resolver = LocationResolver()

    def test_resolve_known_place_name(self):
        loc = self.resolver.resolve("Leh, Ladakh")
        self.assertIsInstance(loc, Location)
        self.assertIn("Leh", loc.place_name)
        self.assertAlmostEqual(loc.latitude, 34.1526, places=2)
        self.assertAlmostEqual(loc.longitude, 77.5771, places=2)
        self.assertEqual(loc.elevation, 3524.0)

    def test_resolve_case_insensitive_name(self):
        loc = self.resolver.resolve("jaisalmer")
        self.assertIn("Jaisalmer", loc.place_name)
        self.assertAlmostEqual(loc.latitude, 26.9157, places=2)

    def test_resolve_tuple_coordinates(self):
        loc = self.resolver.resolve((13.0827, 80.2707))
        self.assertIsInstance(loc, Location)
        self.assertAlmostEqual(loc.latitude, 13.0827)
        self.assertAlmostEqual(loc.longitude, 80.2707)
        # Should identify proximity to Chennai
        self.assertIn("Chennai", loc.place_name)

    def test_resolve_coordinate_string(self):
        loc = self.resolver.resolve("34.1526, 77.5771")
        self.assertIsInstance(loc, Location)
        self.assertAlmostEqual(loc.latitude, 34.1526)
        self.assertAlmostEqual(loc.longitude, 77.5771)

    def test_invalid_coordinates_raise_value_error(self):
        with self.assertRaises(ValueError):
            self.resolver.resolve((100.0, 77.0))

        with self.assertRaises(ValueError):
            self.resolver.resolve((34.0, -190.0))

    def test_unknown_place_offline_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.resolver.resolve_from_name("NonExistentAtlantisCity", allow_online=False)

    def test_haversine_distance_calculation(self):
        # Distance between Leh (34.15, 77.58) and Kargil (34.55, 76.13) is ~140 km
        dist = LocationResolver.haversine_distance_km(34.1526, 77.5771, 34.5539, 76.1349)
        self.assertGreater(dist, 100.0)
        self.assertLess(dist, 180.0)


if __name__ == "__main__":
    unittest.main()
