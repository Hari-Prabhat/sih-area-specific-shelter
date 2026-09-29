"""
Unit & Integration Tests for Optimization API & Adapter
======================================================
Validates the POST /api/optimization/run endpoint, canonical digital twin
mapping via OptimizationAdapter, error handling, parameter variation,
and JSON serialization.
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from services.contracts import (
    OptimizationInput,
    OptimizationResult,
    OptimizationCandidate,
    ShelterDesign,
    create_mock_shelter_design,
)
from services.simulation_adapter import OptimizationAdapter

client = TestClient(app)


# =====================================================================
# 1. OPTIMIZATION ADAPTER CANONICAL MAPPING TESTS
# =====================================================================

def test_adapter_from_shelter_design():
    """Verify OptimizationAdapter converts canonical ShelterDesign to OptimizationInput."""
    sd = create_mock_shelter_design(
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=2.5,
        glazing="double_clear",
        occupants=3,
        shelter_type="Permanent",
    )

    opt_in = OptimizationAdapter.from_shelter_design(
        design=sd,
        city_or_climate="leh",
        n_trials=5,
    )

    assert isinstance(opt_in, OptimizationInput)
    assert opt_in.city == "leh"
    assert opt_in.home_type == "Permanent"
    assert opt_in.length == sd.length
    assert opt_in.width == sd.width
    assert opt_in.height == sd.height
    assert opt_in.occupants == 3
    assert opt_in.n_trials == 5


def test_adapter_candidate_to_canonical_shelter_design():
    """Verify OptimizationAdapter converts an OptimizationCandidate into a canonical digital twin."""
    sd_base = create_mock_shelter_design()
    candidate = OptimizationCandidate(
        rank=1,
        label="Design #1",
        rationale="Optimal passive configuration",
        overall_score=85.5,
        sub_scores={"comfort": 90.0, "efficiency": 80.0, "solar": 85.0},
        insulation_mm=80.0,
        insulation_thickness_m=0.08,
        window_area_m2=3.0,
        wall_material="puf_insulation",
        wall_material_name="PUF Insulation",
        glazing="double_low_e",
        glazing_name="Double Low-E",
        orientation="south",
        comfort_hours=140.0,
        comfort_percentage=83.3,
        discomfort_dh=25.0,
        total_heat_loss_kwh=120.0,
        solar_gain_kwh=45.0,
        u_values={"wall_u": 0.28, "roof_u": 0.35, "floor_u": 0.40, "window_u": 1.8},
    )

    cand_sd = OptimizationAdapter.candidate_to_shelter_design(candidate, base_design=sd_base)

    assert isinstance(cand_sd, ShelterDesign)
    assert cand_sd.length == sd_base.length
    assert cand_sd.width == sd_base.width
    assert cand_sd.wall_material == "puf_insulation"
    assert cand_sd.insulation_thickness_m == 0.08
    assert cand_sd.window_area == 3.0
    assert cand_sd.orientation in ["south", 180.0]
    assert cand_sd.provenance == "optimized"


# =====================================================================
# 2. FASTAPI ENDPOINT: POST /api/optimization/run (REAL OPTIMIZER)
# =====================================================================

def test_optimization_endpoint_valid_request():
    """Verify POST /api/optimization/run executes real Optuna TPE and returns ranked designs."""
    payload = {
        "city": "leh",
        "home_type": "Permanent",
        "design": {
            "length": 4.0,
            "width": 3.0,
            "height": 2.8,
            "wall_material": "brick",
            "insulation_thickness_m": 0.0,
            "window_area": 1.5,
            "glazing": "single_clear",
            "occupants": 2,
        },
        "n_trials": 3,
        "substeps": 15,
        "hours_to_simulate": 48,
    }

    response = client.post("/api/optimization/run", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Core response assertions
    assert data["city"] == "leh"
    assert data["home_type"] == "Permanent"
    assert "discomfort_score" in data
    assert "simulation_result" in data
    assert "ranked_designs" in data
    assert len(data["ranked_designs"]) >= 1

    # Recommended design exposed clearly
    assert "recommended_design" in data
    rec = data["recommended_design"]
    assert rec["rank"] == 1
    assert "overall_score" in rec
    assert "sub_scores" in rec
    assert "canonical_design" in rec


def test_optimization_endpoint_rejects_invalid_design():
    """Verify endpoint rejects design with invalid dimensions (<= 0) with HTTP 422."""
    payload = {
        "city": "leh",
        "design": {
            "length": -4.0,  # Invalid negative length
            "width": 3.0,
            "height": 2.8,
        },
        "n_trials": 2,
    }

    response = client.post("/api/optimization/run", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert "detail" in err


def test_optimization_endpoint_rejects_invalid_climate():
    """Verify endpoint rejects unrecognized/invalid city with HTTP 422."""
    payload = {
        "city": "invalid_nonexistent_city_xyz_999",
        "design": {
            "length": 4.0,
            "width": 3.0,
            "height": 2.8,
        },
        "n_trials": 2,
    }

    response = client.post("/api/optimization/run", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert "detail" in err


def test_optimization_candidate_differs_from_unoptimized_baseline():
    """
    Verify that the optimizer varies parameters and produces a recommended candidate
    that differs from an uninsulated baseline (higher insulation or improved glazing).
    """
    baseline_design = {
        "length": 4.0,
        "width": 3.0,
        "height": 2.8,
        "wall_material": "brick",
        "insulation_thickness_m": 0.0,
        "window_area": 1.0,
        "glazing": "single_clear",
        "orientation": "north",
    }

    payload = {
        "city": "leh",
        "home_type": "Permanent",
        "design": baseline_design,
        "min_insulation_m": 0.05,
        "max_insulation_m": 0.15,
        "n_trials": 4,
        "substeps": 15,
        "hours_to_simulate": 48,
    }

    response = client.post("/api/optimization/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    rec = data["recommended_design"]
    # Insulation must be >= min_insulation_m (0.05m), differing from baseline 0.0m
    assert rec["insulation_thickness_m"] >= 0.05
    assert rec["insulation_thickness_m"] > baseline_design["insulation_thickness_m"]


def test_optimization_response_is_fully_json_serializable():
    """Verify all returned candidate records and nested structures are strictly JSON serializable."""
    payload = {
        "city": "leh",
        "home_type": "Permanent",
        "n_trials": 3,
        "substeps": 15,
        "hours_to_simulate": 48,
    }

    response = client.post("/api/optimization/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Round-trip JSON dump & load verification
    serialized_str = json.dumps(data)
    assert len(serialized_str) > 0
    deserialized = json.loads(serialized_str)

    assert deserialized["city"] == "leh"
    assert len(deserialized["ranked_designs"]) >= 1
    for cand in deserialized["ranked_designs"]:
        assert "rank" in cand
        assert "overall_score" in cand
        assert "sub_scores" in cand
        assert "canonical_design" in cand
        assert isinstance(cand["sub_scores"], dict)
