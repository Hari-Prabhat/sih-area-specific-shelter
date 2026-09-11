"""
THERMOSHELTER AI - Thermal Comfort & Performance Statistics
============================================================
Formulas for temperature evaluation, comfort duration metrics,
temperature summary statistics, and multi-criteria design scoring.
"""

from typing import Dict, List, Optional, Union
import numpy as np
from services.formula_constants import (
    DEFAULT_COMFORT_MAX,
    DEFAULT_COMFORT_MIN,
)


def calculate_comfort_status(
    indoor_temperature: float,
    comfort_min: float = DEFAULT_COMFORT_MIN,
    comfort_max: float = DEFAULT_COMFORT_MAX
) -> str:
    """
    Evaluates indoor temperature against a static thermal comfort band.

    Parameters:
        indoor_temperature (float): Indoor air temperature in degrees Celsius (°C).
        comfort_min (float): Minimum acceptable comfort temperature in °C. Default is 18.0°C.
        comfort_max (float): Maximum acceptable comfort temperature in °C. Default is 24.0°C.

    Returns:
        str: "too_cold" if T < comfort_min, "comfortable" if comfort_min <= T <= comfort_max, "too_hot" if T > comfort_max.

    Assumptions:
        Simplified operative temperature range indicator. Not a full Fanger PMV/PPD or Adaptive ASHRAE 55 model.

    Raises:
        ValueError: If comfort_min > comfort_max.
    """
    if comfort_min > comfort_max:
        raise ValueError(f"comfort_min ({comfort_min}°C) cannot exceed comfort_max ({comfort_max}°C)")

    if indoor_temperature < comfort_min:
        return "too_cold"
    elif indoor_temperature > comfort_max:
        return "too_hot"
    else:
        return "comfortable"


def is_comfortable(
    indoor_temperature: float,
    comfort_min: float = DEFAULT_COMFORT_MIN,
    comfort_max: float = DEFAULT_COMFORT_MAX
) -> bool:
    """
    Returns True if indoor temperature lies within the comfort band [comfort_min, comfort_max].
    """
    return calculate_comfort_status(indoor_temperature, comfort_min, comfort_max) == "comfortable"


def calculate_comfort_hours(
    temperature_series: Union[List[float], np.ndarray],
    comfort_min: float = DEFAULT_COMFORT_MIN,
    comfort_max: float = DEFAULT_COMFORT_MAX,
    time_step_hours: float = 1.0
) -> float:
    """
    Calculates total hours during which indoor temperature was within the comfort range.

    Formula:
        comfort_hours = count(comfort_min <= T_i <= comfort_max) * delta_t_hours

    Parameters:
        temperature_series (List[float] or np.ndarray): Series of indoor temperatures in °C.
        comfort_min (float): Lower threshold (°C).
        comfort_max (float): Upper threshold (°C).
        time_step_hours (float): Duration per timestep in hours. Default is 1.0h.

    Returns:
        float: Cumulative comfortable hours (h).

    Raises:
        ValueError: If temperature_series is empty, comfort_min > comfort_max, or time_step_hours <= 0.
    """
    if comfort_min > comfort_max:
        raise ValueError(f"comfort_min ({comfort_min}) cannot exceed comfort_max ({comfort_max})")
    if time_step_hours <= 0.0:
        raise ValueError(f"Time step must be positive, got {time_step_hours}")

    arr = np.asarray(temperature_series, dtype=float)
    if arr.size == 0:
        raise ValueError("Temperature series cannot be empty.")

    mask = (arr >= comfort_min) & (arr <= comfort_max)
    return float(np.sum(mask) * time_step_hours)


def calculate_comfort_percentage(
    comfortable_hours: float,
    total_hours: float
) -> float:
    """
    Calculates the percentage of total simulation hours that were thermally comfortable.

    Formula:
        percentage = (comfortable_hours / total_hours) * 100

    Parameters:
        comfortable_hours (float): Hours inside comfort zone (h). Must be >= 0.
        total_hours (float): Total simulation duration (h). Must be > 0.

    Returns:
        float: Comfort percentage from 0.0% to 100.0%.

    Raises:
        ValueError: If comfortable_hours < 0, total_hours <= 0, or comfortable_hours > total_hours.
    """
    if comfortable_hours < 0.0:
        raise ValueError(f"Comfortable hours cannot be negative, got {comfortable_hours}")
    if total_hours <= 0.0:
        raise ValueError(f"Total hours must be strictly positive, got {total_hours}")
    if comfortable_hours > total_hours:
        raise ValueError(f"Comfortable hours ({comfortable_hours}) cannot exceed total hours ({total_hours})")

    return float((comfortable_hours / total_hours) * 100.0)


def calculate_min_temperature(series: Union[List[float], np.ndarray]) -> float:
    """Returns the minimum temperature in the series in °C."""
    arr = np.asarray(series, dtype=float)
    if arr.size == 0:
        raise ValueError("Temperature series cannot be empty.")
    return float(np.min(arr))


def calculate_max_temperature(series: Union[List[float], np.ndarray]) -> float:
    """Returns the maximum temperature in the series in °C."""
    arr = np.asarray(series, dtype=float)
    if arr.size == 0:
        raise ValueError("Temperature series cannot be empty.")
    return float(np.max(arr))


