"""
Unit and Physics Sanity Tests for THERMOSHELTER AI Formula Engine
=================================================================
"""

import math
import pytest
import numpy as np

import services.formulas as f
from services.formula_constants import (
    AIR_DENSITY_DEFAULT,
    AIR_SPECIFIC_HEAT,
    CELSIUS_TO_KELVIN,
    DEFAULT_COMFORT_MAX,
    DEFAULT_COMFORT_MIN,
    STEFAN_BOLTZMANN,
)


# =====================================================================
# 1. TEMPERATURE CONVERSIONS & CONSTANTS
# =====================================================================

def test_constants():
    assert f.STEFAN_BOLTZMANN == pytest.approx(5.670374419e-8)
    assert f.AIR_DENSITY_DEFAULT == 1.225
    assert f.AIR_SPECIFIC_HEAT == 1005.0
    assert f.SECONDS_PER_HOUR == 3600.0
    assert f.CELSIUS_TO_KELVIN == 273.15


def test_celsius_to_kelvin_nominal():
    assert f.celsius_to_kelvin(0.0) == 273.15
    assert f.celsius_to_kelvin(25.0) == 298.15
    assert f.celsius_to_kelvin(-15.0) == 258.15


def test_celsius_to_kelvin_numpy():
    arr = np.array([0.0, 100.0, -20.0])
    res = f.celsius_to_kelvin(arr)
    assert np.allclose(res, np.array([273.15, 373.15, 253.15]))


def test_kelvin_to_celsius_nominal():
    assert f.kelvin_to_celsius(273.15) == 0.0
    assert f.kelvin_to_celsius(300.0) == pytest.approx(26.85)


def test_kelvin_to_celsius_invalid():
    with pytest.raises(ValueError):
        f.kelvin_to_celsius(-1.0)


# =====================================================================
# 2. GEOMETRY FORMULAS
# =====================================================================

def test_calculate_floor_area():
    assert f.calculate_floor_area(4.0, 3.0) == 12.0
    with pytest.raises(ValueError):
        f.calculate_floor_area(-4.0, 3.0)
    with pytest.raises(ValueError):
        f.calculate_floor_area(4.0, 0.0)


def test_calculate_volume():
    assert f.calculate_volume(4.0, 3.0, 2.5) == 30.0
    with pytest.raises(ValueError):
        f.calculate_volume(4.0, 3.0, -2.5)


def test_calculate_wall_area():
    # 2 * (4 + 3) * 2.5 = 2 * 7 * 2.5 = 35.0
    assert f.calculate_wall_area(4.0, 3.0, 2.5) == 35.0


def test_calculate_roof_area_flat():
    assert f.calculate_roof_area_flat(5.0, 3.5) == 17.5


def test_calculate_total_envelope_area():
    # Walls = 35, Floor = 12, Roof = 12 -> Total = 59
    assert f.calculate_total_envelope_area(4.0, 3.0, 2.5) == 59.0


def test_calculate_net_wall_area():
    gross = 35.0
    windows = 3.0
    doors = 1.8
    assert f.calculate_net_wall_area(gross, windows, doors) == pytest.approx(30.2)


def test_calculate_net_wall_area_invalid():
    with pytest.raises(ValueError):
        f.calculate_net_wall_area(20.0, 25.0, 0.0)  # Openings > Gross


# =====================================================================
# 3. THERMAL RESISTANCE & U-VALUES
# =====================================================================

def test_calculate_layer_resistance():
    # L = 0.2m, k = 0.6 W/m.K -> R = 0.3333 m2.K/W
    assert f.calculate_layer_resistance(0.2, 0.6) == pytest.approx(0.33333333)
    with pytest.raises(ValueError):
        f.calculate_layer_resistance(-0.1, 0.5)
    with pytest.raises(ValueError):
        f.calculate_layer_resistance(0.1, 0.0)


def test_calculate_total_resistance():
    r_in = 0.13
    r_out = 0.04
    layers = [(0.20, 0.60), (0.05, 0.036)]  # Mud brick + EPS insulation
    # R_mud = 0.2/0.6 = 0.3333, R_eps = 0.05/0.036 = 1.38888
    # Total = 0.13 + 0.333333 + 1.388888 + 0.04 = 1.892222
    r_tot = f.calculate_total_resistance(r_in, layers, r_out)
    assert r_tot == pytest.approx(1.892222, rel=1e-4)


