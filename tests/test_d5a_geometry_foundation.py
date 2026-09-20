"""
THERMOSHELTER - D5-A Geometry-Optimization Foundation Tests
===========================================================

Verifies the D5-A CONTRACT-ONLY foundation:

  1. OptimizationInput geometry bounds validation (positivity, finiteness,
     min <= max, explicit bounds required, base dimension within bounds).
  2. Backward compatibility: optimize_geometry=False behaves exactly as
     Phase C (no geometry fields required, no optimizer behaviour change).
  3. Candidate DTO geometry fields round-trip through the contract.
  4. Existing (non-geometry) candidates report their BASE geometry
     accurately, sourced from the engine's own result block.
  5. Apply-Candidate preparation: geometry carried only when present.
  6. Opening-feasibility boundary helpers (no invented margins).
  7. Climate scenario flow unchanged (supplied profile is THE scenario).
  8. Explicit rejection when optimize_geometry=True is requested before
     D5-B implements the search.

No arbitrary engineering limits are introduced or tested - the contract
must FAIL when bounds are missing, never invent them.
"""

import pytest

from services.contracts import (
    OptimizationCandidate,
    OptimizationInput,
    create_mock_climate_profile,
    create_mock_shelter_design,
)
from services.geometry import calculate_wall_area
from services.geometry_feasibility import openings_fit_within_envelope
from services.simulation_adapter import OptimizationAdapter


# =====================================================================
# 1. GEOMETRY BOUNDS VALIDATION
# =====================================================================

VALID_BOUNDS = {
    "optimize_geometry": True,
    "min_length_m": 3.0,
    "max_length_m": 6.0,
    "min_width_m": 2.0,
    "max_width_m": 4.0,
    "min_height_m": 2.0,
    "max_height_m": 3.0,
}


def test_valid_geometry_bounds_accepted():
    """A complete, valid geometry configuration constructs without error."""
    oi = OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8, **VALID_BOUNDS)
    assert oi.optimize_geometry is True
    assert oi.min_length_m == 3.0 and oi.max_length_m == 6.0
    assert oi.min_width_m == 2.0 and oi.max_width_m == 4.0
    assert oi.min_height_m == 2.0 and oi.max_height_m == 3.0


def test_min_greater_than_max_rejected():
    """min > max is mathematically invalid and must be rejected."""
    for dim in ("length", "width", "height"):
        bad = dict(VALID_BOUNDS)
        bad[f"min_{dim}_m"], bad[f"max_{dim}_m"] = 5.0, 4.0
        with pytest.raises(ValueError, match="cannot be less than"):
            OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8, **bad)


def test_non_finite_bounds_rejected():
    """NaN and infinite bounds must be rejected (not silently accepted)."""
    import math
    for bad_value in (float("nan"), float("inf"), float("-inf")):
        bad = dict(VALID_BOUNDS)
        bad["min_length_m"] = bad_value
        with pytest.raises(ValueError, match="finite"):
            OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8, **bad)
    assert math.isnan(float("nan"))  # sanity: math import used


def test_non_positive_bounds_rejected():
    """Dimensions are physical lengths: zero and negative bounds are invalid."""
    for bad_value in (0.0, -1.0):
        bad = dict(VALID_BOUNDS)
        bad["max_height_m"] = bad_value
        with pytest.raises(ValueError, match="strictly positive"):
            OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8, **bad)


def test_missing_bounds_fail_loudly():
    """optimize_geometry=True with ANY missing bound must fail - no invented defaults."""
    fields = ("min_length_m", "max_length_m", "min_width_m", "max_width_m", "min_height_m", "max_height_m")
    for missing in fields:
        partial = {k: v for k, v in VALID_BOUNDS.items() if k != missing}
        with pytest.raises(ValueError, match="explicit"):
            OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8, **partial)


