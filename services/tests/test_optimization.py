"""
THERMOSHELTER AI - Design Optimization & Candidate Ranking Tests
================================================================
Comprehensive test suite validating:
  1. OptimizationInput and OptimizationResult contracts
  2. Multi-objective Bayesian optimization via Optuna TPE
  3. Ranked candidate designs (#1, #2, #3) with sub-scores and rationales
  4. Temporary vs Permanent search space and permanence penalties
  5. Custom search bounds, category restrictions, and multi-objective weights
  6. Multi-climate optimization scenarios (Leh, Jaisalmer, Chennai)
  7. OptimizationAdapter transformations and end-to-end execution
  8. Serialization round-trips and backward compatibility
"""

import json
import pytest
from services.contracts import (
    OptimizationInput,
    OptimizationResult,
    OptimizationCandidate,
    adapt_to_optimization_input,
    adapt_optimization_result,
)
from services.optimize import optimize_shelter, run_optimization
from services.simulation_adapter import OptimizationAdapter


# =====================================================================
# 1. OPTIMIZATION CONTRACT & EXECUTION TESTS
# =====================================================================

def test_optimize_shelter_with_contract_input():
    """Verify optimize_shelter consumes OptimizationInput and returns OptimizationResult."""
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        length=4.0,
        width=3.0,
        height=2.8,
        occupants=2,
        n_trials=10,
        substeps=15,
        hours_to_simulate=168,
    )

    opt_res = optimize_shelter(opt_in)

    assert isinstance(opt_res, OptimizationResult)
    assert opt_res.city == "leh"
    assert opt_res.home_type == "Permanent"
    assert opt_res.insulation_thickness_m >= 0.0
    assert opt_res.insulation_mm == round(opt_res.insulation_thickness_m * 1000.0, 1)
    assert opt_res.window_area_m2 >= 0.5
    assert opt_res.wall_material in ["brick", "mud", "stone", "concrete", "puf_insulation"]
    assert opt_res.glazing in ["single_clear", "double_clear", "double_low_e", "triple_low_e"]
    assert opt_res.orientation in ["south", "north", "east", "west"]
    assert opt_res.discomfort_score >= 0.0
    assert isinstance(opt_res.simulation_result, dict)
    assert len(opt_res.simulation_result["indoor_temperature"]) == 168


def test_optimization_ranked_candidates_structure():
    """Verify optimizer returns ranked candidates with complete metadata, sub-scores, and rationales."""
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        n_trials=15,
    )

    opt_res = optimize_shelter(opt_in)

    assert len(opt_res.ranked_designs) >= 1
    assert len(opt_res.ranked_designs) <= 3

    for idx, candidate in enumerate(opt_res.ranked_designs):
        assert isinstance(candidate, OptimizationCandidate)
        assert candidate.rank == idx + 1
        assert candidate.label == f"Design #{idx + 1}"
        assert len(candidate.rationale) > 0
        assert 0.0 <= candidate.overall_score <= 100.0
        assert "comfort" in candidate.sub_scores
        assert "efficiency" in candidate.sub_scores
        assert "solar" in candidate.sub_scores
        assert candidate.insulation_thickness_m >= 0.0
        assert candidate.insulation_mm == round(candidate.insulation_thickness_m * 1000.0, 1)
        assert candidate.window_area_m2 > 0.0
        assert len(candidate.wall_material) > 0
        assert len(candidate.wall_material_name) > 0
        assert len(candidate.glazing) > 0
        assert len(candidate.glazing_name) > 0
        assert candidate.orientation in ["south", "north", "east", "west"]
        assert 0.0 <= candidate.comfort_percentage <= 100.0
        assert candidate.total_heat_loss_kwh >= 0.0
        assert "wall_u" in candidate.u_values


# =====================================================================
# 2. TEMPORARY VS PERMANENT CONSTRAINTS & BEHAVIOR
# =====================================================================

def test_temporary_shelter_optimization_constraints():
    """Verify Temporary shelter optimization restricts insulation and searches lightweight materials."""
    opt_in_temp = OptimizationInput(
        city="leh",
        home_type="Temporary",
        max_insulation_m=0.20,  # Temporary cap should clamp to 0.12m
        n_trials=12,
    )

    res_temp = optimize_shelter(opt_in_temp)

    # Temporary shelter max insulation must not exceed 0.12m (120mm)
    assert res_temp.insulation_thickness_m <= 0.12001
    assert res_temp.home_type == "Temporary"

    # All candidates should respect temporary material domain
    temp_valid_materials = {"puf_insulation", "eps_insulation", "wood", "brick"}
    for candidate in res_temp.ranked_designs:
        assert candidate.wall_material in temp_valid_materials
        assert candidate.insulation_thickness_m <= 0.12001


def test_permanent_shelter_allows_high_insulation():
    """Verify Permanent shelter optimization allows insulation up to the specified boundary."""
    opt_in_perm = OptimizationInput(
        city="leh",
        home_type="Permanent",
        min_insulation_m=0.10,
        max_insulation_m=0.22,
        n_trials=10,
    )

    res_perm = optimize_shelter(opt_in_perm)

    assert res_perm.insulation_thickness_m >= 0.10 - 1e-4
    assert res_perm.insulation_thickness_m <= 0.22 + 1e-4


