"""
Unit Tests for Subsystem Contracts and Data Models (Phase B)
============================================================
"""

import json
import pytest
from services.contracts import (
    ClimateProfile,
    ShelterDesign,
    SimulationInput,
    SimulationResult,
    OptimizationInput,
    OptimizationResult,
    OptimizationCandidate,
    create_mock_climate_profile,
    create_mock_shelter_design,
    adapt_to_climate_profile,
    adapt_to_shelter_design,
    adapt_simulation_result,
)


# =====================================================================
# 1. CLIMATE PROFILE TESTS
# =====================================================================

def test_climate_profile_valid():
    profile = create_mock_climate_profile("leh", hours=24)
    assert profile.city == "leh"
    assert len(profile.hourly_temperature) == 24
    assert len(profile.hourly_direct_solar) == 24
    assert len(profile.hourly_diffuse_solar) == 24
    assert profile.climate_zone == "cold"

    # Serialization roundtrip
    d = profile.to_dict()
    assert isinstance(d, dict)
    profile_reconstructed = ClimateProfile.from_dict(d)
    assert profile_reconstructed.city == profile.city
    assert profile_reconstructed.hourly_temperature == profile.hourly_temperature


def test_climate_profile_invalid_lengths():
    with pytest.raises(ValueError, match="must match hourly_temperature length"):
        ClimateProfile(
            city="leh",
            latitude=34.0,
            longitude=77.0,
            hourly_temperature=[10.0, 12.0],
            hourly_direct_solar=[100.0],  # Mismatched length
            hourly_diffuse_solar=[50.0, 50.0],
        )


def test_climate_profile_invalid_coordinates():
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        ClimateProfile(
            city="leh",
            latitude=95.0,  # Invalid
            longitude=77.0,
            hourly_temperature=[10.0],
            hourly_direct_solar=[100.0],
            hourly_diffuse_solar=[50.0],
        )


def test_climate_profile_invalid_temperatures():
    with pytest.raises(ValueError, match="Invalid hourly temperature"):
        ClimateProfile(
            city="leh",
            latitude=34.0,
            longitude=77.0,
            hourly_temperature=[-150.0],  # Impossible physical temp
            hourly_direct_solar=[100.0],
            hourly_diffuse_solar=[50.0],
        )


# =====================================================================
# 2. SHELTER DESIGN TESTS
# =====================================================================

def test_shelter_design_valid():
    design = create_mock_shelter_design("Permanent", wall_material="brick", insulation_thickness_m=0.08)
    assert design.length == 4.5
    assert design.width == 3.2
    assert design.height == 2.8
    assert design.wall_material == "brick"
    assert design.insulation_thickness_m == 0.08
    assert design.shelter_type == "Permanent"

    # Serialization roundtrip
    d = design.to_dict()
    assert isinstance(d, dict)
    reconstructed = ShelterDesign.from_dict(d)
    assert reconstructed.length == design.length
    assert reconstructed.shelter_type == design.shelter_type


def test_shelter_design_temporary_defaults():
    design = create_mock_shelter_design("Temporary")
    assert design.shelter_type == "Temporary"
    assert design.height == 2.6
    assert design.roof_type == "flat"


def test_shelter_design_invalid_dimensions():
    with pytest.raises(ValueError, match="length must be strictly positive"):
        ShelterDesign(length=-1.0, width=3.0, height=2.8)

    with pytest.raises(ValueError, match="cannot exceed total wall area"):
        # Total wall area = 2 * (4 + 3) * 2.8 = 39.2 m²
        ShelterDesign(length=4.0, width=3.0, height=2.8, window_area=50.0)


def test_shelter_design_invalid_type():
    with pytest.raises(ValueError, match="shelter_type must be 'Permanent' or 'Temporary'"):
        ShelterDesign(shelter_type="TentOrSomethingElse")


# =====================================================================
# 3. SIMULATION INPUT TESTS
# =====================================================================

