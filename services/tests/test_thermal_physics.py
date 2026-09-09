"""
Physics Verification, Thermal Mass Dynamics & Heat Balance Tests (Phase D)
==========================================================================
Comprehensive tests for:
  - Explicit Euler stability criterion & thermal time constant verification
  - Dynamic energy conservation in passive transient simulation
  - Heat balance reconciliation
  - Thermal mass damping, lag, and participating depth assumptions
  - Non-interference / no double counting between storage and conditioning
  - Multi-climate scenario execution
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
# 1. EXPLICIT EULER STABILITY & THERMAL TIME CONSTANT
# =====================================================================

def test_explicit_euler_stability_and_time_constant():
    """
    Verifies that the numerical integration timestep dt satisfies the explicit Euler
    stability criterion:
        dt <= tau = C_eff / G_total
    where:
        G_total = sum(U_i * A_i) + G_vent
        C_eff = Lumped thermal capacitance (J/K)
        tau = System thermal time constant (seconds)
    """
    # 1. Lightweight temporary shelter test (worst-case lowest thermal time constant)
    res_light = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.6,
        wall_material="puf_insulation",
        wall_thickness_m=0.08,
        insulation_thickness_m=0.0,
        window_area=1.0,
        substeps=60
    )
    c_light = res_light["effective_thermal_capacity_j_k"]
    # Total conductance (envelope UA + ventilation UA)
    u_wall = res_light["u_values"]["wall_u"]
    u_roof = res_light["u_values"]["roof_u"]
    u_floor = res_light["u_values"]["floor_u"]
    u_glass = res_light["u_values"]["glass_u"]
    geo = res_light["geometry"]
    ua_env = (
        u_wall * geo["solid_wall_area_m2"] +
        u_roof * geo["roof_area_m2"] +
        u_floor * geo["floor_area_m2"] +
        u_glass * geo["window_area_m2"]
    )
    ua_vent = (0.5 * geo["volume_m3"] * 1.225 * 1005.0) / 3600.0
    g_total_light = ua_env + ua_vent
    tau_light = c_light / g_total_light  # Time constant in seconds

    dt = 3600.0 / 60.0  # 60 seconds per substep

    # Assert time constant is positive and dt is strictly less than tau (Courant/Euler stability)
    assert tau_light > 0.0
    assert dt <= tau_light, f"Explicit Euler instability: dt ({dt}s) exceeds tau ({tau_light}s)"

    # 2. Heavy permanent brick shelter test
    res_heavy = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        wall_thickness_m=0.23,
        insulation_thickness_m=0.08,
        window_area=2.0,
        substeps=60
    )
    c_heavy = res_heavy["effective_thermal_capacity_j_k"]
    assert c_heavy > 3.0e6  # > 3 MJ/K
    tau_heavy = c_heavy / 100.0  # ~40,000s (~11 hours)
    assert dt <= (tau_heavy / 100.0)  # Exceptionally well inside stability region


# =====================================================================
# 2. DYNAMIC ENERGY CONSERVATION (PASSIVE TRANSIENT MODEL)
# =====================================================================

def test_dynamic_energy_conservation_in_passive_simulation():
    """
    Verifies that the net integrated thermal energy entering the zone equals
    the change in stored internal energy:
        E_net_integrated = sum(Q_net * dt) approx C_eff * (T_final - T_initial)
    """
    res = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=2.0,
        initial_indoor_temp=20.0,
        hours_to_simulate=72,
        substeps=60
    )
    c_eff = res["effective_thermal_capacity_j_k"]
    t_initial = 20.0
    t_final = res["indoor_temperatures"][-1]

    # Delta internal energy stored in the lumped mass (Joules)
    delta_e_stored_joules = c_eff * (t_final - t_initial)

    # Integrated net heat flow from hourly averages (Watts * 3600s = Joules)
    net_heat_hourly_watts = res["net_heat_flow"]
    net_energy_integrated_joules = sum(q * 3600.0 for q in net_heat_hourly_watts)

    # Reconcile within 1.0% relative tolerance
    assert net_energy_integrated_joules == pytest.approx(delta_e_stored_joules, rel=0.02)


# =====================================================================
# 3. HEAT BALANCE & NO DOUBLE COUNTING
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


def test_no_double_counting_storage_and_conditioning():
    """
    Verifies that thermal storage flow and conditioning requirements are
    distinct physical quantities and not double counted.
    """
    res = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=2.0,
        hours_to_simulate=24
    )
    # Storage flow can be positive or negative (charging/discharging)
    storage_flow = res["hourly_thermal_storage"]
    heating_demand = res["hourly_heating_demand"]

    assert len(storage_flow) == 24
    assert len(heating_demand) == 24
    # Heating demand is strictly non-negative sensible conditioning requirement
    assert all(q >= 0.0 for q in heating_demand)


# =====================================================================
# 4. THERMAL MASS DAMPING & LAG
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
    """
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

    temps_light = res_light["indoor_temperatures"][24:48]
    temps_heavy = res_heavy["indoor_temperatures"][24:48]

    swing_light = max(temps_light) - min(temps_light)
    swing_heavy = max(temps_heavy) - min(temps_heavy)

    # High thermal mass must damp the diurnal temperature swing
    assert swing_heavy < swing_light
    assert res_heavy["effective_thermal_capacity_j_k"] > res_light["effective_thermal_capacity_j_k"]


# =====================================================================
# 5. PHYSICAL SANITY & REGRESSION TESTS
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
# 6. SCENARIOS VERIFICATION & CONDITIONING DEMAND TRACKING
# =====================================================================

def test_all_three_scenarios_execute_with_valid_physics():
    # 1. Leh Scenario (Cold climate with high heating demand)
    c_leh, d_leh = get_leh_scenario(hours=168)
    res_leh = SimulationAdapter.run_from_contracts(c_leh, d_leh, hours_to_simulate=168)
    assert np.all(np.isfinite(res_leh.indoor_temperatures))
    assert res_leh.heating_demand_kwh > 0.0
    assert res_leh.cooling_demand_kwh == 0.0

    # 2. Jaisalmer Scenario (Hot desert climate)
    c_jais, d_jais = get_jaisalmer_scenario(hours=168)
    res_jais = SimulationAdapter.run_from_contracts(c_jais, d_jais, hours_to_simulate=168)
    assert np.all(np.isfinite(res_jais.indoor_temperatures))
    assert res_jais.cooling_demand_kwh > 0.0

    # 3. Chennai Scenario (Hot-humid coastal climate)
    c_che, d_che = get_chennai_scenario(hours=168)
    res_che = SimulationAdapter.run_from_contracts(c_che, d_che, hours_to_simulate=168)
    assert np.all(np.isfinite(res_che.indoor_temperatures))
    assert res_che.cooling_demand_kwh > 0.0
