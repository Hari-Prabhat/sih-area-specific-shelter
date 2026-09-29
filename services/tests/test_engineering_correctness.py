"""
THERMOSHELTER AI - Engineering Correctness & Physics Verification Tests
========================================================================
Validates:
1. Continuous physical orientation solar azimuth response across [0, 360] degrees.
2. Building envelope door conductance (UA_door), timeseries heat flow, and total kWh loss.
3. Strict energy balance accounting identity across all 7 physical heat flow components.
4. Parametric pitched roof geometry consistency.
5. Canonical digital twin and SimulationEnvelopeParameters contract integrity.
"""

import math
import pytest
from services.contracts import (
    ClimateProfile,
    ShelterDesign,
    SimulationEnvelopeParameters,
    SimulationInput,
    SimulationResult,
    create_mock_climate_profile,
)
from services.simulation_service import run_simulation
from services.simulation_adapter import SimulationAdapter
from services.geometry import calculate_pitched_roof_geometry


def test_orientation_continuous_physical_response():
    """
    Validates continuous physical solar azimuth model across [0, 360] degrees:
    - South (180°) produces peak solar harvesting.
    - North (0° / 360°) produces minimum solar harvesting.
    - East (90°) and West (270°) provide intermediate solar gains.
    - Intermediate angles (45°, 135°, 225°, 315°) transition smoothly without discontinuity.
    """
    res_south = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.0, orientation=180.0, hours_to_simulate=48)
    res_north = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.0, orientation=0.0, hours_to_simulate=48)
    res_east = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.0, orientation=90.0, hours_to_simulate=48)
    res_west = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.0, orientation=270.0, hours_to_simulate=48)
    res_se = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.0, orientation=135.0, hours_to_simulate=48)

    q_south = res_south["energy_totals_kwh"]["solar_gain_kwh"]
    q_north = res_north["energy_totals_kwh"]["solar_gain_kwh"]
    q_east = res_east["energy_totals_kwh"]["solar_gain_kwh"]
    q_west = res_west["energy_totals_kwh"]["solar_gain_kwh"]
    q_se = res_se["energy_totals_kwh"]["solar_gain_kwh"]

    # Monotonic physical hierarchy in northern hemisphere
    assert q_south > q_se > q_east > q_north, (
        f"Expected South ({q_south}) > SE ({q_se}) > East ({q_east}) > North ({q_north})"
    )
    assert q_south > q_west > q_north, (
        f"Expected South ({q_south}) > West ({q_west}) > North ({q_north})"
    )

    # Both string and degree conventions should match
    res_south_str = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.0, orientation="south", hours_to_simulate=48)
    assert pytest.approx(res_south_str["energy_totals_kwh"]["solar_gain_kwh"], rel=1e-3) == q_south


def test_door_heat_loss_sensitivity_and_accounting():
    """
    Verifies door thermal conductance modeling:
    - Increasing door area increases total heat loss and door heat loss.
    - Net solid wall area properly subtracts both window and door areas.
    - Door heat loss is accurately tracked in timeseries and kWh totals.
    """
    res_no_door = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=2.0, door_area=0.0, hours_to_simulate=72)
    res_std_door = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=2.0, door_area=2.0, hours_to_simulate=72)
    res_large_door = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=2.0, door_area=3.5, hours_to_simulate=72)

    # 1. Door loss strictly increases with area
    loss_no = res_no_door["component_heat_loss_kwh"]["door_loss_kwh"]
    loss_std = res_std_door["component_heat_loss_kwh"]["door_loss_kwh"]
    loss_large = res_large_door["component_heat_loss_kwh"]["door_loss_kwh"]

    assert loss_no == 0.0
    assert loss_std > 0.0
    assert loss_large > loss_std

    # 2. Solid wall area shrinks as door area increases
    assert res_no_door["geometry"]["solid_wall_area_m2"] > res_std_door["geometry"]["solid_wall_area_m2"]
    assert res_std_door["geometry"]["solid_wall_area_m2"] > res_large_door["geometry"]["solid_wall_area_m2"]

    # 3. Door heat flow timeseries exists and has matching length
    assert "door_heat_flow" in res_std_door
    assert len(res_std_door["door_heat_flow"]) == 72