def test_base_dimension_outside_bounds_rejected():
    """The baseline geometry must lie inside the search space it defines."""
    bad = dict(VALID_BOUNDS)
    bad["min_height_m"], bad["max_height_m"] = 3.0, 4.0  # base height 2.8 outside
    with pytest.raises(ValueError, match="outside the geometry bounds"):
        OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8, **bad)


# =====================================================================
# 2. BACKWARD COMPATIBILITY (optimize_geometry=False)
# =====================================================================

def test_geometry_bounds_ignored_when_disabled():
    """Without optimize_geometry, missing bounds are fine and validation passes."""
    oi = OptimizationInput(city="leh", length=4.0, width=3.0, height=2.8)
    assert oi.optimize_geometry is False
    assert oi.min_length_m is None  # nothing invented


def test_optimize_geometry_true_runs_geometry_search():
    """
    D5-B SUPERSEDES the D5-A interim guard: requesting geometry optimization
    now RUNS the geometry search (which previously raised "not yet
    implemented"). The D5-A guard existed only to prevent a silent
    fixed-geometry search pretending to optimize; the real search removes
    that hazard. Assert the search executes and returns geometry-carrying
    candidates within the supplied bounds.
    """
    from services.optimize import optimize_shelter

    sd = create_mock_shelter_design()  # 4.5 x 3.2 x 2.8
    opt_input = OptimizationAdapter.from_shelter_design(
        design=sd,
        city_or_climate=create_mock_climate_profile(),
        n_trials=2,
        optimize_geometry=True,
        min_length_m=3.0, max_length_m=6.0,
        min_width_m=2.0, max_width_m=4.0,
        min_height_m=2.0, max_height_m=3.0,
    )
    result = optimize_shelter(opt_input)
    assert result.ranked_designs, "geometry search must produce candidates"
    for c in result.ranked_designs:
        assert c.length_m is not None
        assert 3.0 <= c.length_m <= 6.0
        assert 2.0 <= c.width_m <= 4.0
        assert 2.0 <= c.height_m <= 3.0


def test_adapter_passes_geometry_bounds_through():
    """OptimizationAdapter.from_shelter_design forwards geometry configuration."""
    sd = create_mock_shelter_design()
    opt_input = OptimizationAdapter.from_shelter_design(
        design=sd,
        city_or_climate="leh",
        optimize_geometry=True,
        min_length_m=3.0, max_length_m=6.0,
        min_width_m=2.0, max_width_m=4.0,
        min_height_m=2.0, max_height_m=3.0,
    )
    assert opt_input.optimize_geometry is True
    assert opt_input.max_length_m == 6.0
    # Round-trip through dict preserves the contract (serialization check)
    restored = OptimizationInput.from_dict(opt_input.to_dict())
    assert restored.optimize_geometry is True
    assert restored.min_width_m == 2.0
    assert restored.max_height_m == 3.0


# =====================================================================
# 3. CANDIDATE DTO GEOMETRY FIELDS
# =====================================================================

def test_candidate_geometry_round_trip():
    """Candidate geometry fields serialize and deserialize losslessly."""
    cand = OptimizationCandidate(
        rank=1,
        label="Design #1",
        rationale="test",
        overall_score=80.0,
        sub_scores={"comfort": 60.0, "efficiency": 70.0, "solar": 10.0},
        insulation_mm=50.0,
        insulation_thickness_m=0.05,
        window_area_m2=2.0,
        wall_material="brick",
        wall_material_name="Brick",
        glazing="double_clear",
        glazing_name="Double Glazed",
        orientation="south",
        comfort_hours=100.0,
        comfort_percentage=59.5,
        discomfort_dh=606.0,
        total_heat_loss_kwh=30.0,
        solar_gain_kwh=5.0,
        u_values={"wall_u": 0.5, "roof_u": 0.4, "floor_u": 0.6, "window_u": 2.8},
        length_m=4.0,
        width_m=3.0,
        height_m=2.8,
        floor_area_m2=12.0,
        surface_to_volume_ratio=2.6,
    )
    d = cand.to_dict()
    assert d["length_m"] == 4.0 and d["floor_area_m2"] == 12.0
    restored = OptimizationCandidate.from_dict(d)
    assert restored.length_m == 4.0
    assert restored.width_m == 3.0
    assert restored.height_m == 2.8
    assert restored.floor_area_m2 == 12.0
    assert restored.surface_to_volume_ratio == 2.6


