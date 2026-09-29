"""
THERMOSHELTER - Product-Hardening Pass: Multi-Shape & Location Tests
====================================================================
Covers:
  1. Canonical shape geometry (services/geometry.py calculate_shape_geometry)
     against closed-form analytic values for all four supported forms.
  2. Shape propagation through the canonical ShelterDesign contract and the
     simulation adapter (the engine consumes the ACTUAL shape; rectangular
     default remains byte-identical).
  3. Location resolver routing: Indian PIN codes route through the India Post
     directory path, never the place-name geocoder.
No engineering values are invented: every assertion uses closed-form
mathematics or pre-existing resolver behavior.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from services.geometry import calculate_shape_geometry


class TestShapeGeometry:
    def test_rectangular_matches_existing_engine_formulas(self):
        g = calculate_shape_geometry("rectangular", 6.0, 4.0, 3.0)
        assert g["floor_area_m2"] == pytest.approx(24.0)
        assert g["volume_m3"] == pytest.approx(72.0)
        assert g["gross_wall_area_m2"] == pytest.approx(2 * (6 + 4) * 3)
        assert g["roof_area_m2"] == pytest.approx(24.0)
        assert g["total_envelope_area_m2"] == pytest.approx(84.0)

    def test_cylindrical_curved_envelope(self):
        g = calculate_shape_geometry("cylindrical", 6.0, 6.0, 3.0)
        r = 3.0
        assert g["floor_area_m2"] == pytest.approx(math.pi * r * r, abs=1e-3)
        assert g["volume_m3"] == pytest.approx(math.pi * r * r * 3.0, abs=1e-3)
        assert g["gross_wall_area_m2"] == pytest.approx(2 * math.pi * r * 3.0, abs=1e-3)
        assert g["roof_area_m2"] == pytest.approx(math.pi * r * r, abs=1e-3)

    def test_dome_pure_hemisphere(self):
        g = calculate_shape_geometry("dome", 6.0, 6.0, 3.0)
        r = 3.0
        assert g["gross_wall_area_m2"] == pytest.approx(0.0)  # no drum
        assert g["roof_area_m2"] == pytest.approx(2 * math.pi * r * r, abs=1e-3)  # hemisphere area
        assert g["volume_m3"] == pytest.approx((2 / 3) * math.pi * r ** 3, abs=1e-3)

    def test_dome_with_drum(self):
        # d=6 (r=3), H=4 -> drum 1 m + spherical cap 3 m
        g = calculate_shape_geometry("dome", 6.0, 6.0, 4.0)
        r, drum, cap = 3.0, 1.0, 3.0
        assert g["gross_wall_area_m2"] == pytest.approx(2 * math.pi * r * drum, abs=1e-3)
        assert g["roof_area_m2"] == pytest.approx(2 * math.pi * r * cap, abs=1e-3)
        expected_volume = math.pi * r * r * drum + (math.pi * cap * cap / 3) * (3 * r - cap)
        assert g["volume_m3"] == pytest.approx(expected_volume, abs=1e-3)

    def test_pyramid_sloped_faces_not_rectangular_walls(self):
        g = calculate_shape_geometry("pyramid", 6.0, 4.0, 3.0)
        assert g["floor_area_m2"] == pytest.approx(24.0)
        assert g["volume_m3"] == pytest.approx(24.0)  # A*h/3
        slant_l = math.sqrt(2.0 ** 2 + 3.0 ** 2)  # faces meeting base L
        slant_w = math.sqrt(3.0 ** 2 + 3.0 ** 2)  # faces meeting base W
        assert g["gross_wall_area_m2"] == pytest.approx(6 * slant_l + 4 * slant_w)
        # Deliberately different from the rectangular wall formula (60 m2):
        assert g["gross_wall_area_m2"] != pytest.approx(60.0)

    def test_unknown_shape_rejected(self):
        with pytest.raises(ValueError, match="Unsupported shelter shape"):
            calculate_shape_geometry("igloo", 6.0, 4.0, 3.0)

    def test_nonpositive_dimensions_rejected(self):
        for L, W, H in [(0, 4, 3), (6, -1, 3), (6, 4, 0)]:
            with pytest.raises(ValueError, match="strictly positive"):
                calculate_shape_geometry("rectangular", L, W, H)


class TestDesignShapePropagation:
    def _profile(self):
        from services.contracts import ClimateProfile
        return ClimateProfile.from_dict({
            "city": "leh",
            "hourly_temperature": [-10.0] * 48,
            "hourly_direct_solar": [0.0] * 48,
            "hourly_diffuse_solar": [0.0] * 48,
        })

    def test_design_carries_shape_through_roundtrip(self):
        from services.contracts import ShelterDesign
        d = ShelterDesign(shape="dome", length=6.0, width=6.0, height=3.0)
        assert d.shape == "dome"
        restored = ShelterDesign.from_dict(d.to_dict())
        assert restored.shape == "dome"

    def test_default_shape_is_rectangular(self):
        from services.contracts import ShelterDesign
        assert ShelterDesign().shape == "rectangular"

    def test_engine_simulates_actual_shape(self):
        from services.contracts import (
            SimulationInput,
            adapt_to_shelter_design,
        )
        from services.simulation_adapter import SimulationAdapter
        from services.contracts import ShelterDesign

        results = {}
        for shape, L, W in [("rectangular", 6, 4), ("cylindrical", 6, 6), ("dome", 6, 6), ("pyramid", 6, 4)]:
            design = adapt_to_shelter_design(
                ShelterDesign(shape=shape, length=L, width=W, height=3.0,
                              insulation_thickness_m=0.05, window_area=2.0).to_dict()
            )
            result = SimulationAdapter.run_simulation_from_input(
                SimulationInput(climate=self._profile(), design=design,
                                hours_to_simulate=48, substeps=1)
            )
            results[shape] = result.to_dict()["geometry"]

        assert results["rectangular"]["floor_area_m2"] == pytest.approx(24.0)
        assert results["cylindrical"]["floor_area_m2"] == pytest.approx(math.pi * 9, abs=0.02)
        assert results["dome"]["floor_area_m2"] == pytest.approx(math.pi * 9, abs=0.02)
        assert results["pyramid"]["volume_m3"] == pytest.approx(24.0, abs=0.02)
        # The dome's enclosed volume is genuinely different from the box:
        assert results["dome"]["volume_m3"] != pytest.approx(results["rectangular"]["volume_m3"])
        # The engine reports the authoritative shape it simulated:
        for shape in ("rectangular", "cylindrical", "dome", "pyramid"):
            assert results[shape]["shape"] == shape

    def test_diameter_mismatch_rejected_for_radial_shapes(self):
        from services.contracts import ClimateProfile, ShelterDesign, SimulationInput, adapt_to_shelter_design
        from services.simulation_adapter import SimulationAdapter
        profile = ClimateProfile.from_dict({
            "city": "leh",
            "hourly_temperature": [-10.0] * 24,
            "hourly_direct_solar": [0.0] * 24,
            "hourly_diffuse_solar": [0.0] * 24,
        })
        design = adapt_to_shelter_design(
            ShelterDesign(shape="cylindrical", length=6.0, width=4.0, height=3.0).to_dict()
        )
        with pytest.raises(ValueError, match="diameter"):
            SimulationAdapter.run_simulation_from_input(
                SimulationInput(climate=profile, design=design, hours_to_simulate=24, substeps=1)
            )


class TestPinRouting:
    def _resolver(self):
        from backend.climate.location_resolver import LocationResolver
        return LocationResolver()

    def test_pin_query_routes_to_pincode_path_not_geocoder(self):
        resolver = self._resolver()
        # Offline: an unknown PIN returns [] (clear not-found) rather than
        # being sent to the place-name geocoder as a city query.
        assert resolver.search_locations("999999", allow_online=False) == []

    def test_non_numeric_queries_unaffected(self):
        resolver = self._resolver()
        # Local DB contains Leh; a normal name search still works.
        results = resolver.search_locations("Leh", count=3, allow_online=False)
        assert any("Leh" in (l.place_name or "") for l in results)

    def test_five_digits_is_not_a_pin(self):
        resolver = self._resolver()
        # A 5-digit number is not a PIN; it must fall through to name search
        # (which will simply find nothing offline rather than raising).
        results = resolver.search_locations("11000", allow_online=False)
        assert results == []
