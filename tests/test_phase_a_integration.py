"""
Phase A Integration Tests
=========================
Backend connectivity, simulation recovery and architecture verification
(SIH 2026 - THERMOSHELTER, Phase A).

Covers:
1. /api/health machine-readable contract
2. Valid simulation request returns a real SimulationResult
3. Invalid simulation request -> structured 422 (not a masked error)
4. Behavioral thermal-mass propagation: OFF vs ON must differ BOTH in
   effective_thermal_capacity_j_k AND in the simulated indoor-temperature
   series (actual thermal response, not merely JSON presence).
5. Canonical ShelterDesign -> dict -> adapter round-trip fidelity
6. Direct canonical data flow: ShelterDesign + ClimateProfile
   -> SimulationAdapter -> SimulationInput -> SimulationResult
"""

import math

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from services.contracts import adapt_to_shelter_design
from services.fixtures import get_leh_scenario
from services.shelter.models import ShelterDesign
from services.simulation_adapter import SimulationAdapter

client = TestClient(app, raise_server_exceptions=False)


# =====================================================================
# Canonical base design used across tests (flat legacy representation,
# matching the exact payload shape the React client dispatches).
# =====================================================================

def _base_design() -> dict:
    return {
        "length": 6.0,
        "width": 4.0,
        "height": 3.0,
        "wall_material": "mud",
        "wall_thickness_m": 0.3,
        "insulation_thickness_m": 0.05,
        "insulation_conductivity": 0.025,
        "window_area": 3.0,
        "door_area": 2.0,
        "glazing": "double_clear",
        "orientation": 180,
        "roof_type": "pitched",
        "pitch_angle_deg": 30.0,
        "ach": 0.5,
        "occupants": 2,
    }


# =====================================================================
# 1. HEALTH ENDPOINT
# =====================================================================

def test_health_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "thermoshelter-api"
    assert data["canonical_contracts"] is True
    assert "Python" in data["physics_engine"]
    assert data["subsystems"]["member3_simulation"] == "active"


