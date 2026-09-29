"""
Golden Scenario and Multi-Location Differential Validation Test.
===============================================================
Validates:
1. Primary Golden Scenario: Leh, Ladakh -> EXTREME COLD -> PassiveStrategy
2. Multi-Location Benchmark Contrast: Leh vs Jaisalmer vs Chennai
"""

import unittest
from backend.climate.schemas import ClimateZone, PriorityLevel
from backend.climate.service import ClimateService


class TestGoldenScenarioAndMultiLocation(unittest.TestCase):
    """
    Executes the definitive validation checks specified in Member 1 requirements.
    """

    def setUp(self):
        self.service = ClimateService(enable_online=False)

    def test_golden_scenario_leh_ladakh(self):
        """
        Golden Scenario:
        Input: Location: Leh, Ladakh
        Downstream context: 4 occupants, permanent shelter, thermal comfort priority.
        Member 1 responsibility: Location -> ClimateProfile -> EXTREME_COLD -> PassiveStrategy.
        """
        result = self.service.analyze("Leh, Ladakh")

        # 1. Location
        self.assertEqual(result.location.place_name, "Leh, Ladakh")
        self.assertAlmostEqual(result.location.latitude, 34.1526, places=2)
        self.assertAlmostEqual(result.location.longitude, 77.5771, places=2)
        self.assertEqual(result.location.elevation, 3524.0)

        # 2. Temperature & Design Extremes
        self.assertAlmostEqual(result.profile.climate.annual_mean_temperature, 5.3, places=1)
        self.assertAlmostEqual(result.profile.design_extremes.cold_extreme, -18.5, places=1)
        self.assertGreater(result.profile.design_extremes.heating_degree_days_18c, 4000.0)

        # 3. Solar, Wind, Humidity
        self.assertGreater(result.profile.solar.GHI, 200.0)
        self.assertAlmostEqual(result.profile.solar.annual_solar_ghi_kwh_m2, 2100.0, places=0)
        self.assertGreater(result.profile.wind.average_speed, 0.0)
        self.assertLess(result.profile.humidity.average_relative_humidity, 45.0)

        # 4. Confidence & Provenance
        self.assertEqual(result.profile.data_quality.provenance.value, "HISTORICAL")
        self.assertEqual(result.profile.data_quality.confidence.value, "HIGH")

        # 5. Climate Classification
        self.assertEqual(result.classification.zone, ClimateZone.EXTREME_COLD)

        # 6. PassiveStrategy Recommendations
        strategy = result.strategy
        self.assertEqual(strategy.climate_mode, ClimateZone.EXTREME_COLD)
        self.assertIn("Solar heat capture", strategy.primary_strategy)
        self.assertIn("envelope thermal protection", strategy.primary_strategy)

        # Assert specific passive recommendations
        self.assertEqual(strategy.solar_capture, PriorityLevel.HIGH)
        self.assertEqual(strategy.thermal_mass, PriorityLevel.HIGH)
        self.assertEqual(strategy.insulation_priority, PriorityLevel.HIGH)
        self.assertTrue(strategy.airlock, "Airlock must be True for EXTREME COLD")
        self.assertTrue(strategy.thermal_buffer, "Thermal buffer must be True for EXTREME COLD")

        # Assert explanation is physics-grounded
        self.assertIn("-18.5", strategy.explanation)
        self.assertIn("heating degree days", strategy.explanation)

    def test_multi_location_differentiation(self):
        """
        Validates distinct, climate-aware outputs across three contrasting climate regimes:
          - Leh, Ladakh: Alpine Cold Desert (EXTREME COLD)
          - Jaisalmer, Rajasthan: Arid Thar Desert (HOT DRY)
          - Chennai, Tamil Nadu: Tropical Coastal (HOT HUMID)
        """
        leh = self.service.analyze("Leh, Ladakh")
        jaisalmer = self.service.analyze("Jaisalmer, Rajasthan")
        chennai = self.service.analyze("Chennai, Tamil Nadu")

        # Classification distinction
        self.assertEqual(leh.classification.zone, ClimateZone.EXTREME_COLD)
        self.assertEqual(jaisalmer.classification.zone, ClimateZone.HOT_DRY)
        self.assertEqual(chennai.classification.zone, ClimateZone.HOT_HUMID)

        # Design extremes distinction
        self.assertLess(leh.profile.design_extremes.cold_extreme, 0.0)
        self.assertGreater(jaisalmer.profile.design_extremes.hot_extreme, 40.0)
        self.assertGreater(chennai.profile.design_extremes.cold_extreme, 15.0)

        # Humidity distinction
        self.assertLess(jaisalmer.profile.humidity.average_relative_humidity, 35.0)
        self.assertGreater(chennai.profile.humidity.average_relative_humidity, 65.0)

        # Passive strategy distinctions:
        # 1. Airlock only in extreme cold
        self.assertTrue(leh.strategy.airlock)
        self.assertFalse(jaisalmer.strategy.airlock)
        self.assertFalse(chennai.strategy.airlock)

        # 2. Solar capture priority: High in Leh, Low in Jaisalmer, Minimized in Chennai
        self.assertEqual(leh.strategy.solar_capture, PriorityLevel.HIGH)
        self.assertEqual(jaisalmer.strategy.solar_capture, PriorityLevel.LOW)
        self.assertEqual(chennai.strategy.solar_capture, PriorityLevel.MINIMIZED)

        # 3. Ventilation strategy: Controlled in Leh, Night flush in Jaisalmer, Cross-vent in Chennai
        self.assertIn("MINIMAL", leh.strategy.ventilation_strategy)
        self.assertIn("NIGHT_FLUSH", jaisalmer.strategy.ventilation_strategy)
        self.assertIn("CROSS_VENTILATION", chennai.strategy.ventilation_strategy)

        # 4. Thermal mass: High in Leh and Jaisalmer, Low in Chennai
        self.assertEqual(leh.strategy.thermal_mass, PriorityLevel.HIGH)
        self.assertEqual(jaisalmer.strategy.thermal_mass, PriorityLevel.HIGH)
        self.assertEqual(chennai.strategy.thermal_mass, PriorityLevel.LOW)


if __name__ == "__main__":
    unittest.main()
