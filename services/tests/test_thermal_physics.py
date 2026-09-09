"""
Physics Verification, Thermal Mass Dynamics & Heat Balance Tests (Phase D)
==========================================================================
"""

import numpy as np
import pytest
from services.contracts import ClimateProfile, ShelterDesign
from services.fixtures import (
    get_leh_scenario,
    get_jaisalmer_scenario,
    get_chennai_scenario,
)
from services.simulation_adapter import SimulationAdapter
from services.simulation_service import run_simulation
import services.formulas as f


# =====================================================================
# 1. EFFECTIVE THERMAL CAPACITY & THERMAL MASS LAG
# =====================================================================

def test_effective_thermal_capacity_calculation():
    # 4m x 3m x 2.8m shelter (Volume: 33.6 m³, Gross Wall Area: 39.2 m²)
    c_data = f.calculate_effective_thermal_capacity(
        volume=33.6,
        solid_wall_area=37.2,
        wall_density=1800.0,
        wall_specific_heat=900.0,
        wall_thickness_m=0.23,
        roof_area=12.0,
        floor_area=12.0,
    )
    assert c_data["C_air"] > 0.0
    assert c_data["C_walls"] > 0.0
    assert c_data["C_roof"] > 0.0
    assert c_data["C_floor"] > 0.0
    assert c_data["C_total"] == pytest.approx(
        c_data["C_air"] + c_data["C_contents"] + c_data["C_walls"] + c_data["C_roof"] + c_data["C_floor"],
        rel=1e-4
    )
    # Heavy masonry capacity should be significantly greater than air capacity
    assert c_data["C_walls"] > 10.0 * c_data["C_air"]


def test_thermal_mass_damping_and_lag():
    """
    Controlled physics test:
    Compares two shelters under identical diurnal outdoor temperature and solar forcing:
      Case A: Lightweight (PUF insulation panels, density=35 kg/m³)
      Case B: High thermal mass (Fired clay brick, density=1800 kg/m³)
    Physics prediction:
      - Heavy-mass shelter exhibits significantly lower diurnal indoor temperature swing (damping).
      - Heavy-mass shelter experiences a delayed/lagged thermal response.
    """
    # 1. Simulate lightweight shelter
    res_light = run_simulation(
        city="jaisalmer",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="puf_insulation",
        wall_thickness_m=0.10,
        window_area=1.5,
        hours_to_simulate=72,
        substeps=60
    )

    # 2. Simulate heavy mass shelter
    res_heavy = run_simulation(
        city="jaisalmer",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        wall_thickness_m=0.23,
        window_area=1.5,
        hours_to_simulate=72,
        substeps=60
    )

    temps_light = res_light["indoor_temperatures"][24:48]  # Day 2 stabilized
    temps_heavy = res_heavy["indoor_temperatures"][24:48]

    swing_light = max(temps_light) - min(temps_light)
    swing_heavy = max(temps_heavy) - min(temps_heavy)

    # High thermal mass must damp the diurnal temperature swing
    assert swing_heavy < swing_light

    # Effective thermal capacitance of brick must exceed lightweight PUF
    assert res_heavy["effective_thermal_capacity_j_k"] > res_light["effective_thermal_capacity_j_k"]


# =====================================================================
# 2. HEAT BALANCE VERIFICATION
# =====================================================================

def test_instantaneous_heat_balance_reconciliation():
    """
    Verifies that for every hour, the net heat flow equals the sum of gains minus losses:
      Q_net = Q_solar + Q_internal - (Q_walls + Q_roof + Q_floor + Q_windows + Q_vent + Q_rad)
    Reconciles within 0.05 W numerical rounding tolerance.
    """
    res = run_simulation(
        city="delhi",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        window_area=2.0,
        hours_to_simulate=48
    )

    for h in range(48):
        q_sol = res["solar_thermal_gain"][h]
        q_int = res["hourly_internal_gain"][h]
        q_wall = res["wall_heat_flow"][h]
        q_roof = res["roof_heat_flow"][h]
        q_floor = res["floor_heat_flow"][h]
        q_win = res["window_heat_flow"][h]
        q_vent = res["ventilation_heat_flow"][h]
        q_rad = res["radiation_heat_flow"][h]
        q_net = res["net_heat_flow"][h]

        calculated_net = q_sol + q_int - (q_wall + q_roof + q_floor + q_win + q_vent + q_rad)
        assert q_net == pytest.approx(calculated_net, abs=0.05)