def test_simulation_input_valid():
    climate = create_mock_climate_profile("leh", hours=168)
    design = create_mock_shelter_design("Permanent")
    sim_input = SimulationInput(climate=climate, design=design, hours_to_simulate=168, substeps=60)

    assert sim_input.hours_to_simulate == 168
    assert sim_input.substeps == 60

    d = sim_input.to_dict()
    reconstructed = SimulationInput.from_dict(d)
    assert reconstructed.climate.city == "leh"
    assert reconstructed.design.wall_material == design.wall_material


def test_simulation_input_type_errors():
    design = create_mock_shelter_design("Permanent")
    with pytest.raises(TypeError, match="climate must be an instance of ClimateProfile"):
        SimulationInput(climate={"city": "leh"}, design=design)  # Raw dict instead of object


def test_simulation_input_hours_overflow():
    climate = create_mock_climate_profile("leh", hours=24)
    design = create_mock_shelter_design("Permanent")
    with pytest.raises(ValueError, match="exceeds available weather hours"):
        SimulationInput(climate=climate, design=design, hours_to_simulate=168)


# =====================================================================
# 4. SIMULATION RESULT TESTS
# =====================================================================

def test_simulation_result_valid_and_serialization():
    res = SimulationResult(
        city="leh",
        indoor_temperatures=[18.5, 19.0, 19.2],
        outdoor_temperatures=[-5.0, -4.0, -3.0],
        solar_irradiance=[200.0, 400.0, 500.0],
        solar_power=[400.0, 800.0, 1000.0],
        solar_thermal_gain=[250.0, 500.0, 650.0],
        hourly_internal_gain=[200.0, 200.0, 200.0],
        wall_heat_flow=[150.0, 140.0, 130.0],
        roof_heat_flow=[100.0, 95.0, 90.0],
        floor_heat_flow=[50.0, 48.0, 46.0],
        window_heat_flow=[60.0, 55.0, 50.0],
        ventilation_heat_flow=[80.0, 75.0, 70.0],
        radiation_heat_flow=[30.0, 28.0, 26.0],
        net_heat_flow=[80.0, 150.0, 200.0],
        comfort_status="Comfortable",
        comfort_status_series=["comfortable", "comfortable", "comfortable"],
        comfort_hours=3.0,
        comfort_percentage=100.0,
        discomfort_degree_hours=0.0,
        integrated_solar_energy_kwh=1.4,
        integrated_incident_solar_kwh=2.2,
        component_heat_loss_kwh={"wall_loss_kwh": 0.42, "roof_loss_kwh": 0.28},
        total_heat_loss_kwh=0.70,
        comfort_metrics={"avg": 18.9, "min_t": 18.5, "max_t": 19.2},
        energy_totals_kwh={"solar_gain_kwh": 1.4, "total_heat_loss_kwh": 0.70},
        u_values={"wall_u": 0.25, "roof_u": 0.20},
        geometry={"floor_area_m2": 14.4},
        specs={"wall_material": "brick"},
    )

    # Check legacy property aliases
    assert res.indoor_temperature == [18.5, 19.0, 19.2]
    assert res.outdoor_temperature == [-5.0, -4.0, -3.0]

    # Check dictionary serialization
    d = res.to_dict()
    assert d["city"] == "leh"
    assert "indoor_temperature" in d
    assert "indoor_temperatures" in d
    assert "hourly_solar_gain" in d

    # JSON serialization
    json_str = json.dumps(d)
    assert "leh" in json_str

    # Deserialization
    reconstructed = SimulationResult.from_dict(json.loads(json_str))
    assert reconstructed.city == "leh"
    assert reconstructed.comfort_percentage == 100.0


# =====================================================================
# 5. OPTIMIZATION INPUT & RESULT TESTS
# =====================================================================

