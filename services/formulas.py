"""
THERMOSHELTER AI - Centralized Mathematical & Thermal Formula Engine
====================================================================
Single master centralized module containing ALL reusable mathematical,
thermal, solar, geometric, ventilation, comfort, and energy formulas
for the ThermoShelter AI platform.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np

# Re-export all Constants
from services.formula_constants import (
    AIR_DENSITY_DEFAULT,
    AIR_SPECIFIC_HEAT,
    CELSIUS_TO_KELVIN,
    DEFAULT_ACH,
    DEFAULT_COMFORT_MAX,
    DEFAULT_COMFORT_MIN,
    DEFAULT_OCCUPANT_HEAT_GAIN,
    DEFAULT_R_INSIDE_HORIZONTAL,
    DEFAULT_R_INSIDE_VERTICAL,
    DEFAULT_R_OUTSIDE_HORIZONTAL,
    DEFAULT_R_OUTSIDE_VERTICAL,
    JOULES_PER_KWH,
    SECONDS_PER_HOUR,
    STEFAN_BOLTZMANN,
)

# Re-export Geometry
from services.geometry import (
    calculate_floor_area,
    calculate_net_wall_area,
    calculate_pitched_roof_geometry,
    calculate_roof_area_flat,
    calculate_total_envelope_area,
    calculate_volume,
    calculate_wall_area,
)


# Re-export Solar
from services.solar import (
    calculate_energy_from_power,
    calculate_energy_kwh,
    calculate_glazing_solar_gain,
    calculate_incidence_factor,
    calculate_orientation_factor,
    calculate_solar_gain,
    integrate_power_over_time,
)

# Re-export Ventilation
from services.ventilation import (
    calculate_airflow_from_ach,
    calculate_ventilation_heat_loss,
    calculate_ventilation_loss_from_ach,
)

# Re-export Comfort & Statistics
from services.comfort import (
    calculate_average_temperature,
    calculate_comfort_hours,
    calculate_comfort_percentage,
    calculate_comfort_status,
    calculate_design_score,
    calculate_external_energy_requirement,
    calculate_max_temperature,
    calculate_min_temperature,
    calculate_temperature_range,
    calculate_total_heat_loss,
    calculate_total_solar_energy,
    is_comfortable,
)

# Re-export Thermal
from services.thermal import (
    calculate_conduction_heat_loss,
    calculate_heat_flow,
    calculate_heat_loss_coefficient,
    calculate_heating_requirement,
    calculate_insulation_effect,
    calculate_internal_heat_gain,
    calculate_layer_resistance,
    calculate_multilayer_heat_transfer,
    calculate_net_heat_flow,
    calculate_radiative_heat_transfer,
    calculate_stored_thermal_energy,
    calculate_temperature_change,
    calculate_temperature_update,
    calculate_thermal_capacity,
    calculate_total_heat_loss_coefficient,
    calculate_total_resistance,
    calculate_u_value,
    celsius_to_kelvin,
    kelvin_to_celsius,
    simulate_temperature_step,
)


# =====================================================================
# ADDITIONAL UNIT CONVERSION UTILITIES
# =====================================================================

def watts_to_kw(power_watts: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Converts thermal power from Watts (W) to Kilowatts (kW)."""
    return power_watts / 1000.0