def test_calculate_u_value():
    assert f.calculate_u_value(2.0) == 0.5
    assert f.calculate_u_value(0.5) == 2.0
    with pytest.raises(ValueError):
        f.calculate_u_value(0.0)


def test_calculate_insulation_effect():
    # Existing R = 0.5. Add 50mm EPS (k=0.036 -> added R = 1.38888). New R = 1.88888, New U = 0.5294
    new_r, new_u = f.calculate_insulation_effect(0.5, 0.05, 0.036)
    assert new_r == pytest.approx(1.888888, rel=1e-4)
    assert new_u == pytest.approx(1.0 / 1.888888, rel=1e-4)


# =====================================================================
# 4. CONDUCTIVE HEAT TRANSFER & HEAT LOSS COEFFICIENT
# =====================================================================

def test_calculate_conduction_heat_loss():
    # U = 0.5 W/m2.K, A = 30 m2, Tin = 20 C, Tout = -10 C (deltaT = 30 K) -> Q = 450 W
    q = f.calculate_conduction_heat_loss(0.5, 30.0, 20.0, -10.0)
    assert q == 450.0

    # Negative when ambient is hotter (heat enters shelter)
    q_summer = f.calculate_conduction_heat_loss(0.5, 30.0, 24.0, 34.0)
    assert q_summer == -150.0


def test_conduction_scaling_sanity():
    # If area doubles, heat loss must double
    q1 = f.calculate_conduction_heat_loss(0.5, 20.0, 20.0, 0.0)
    q2 = f.calculate_conduction_heat_loss(0.5, 40.0, 20.0, 0.0)
    assert q2 == pytest.approx(2.0 * q1)


def test_calculate_multilayer_heat_transfer():
    res = f.calculate_multilayer_heat_transfer(
        layers=[(0.2, 0.6)],
        area=10.0,
        indoor_temperature=20.0,
        outdoor_temperature=0.0,
        r_inside=0.13,
        r_outside=0.04
    )
    assert "R_total" in res
    assert "U_value" in res
    assert "heat_loss_watts" in res
    assert res["heat_loss_watts"] == pytest.approx(res["U_value"] * 10.0 * 20.0)


def test_calculate_heat_loss_coefficient():
    assert f.calculate_heat_loss_coefficient(0.5, 40.0) == 20.0


def test_calculate_total_heat_loss_coefficient():
    components = [(0.5, 40.0), (1.2, 3.0), (0.3, 15.0)]
    # (0.5*40) + (1.2*3) + (0.3*15) = 20 + 3.6 + 4.5 = 28.1 W/K
    assert f.calculate_total_heat_loss_coefficient(components) == pytest.approx(28.1)


# =====================================================================
# 5. SOLAR ENERGY & OPTICAL GAINS
# =====================================================================

def test_calculate_solar_gain():
    # I = 800 W/m2, A = 10 m2, alpha = 0.7 -> Q = 5600 W
    assert f.calculate_solar_gain(800.0, 10.0, 0.7) == 5600.0


def test_calculate_glazing_solar_gain():
    # I = 800 W/m2, A_win = 3.0 m2, SHGC = 0.60, shading = 0.90 -> Q = 800 * 3 * 0.6 * 0.9 = 1296 W
    assert f.calculate_glazing_solar_gain(800.0, 3.0, 0.60, 0.90) == pytest.approx(1296.0)


def test_solar_gain_scaling_sanity():
    # If solar irradiance doubles, solar gain doubles
    q1 = f.calculate_solar_gain(400.0, 10.0, 0.7)
    q2 = f.calculate_solar_gain(800.0, 10.0, 0.7)
    assert q2 == pytest.approx(2.0 * q1)


def test_integrate_power_over_time():
    # Constant 1000 W power over 4 hours (4 * 3600s) -> 1000 * 3 * 3600 = 10.8 MJ for 4 points
    power_profile = [1000.0, 1000.0, 1000.0, 1000.0]
    e_joules = f.integrate_power_over_time(power_profile, time_step_seconds=3600.0)
    assert e_joules == pytest.approx(3.0 * 1000.0 * 3600.0)


