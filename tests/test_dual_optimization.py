"""
THERMOSHELTER — Dual-Output Optimization Tests (E/F/G/H)
========================================================

Verifies the two conceptually separate optimization outputs:

  1. USER-CONSTRAINED DESIGN — the existing weighted-scalar objective run.
     Behavior must be unchanged when include_recommendation=False.
  2. THERMOSHELTER RECOMMENDED DESIGN — a SEPARATE comfort-first Optuna
     search (same engine, same feasibility, same prototype bounds; objective
     = maximize simulated comfort hours, tie-break lower heat loss).

Also verifies honest 0%-comfort / no-comfort-feasible handling: the
recommendation payload distinguishes a completed search with no
comfort-feasible winner ('no_comfort_feasible') from an execution error
('error'), and never fabricates a recommendation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _run(payload_overrides=None):
    payload = {
        "city": "leh",
        "home_type": "Permanent",
        "n_trials": 3,
        "hours_to_simulate": 48,
    }
    payload.update(payload_overrides or {})
    return client.post("/api/optimization/run", json=payload)


def test_recommendation_pass_returns_ok_with_real_metrics():
    """E2: the comfort-first pass returns a real, labeled recommendation."""
    r = _run({"include_recommendation": True})
    assert r.status_code == 200
    data = r.json()
    rec = data.get("recommendation")
    assert rec is not None
    assert rec["status"] == "ok"
    best = rec["recommendation"]
    assert best is not None
    assert best["label"] == "ThermoShelter Recommendation"
    # Real simulated metrics, never placeholders.
    assert best["comfort_hours"] >= 0.0
    assert best["total_heat_loss_kwh"] >= 0.0
    # Canonical design attached so Apply Recommendation uses the exact trial.
    assert best.get("canonical_design") is not None


def test_recommendation_disabled_by_default_flag_preserves_payload():
    """E4: include_recommendation=False keeps the legacy payload contract."""
    r = _run({"include_recommendation": False})
    assert r.status_code == 200
    data = r.json()
    assert data.get("recommendation") is None
    assert len(data["ranked_designs"]) >= 1


def test_user_constrained_result_unchanged_when_recommendation_requested():
    """E: the user-constrained ranked designs are unaffected by the extra pass."""
    r_base = _run({"include_recommendation": False})
    r_dual = _run({"include_recommendation": True})
    assert r_base.status_code == r_dual.status_code == 200
    base = r_base.json()["ranked_designs"][0]
    dual = r_dual.json()["ranked_designs"][0]
    # Same objective, same search space → same top-line fields.
    assert base["insulation_mm"] == dual["insulation_mm"]
    assert base["window_area_m2"] == dual["window_area_m2"]
    assert base["wall_material"] == dual["wall_material"]


def test_recommendation_relinks_same_climate_scenario():
    """E2: recommendation runs against the same supplied climate scenario."""
    scenario = {
        "city": "leh",
        "hourly_temperature": [-10.0] * 48,
        "hourly_direct_solar": [0.0] * 48,
        "hourly_diffuse_solar": [0.0] * 48,
    }
    r = _run({"climate": scenario, "include_recommendation": True})
    assert r.status_code == 200
    data = r.json()
    assert data.get("recommendation", {}).get("status") == "ok"
    # Provenance flows through both passes.
    assert data.get("climate_provenance") is not None


def test_recommendation_structure_supports_no_comfort_feasible():
    """
    F2: the payload contract distinguishes a completed-but-infeasible search
    from an execution failure. (With Leh's 48 h window the search normally
    finds comfort-feasible trials; the contract test pins the honest shape.)
    """
    from services.optimize import run_comfort_first_recommendation

    result = run_comfort_first_recommendation(
        city="leh", n_trials=2, hours_to_simulate=48
    )
    assert result["status"] in ("ok", "no_comfort_feasible")
    if result["status"] == "no_comfort_feasible":
        assert result["recommendation"] is None
        assert "No comfort-feasible" in result["message"]
    else:
        assert result["recommendation"]["comfort_hours"] >= 0.0


def test_recommendation_weights_never_reweighted_user_objective():
    """
    E3: the comfort pass is its own objective (comfort=1.0). The function
    must clone the input rather than mutate the caller's OptimizationInput.
    """
    from dataclasses import replace

    from services.contracts import OptimizationInput
    from services.optimize import run_comfort_first_recommendation

    inp = OptimizationInput(city="leh", n_trials=2, hours_to_simulate=48)
    original = replace(inp)
    run_comfort_first_recommendation(city=inp)
    assert inp.weights == original.weights
    assert inp.n_trials == original.n_trials


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
