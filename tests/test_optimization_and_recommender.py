"""
Tests for Optimization, Multi-Candidate Ranking & Recommender Engine
"""

import pytest
from services.optimize import run_optimization
from services.recommender import get_recommendation, generate_design_explanation
from services.simulation_service import run_simulation


def test_optimization_ranked_candidates():
    """Verify optimizer returns ranked candidate designs with complete scores."""
    res = run_optimization(city="leh", home_type="Permanent", n_trials=15)

    assert "ranked_designs" in res
    ranked = res["ranked_designs"]
    assert len(ranked) >= 1
    assert ranked[0]["rank"] == 1
    assert "overall_score" in ranked[0]
    assert "sub_scores" in ranked[0]
    assert "comfort" in ranked[0]["sub_scores"]
    assert "efficiency" in ranked[0]["sub_scores"]


def test_simulation_168_hours_numerical_soundness():
    """Verify 168-hour simulation generates all component heat flows and temperature series."""
    sim = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=2.5,
        occupants=4,
        hours_to_simulate=168,
    )

    assert "error" not in sim
    assert len(sim["indoor_temperature"]) == 168
    assert len(sim["outdoor_temperature"]) == 168
    assert len(sim["solar_irradiance"]) == 168
    assert len(sim["solar_thermal_gain"]) == 168
    assert len(sim["wall_heat_flow"]) == 168
    assert len(sim["roof_heat_flow"]) == 168
    assert len(sim["floor_heat_flow"]) == 168
    assert len(sim["window_heat_flow"]) == 168
    assert len(sim["ventilation_heat_flow"]) == 168
    assert len(sim["net_heat_flow"]) == 168
    assert sim["total_heat_loss_kwh"] > 0
    assert 0 <= sim["comfort_percentage"] <= 100


def test_baseline_vs_optimized_real_improvement():
    """Verify baseline and optimized simulation results differ and show real improvement."""
    sim_base = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.0,
        window_area=2.0,
        glazing="single_clear",
        occupants=4,
        hours_to_simulate=168,
    )
    sim_opt = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.08,
        window_area=2.0,
        glazing="double_low_e",
        occupants=4,
        hours_to_simulate=168,
    )

    assert sim_opt["u_values"]["wall_u"] < sim_base["u_values"]["wall_u"]
    assert sim_opt["component_heat_loss_kwh"]["wall_loss_kwh"] < sim_base["component_heat_loss_kwh"]["wall_loss_kwh"]
    assert sim_opt["discomfort_degree_hours"] <= sim_base["discomfort_degree_hours"]
    assert sim_opt["comfort_percentage"] >= sim_base["comfort_percentage"]


def test_invalid_input_error_handling():
    """Verify graceful error handling for missing/invalid cities."""
    sim_invalid = run_simulation(city="non_existent_city_xyz")
    assert "error" in sim_invalid
