"""
Unit and Integration Tests for Simulation Service
=================================================
"""

import pytest
import numpy as np
from services.simulation_service import (
    calculate_assembly_u_value,
    run_simulation,
    simulate_shelter,
)


def test_calculate_assembly_u_value_uninsulated_wall():
    # Test with custom material dict: k = 0.72, R_layer = 0.23 / 0.72 ≈ 0.3194
    # R_in = 0.13, R_out = 0.04 -> R_total ≈ 0.4894, U ≈ 2.043
    res_custom = calculate_assembly_u_value({"thermal_conductivity": 0.72}, base_thickness_m=0.23, insulation_thickness_m=0.0)
    assert res_custom["R_total"] == pytest.approx(0.4894, abs=0.01)
    assert res_custom["U_value"] == pytest.approx(2.043, abs=0.05)

    # Test with material database ID "brick" (fired_clay_brick: k = 0.81)
    # R_layer = 0.23 / 0.81 ≈ 0.2840 -> R_total ≈ 0.4540, U ≈ 2.203
    res_db = calculate_assembly_u_value("brick", base_thickness_m=0.23, insulation_thickness_m=0.0)
    assert res_db["R_total"] == pytest.approx(0.4540, abs=0.01)
    assert res_db["U_value"] == pytest.approx(2.203, abs=0.05)


def test_calculate_assembly_u_value_with_insulation():
    # 230mm brick + 100mm PUF (k=0.025 -> R_ins = 4.0)
    # R_total ≈ 0.4540 + 4.0 = 4.4540, U ≈ 0.2245
    res = calculate_assembly_u_value("brick", base_thickness_m=0.23, insulation_thickness_m=0.10)
    assert res["insulation_R"] == pytest.approx(4.0, abs=0.01)
    assert res["R_total"] == pytest.approx(4.4540, abs=0.02)
    assert res["U_value"] == pytest.approx(0.2245, abs=0.02)



def test_simulation_numerical_stability():
    # Extreme cold city (Leh) with large glazing
    result = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=3.0,
        hours_to_simulate=168,
        substeps=60
    )
    assert "error" not in result
    temps = result["indoor_temperatures"]
    assert len(temps) == 168
    # Ensure no NaN or infinite or exploding temperatures
    assert np.all(np.isfinite(temps))
    assert -50.0 < min(temps) < 50.0
    assert -50.0 < max(temps) < 50.0


def test_insulation_impact_on_temperature():
    # Adding insulation in cold Leh should raise the minimum indoor temperature
    uninsulated = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.0,
        window_area=2.0,
        hours_to_simulate=168
    )
    insulated = run_simulation(
        city="leh",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.10,
        window_area=2.0,
        hours_to_simulate=168
    )
    # Insulated shelter should have higher average and min temperature in winter
    assert insulated["comfort_metrics"]["avg"] > uninsulated["comfort_metrics"]["avg"]
    assert insulated["comfort_metrics"]["min_t"] > uninsulated["comfort_metrics"]["min_t"]
    # Total conductive wall loss should be strictly lower with insulation
    assert insulated["energy_totals_kwh"]["wall_loss_kwh"] < uninsulated["energy_totals_kwh"]["wall_loss_kwh"]


def test_simulation_component_heat_flows():
    result = run_simulation(
        city="chennai",
        length=4.0,
        width=3.0,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.05,
        window_area=2.0,
        hours_to_simulate=168
    )
    assert "hourly_solar_gain" in result
    assert "hourly_wall_loss" in result
    assert "hourly_roof_loss" in result
    assert "hourly_window_loss" in result
    assert "hourly_vent_loss" in result
    assert len(result["hourly_solar_gain"]) == 168
    assert result["energy_totals_kwh"]["solar_gain_kwh"] >= 0.0


def test_simulate_shelter_compatibility():
    temps = simulate_shelter("leh", 4.0, 3.0, 2.8, "brick", 2.0, insulation_thickness_m=0.05)
    assert isinstance(temps, list)
    assert len(temps) == 168

    full_dict = simulate_shelter("leh", 4.0, 3.0, 2.8, "brick", 2.0, return_full_dict=True)
    assert isinstance(full_dict, dict)
    assert "comfort_metrics" in full_dict


def test_glazing_and_orientation_effects():
    # Single clear glass vs Triple Low-E in cold Leh
    single_glass_res = run_simulation("leh", length=4.0, width=3.0, height=2.8, glazing="single_clear", orientation="south", window_area=2.5)
    triple_glass_res = run_simulation("leh", length=4.0, width=3.0, height=2.8, glazing="triple_low_e", orientation="south", window_area=2.5)

    # Triple glass U-value is much lower
    assert triple_glass_res["u_values"]["glass_u"] < single_glass_res["u_values"]["glass_u"]
    # Triple glass window heat loss should be strictly lower
    assert triple_glass_res["energy_totals_kwh"]["window_loss_kwh"] < single_glass_res["energy_totals_kwh"]["window_loss_kwh"]

    # South vs North orientation solar gain
    south_res = run_simulation("leh", length=4.0, width=3.0, height=2.8, glazing="double_clear", orientation="south", window_area=2.5)
    north_res = run_simulation("leh", length=4.0, width=3.0, height=2.8, glazing="double_clear", orientation="north", window_area=2.5)
    assert south_res["energy_totals_kwh"]["solar_gain_kwh"] > north_res["energy_totals_kwh"]["solar_gain_kwh"]