def test_calculate_orientation_factor():
    # Sun due south (180), Wall facing south (180) -> factor = cos(0) = 1.0
    assert f.calculate_orientation_factor(180.0, 180.0) == pytest.approx(1.0)
    # Sun south (180), Wall north (0) -> factor = 0.0 (clamped)
    assert f.calculate_orientation_factor(0.0, 180.0) == 0.0


def test_calculate_incidence_factor():
    # Overhead sun (zenith 0) on flat horizontal roof (tilt 0) -> cos(0)*cos(0) = 1.0
    assert f.calculate_incidence_factor(0.0, 0.0) == pytest.approx(1.0)
    # Sun below horizon (zenith 95) -> 0.0
    assert f.calculate_incidence_factor(95.0, 90.0) == 0.0


# =====================================================================
# 6. VENTILATION & INFILTRATION
# =====================================================================

def test_calculate_airflow_from_ach():
    # ACH = 0.5, V = 72 m3 -> V_dot = (0.5 * 72) / 3600 = 0.01 m3/s
    assert f.calculate_airflow_from_ach(0.5, 72.0) == 0.01


def test_calculate_ventilation_heat_loss():
    # rho = 1.225 kg/m3, V_dot = 0.01 m3/s, cp = 1005 J/kg.K, deltaT = 30 K
    # Q = 1.225 * 0.01 * 1005 * 30 = 369.3375 W
    q = f.calculate_ventilation_heat_loss(1.225, 0.01, 1005.0, 20.0, -10.0)
    assert q == pytest.approx(369.3375)


def test_calculate_ventilation_loss_from_ach():
    q = f.calculate_ventilation_loss_from_ach(0.5, 72.0, 20.0, -10.0)
    assert q == pytest.approx(369.3375)


# =====================================================================
# 7. THERMAL MASS & CAPACITANCE
# =====================================================================

def test_calculate_thermal_capacity():
    # m = 5000 kg, cp = 1000 J/kg.K -> C = 5.0e6 J/K
    assert f.calculate_thermal_capacity(5000.0, 1000.0) == 5.0e6


def test_calculate_temperature_change():
    # Q = 5.0e6 J, C = 5.0e6 J/K -> deltaT = 1.0 K
    assert f.calculate_temperature_change(5.0e6, 5.0e6) == 1.0


def test_thermal_mass_damping_sanity():
    # Higher mass yields smaller temperature change for the same energy
    dt_light = f.calculate_temperature_change(1e6, f.calculate_thermal_capacity(1000.0, 1000.0))
    dt_heavy = f.calculate_temperature_change(1e6, f.calculate_thermal_capacity(5000.0, 1000.0))
    assert dt_heavy < dt_light
    assert dt_light == pytest.approx(5.0 * dt_heavy)


# =====================================================================
# 8. RADIATION & INTERNAL HEAT
# =====================================================================

def test_calculate_radiative_heat_transfer():
    # Epsilon = 0.90, A = 10 m2, Ts = 20 C (293.15 K), Tsurr = 0 C (273.15 K)
    q_rad = f.calculate_radiative_heat_transfer(0.90, 10.0, 20.0, 0.0)
    assert q_rad > 0.0
    # Higher temperature difference -> higher radiation
    q_rad_extreme = f.calculate_radiative_heat_transfer(0.90, 10.0, 20.0, -20.0)
    assert q_rad_extreme > q_rad


def test_calculate_internal_heat_gain():
    assert f.calculate_internal_heat_gain(4, 80.0) == 320.0
    assert f.calculate_internal_heat_gain(0, 80.0) == 0.0


# =====================================================================
# 9. NET HEAT BALANCE & TRANSIENT TIME-STEP
# =====================================================================

def test_calculate_net_heat_flow():
    # Q_solar = 1200 W, Q_int = 320 W, Q_cond = 500 W, Q_vent = 200 W
    # Q_net = 1200 + 320 - 500 - 200 = 820 W
    q_net = f.calculate_net_heat_flow(1200.0, 320.0, 500.0, 200.0, 0.0)
    assert q_net == 820.0


