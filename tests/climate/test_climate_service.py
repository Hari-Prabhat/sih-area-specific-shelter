"""
Integration tests for ClimateService and ClimateAPI dispatchers.
"""

import unittest
from backend.climate.api import ClimateAPI, LocationRequest, AnalyzeRequest
from backend.climate.schemas import ClimateZone, PriorityLevel
from backend.climate.service import ClimateService


class TestClimateServiceIntegration(unittest.TestCase):
    """End-to-end service and API integration tests."""

    def setUp(self):
        # Offline mode to guarantee hermetic test execution
        self.service = ClimateService(enable_online=False)
        self.api = ClimateAPI(service=self.service)

    def test_service_analyze_place_name(self):
        res = self.service.analyze("Leh, Ladakh")
        self.assertEqual(res.location.place_name, "Leh, Ladakh")
        self.assertEqual(res.classification.zone, ClimateZone.EXTREME_COLD)
        self.assertEqual(res.strategy.solar_capture, PriorityLevel.HIGH)
        self.assertEqual(res.strategy.insulation_priority, PriorityLevel.HIGH)
        self.assertTrue(res.strategy.airlock)
        self.assertTrue(res.strategy.thermal_buffer)

    def test_service_analyze_coordinates(self):
        # Coordinates for Jaisalmer
        res = self.service.analyze((26.9157, 70.9083))
        self.assertEqual(res.classification.zone, ClimateZone.HOT_DRY)
        self.assertEqual(res.strategy.thermal_mass, PriorityLevel.HIGH)
        self.assertFalse(res.strategy.airlock)

    def test_api_location_dispatch(self):
        resp = self.api.handle_location({"query": "chennai"})
        self.assertIn("Chennai", resp["place_name"])
        self.assertAlmostEqual(resp["latitude"], 13.0827, places=2)

    def test_api_analyze_dispatch(self):
        resp = self.api.handle_analyze({"location": "Leh, Ladakh"})
        self.assertIn("profile", resp)
        self.assertIn("classification", resp)
        self.assertIn("strategy", resp)
        self.assertEqual(resp["classification"]["zone"], "EXTREME COLD")
        self.assertTrue(resp["strategy"]["airlock"])

    def test_invalid_coordinates_handled_gracefully(self):
        with self.assertRaises(ValueError):
            self.service.analyze((120.0, 75.0))


if __name__ == "__main__":
    unittest.main()