def test_optimizer_five_variables():
    from services.optimize import run_optimization
    res = run_optimization("leh", length=4.0, width=3.0, height=2.8, occupants=2, n_trials=10)

    # Check that all 5 variables are returned
    assert "insulation_thickness_m" in res
    assert "window_area_m2" in res
    assert "wall_material" in res
    assert "glazing" in res
    assert "orientation" in res
    assert "discomfort_score" in res
    assert "simulation_result" in res

    sim = res["simulation_result"]
    assert "indoor_temperatures" in sim
    assert len(sim["indoor_temperatures"]) == 168
    assert sim["specs"]["insulation_thickness_m"] == res["insulation_thickness_m"]
    assert sim["specs"]["window_area_m2"] == res["window_area_m2"]
    assert sim["specs"]["wall_material"] == res["wall_material"]
    assert sim["specs"]["glazing"] == res["glazing"]
    assert sim["specs"]["orientation"] == res["orientation"]


def test_sih_required_simulation_outputs():
    result = run_simulation("delhi", length=4.0, width=3.0, height=2.8, wall_material="brick", window_area=2.0)
    
    # 1. Temperature outputs
    assert "indoor_temperature" in result
    assert "outdoor_temperature" in result
    assert len(result["indoor_temperature"]) == 168
    assert len(result["outdoor_temperature"]) == 168

    # 2. Solar outputs
    assert "solar_irradiance" in result
    assert "solar_power" in result
    assert "solar_thermal_gain" in result
    assert len(result["solar_irradiance"]) == 168
    assert len(result["solar_power"]) == 168
    assert len(result["solar_thermal_gain"]) == 168
    assert result["integrated_solar_energy_kwh"] >= 0.0
    assert result["integrated_incident_solar_kwh"] >= result["integrated_solar_energy_kwh"]

    # 3. Heat flow & heat loss outputs
    assert "wall_heat_flow" in result
    assert "roof_heat_flow" in result
    assert "floor_heat_flow" in result
    assert "window_heat_flow" in result
    assert "ventilation_heat_flow" in result
    assert "radiation_heat_flow" in result
    assert "net_heat_flow" in result
    assert len(result["wall_heat_flow"]) == 168
    assert len(result["roof_heat_flow"]) == 168
    assert len(result["floor_heat_flow"]) == 168
    assert len(result["window_heat_flow"]) == 168
    assert len(result["ventilation_heat_flow"]) == 168
    assert len(result["radiation_heat_flow"]) == 168
    assert len(result["net_heat_flow"]) == 168

    # 4. Component energy totals & comfort indicators
    assert "component_heat_loss_kwh" in result
    assert "wall_loss_kwh" in result["component_heat_loss_kwh"]
    assert "roof_loss_kwh" in result["component_heat_loss_kwh"]
    assert "floor_loss_kwh" in result["component_heat_loss_kwh"]
    assert "window_loss_kwh" in result["component_heat_loss_kwh"]
    assert "ventilation_loss_kwh" in result["component_heat_loss_kwh"]
    assert "radiation_loss_kwh" in result["component_heat_loss_kwh"]
    assert "comfort_status" in result
    assert "comfort_hours" in result
    assert "comfort_percentage" in result
    assert "discomfort_degree_hours" in result


def test_pitched_roof_geometry():
    from services.geometry import calculate_pitched_roof_geometry
    geo = calculate_pitched_roof_geometry(length=4.0, width=3.0, height=2.8, pitch_angle_deg=30.0)
    assert geo["roof_area"] > 4.0 * 3.0  # Pitched slope area > flat area
    assert geo["gable_area"] > 0.0
    assert geo["volume"] > 4.0 * 3.0 * 2.8  # Attic volume included
    assert geo["total_height"] > 2.8


def test_multiple_shelter_models():
    from services.simulation_service import SHELTER_MODELS
    assert "rectangular_flat" in SHELTER_MODELS
    assert "rectangular_pitched" in SHELTER_MODELS
    assert "compact_shelter" in SHELTER_MODELS
    assert "elongated_shelter" in SHELTER_MODELS
    assert "custom_dimensions" in SHELTER_MODELS

    for m_key in ["rectangular_flat", "rectangular_pitched", "compact_shelter", "elongated_shelter"]:
        res = run_simulation(
            city="leh",
            length=4.5,
            width=3.2,
            height=2.8,
            shelter_model=m_key,
            wall_material="brick",
            insulation_thickness_m=0.08,
            window_area=2.0,
            hours_to_simulate=168
        )
        assert "error" not in res
        assert len(res["indoor_temperature"]) == 168
        assert res["geometry"]["shelter_model"] == m_key