def test_candidate_geometry_fields_optional():
    """Legacy candidate dicts without geometry fields deserialize to None (no fabrication)."""
    legacy = {
        "rank": 2,
        "label": "Design #2",
        "rationale": "",
        "overall_score": 70.0,
        "sub_scores": {},
        "insulation_mm": 100.0,
        "insulation_thickness_m": 0.1,
        "window_area_m2": 1.5,
        "wall_material": "brick",
        "wall_material_name": "Brick",
        "glazing": "double_clear",
        "glazing_name": "Double Glazed",
        "orientation": "south",
        "comfort_hours": 90.0,
        "comfort_percentage": 53.6,
        "discomfort_dh": 700.0,
        "total_heat_loss_kwh": 35.0,
        "solar_gain_kwh": 4.0,
        "u_values": {},
    }
    cand = OptimizationCandidate.from_dict(legacy)
    assert cand.length_m is None
    assert cand.surface_to_volume_ratio is None


# =====================================================================
# 4. EXISTING CANDIDATES REPORT BASE GEOMETRY ACCURATELY
# =====================================================================

def test_candidate_geometry_helper_uses_engine_reported_values():
    """
    _candidate_geometry_fields must prefer the ENGINE's own geometry block
    (single authority). A synthetic engine result with known values proves
    the engine path; the fallback path is only defensive.
    """
    from services.optimize import _candidate_geometry_fields

    engine_result = {
        "geometry": {
            "floor_area_m2": 12.0,   # engine says 12.0 (4.0 x 3.0)
            "volume_m3": 33.6,       # engine says 33.6
            "roof_area_m2": 12.0,    # flat roof
        }
    }
    fields = _candidate_geometry_fields(engine_result, 4.0, 3.0, 2.8)
    assert fields["length_m"] == 4.0
    assert fields["width_m"] == 3.0
    assert fields["height_m"] == 2.8
    assert fields["floor_area_m2"] == 12.0  # engine value, not recomputed
    # S/V = (walls 39.2 + roof 12.0 + floor 12.0) / 33.6
    assert fields["surface_to_volume_ratio"] == round((39.2 + 12.0 + 12.0) / 33.6, 4)


def test_candidate_geometry_helper_handles_missing_roof_area():
    """Without a roof area the helper falls back to canonical envelope formula."""
    from services.optimize import _candidate_geometry_fields
    from services.geometry import calculate_total_envelope_area

    fields = _candidate_geometry_fields({"geometry": {}}, 4.0, 3.0, 2.8)
    expected_envelope = calculate_total_envelope_area(4.0, 3.0, 2.8)
    assert fields["floor_area_m2"] == 12.0
    assert fields["surface_to_volume_ratio"] == round(expected_envelope / 33.6, 4)


def test_candidate_geometry_helper_zero_volume_yields_none():
    """Physically impossible zero volume yields None, never a fabricated ratio."""
    from services.optimize import _candidate_geometry_fields

    fields = _candidate_geometry_fields({"geometry": {"volume_m3": 0.0}}, 4.0, 3.0, 2.8)
    assert fields["surface_to_volume_ratio"] is None


# =====================================================================
# 5. APPLY-CANDIDATE PREPARATION (frontend contract mirrored here)
# =====================================================================

