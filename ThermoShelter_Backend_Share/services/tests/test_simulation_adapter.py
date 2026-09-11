"""
Unit and Integration Tests for Simulation Adapter and Scenario Fixtures (Phase C)
================================================================================
"""

import pytest
from services.contracts import (
    ClimateProfile,
    ShelterDesign,
    SimulationInput,
    SimulationResult,
)
from services.fixtures import (
    get_leh_scenario,
    get_jaisalmer_scenario,
    get_chennai_scenario,
)
from services.simulation_adapter import SimulationAdapter
from services.simulation_service import run_simulation


# =====================================================================
# 1. ADAPTER CONVERSION & PRESERVATION TESTS
# =====================================================================

def test_adapter_valid_conversion():
    climate, design = get_leh_scenario(hours=168, occupants=4)
    sim_input = SimulationAdapter.to_simulation_input(climate, design, hours_to_simulate=168, substeps=60)

    assert isinstance(sim_input, SimulationInput)
    assert sim_input.climate.city == "leh"
    assert sim_input.design.occupants == 4
    assert sim_input.hours_to_simulate == 168
    assert sim_input.substeps == 60


def test_adapter_field_and_unit_preservation():
    climate, design = get_leh_scenario()
    sim_input = SimulationAdapter.to_simulation_input(climate, design)

    # Dimensional preservation (meters)
    assert sim_input.design.length == 4.5
    assert sim_input.design.width == 3.2
    assert sim_input.design.height == 2.8

    # Thermal properties preservation (meters, W/mK)
    assert sim_input.design.wall_material == "brick"
    assert sim_input.design.wall_thickness_m == 0.23
    assert sim_input.design.insulation_thickness_m == 0.08
    assert sim_input.design.insulation_conductivity == 0.025
    assert sim_input.design.roof_thickness_m == 0.15
    assert sim_input.design.roof_conductivity == 0.50
    assert sim_input.design.roof_insulation_m == 0.08

    # Fenestration & ventilation preservation (m², ACH, orientation)
    assert sim_input.design.window_area == 2.5
    assert sim_input.design.glazing == "double_low_e"
    assert sim_input.design.orientation == "south"
    assert sim_input.design.ach == 0.5
    assert sim_input.design.occupants == 4
    assert sim_input.design.shelter_type == "Permanent"


def test_adapter_determinism():
    climate1, design1 = get_leh_scenario()
    climate2, design2 = get_leh_scenario()

    sim_in1 = SimulationAdapter.to_simulation_input(climate1, design1)
    sim_in2 = SimulationAdapter.to_simulation_input(climate2, design2)

    assert sim_in1.to_dict() == sim_in2.to_dict()


def test_adapter_invalid_inputs_rejected():
    climate, design = get_leh_scenario(hours=24)

    # Requesting more hours than available in climate profile
    with pytest.raises(ValueError, match="exceeds available weather hours"):
        SimulationAdapter.to_simulation_input(climate, design, hours_to_simulate=168)

    # Invalid substeps
    with pytest.raises(ValueError, match="substeps must be between"):
        SimulationAdapter.to_simulation_input(climate, design, hours_to_simulate=24, substeps=0)


# =====================================================================
# 2. SCENARIO FIXTURE VALIDATION TESTS
# =====================================================================

def test_leh_scenario_fixture():
    climate, design = get_leh_scenario()

    assert climate.city == "leh"
    assert climate.climate_zone == "cold"
    assert len(climate.hourly_temperature) == 168
    assert min(climate.hourly_temperature) < 0.0  # Cold Leh subzero conditions
    assert max(climate.hourly_direct_solar) >= 700.0  # High-altitude solar radiation

    assert design.shelter_type == "Permanent"
    assert design.orientation == "south"
    assert design.glazing == "double_low_e"
    assert design.insulation_thickness_m == 0.08


def test_jaisalmer_scenario_fixture():
    climate, design = get_jaisalmer_scenario()

    assert climate.city == "jaisalmer"
    assert climate.climate_zone == "hot_dry"
    assert len(climate.hourly_temperature) == 168
    assert min(climate.hourly_temperature) >= 25.0  # Hot desert climate
    assert max(climate.hourly_temperature) >= 40.0
    assert max(climate.hourly_direct_solar) >= 800.0

    assert design.wall_material == "mud"
    assert design.wall_thickness_m == 0.30
    assert design.orientation == "north"


def test_chennai_scenario_fixture():
    climate, design = get_chennai_scenario()

    assert climate.city == "chennai"
    assert climate.climate_zone == "hot_humid"
    assert len(climate.hourly_temperature) == 168
    assert min(climate.hourly_temperature) >= 25.0
    assert all(h == 80.0 for h in climate.hourly_humidity)  # High humidity
    assert design.ach == 1.5  # Higher ventilation rate


# =====================================================================
# 3. END-TO-END EXECUTION BRIDGE TESTS
# =====================================================================

def test_run_simulation_from_input_leh():
    climate, design = get_leh_scenario(hours=168)
    sim_in = SimulationAdapter.to_simulation_input(climate, design, hours_to_simulate=168)
    result = SimulationAdapter.run_simulation_from_input(sim_in)

    assert isinstance(result, SimulationResult)
    assert result.city == "leh"
    assert len(result.indoor_temperatures) == 168
    assert len(result.outdoor_temperatures) == 168
    assert len(result.wall_heat_flow) == 168
    assert len(result.solar_thermal_gain) == 168
    assert result.total_heat_loss_kwh > 0.0
    assert "avg" in result.comfort_metrics


def test_run_simulation_from_input_jaisalmer():
    climate, design = get_jaisalmer_scenario(hours=168)
    sim_in = SimulationAdapter.to_simulation_input(climate, design, hours_to_simulate=168)
    result = SimulationAdapter.run_simulation_from_input(sim_in)

    assert isinstance(result, SimulationResult)
    assert result.city == "jaisalmer"
    assert len(result.indoor_temperatures) == 168
    assert result.total_heat_loss_kwh > 0.0


def test_run_simulation_from_input_chennai():
    climate, design = get_chennai_scenario(hours=168)
    sim_in = SimulationAdapter.to_simulation_input(climate, design, hours_to_simulate=168)
    result = SimulationAdapter.run_simulation_from_input(sim_in)

    assert isinstance(result, SimulationResult)
    assert result.city == "chennai"
    assert len(result.indoor_temperatures) == 168
    assert result.total_heat_loss_kwh > 0.0


def test_run_from_contracts_convenience():
    climate, design = get_leh_scenario(hours=72)
    result = SimulationAdapter.run_from_contracts(climate, design, hours_to_simulate=72)

    assert isinstance(result, SimulationResult)
    assert len(result.indoor_temperatures) == 72