def test_calculate_temperature_update():
    # T_current = 10 C, Q_net = 1000 W, C = 3.6e6 J/K, dt = 3600s
    # delta_E = 1000 * 3600 = 3.6e6 J -> delta_T = 1.0 C -> T_next = 11.0 C
    t_next = f.calculate_temperature_update(10.0, 1000.0, 3.6e6, 3600.0)
    assert t_next == pytest.approx(11.0)


def test_simulate_temperature_step():
    step = f.simulate_temperature_step(
        indoor_temperature=15.0,
        outdoor_temperature=-10.0,
        solar_irradiance=800.0,
        window_area=3.0,
        shgc=0.60,
        envelope_ua=20.0,
        ach=0.5,
        volume=50.0,
        occupants=2,
        thermal_capacity=2.0e6,
        time_step_seconds=3600.0
    )
    assert "indoor_temperature" in step
    assert "q_solar" in step
    assert "q_conduction" in step
    assert "q_ventilation" in step
    assert "q_net" in step


def test_calculate_heating_requirement():
    # Target = 18 C, Current = 12 C, C = 2.0e6 J/K, dt = 3600s
    # Energy needed = 2.0e6 * 6 = 12.0e6 J -> Power = 12.0e6 / 3600 = 3333.33 W
    q_heat = f.calculate_heating_requirement(12.0, 18.0, 2.0e6, 3600.0)
    assert q_heat == pytest.approx(3333.333, rel=1e-3)

    # 0 if already comfortable
    assert f.calculate_heating_requirement(20.0, 18.0, 2.0e6, 3600.0) == 0.0


# =====================================================================
# 10. COMFORT & SUMMARY STATISTICS
# =====================================================================

def test_calculate_comfort_status():
    assert f.calculate_comfort_status(15.0, 18.0, 24.0) == "too_cold"
    assert f.calculate_comfort_status(21.0, 18.0, 24.0) == "comfortable"
    assert f.calculate_comfort_status(26.0, 18.0, 24.0) == "too_hot"
    assert f.is_comfortable(20.0, 18.0, 24.0) is True
    assert f.is_comfortable(10.0, 18.0, 24.0) is False


def test_comfort_hours_and_percentage():
    temps = [12.0, 15.0, 18.5, 20.0, 22.0, 23.5, 25.0, 16.0]  # 4 comfortable hours (18.5, 20, 22, 23.5)
    c_hours = f.calculate_comfort_hours(temps, 18.0, 24.0, time_step_hours=1.0)
    assert c_hours == 4.0
    c_pct = f.calculate_comfort_percentage(c_hours, len(temps))
    assert c_pct == 50.0


def test_temperature_statistics():
    temps = [10.0, 15.0, 25.0, 20.0]
    assert f.calculate_min_temperature(temps) == 10.0
    assert f.calculate_max_temperature(temps) == 25.0
    assert f.calculate_average_temperature(temps) == 17.5
    assert f.calculate_temperature_range(temps) == 15.0


def test_calculate_design_score():
    score = f.calculate_design_score(
        comfort_score=80.0,
        energy_score=70.0,
        heat_loss_score=60.0,
        solar_score=90.0,
        weights={"comfort": 0.4, "energy": 0.3, "heat_loss": 0.2, "solar": 0.1}
    )
    # 0.4*80 + 0.3*70 + 0.2*60 + 0.1*90 = 32 + 21 + 12 + 9 = 74.0
    assert score == 74.0


# =====================================================================
# 11. UNIT CONVERSIONS & REGISTRY
# =====================================================================

def test_unit_conversions():
    assert f.watts_to_kw(2500.0) == 2.5
    assert f.kw_to_watts(2.5) == 2500.0
    assert f.joules_to_kwh(3.6e6) == 1.0
    assert f.kwh_to_joules(1.0) == 3.6e6
    assert f.hours_to_seconds(2.5) == 9000.0


def test_formula_registry_and_metadata():
    assert "u_value" in f.FORMULA_REGISTRY
    assert callable(f.FORMULA_REGISTRY["u_value"])
    assert "conduction_heat_loss" in f.FORMULA_REGISTRY
    assert "u_value" in f.FORMULA_METADATA
    assert "equation" in f.FORMULA_METADATA["u_value"]