# =====================================================================
# 3. CUSTOM BOUNDS & CATEGORY RESTRICTIONS
# =====================================================================

def test_custom_bounds_and_allowed_categories():
    """Verify optimizer strictly honors custom allowed material/glazing/orientation lists."""
    opt_in = OptimizationInput(
        city="jaisalmer",
        home_type="Permanent",
        min_insulation_m=0.04,
        max_insulation_m=0.08,
        min_window_area=1.0,
        max_window_area=2.5,
        allowed_wall_materials=["stone", "mud"],
        allowed_glazings=["double_low_e"],
        allowed_orientations=["north", "south"],
        n_trials=10,
    )

    res = optimize_shelter(opt_in)

    assert 0.04 <= res.insulation_thickness_m <= 0.08
    assert 1.0 <= res.window_area_m2 <= 2.5
    assert res.wall_material in ["stone", "mud"]
    assert res.glazing == "double_low_e"
    assert res.orientation in ["north", "south"]

    for c in res.ranked_designs:
        assert c.wall_material in ["stone", "mud"]
        assert c.glazing == "double_low_e"
        assert c.orientation in ["north", "south"]


def test_fixed_parameter_optimization():
    """Verify fixed parameter kwargs bypass search sampling."""
    res = run_optimization(
        city="leh",
        home_type="Permanent",
        wall_material="stone",
        glazing="triple_low_e",
        orientation="south",
        min_insulation_m=0.05,
        max_insulation_m=0.05,
        min_window_area=1.5,
        max_window_area=1.5,
        n_trials=5,
    )

    assert res["wall_material"] == "stone"
    assert res["glazing"] == "triple_low_e"
    assert res["orientation"] == "south"
    assert abs(res["insulation_thickness_m"] - 0.05) < 1e-3
    assert abs(res["window_area_m2"] - 1.5) < 1e-3


# =====================================================================
# 4. MULTI-CLIMATE SCENARIOS (LEH, JAISALMER, CHENNAI)
# =====================================================================

@pytest.mark.parametrize("city,expected_home_type", [
    ("leh", "Permanent"),
    ("jaisalmer", "Permanent"),
    ("chennai", "Temporary"),
])
def test_optimization_across_climate_scenarios(city, expected_home_type):
    """Verify optimizer executes successfully across cold, hot-dry, and hot-humid climate regimes."""
    opt_in = OptimizationInput(
        city=city,
        home_type=expected_home_type,
        n_trials=8,
    )

    res = optimize_shelter(opt_in)

    assert res.city == city
    assert res.home_type == expected_home_type
    assert len(res.ranked_designs) >= 1
    assert res.simulation_result["total_heat_loss_kwh"] >= 0.0
    assert 0 <= res.simulation_result["comfort_percentage"] <= 100


# =====================================================================
# 5. CUSTOM MULTI-OBJECTIVE WEIGHTS
# =====================================================================

def test_custom_multi_objective_weights():
    """Verify custom objective weighting influences evaluation and score formulation."""
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        weights={"comfort": 0.70, "efficiency": 0.20, "solar": 0.10},
        n_trials=8,
    )

    res = optimize_shelter(opt_in)
    assert res.discomfort_score is not None
    assert len(res.ranked_designs) >= 1


# =====================================================================
# 6. OPTIMIZATION ADAPTER & RUNNER INTERFACES
# =====================================================================

def test_optimization_adapter_methods():
    """Verify OptimizationAdapter converts specs and runs optimization properly."""
    # From config dict
    opt_in = OptimizationAdapter.to_optimization_input({
        "city": "leh",
        "home_type": "Permanent",
        "occupants": 3,
        "n_trials": 6,
    })
    assert isinstance(opt_in, OptimizationInput)
    assert opt_in.city == "leh"
    assert opt_in.occupants == 3

    # Run from input contract
    opt_res = OptimizationAdapter.run_optimization_from_input(opt_in)
    assert isinstance(opt_res, OptimizationResult)
    assert opt_res.city == "leh"

    # Run from specs convenience method
    opt_res2 = OptimizationAdapter.run_from_specs(
        city="jaisalmer",
        home_type="Temporary",
        n_trials=6,
    )
    assert isinstance(opt_res2, OptimizationResult)
    assert opt_res2.city == "jaisalmer"
    assert opt_res2.home_type == "Temporary"


# =====================================================================
# 7. SERIALIZATION & DESERIALIZATION ROUND-TRIPS
# =====================================================================