def kw_to_watts(power_kw: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Converts thermal power from Kilowatts (kW) to Watts (W)."""
    return power_kw * 1000.0


def joules_to_kwh(energy_joules: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Converts thermal energy from Joules (J) to Kilowatt-hours (kWh)."""
    return energy_joules / JOULES_PER_KWH


def kwh_to_joules(energy_kwh: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Converts thermal energy from Kilowatt-hours (kWh) to Joules (J)."""
    return energy_kwh * JOULES_PER_KWH


def hours_to_seconds(hours: float) -> float:
    """Converts duration in hours (h) to seconds (s)."""
    if hours < 0.0:
        raise ValueError(f"Duration cannot be negative, got {hours}")
    return float(hours * SECONDS_PER_HOUR)


# =====================================================================
# FORMULA REGISTRY
# =====================================================================

FORMULA_REGISTRY: Dict[str, Callable[..., Any]] = {
    # Temperature conversion
    "celsius_to_kelvin": celsius_to_kelvin,
    "kelvin_to_celsius": kelvin_to_celsius,
    # Geometry
    "floor_area": calculate_floor_area,
    "volume": calculate_volume,
    "wall_area": calculate_wall_area,
    "roof_area_flat": calculate_roof_area_flat,
    "total_envelope_area": calculate_total_envelope_area,
    "net_wall_area": calculate_net_wall_area,
    # Thermal resistance & U-value
    "layer_resistance": calculate_layer_resistance,
    "total_resistance": calculate_total_resistance,
    "u_value": calculate_u_value,
    "insulation_effect": calculate_insulation_effect,
    # Conduction
    "conduction_heat_loss": calculate_conduction_heat_loss,
    "heat_flow": calculate_heat_flow,
    "multilayer_heat_transfer": calculate_multilayer_heat_transfer,
    "heat_loss_coefficient": calculate_heat_loss_coefficient,
    "total_heat_loss_coefficient": calculate_total_heat_loss_coefficient,
    # Solar
    "solar_gain": calculate_solar_gain,
    "glazing_solar_gain": calculate_glazing_solar_gain,
    "orientation_factor": calculate_orientation_factor,
    "incidence_factor": calculate_incidence_factor,
    "integrate_power": integrate_power_over_time,
    # Ventilation
    "airflow_from_ach": calculate_airflow_from_ach,
    "ventilation_heat_loss": calculate_ventilation_heat_loss,
    "ventilation_loss_from_ach": calculate_ventilation_loss_from_ach,
    # Thermal mass
    "thermal_capacity": calculate_thermal_capacity,
    "temperature_change": calculate_temperature_change,
    "stored_thermal_energy": calculate_stored_thermal_energy,
    # Radiation & Internal heat
    "radiation": calculate_radiative_heat_transfer,
    "internal_heat_gain": calculate_internal_heat_gain,
    # Net balance & simulation
    "net_heat_flow": calculate_net_heat_flow,
    "temperature_update": calculate_temperature_update,
    "simulate_temperature_step": simulate_temperature_step,
    "heating_requirement": calculate_heating_requirement,
    # Comfort & statistics
    "comfort_status": calculate_comfort_status,
    "is_comfortable": is_comfortable,
    "comfort_hours": calculate_comfort_hours,
    "comfort_percentage": calculate_comfort_percentage,
    "min_temperature": calculate_min_temperature,
    "max_temperature": calculate_max_temperature,
    "average_temperature": calculate_average_temperature,
    "temperature_range": calculate_temperature_range,
    "design_score": calculate_design_score,
}


# =====================================================================
# FORMULA METADATA INTROSPECTION DICTIONARY
# =====================================================================

FORMULA_METADATA: Dict[str, Dict[str, str]] = {
    "u_value": {
        "description": "Overall thermal transmittance across an envelope assembly",
        "equation": "U = 1 / R_total",
        "input_units": "R in m²·K/W",
        "output_units": "W/(m²·K)",
        "model_type": "Physically rigorous 1D steady-state"
    },
    "conduction_heat_loss": {
        "description": "Conductive heat transfer rate through building envelope surfaces",
        "equation": "Q = U * A * (T_in - T_out)",
        "input_units": "U: W/(m²·K), A: m², T: °C",
        "output_units": "Watts (W)",
        "model_type": "Physically rigorous 1D steady-state"
    },
    "glazing_solar_gain": {
        "description": "Instantaneous useful solar thermal heat gain through windows",
        "equation": "Q_solar = I * A_window * SHGC * F_shading",
        "input_units": "I: W/m², A: m², SHGC: dimensionless",
        "output_units": "Watts (W)",
        "model_type": "Standard ASHRAE SHGC lumped model (Simplified MVP)"
    },
    "ventilation_heat_loss": {
        "description": "Sensible heat loss caused by infiltration / ventilation air change",
        "equation": "Q_vent = rho * V_dot * c_p * (T_in - T_out)",
        "input_units": "rho: kg/m³, V_dot: m³/s, c_p: J/(kg·K), T: °C",
        "output_units": "Watts (W)",
        "model_type": "Sensible energy balance (Physically rigorous)"
    },
    "thermal_capacity": {
        "description": "Lumped thermal heat capacitance of construction and thermal mass elements",
        "equation": "C = m * c_p",
        "input_units": "m: kg, c_p: J/(kg·K)",
        "output_units": "Joules per Kelvin (J/K)",
        "model_type": "Lumped single-node capacitance"
    },
    "radiation": {
        "description": "Longwave infrared thermal radiation exchange",
        "equation": "Q_rad = epsilon * sigma * A * (T_s,K^4 - T_surr,K^4)",
        "input_units": "epsilon: dimensionless, A: m², T: °C / K",
        "output_units": "Watts (W)",
        "model_type": "Stefan-Boltzmann gray-body radiation"
    },
    "temperature_update": {
        "description": "Explicit forward Euler time-step indoor temperature integration",
        "equation": "T_{t+dt} = T_t + (Q_net * dt) / C_thermal",
        "input_units": "T: °C, Q_net: Watts, C: J/K, dt: seconds",
        "output_units": "Degrees Celsius (°C)",
        "model_type": "First-order lumped transient Euler update"
    },
    "design_score": {
        "description": "Normalized multi-objective composite optimization score",
        "equation": "Score = w_c*S_comfort + w_e*S_energy + w_hl*S_heat_loss + w_s*S_solar",
        "input_units": "Scores: 0-100, Weights: sum to 1.0",
        "output_units": "Score (0 - 100)",
        "model_type": "Linear Multi-Attribute Utility Decision Support"
    }
}