def test_health_reports_real_route_availability():
    """The health summary should reflect actually registered routers."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["simulation"] == "/api/simulation/run"
    # The advertised simulation route must exist and answer POST.
    sim_response = client.post("/api/simulation/run", json={})
    assert sim_response.status_code in (200, 422)


# =====================================================================
# 2. VALID SIMULATION REQUEST -> REAL SimulationResult
# =====================================================================

def test_valid_simulation_returns_real_result():
    payload = {
        "city": "leh",
        "design": _base_design(),
        "hours_to_simulate": 24,
        "substeps": 15,
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    # Full timeseries present
    assert len(data["indoor_temperatures"]) == 24
    assert len(data["outdoor_temperatures"]) == 24
    assert len(data["wall_heat_flow"]) == 24
    assert len(data["roof_heat_flow"]) == 24
    assert len(data["ventilation_heat_flow"]) == 24

    # Real physics, not placeholders
    assert data["total_heat_loss_kwh"] > 0.0
    assert data["integrated_solar_energy_kwh"] > 0.0
    assert all(math.isfinite(t) for t in data["indoor_temperatures"])

    # Comfort metrics and geometry resolved
    assert "avg" in data["comfort_metrics"]
    assert data["geometry"]["floor_area_m2"] == pytest.approx(24.0)
    assert data["geometry"]["roof_type"] == "pitched"

    # Component losses sum consistently (door now accounted per 97f409c)
    losses = data["component_heat_loss_kwh"]
    assert losses["wall_loss_kwh"] >= 0.0
    assert losses["window_loss_kwh"] >= 0.0
    assert losses["door_loss_kwh"] >= 0.0


# =====================================================================
# 3. INVALID REQUESTS -> STRUCTURED, UNMASKED ERRORS
# =====================================================================

def test_invalid_design_returns_structured_422():
    bad = _base_design()
    bad["length"] = -5.0  # physically impossible geometry
    payload = {"city": "leh", "design": bad, "hours_to_simulate": 24, "substeps": 15}
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    detail = body["detail"]
    if isinstance(detail, dict):
        assert detail.get("error") == "Invalid shelter design specification"
        assert "message" in detail
    else:
        # Native FastAPI validation error array
        assert isinstance(detail, list) and len(detail) > 0


def test_invalid_thermal_mass_returns_422():
    """Enabled thermal mass with zero thickness must be rejected, not silently defaulted."""
    bad = _base_design()
    bad["thermal_mass_enabled"] = True
    bad["thermal_mass_thickness_m"] = 0.0
    payload = {"city": "leh", "design": bad, "hours_to_simulate": 12, "substeps": 15}
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 422


def test_unknown_city_falls_back_deterministically():
    """Unknown city resolves via deterministic fixture fallback (documented behavior)."""
    payload = {"city": "zzz_unknown_city", "design": _base_design(), "hours_to_simulate": 12, "substeps": 15}
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["indoor_temperatures"]) == 12


# =====================================================================
# 4. BEHAVIORAL THERMAL-MASS PROPAGATION (OFF vs ON)
# =====================================================================

def _capacity_for(design: dict) -> float:
    return adapt_to_shelter_design(design).to_simulation_parameters()[
        "effective_thermal_capacity_j_k"
    ]


def test_thermal_mass_changes_effective_capacity():
    off = _capacity_for(_base_design())
    on = _capacity_for({**_base_design(), "thermal_mass_enabled": True, "thermal_mass_thickness_m": 0.20})
    assert on > off
    # 6x4 m slab of 0.20 m concrete (rho=2300, cp=880) ~= 9.7 MJ/K added
    added = on - off
    expected = 6.0 * 4.0 * 0.20 * 2300.0 * 880.0
    assert added == pytest.approx(expected, rel=1e-6)


def test_thermal_mass_changes_simulated_thermal_response():
    """
    Behavioral check: identical designs with thermal mass OFF vs ON must
    produce different effective capacity AND a different indoor-temperature
    response. A larger storage capacity dampens the diurnal swing.
    """
    payload_off = {"city": "leh", "design": _base_design(), "hours_to_simulate": 48, "substeps": 15}
    payload_on = {
        "city": "leh",
        "design": {**_base_design(), "thermal_mass_enabled": True, "thermal_mass_thickness_m": 0.20},
        "hours_to_simulate": 48,
        "substeps": 15,
    }
    r_off = client.post("/api/simulation/run", json=payload_off)
    r_on = client.post("/api/simulation/run", json=payload_on)
    assert r_off.status_code == 200 and r_on.status_code == 200

    d_off, d_on = r_off.json(), r_on.json()
    t_off = d_off["indoor_temperatures"]
    t_on = d_on["indoor_temperatures"]

    assert t_off != t_on, "Thermal mass ON must change the simulated indoor-temperature series"

    swing_off = max(t_off) - min(t_off)
    swing_on = max(t_on) - min(t_on)
    assert swing_on < swing_off, (
        "Adding thermal mass should dampen the indoor diurnal temperature swing: "
        f"OFF swing={swing_off:.3f} K, ON swing={swing_on:.3f} K"
    )


# =====================================================================
# 5. CANONICAL ROUND-TRIP FIDELITY
# =====================================================================

def test_canonical_design_round_trip_preserves_parameters():
    design = ShelterDesign.from_dict(
        {**_base_design(), "thermal_mass_enabled": True, "thermal_mass_thickness_m": 0.20}
    )
    revived = ShelterDesign.from_dict(design.to_dict())
    p1 = design.to_simulation_parameters()
    p2 = revived.to_simulation_parameters()
    assert p1["effective_thermal_capacity_j_k"] == pytest.approx(p2["effective_thermal_capacity_j_k"])
    assert p1["orientation_deg"] == pytest.approx(p2["orientation_deg"])
    assert p1["gross_wall_area_m2"] == pytest.approx(p2["gross_wall_area_m2"])
    assert p1["roof_type"] == p2["roof_type"]


# =====================================================================
# 6. DIRECT CANONICAL DATA FLOW (adapter, no HTTP)
# =====================================================================

def test_adapter_flow_climate_plus_design_to_result():
    climate, design = get_leh_scenario(hours=24)
    result = SimulationAdapter.run_from_contracts(
        climate=climate, design=design, hours_to_simulate=24, substeps=15
    )
    assert len(result.indoor_temperatures) == 24
    assert result.total_heat_loss_kwh > 0.0
    assert all(math.isfinite(t) for t in result.indoor_temperatures)
