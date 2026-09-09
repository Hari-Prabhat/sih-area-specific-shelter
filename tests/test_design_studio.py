"""
Unit and Integration Tests for Design Studio & Reusable Components
==================================================================
Tests:
  - Climate metadata completeness & helper queries
  - Site Profile & Design DNA schema validation
  - Provenance badge rendering (Calculated vs Simulated vs Optimized vs Specified vs Demo)
  - Auto-sizing & mission parameter constraints
  - Hero Demo (Leh, Ladakh) scenario verification
  - End-to-end recommendation & simulation payload generation
"""

import pytest
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from components.inputs import (
    CITIES_METADATA,
    get_city_metadata,
    get_all_supported_cities,
)
from components.design_studio import (
    render_provenance_badge,
    load_hero_demo_preset,
)
from services.recommender import (
    auto_size_shelter,
    recommend_materials,
    get_recommendation,
)
from services.simulation_service import run_simulation


def test_supported_cities_metadata():
    """Verify all 5 supported simulation cities have complete meteorological metadata."""
    cities = get_all_supported_cities()
    expected = ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
    for c in expected:
        assert c in cities, f"City '{c}' must be in supported cities"
        meta = get_city_metadata(c)
        assert meta["id"] == c
        assert "display" in meta
        assert "elevation" in meta
        assert "latitude" in meta and "longitude" in meta
        assert "winter_temp" in meta and "summer_temp" in meta
        assert "solar_ghi" in meta
        assert "hdd" in meta
        assert "source" in meta
        assert "type" in meta


def test_city_metadata_fallback():
    """Verify fallback to 'leh' when querying an unknown city."""
    unknown = get_city_metadata("atlantis_underwater")
    assert unknown["id"] == "leh"
    assert "Ladakh" in unknown["display"]


def test_provenance_badges():
    """Verify that all provenance badges return valid HTML with required text."""
    calc_badge = render_provenance_badge("calculated")
    assert "CALCULATED: ISO 6946" in calc_badge

    sim_badge = render_provenance_badge("simulated")
    assert "SIMULATED: 168-HR EULER" in sim_badge

    opt_badge = render_provenance_badge("optimized")
    assert "OPTIMIZED: TPE BAYESIAN" in opt_badge

    spec_badge = render_provenance_badge("specified")
    assert "SPECIFIED MISSION INPUT" in spec_badge

    demo_badge = render_provenance_badge("demo")
    assert "DEMO / ESTIMATE PROXY" in demo_badge


def test_mission_auto_sizing():
    """Verify auto-sizing per SP 41 (4.5 m²/person, minimum 12.0 m²)."""
    # 2 occupants: 2 * 4.5 = 9.0 -> clamps to minimum 12.0 m²
    geo_2 = auto_size_shelter(2, "Permanent")
    assert geo_2["floor_area_m2"] == 12.0
    assert geo_2["height_m"] == 2.8

    # 4 occupants: 4 * 4.5 = 18.0 m²
    geo_4 = auto_size_shelter(4, "Permanent")
    assert geo_4["floor_area_m2"] == 18.0
    assert geo_4["height_m"] == 2.8
    assert geo_4["length_m"] > 0
    assert geo_4["width_m"] > 0
    assert geo_4["volume_m3"] == pytest.approx(geo_4["length_m"] * geo_4["width_m"] * 2.8, abs=0.1)

    # Temporary shelter has lower ceiling height (2.6 m)
    geo_temp = auto_size_shelter(4, "Temporary")
    assert geo_temp["height_m"] == 2.6


def test_hero_demo_preset_logic():
    """Verify the hero demo preset (Leh, Ladakh) payload."""
    city = "leh"
    meta = get_city_metadata(city)
    assert meta["badge"] == "⭐ Hero Demo (High-Altitude Cold)"
    assert meta["design_winter_temp_c"] == -18.5
    assert meta["heating_degree_days_18c"] == 4850

    # Material recommendation for Leh permanent shelter
    mats_perm = recommend_materials("cold", "Permanent")
    assert mats_perm["roof_type"] == "pitched"
    assert "Double" in mats_perm["glazing_type"] or "Triple" in mats_perm["glazing_type"]
    assert "South" in mats_perm["orientation_advice"]


def test_end_to_end_design_generation_leh():
    """Verify end-to-end recommendation & simulation generation for Leh."""
    # Fast test with 5 trials to keep test suite fast
    rec = get_recommendation(
        city="leh",
        people=4,
        home_type="Permanent",
        n_trials=5,
        max_insulation_mm=200.0,
        max_window_area=4.0,
    )
    assert rec["city"] == "leh"
    assert rec["home_type"] == "Permanent"
    assert rec["people"] == 4
    assert rec["optimal_insulation_mm"] > 0.0
    assert rec["optimal_window_area_m2"] > 0.0

    sim_res = rec["simulation_result"]
    assert sim_res is not None
    assert "indoor_temperature" in sim_res
    assert len(sim_res["indoor_temperature"]) == 168
    assert "comfort_percentage" in sim_res
    assert "discomfort_degree_hours" in sim_res
    assert "total_heat_loss_kwh" in sim_res
    assert "u_values" in sim_res
    assert sim_res["u_values"]["wall_u"] > 0.0
    assert sim_res["u_values"]["roof_u"] > 0.0