def calculate_average_temperature(series: Union[List[float], np.ndarray]) -> float:
    """Returns the arithmetic mean temperature in the series in °C."""
    arr = np.asarray(series, dtype=float)
    if arr.size == 0:
        raise ValueError("Temperature series cannot be empty.")
    return float(np.mean(arr))


def calculate_temperature_range(series: Union[List[float], np.ndarray]) -> float:
    """
    Calculates temperature oscillation amplitude (diurnal swing).

    Formula:
        delta_T = max(T) - min(T)
    """
    arr = np.asarray(series, dtype=float)
    if arr.size == 0:
        raise ValueError("Temperature series cannot be empty.")
    return float(np.max(arr) - np.min(arr))


def calculate_total_heat_loss(
    power_series_watts: Union[List[float], np.ndarray],
    time_step_hours: float = 1.0
) -> float:
    """
    Integrates total conductive and ventilation heat losses into cumulative kilowatt-hours (kWh).

    Formula:
        E_loss_kWh = sum(max(0, P_i) * delta_t_hours) / 1000

    Parameters:
        power_series_watts (List[float] or np.ndarray): Instantaneous heat loss power values in Watts.
        time_step_hours (float): Timestep in hours. Default is 1.0.

    Returns:
        float: Cumulative thermal heat loss in kWh.
    """
    if time_step_hours <= 0.0:
        raise ValueError(f"Timestep must be positive, got {time_step_hours}")
    arr = np.asarray(power_series_watts, dtype=float)
    pos_power = np.maximum(0.0, arr)
    return float(np.sum(pos_power * time_step_hours) / 1000.0)


def calculate_total_solar_energy(
    solar_power_series_watts: Union[List[float], np.ndarray],
    time_step_hours: float = 1.0
) -> float:
    """
    Integrates total useful solar heat admitted into the shelter in kilowatt-hours (kWh).

    Formula:
        E_solar_kWh = sum(P_solar_i * delta_t_hours) / 1000
    """
    if time_step_hours <= 0.0:
        raise ValueError(f"Timestep must be positive, got {time_step_hours}")
    arr = np.asarray(solar_power_series_watts, dtype=float)
    pos_power = np.maximum(0.0, arr)
    return float(np.sum(pos_power * time_step_hours) / 1000.0)


def calculate_external_energy_requirement(
    heating_demand_watts: Union[List[float], np.ndarray],
    time_step_hours: float = 1.0
) -> float:
    """
    Calculates total supplemental active heating energy required to maintain indoor target temperature.

    Formula:
        E_aux_kWh = sum(max(0, Q_aux_i) * delta_t_hours) / 1000
    """
    if time_step_hours <= 0.0:
        raise ValueError(f"Timestep must be positive, got {time_step_hours}")
    arr = np.asarray(heating_demand_watts, dtype=float)
    pos_power = np.maximum(0.0, arr)
    return float(np.sum(pos_power * time_step_hours) / 1000.0)


def calculate_design_score(
    comfort_score: float,
    energy_score: float,
    heat_loss_score: float,
    solar_score: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Computes a normalized composite multi-objective design performance score (0 to 100).

    Formula:
        Score = w_c * S_comfort + w_e * S_energy + w_hl * S_heat_loss + w_s * S_solar

    Parameters:
        comfort_score (float): Normalized thermal comfort score (0 - 100).
        energy_score (float): Normalized energy conservation score (0 - 100).
        heat_loss_score (float): Normalized thermal envelope retention score (0 - 100).
        solar_score (float): Normalized passive solar harvesting score (0 - 100).
        weights (Optional[Dict[str, float]]): Custom weights dictionary.
            Defaults to: {"comfort": 0.40, "energy": 0.30, "heat_loss": 0.20, "solar": 0.10}

    Returns:
        float: Composite performance score between 0.0 and 100.0.

    Assumptions:
        Linear additive multi-attribute utility theory (MAUT) decision support metric.

    Raises:
        ValueError: If weights are missing, negative, or do not sum to approximately 1.0.
    """
    if weights is None:
        weights = {
            "comfort": 0.40,
            "energy": 0.30,
            "heat_loss": 0.20,
            "solar": 0.10,
        }

    req_keys = {"comfort", "energy", "heat_loss", "solar"}
    if not req_keys.issubset(weights.keys()):
        raise ValueError(f"Weights dict must contain all required keys: {req_keys}")

    for k in req_keys:
        if weights[k] < 0.0:
            raise ValueError(f"Weight '{k}' cannot be negative, got {weights[k]}")

    w_sum = sum(weights[k] for k in req_keys)
    if not (0.99 <= w_sum <= 1.01):
        raise ValueError(f"Weights must sum to 1.0 (within tolerance), got sum = {w_sum}")

    # Validate individual scores
    for name, s in [("comfort", comfort_score), ("energy", energy_score), ("heat_loss", heat_loss_score), ("solar", solar_score)]:
        if s < 0.0 or s > 100.0:
            raise ValueError(f"{name}_score must be between 0.0 and 100.0, got {s}")

    score = (
        weights["comfort"] * comfort_score +
        weights["energy"] * energy_score +
        weights["heat_loss"] * heat_loss_score +
        weights["solar"] * solar_score
    )
    return float(round(score, 2))
