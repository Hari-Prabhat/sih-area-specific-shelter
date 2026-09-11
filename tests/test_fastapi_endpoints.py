"""
Unit & Integration Tests for ThermoShelter FastAPI Backend
===========================================================
Tests health endpoint, simulation execution pipeline, climate routes,
and validation rejection error handling.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from services.fixtures import get_golden_ladakh_scenario, get_leh_scenario

client = TestClient(app)


# =====================================================================
# 1. HEALTH CHECK ENDPOINT
# =====================================================================

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["canonical_contracts"] is True
    assert "Python" in data["physics_engine"]
    assert data["subsystems"]["member3_simulation"] == "active"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "simulation" in data


# =====================================================================
# 2. SIMULATION ENDPOINT: CANONICAL INPUT
# =====================================================================

def test_run_simulation_with_canonical_contracts():
    """
    Tests simulation endpoint using full canonical ShelterDesign and ClimateProfile contracts.
    Proves real end-to-end execution through SimulationAdapter into the Python thermal engine.
    """
    climate, design = get_golden_ladakh_scenario(hours=48)

    payload = {
        "design": design.to_dict(),
        "climate": climate.to_dict(),
        "hours_to_simulate": 48,
        "substeps": 30,
        "initial_indoor_temp": 18.0,
    }

    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Verify timeseries outputs
    assert len(data["indoor_temperatures"]) == 48
    assert len(data["outdoor_temperatures"]) == 48
    assert len(data["solar_thermal_gain"]) == 48
    assert len(data["wall_heat_flow"]) == 48
    assert len(data["roof_heat_flow"]) == 48
    assert len(data["floor_heat_flow"]) == 48
    assert len(data["window_heat_flow"]) == 48
    assert len(data["ventilation_heat_flow"]) == 48

    # Verify physical metrics
    assert data["total_heat_loss_kwh"] > 0.0
    assert data["integrated_solar_energy_kwh"] > 0.0
    assert "avg" in data["comfort_metrics"]
    assert "wall_u" in data["u_values"]

    # Verify real physical calculations (shelter temp is physical and responds to boundary conditions)
    avg_in = data["comfort_metrics"]["avg"]
    avg_out = sum(data["outdoor_temperatures"]) / len(data["outdoor_temperatures"])
    assert avg_in > avg_out, "Indoor temperature should be warmer than outdoor in cold Ladakh scenario"


# =====================================================================
# 3. SIMULATION ENDPOINT: CITY SHORTCUT & ERGONOMIC INPUT
# =====================================================================

def test_run_simulation_with_city_and_flat_design():
    """
    Tests simulation endpoint with standard frontend parameters:
    city name + flat design specs.
    """
    payload = {
        "city": "leh",
        "design": {
            "length": 4.5,
            "width": 3.2,
            "height": 2.8,
            "wall_material": "brick",
            "wall_thickness_m": 0.23,
            "insulation_thickness_m": 0.08,
            "window_area": 2.5,
            "glazing": "double_low_e",
            "orientation": "south",
            "ach": 0.5,
            "occupants": 4,
        },
        "hours_to_simulate": 24,
        "substeps": 30,
    }

    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["city"] == "leh"
    assert len(data["indoor_temperatures"]) == 24
    assert data["geometry"]["floor_area_m2"] == pytest.approx(14.4, abs=0.1)


def test_run_simulation_top_level_design_params():
    """
    Tests simulation endpoint where design properties are supplied at root level.
    """
    payload = {
        "city": "jaisalmer",
        "length": 5.0,
        "width": 4.0,
        "height": 3.0,
        "wall_material": "mud",
        "wall_thickness_m": 0.30,
        "hours_to_simulate": 24,
    }

    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "jaisalmer"
    assert len(data["indoor_temperatures"]) == 24


# =====================================================================
# 4. ERROR HANDLING & VALIDATION REJECTION
# =====================================================================

def test_reject_invalid_geometry():
    """Negative or zero dimensions must be rejected with HTTP 422."""
    payload = {
        "city": "leh",
        "design": {
            "length": -5.0,  # Negative length
            "width": 3.0,
            "height": 2.8,
        }
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data or "detail" in data


def test_reject_excessive_window_area():
    """Window area exceeding total wall area must be rejected with HTTP 422."""
    payload = {
        "city": "leh",
        "design": {
            "length": 4.0,
            "width": 3.0,
            "height": 2.5,  # Gross wall area = 2 * (4+3) * 2.5 = 35 m²
            "window_area": 50.0,  # Exceeds total wall area
        }
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 422


def test_reject_invalid_simulation_parameters():
    """Invalid hours or substeps must be rejected."""
    payload = {
        "city": "leh",
        "hours_to_simulate": 0,  # Invalid
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 422


# =====================================================================
# 5. CLIMATE ROUTES INTEGRATION
# =====================================================================

def test_climate_location_route():
    payload = {"query": "Leh, Ladakh"}
    response = client.post("/api/climate/location", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "latitude" in data
    assert "longitude" in data


def test_climate_analyze_route():
    payload = {"location": "Leh, Ladakh", "include_current_weather": False}
    response = client.post("/api/climate/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "location" in data
    assert "profile" in data
    assert "classification" in data
    assert "strategy" in data
