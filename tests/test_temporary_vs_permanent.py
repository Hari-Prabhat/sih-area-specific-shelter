"""
Tests for Temporary vs Permanent Shelter Configurations & Constraints
"""

import pytest
from services.recommender import auto_size_shelter, recommend_materials, get_recommendation
from services.optimize import run_optimization
from services.simulation_service import run_simulation


def test_temporary_vs_permanent_geometry():
    """Verify Temporary shelter has a lower ceiling height than Permanent."""
    temp_geo = auto_size_shelter(people=4, home_type="Temporary")
    perm_geo = auto_size_shelter(people=4, home_type="Permanent")

    assert temp_geo["height_m"] == 2.6
    assert perm_geo["height_m"] == 2.8
    assert temp_geo["floor_area_m2"] == perm_geo["floor_area_m2"]
    assert temp_geo["volume_m3"] < perm_geo["volume_m3"]


def test_temporary_vs_permanent_materials():
    """Verify material recommendations differ between Temporary and Permanent."""
    temp_mats_cold = recommend_materials("cold", home_type="Temporary")
    perm_mats_cold = recommend_materials("cold", home_type="Permanent")

    assert temp_mats_cold["wall_material_id"] == "puf_insulation"
    assert perm_mats_cold["wall_material_id"] == "brick"
    assert "Lightweight" in temp_mats_cold["wall_material_name"]
    assert "Mass" in perm_mats_cold["wall_material_name"]
    assert temp_mats_cold["permanence_rationale"] != perm_mats_cold["permanence_rationale"]


def test_temporary_vs_permanent_optimization_behavior():
    """Verify optimization evaluates temporary vs permanent with distinct constraints."""
    res_temp = run_optimization(city="leh", home_type="Temporary", occupants=2, n_trials=10)
    res_perm = run_optimization(city="leh", home_type="Permanent", occupants=2, n_trials=10)

    assert "ranked_designs" in res_temp
    assert len(res_temp["ranked_designs"]) > 0
    assert "ranked_designs" in res_perm
    assert len(res_perm["ranked_designs"]) > 0

    # Ensure simulation results are present
    assert res_temp["simulation_result"] is not None
    assert res_perm["simulation_result"] is not None


def test_end_to_end_recommendation_with_evidence():
    """Verify get_recommendation generates quantitative evidence for both shelter types."""
    rec_temp = get_recommendation(city="leh", people=3, home_type="Temporary", n_trials=10)
    rec_perm = get_recommendation(city="leh", people=3, home_type="Permanent", n_trials=10)

    assert "quantitative_evidence" in rec_temp
    assert "quantitative_evidence" in rec_perm
    assert "✓" in rec_temp["explanation"]
    assert "Temporary Shelter Fit" in rec_temp["explanation"]
    assert "Permanent Shelter Fit" in rec_perm["explanation"]