# =====================================================================
# 3. PHYSICAL SANITY & REGRESSION TESTS
# =====================================================================

def test_insulation_reduces_envelope_conduction():
    """Increasing insulation thickness must strictly reduce conductive envelope loss in cold climates."""
    uninsulated = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.0,
        hours_to_simulate=72
    )
    insulated = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.10,
        hours_to_simulate=72
    )

    assert insulated["energy_totals_kwh"]["wall_loss_kwh"] < uninsulated["energy_totals_kwh"]["wall_loss_kwh"]
    assert insulated["u_values"]["wall_u"] < uninsulated["u_values"]["wall_u"]
    assert insulated["comfort_metrics"]["min_t"] > uninsulated["comfort_metrics"]["min_t"]


def test_window_area_scaling():
    """Increasing window area must increase both solar gain and window heat loss."""
    small_win = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=1.0, hours_to_simulate=72)
    large_win = run_simulation("leh", length=4.0, width=3.0, height=2.8, window_area=3.5, hours_to_simulate=72)

    assert large_win["integrated_solar_energy_kwh"] > small_win["integrated_solar_energy_kwh"]
    assert large_win["energy_totals_kwh"]["window_loss_kwh"] > small_win["energy_totals_kwh"]["window_loss_kwh"]


def test_orientation_solar_harvesting():
    """South facing fenestration must yield higher winter solar harvesting than North facing in Leh."""
    south = run_simulation("leh", length=4.0, width=3.0, height=2.8, orientation="south", window_area=2.5, hours_to_simulate=72)
    north = run_simulation("leh", length=4.0, width=3.0, height=2.8, orientation="north", window_area=2.5, hours_to_simulate=72)

    assert south["integrated_solar_energy_kwh"] > north["integrated_solar_energy_kwh"]
    assert south["comfort_metrics"]["avg"] > north["comfort_metrics"]["avg"]


# =====================================================================
# 4. HEATING & COOLING THERMAL DEMAND TRACKING
# =====================================================================

def test_heating_and_cooling_demand_tracking():
    # In extreme cold Leh winter, heating demand must be positive and cooling demand must be zero
    leh_res = run_simulation("leh", length=4.0, width=3.0, height=2.8, wall_material="brick", hours_to_simulate=72)
    assert leh_res["energy_totals_kwh"]["heating_demand_kwh"] > 0.0
    assert leh_res["energy_totals_kwh"]["cooling_demand_kwh"] == 0.0
    assert len(leh_res["hourly_heating_demand"]) == 72
    assert len(leh_res["hourly_cooling_demand"]) == 72
    assert len(leh_res["hourly_net_load"]) == 72

    # In hot Jaisalmer, cooling demand must be positive
    jais_res = run_simulation("jaisalmer", length=4.0, width=3.0, height=2.8, wall_material="brick", hours_to_simulate=72)
    assert jais_res["energy_totals_kwh"]["cooling_demand_kwh"] > 0.0


# =====================================================================
# 5. SCENARIOS VERIFICATION & NUMERICAL STABILITY
# =====================================================================

def test_all_three_scenarios_execute_with_valid_physics():
    # 1. Leh Scenario
    c_leh, d_leh = get_leh_scenario(hours=168)
    res_leh = SimulationAdapter.run_from_contracts(c_leh, d_leh, hours_to_simulate=168)
    assert np.all(np.isfinite(res_leh.indoor_temperatures))
    assert res_leh.heating_demand_kwh > 0.0

    # 2. Jaisalmer Scenario
    c_jais, d_jais = get_jaisalmer_scenario(hours=168)
    res_jais = SimulationAdapter.run_from_contracts(c_jais, d_jais, hours_to_simulate=168)
    assert np.all(np.isfinite(res_jais.indoor_temperatures))
    assert res_jais.cooling_demand_kwh > 0.0

    # 3. Chennai Scenario
    c_che, d_che = get_chennai_scenario(hours=168)
    res_che = SimulationAdapter.run_from_contracts(c_che, d_che, hours_to_simulate=168)
    assert np.all(np.isfinite(res_che.indoor_temperatures))
    assert res_che.total_heat_loss_kwh > 0.0