def test_candidate_patch_carries_geometry_only_when_present():
    """
    The frontend candidateDesignPatch applies geometry ONLY when the
    candidate actually carries geometry values. Contract mirrored:
    absent geometry fields must not zero-out or overwrite base design.
    (Frontend implementation is tested in the Vitest suite; here we pin
    the contract that candidates without geometry expose None.)
    """
    cand_without = OptimizationCandidate.from_dict({
        "rank": 1, "label": "L", "rationale": "", "overall_score": 1.0,
        "sub_scores": {}, "insulation_mm": 0.0, "insulation_thickness_m": 0.0,
        "window_area_m2": 1.0, "wall_material": "brick", "wall_material_name": "B",
        "glazing": "double_clear", "glazing_name": "D", "orientation": "south",
        "comfort_hours": 0.0, "comfort_percentage": 0.0, "discomfort_dh": 0.0,
        "total_heat_loss_kwh": 0.0, "solar_gain_kwh": 0.0, "u_values": {},
    })
    assert cand_without.length_m is None  # patch must skip geometry


# =====================================================================
# 6. OPENING-FEASIBILITY BOUNDARY (D5-B preparation)
# =====================================================================

def test_openings_fit_within_envelope_valid():
    """Standard design passes with engine-derived wall area."""
    verdict = openings_fit_within_envelope(4.0, 3.0, 2.8, window_area=2.0, door_area=1.8)
    assert verdict["feasible"] is True
    assert verdict["reason"] is None
    assert verdict["gross_wall_area_m2"] == pytest.approx(calculate_wall_area(4.0, 3.0, 2.8), abs=1e-9)


def test_openings_exceeding_wall_area_rejected():
    """Openings larger than the gross wall area are infeasible (no clamping)."""
    verdict = openings_fit_within_envelope(2.0, 2.0, 2.0, window_area=10.0, door_area=10.0)
    assert verdict["feasible"] is False
    assert "exceeds gross wall area" in verdict["reason"]


def test_openings_boundary_rejects_invalid_geometry():
    """Non-positive and non-finite geometry fail honestly with no fabricated areas."""
    for bad_dims in ((0.0, 3.0, 2.8), (-4.0, 3.0, 2.8)):
        verdict = openings_fit_within_envelope(*bad_dims, window_area=1.0, door_area=1.0)
        assert verdict["feasible"] is False
        assert verdict["gross_wall_area_m2"] is None
    import math
    verdict = openings_fit_within_envelope(float("nan"), 3.0, 2.8, window_area=1.0, door_area=1.0)
    assert verdict["feasible"] is False
    assert math.isnan(float("nan"))  # silence linters re: import placement


def test_openings_boundary_zero_openings_feasible():
    """A sealed envelope (0 openings) is mathematically feasible."""
    verdict = openings_fit_within_envelope(4.0, 3.0, 2.8, window_area=0.0, door_area=0.0)
    assert verdict["feasible"] is True


# =====================================================================
# 7. CLIMATE SCENARIO FLOW UNCHANGED
# =====================================================================

def test_climate_scenario_still_flows_with_geometry_contract():
    """
    Phase C guarantee holds under the extended contract: a supplied
    ClimateProfile remains THE optimization scenario (round-trips through
    OptimizationInput untouched).
    """
    profile = create_mock_climate_profile(city="leh")
    scenario_dict = profile.to_dict()

    opt_input = OptimizationAdapter.from_shelter_design(
        design=create_mock_shelter_design(),
        city_or_climate=profile,
        n_trials=2,
    )
    assert opt_input.climate_scenario is not None
    assert opt_input.climate_scenario.get("hourly_temperature") == scenario_dict.get("hourly_temperature")
    # Geometry contract defaults are inert
    assert opt_input.optimize_geometry is False


def test_optimization_input_dict_round_trip_preserves_scenario_and_geometry():
    """Full dict round-trip: scenario vectors + geometry bounds survive together."""
    profile = create_mock_climate_profile(city="leh")
    payload = {
        "city": "leh",
        "length": 4.0,
        "width": 3.0,
        "height": 2.8,
        "climate_scenario": profile.to_dict(),
        **VALID_BOUNDS,
    }
    restored = OptimizationInput.from_dict(payload)
    assert restored.optimize_geometry is True
    assert restored.max_length_m == 6.0
    assert restored.climate_scenario is not None
    assert len(restored.climate_scenario.get("hourly_temperature", [])) > 0