def test_optimization_input_valid():
    opt_in = OptimizationInput(
        city="leh",
        home_type="Permanent",
        min_insulation_m=0.02,
        max_insulation_m=0.15,
        min_window_area=1.0,
        max_window_area=5.0,
        n_trials=30,
    )
    assert opt_in.city == "leh"
    assert opt_in.n_trials == 30

    d = opt_in.to_dict()
    reconstructed = OptimizationInput.from_dict(d)
    assert reconstructed.min_insulation_m == 0.02
    assert reconstructed.max_insulation_m == 0.15


def test_optimization_input_invalid_bounds():
    with pytest.raises(ValueError, match="cannot be less than min_insulation_m"):
        OptimizationInput(city="leh", min_insulation_m=0.10, max_insulation_m=0.05)

    with pytest.raises(ValueError, match="cannot be less than min_window_area"):
        OptimizationInput(city="leh", min_window_area=4.0, max_window_area=2.0)


def test_optimization_result_valid_and_ranked():
    candidate1 = OptimizationCandidate(
        rank=1,
        label="Design #1",
        rationale="Optimal Balance",
        overall_score=88.5,
        sub_scores={"comfort": 90.0, "efficiency": 85.0, "solar": 90.0},
        insulation_mm=80.0,
        insulation_thickness_m=0.08,
        window_area_m2=2.5,
        wall_material="brick",
        wall_material_name="Fired Clay Brick",
        glazing="double_low_e",
        glazing_name="Double Low-E Glazing",
        orientation="south",
        comfort_hours=150.0,
        comfort_percentage=89.3,
        discomfort_dh=12.5,
        total_heat_loss_kwh=45.2,
        solar_gain_kwh=32.0,
        u_values={"wall_u": 0.28, "roof_u": 0.22},
    )

    opt_res = OptimizationResult(
        city="leh",
        home_type="Permanent",
        insulation_thickness_m=0.08,
        insulation_mm=80.0,
        window_area_m2=2.5,
        wall_material="brick",
        glazing="double_low_e",
        glazing_name="Double Low-E Glazing",
        orientation="south",
        discomfort_score=15.2,
        simulation_result={"comfort_percentage": 89.3},
        ranked_designs=[candidate1],
        n_trials=20,
        explanation="Design #1 selected due to high thermal efficiency.",
    )

    d = opt_res.to_dict()
    assert d["city"] == "leh"
    assert len(d["ranked_designs"]) == 1
    assert d["ranked_designs"][0]["rank"] == 1

    reconstructed = OptimizationResult.from_dict(d)
    assert reconstructed.insulation_mm == 80.0
    assert reconstructed.ranked_designs[0].wall_material == "brick"


# =====================================================================
# 6. ADAPTERS TESTS
# =====================================================================

def test_adapters():
    # Climate adapter
    raw_climate_dict = {
        "city": "jaisalmer",
        "latitude": 26.9,
        "longitude": 70.9,
        "hourly_temperature": [35.0, 36.0],
        "hourly_direct_solar": [600.0, 700.0],
        "hourly_diffuse_solar": [100.0, 120.0],
    }
    cp = adapt_to_climate_profile(raw_climate_dict)
    assert isinstance(cp, ClimateProfile)
    assert cp.city == "jaisalmer"
    assert adapt_to_climate_profile(cp) is cp

    # Design adapter
    raw_design_dict = {
        "length": 5.0,
        "width": 3.5,
        "height": 2.8,
        "wall_material": "mud",
        "window_area": 1.8,
    }
    sd = adapt_to_shelter_design(raw_design_dict)
    assert isinstance(sd, ShelterDesign)
    assert sd.length == 5.0
    assert sd.wall_material == "mud"
    assert adapt_to_shelter_design(sd) is sd

    # Simulation result adapter
    raw_res_dict = {
        "city": "chennai",
        "indoor_temperatures": [28.0],
        "outdoor_temperatures": [30.0],
        "comfort_hours": 1.0,
        "comfort_percentage": 100.0,
    }
    sr = adapt_simulation_result(raw_res_dict)
    assert isinstance(sr, SimulationResult)
    assert sr.city == "chennai"
    assert adapt_simulation_result(sr) is sr