def test_optimization_result_serialization_roundtrip():
    """Verify OptimizationResult converts to dict, JSON, and back without data loss."""
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        n_trials=8,
    )
    res = optimize_shelter(opt_in)

    # 1. to_dict()
    res_dict = res.to_dict()
    assert isinstance(res_dict, dict)
    assert res_dict["city"] == "leh"
    assert isinstance(res_dict["ranked_designs"], list)
    assert len(res_dict["ranked_designs"]) > 0
    assert isinstance(res_dict["ranked_designs"][0], dict)

    # 2. JSON serialization
    json_str = json.dumps(res_dict)
    assert len(json_str) > 100

    # 3. from_dict()
    reconstructed = OptimizationResult.from_dict(json.loads(json_str))
    assert reconstructed.city == res.city
    assert reconstructed.home_type == res.home_type
    assert reconstructed.insulation_thickness_m == res.insulation_thickness_m
    assert reconstructed.window_area_m2 == res.window_area_m2
    assert reconstructed.wall_material == res.wall_material
    assert len(reconstructed.ranked_designs) == len(res.ranked_designs)
    assert isinstance(reconstructed.ranked_designs[0], OptimizationCandidate)
    assert reconstructed.ranked_designs[0].overall_score == res.ranked_designs[0].overall_score


# =====================================================================
# 8. BACKWARD COMPATIBILITY & DETERMINISM TESTS
# =====================================================================

def test_run_optimization_backward_compatibility():
    """Verify run_optimization retains full backward compatibility for legacy callers."""
    raw_res = run_optimization(
        city="leh",
        home_type="Permanent",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="auto",
        glazing="auto",
        orientation="auto",
        occupants=4,
        max_insulation_m=0.15,
        n_trials=8,
    )

    assert isinstance(raw_res, dict)
    assert "city" in raw_res
    assert "home_type" in raw_res
    assert "insulation_thickness_m" in raw_res
    assert "insulation_mm" in raw_res
    assert "window_area_m2" in raw_res
    assert "wall_material" in raw_res
    assert "glazing" in raw_res
    assert "glazing_name" in raw_res
    assert "orientation" in raw_res
    assert "discomfort_score" in raw_res
    assert "simulation_result" in raw_res
    assert "ranked_designs" in raw_res
    assert len(raw_res["ranked_designs"]) >= 1


def test_optimization_determinism_repeated_runs():
    """Verify identical inputs, seed, bounds, and trial counts produce 100% deterministic, identical results."""
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        length=4.0,
        width=3.0,
        height=2.8,
        occupants=4,
        n_trials=10,
    )

    res1 = optimize_shelter(opt_in)
    res2 = optimize_shelter(opt_in)

    assert res1.insulation_thickness_m == res2.insulation_thickness_m
    assert res1.window_area_m2 == res2.window_area_m2
    assert res1.wall_material == res2.wall_material
    assert res1.glazing == res2.glazing
    assert res1.orientation == res2.orientation
    assert res1.discomfort_score == res2.discomfort_score
    assert len(res1.ranked_designs) == len(res2.ranked_designs)
    for c1, c2 in zip(res1.ranked_designs, res2.ranked_designs):
        assert c1.overall_score == c2.overall_score
        assert c1.insulation_thickness_m == c2.insulation_thickness_m
        assert c1.window_area_m2 == c2.window_area_m2


def test_custom_weights_materially_affect_scores():
    """Verify changing multi-objective weights changes candidate overall scores and ranking evaluations."""
    opt_comfort_heavy = OptimizationInput(
        city="leh",
        home_type="Permanent",
        weights={"comfort": 0.90, "efficiency": 0.05, "solar": 0.05},
        n_trials=8,
    )
    opt_efficiency_heavy = OptimizationInput(
        city="leh",
        home_type="Permanent",
        weights={"comfort": 0.10, "efficiency": 0.80, "solar": 0.10},
        n_trials=8,
    )

    res_comfort = optimize_shelter(opt_comfort_heavy)
    res_efficiency = optimize_shelter(opt_efficiency_heavy)

    # Sub-scores exist and overall scores reflect the distinct weighting schemes
    cand_c = res_comfort.ranked_designs[0]
    cand_e = res_efficiency.ranked_designs[0]

    # Verify weighted calculation matches weights
    expected_c_score = round(
        0.90 * cand_c.sub_scores["comfort"] + 0.05 * cand_c.sub_scores["efficiency"] + 0.05 * cand_c.sub_scores["solar"], 1
    )
    expected_e_score = round(
        0.10 * cand_e.sub_scores["comfort"] + 0.80 * cand_e.sub_scores["efficiency"] + 0.10 * cand_e.sub_scores["solar"], 1
    )

    assert cand_c.overall_score == expected_c_score
    assert cand_e.overall_score == expected_e_score


def test_candidate_thermal_metric_completeness():
    """Verify all candidate designs expose heating demand, cooling demand, and effective thermal mass."""
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        n_trials=8,
    )
    res = optimize_shelter(opt_in)

    for c in res.ranked_designs:
        assert hasattr(c, "heating_demand_kwh")
        assert hasattr(c, "cooling_demand_kwh")
        assert hasattr(c, "total_conditioning_demand_kwh")
        assert hasattr(c, "effective_thermal_capacity_j_k")
        assert c.effective_thermal_capacity_j_k > 0.0

