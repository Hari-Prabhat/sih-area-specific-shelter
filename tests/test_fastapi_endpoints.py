"""
Tests for FastAPI API endpoints in api.py
Verifies that all endpoints return expected schema and status codes.
"""

import pytest
from api import (
    health,
    get_cities,
    get_climate,
    get_materials,
    get_single_material,
    get_shelter_models,
    get_glazing,
    get_orientations,
    post_auto_size,
    post_recommend_materials,
    post_simulation,
    post_sensitivity,
    get_validation,
    AutoSizeRequest,
    RecommendMaterialsRequest,
    SimulationRequest,
    SensitivityRequest,
)


def test_api_health():
    res = health()
    assert res["status"] == "ok"
    assert "service" in res


def test_api_get_cities():
    res = get_cities()
    assert "cities" in res
    assert len(res["cities"]) >= 3
    city_ids = [c["id"] for c in res["cities"]]
    assert "leh" in city_ids
    assert "jaisalmer" in city_ids
    assert "chennai" in city_ids


def test_api_get_climate():
    res = get_climate("leh")
    assert res["city"] == "leh"
    assert len(res["hourly_temperature"]) >= 168
    assert res["climate_type"] == "cold"


def test_api_get_materials():
    res = get_materials()
    assert "materials" in res
    assert "brick" in res["materials"]


def test_api_get_single_material():
    mat = get_single_material("brick")
    assert mat["id"] == "brick"
    assert "thermal_conductivity" in mat


def test_api_shelter_models():
    res = get_shelter_models()
    assert "models" in res
    assert "rectangular_pitched" in res["models"]


def test_api_glazing_and_orientations():
    gl = get_glazing()
    assert "double_clear" in gl["glazing"]
    ori = get_orientations()
    assert "south" in ori["orientations"]


def test_api_auto_size():
    req = AutoSizeRequest(people=4, home_type="Permanent")
    res = post_auto_size(req)
    assert res["floor_area_m2"] >= 18.0
    assert res["length_m"] > 0
    assert res["width_m"] > 0


def test_api_recommend_materials():
    req = RecommendMaterialsRequest(climate_type="cold", home_type="Permanent")
    res = post_recommend_materials(req)
    assert "wall_material_name" in res


def test_api_simulation_endpoint():
    req = SimulationRequest(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=2.0,
        glazing="double_clear",
        orientation="south",
        roof_type="flat",
        occupants=2,
        hours_to_simulate=24,
    )
    res = post_simulation(req)
    assert len(res["indoor_temperature"]) == 24
    assert "comfort_percentage" in res
    assert "total_heat_loss_kwh" in res


def test_api_sensitivity_endpoint():
    req = SensitivityRequest(city="leh", parameter="insulation", occupants=2)
    res = post_sensitivity(req)
    assert res["parameter"] == "Insulation Thickness"
    assert len(res["values"]) > 0
    assert len(res["comfort"]) == len(res["values"])


def test_api_validation_endpoint():
    res = get_validation()
    assert "steady_state" in res
    assert "transient" in res
    assert res["steady_state"]["rel_error_pct"] < 0.001