def test_strict_energy_balance_seven_components():
    """
    Validates complete component heat loss reconciliation across all 7 channels:
    total_component_loss_kwh == wall + roof + floor + window + door + ventilation + radiation
    """
    res = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="stone",
        window_area=2.5,
        door_area=2.1,
        roof_type="pitched",
        pitch_angle_deg=25.0,
        hours_to_simulate=168,
    )

    comp = res["component_heat_loss_kwh"]
    total_reported = res["total_heat_loss_kwh"]

    sum_components = (
        comp["wall_loss_kwh"]
        + comp["roof_loss_kwh"]
        + comp["floor_loss_kwh"]
        + comp["window_loss_kwh"]
        + comp["door_loss_kwh"]
        + comp["ventilation_loss_kwh"]
        + comp["radiation_loss_kwh"]
    )

    assert pytest.approx(sum_components, abs=0.05) == total_reported

    # Also verify envelope loss includes door loss
    expected_env = (
        comp["wall_loss_kwh"]
        + comp["roof_loss_kwh"]
        + comp["floor_loss_kwh"]
        + comp["window_loss_kwh"]
        + comp["door_loss_kwh"]
    )
    assert pytest.approx(expected_env, abs=0.05) == res["energy_totals_kwh"]["total_envelope_loss_kwh"]


def test_pitched_roof_parametric_geometry_monotonics():
    """
    Verifies that pitched roof geometry calculations correctly scale:
    - Pitch angle 0° yields flat roof area.
    - Increasing pitch angles (15°, 30°, 45°) strictly increase roof area and attic volume.
    """
    geo_0 = calculate_pitched_roof_geometry(5.0, 4.0, 3.0, 0.0)
    geo_15 = calculate_pitched_roof_geometry(5.0, 4.0, 3.0, 15.0)
    geo_30 = calculate_pitched_roof_geometry(5.0, 4.0, 3.0, 30.0)
    geo_45 = calculate_pitched_roof_geometry(5.0, 4.0, 3.0, 45.0)

    # Base flat area = 5 * 4 = 20 m²
    assert pytest.approx(geo_0["roof_area"], abs=1e-3) == 20.0
    assert geo_15["roof_area"] > geo_0["roof_area"]
    assert geo_30["roof_area"] > geo_15["roof_area"]
    assert geo_45["roof_area"] > geo_30["roof_area"]

    # Attic volume strictly increases with pitch angle
    assert geo_15["volume"] > geo_0["volume"]
    assert geo_30["volume"] > geo_15["volume"]
    assert geo_45["volume"] > geo_30["volume"]


def test_contract_and_adapter_door_integration():
    """
    Verifies that canonical contracts (ShelterDesign, SimulationEnvelopeParameters,
    SimulationResult) cleanly carry door parameters through SimulationAdapter.
    """
    design = ShelterDesign(
        length=4.0,
        width=3.0,
        height=2.8,
        window_area=2.0,
        door_area=2.2,
        roof_type="pitched",
        pitch_angle_deg=30.0,
    )

    assert design.door_area == 2.2

    params = SimulationAdapter.extract_envelope_parameters(design)
    assert isinstance(params, SimulationEnvelopeParameters)
    assert params.door_area_m2 == 2.2
    assert params.door_u_value == 1.80

    sim_res = SimulationAdapter.run_from_contracts(
        climate=create_mock_climate_profile("leh"),
        design=design,
        hours_to_simulate=48,
    )

    assert isinstance(sim_res, SimulationResult)
    assert sim_res.component_heat_loss_kwh["door_loss_kwh"] > 0.0
    assert sim_res.door_heat_flow is not None
    assert len(sim_res.door_heat_flow) == 48

    res_dict = sim_res.to_dict()
    assert "hourly_door_loss" in res_dict
    assert res_dict["hourly_door_loss"] is not None
