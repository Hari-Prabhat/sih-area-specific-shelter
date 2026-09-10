"""
Unit tests for ClimateStrategyEngine and strict boundary assertions.
"""

import json
import unittest
from backend.climate.climate_strategy import ClimateStrategyEngine
from backend.climate.schemas import (
    ClimateMetrics,
    ClimateProfile,
    ClimateZone,
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


class TestClimateStrategy(unittest.TestCase):
    """Tests for PassiveStrategy generation across all climate zones."""

    def _create_profile(self, zone: ClimateZone, cold_ext: float, hot_ext: float, rh: float) -> ClimateProfile:
        return ClimateProfile(
            location=Location(place_name="Test Loc", latitude=30.0, longitude=75.0),
            climate=ClimateMetrics(
                classification=zone,
                annual_mean_temperature=(cold_ext + hot_ext) / 2.0,
                minimum_temperature=cold_ext - 5.0,
                maximum_temperature=hot_ext + 3.0,
                diurnal_range_mean=14.0
            ),
            solar=SolarData(GHI=220.0, annual_solar_ghi_kwh_m2=2000.0),
            wind=WindData(average_speed=3.5),
            humidity=HumidityData(average_relative_humidity=rh),
            design_extremes=DesignExtremes(cold_extreme=cold_ext, hot_extreme=hot_ext),
            data_quality=DataQuality(confidence=DataConfidence.HIGH, provenance=DataProvenance.HISTORICAL)
        )

    def test_extreme_cold_strategy(self):
        p = self._create_profile(ClimateZone.EXTREME_COLD, -18.5, 26.0, 32.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        self.assertEqual(strat.climate_mode, ClimateZone.EXTREME_COLD)
        self.assertEqual(strat.solar_capture, PriorityLevel.HIGH)
        self.assertEqual(strat.thermal_mass, PriorityLevel.HIGH)
        self.assertEqual(strat.insulation_priority, PriorityLevel.HIGH)
        self.assertTrue(strat.airlock)
        self.assertTrue(strat.thermal_buffer)
        self.assertIn("-18.5", strat.explanation)

    def test_cold_strategy(self):
        p = self._create_profile(ClimateZone.COLD, -4.0, 31.0, 65.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        self.assertEqual(strat.climate_mode, ClimateZone.COLD)
        self.assertEqual(strat.solar_capture, PriorityLevel.HIGH)
        self.assertEqual(strat.thermal_mass, PriorityLevel.MODERATE)
        self.assertEqual(strat.insulation_priority, PriorityLevel.HIGH)
        self.assertFalse(strat.airlock)
        self.assertTrue(strat.thermal_buffer)

    def test_hot_dry_strategy(self):
        p = self._create_profile(ClimateZone.HOT_DRY, 7.0, 46.0, 28.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        self.assertEqual(strat.climate_mode, ClimateZone.HOT_DRY)
        self.assertEqual(strat.solar_capture, PriorityLevel.LOW)
        self.assertEqual(strat.thermal_mass, PriorityLevel.HIGH)
        self.assertIn("NIGHT_FLUSH", strat.ventilation_strategy)
        self.assertFalse(strat.airlock)

    def test_hot_humid_strategy(self):
        p = self._create_profile(ClimateZone.HOT_HUMID, 20.0, 39.0, 74.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        self.assertEqual(strat.climate_mode, ClimateZone.HOT_HUMID)
        self.assertEqual(strat.solar_capture, PriorityLevel.MINIMIZED)
        self.assertEqual(strat.thermal_mass, PriorityLevel.LOW)
        self.assertEqual(strat.insulation_priority, PriorityLevel.LOW)
        self.assertIn("CROSS_VENTILATION", strat.ventilation_strategy)
        self.assertFalse(strat.airlock)

    def test_temperate_strategy(self):
        p = self._create_profile(ClimateZone.TEMPERATE, 14.0, 33.0, 60.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        self.assertEqual(strat.climate_mode, ClimateZone.TEMPERATE)
        self.assertEqual(strat.solar_capture, PriorityLevel.MODERATE)
        self.assertEqual(strat.thermal_mass, PriorityLevel.MODERATE)
        self.assertEqual(strat.insulation_priority, PriorityLevel.MODERATE)

    def test_variable_strategy(self):
        p = self._create_profile(ClimateZone.VARIABLE, 5.0, 43.5, 58.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        self.assertEqual(strat.climate_mode, ClimateZone.VARIABLE)
        self.assertIn("Adaptive seasonal", strat.primary_strategy)
        self.assertTrue(strat.thermal_buffer)

    def test_strict_boundary_no_geometry_or_material_dimensions(self):
        """Ensures PassiveStrategy does NOT output building dimensions or material thicknesses."""
        p = self._create_profile(ClimateZone.EXTREME_COLD, -18.5, 26.0, 32.0)
        strat = ClimateStrategyEngine.generate_strategy(p)

        strat_dict = strat.model_dump()
        strat_str = json.dumps(strat_dict).lower()

        # Check that forbidden geometry/dimension keywords are absent from numeric strategy definitions
        forbidden_terms = ["floor_area_m2", "length_m", "width_m", "height_m", "insulation_thickness", "window_area"]
        for term in forbidden_terms:
            self.assertNotIn(term, strat_dict, f"Forbidden geometry/material key found in strategy: {term}")

        # Ensure no specific dimension units like "120 mm" or "4.5 m2" exist
        self.assertNotIn("120 mm", strat_str)
        self.assertNotIn("4.5 m²", strat_str)


if __name__ == "__main__":
    unittest.main()
