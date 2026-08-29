"""
THERMOSHELTER AI - Solar Energy & Radiation Formulas
=====================================================
Formulas for solar irradiance on surfaces, glazing solar heat gain,
orientation factors, and numerical power-energy integration over time.
"""

import math
from typing import List, Union
import numpy as np


def calculate_solar_gain(
    solar_irradiance: float,
    area: float,
    absorptivity: float,
    solar_factor: float = 1.0
) -> float:
    """
    Calculates the instantaneous solar thermal power absorbed by an opaque surface.

    Formula:
        Q_solar = I * A * alpha * F

    Parameters:
        solar_irradiance (float): Incident solar flux (Global/Direct) in Watts per square meter (W/m²). Must be >= 0.
        area (float): Exposed surface area in square meters (m²). Must be >= 0.
        absorptivity (float): Solar absorption coefficient (dimensionless, 0.0 to 1.0).
        solar_factor (float): Effective geometric/shading factor (dimensionless, 0.0 to 1.0). Default is 1.0.

    Returns:
        float: Absorbed solar thermal power in Watts (W).

    Assumptions:
        Simplified quasi-steady state opaque surface absorption model.

    Raises:
        ValueError: If any input is out of physical bounds.
    """
    if solar_irradiance < 0.0:
        raise ValueError(f"Solar irradiance cannot be negative, got {solar_irradiance}")
    if area < 0.0:
        raise ValueError(f"Area cannot be negative, got {area}")
    if not (0.0 <= absorptivity <= 1.0):
        raise ValueError(f"Absorptivity must be between 0.0 and 1.0, got {absorptivity}")
    if not (0.0 <= solar_factor <= 1.0):
        raise ValueError(f"Solar factor must be between 0.0 and 1.0, got {solar_factor}")

    return float(solar_irradiance * area * absorptivity * solar_factor)


def calculate_glazing_solar_gain(
    solar_irradiance: float,
    window_area: float,
    shgc: float,
    shading_factor: float = 1.0
) -> float:
    """
    Calculates instantaneous useful solar heat admitted directly through fenestration/glazing.

    Formula:
        Q_solar = I * A_window * SHGC * F_shading

    Parameters:
        solar_irradiance (float): Solar radiation flux incident on window in Watts per square meter (W/m²). Must be >= 0.
        window_area (float): Net transparent glazed area in square meters (m²). Must be >= 0.
        shgc (float): Solar Heat Gain Coefficient of the glazing assembly (dimensionless, 0.0 to 1.0).
        shading_factor (float): External shading / dirt / frame reduction factor (0.0 to 1.0). Default is 1.0.

    Returns:
        float: Transmitted + absorbed/re-radiated solar thermal gain in Watts (W).

    Assumptions:
        Simplified standard ASHRAE SHGC lumped fenestration model. Suitable for MVP rapid simulation.

    Raises:
        ValueError: If inputs are negative or exceed physical bounds.
    """
    if solar_irradiance < 0.0:
        raise ValueError(f"Solar irradiance cannot be negative, got {solar_irradiance}")
    if window_area < 0.0:
        raise ValueError(f"Window area cannot be negative, got {window_area}")
    if not (0.0 <= shgc <= 1.0):
        raise ValueError(f"SHGC must be between 0.0 and 1.0, got {shgc}")
    if not (0.0 <= shading_factor <= 1.0):
        raise ValueError(f"Shading factor must be between 0.0 and 1.0, got {shading_factor}")

    return float(solar_irradiance * window_area * shgc * shading_factor)


def calculate_energy_from_power(
    power_watts: Union[float, np.ndarray],
    duration_seconds: float
) -> Union[float, np.ndarray]:
    """
    Converts steady thermal power over a fixed duration into cumulative energy.

    Formula:
        E = P * t

    Parameters:
        power_watts (float or np.ndarray): Thermal power in Watts (W).
        duration_seconds (float): Duration in seconds (s). Must be >= 0.

    Returns:
        float or np.ndarray: Thermal energy in Joules (J).

    Raises:
        ValueError: If duration_seconds < 0.
    """
    if duration_seconds < 0.0:
        raise ValueError(f"Duration cannot be negative, got {duration_seconds}")
    return power_watts * duration_seconds


def calculate_energy_kwh(
    power_watts: Union[float, np.ndarray],
    duration_hours: float
) -> Union[float, np.ndarray]:
    """
    Calculates thermal energy in kilowatt-hours (kWh) from power in Watts.

    Formula:
        E_kWh = (P * t_hours) / 1000

    Parameters:
        power_watts (float or np.ndarray): Power in Watts (W).
        duration_hours (float): Duration in hours (h). Must be >= 0.

    Returns:
        float or np.ndarray: Energy in kilowatt-hours (kWh).

    Raises:
        ValueError: If duration_hours < 0.
    """
    if duration_hours < 0.0:
        raise ValueError(f"Duration hours cannot be negative, got {duration_hours}")
    return (power_watts * duration_hours) / 1000.0


def integrate_power_over_time(
    power_values: Union[List[float], np.ndarray],
    time_step_seconds: float = 3600.0
) -> float:
    """
    Performs numerical integration of a power timeseries using the composite Trapezoidal Rule.

    Formula:
        E_total = integral P(t) dt approx sum ( (P_i + P_{i+1}) / 2 * delta_t )

    Parameters:
        power_values (List[float] or np.ndarray): Array/list of instantaneous power values in Watts (W).
        time_step_seconds (float): Uniform timestep in seconds (s). Default is 3600.0s (1 hour).

    Returns:
        float: Total accumulated thermal energy in Joules (J).

    Raises:
        ValueError: If power_values is empty or time_step_seconds <= 0.
    """
    if time_step_seconds <= 0.0:
        raise ValueError(f"Timestep must be strictly positive, got {time_step_seconds}")

    arr = np.asarray(power_values, dtype=float)
    if arr.size == 0:
        raise ValueError("Power values array cannot be empty.")
    if arr.size == 1:
        return float(arr[0] * time_step_seconds)

    # Trapezoidal numerical integration
    total_joules = np.trapezoid(arr, dx=time_step_seconds)
    return float(total_joules)


def calculate_orientation_factor(
    surface_orientation_deg: float,
    solar_azimuth_deg: float
) -> float:
    """
    Calculates the simplified horizontal azimuth alignment factor between a wall and the sun.

    Formula:
        F_orient = max(0.0, cos(theta_surface - theta_sun))

    Parameters:
        surface_orientation_deg (float): Surface facing azimuth in degrees (0°=N, 90°=E, 180°=S, 270°=W).
        solar_azimuth_deg (float): Sun azimuth in degrees (0°=N, 90°=E, 180°=S, 270°=W).

    Returns:
        float: Solar orientation factor in range [0.0, 1.0]. (0.0 when sun is behind the wall).

    Assumptions:
        Simplified horizontal plane geometric projection.
    """
    delta_rad = math.radians(surface_orientation_deg - solar_azimuth_deg)
    cos_val = math.cos(delta_rad)
    return float(max(0.0, cos_val))


def calculate_incidence_factor(
    solar_zenith_deg: float,
    surface_tilt_deg: float,
    surface_azimuth_deg: float = 180.0,
    solar_azimuth_deg: float = 180.0
) -> float:
    """
    Calculates the cosine of solar incidence angle (theta) for a tilted plane.

    Formula:
        cos(theta) = cos(theta_z)*cos(beta) + sin(theta_z)*sin(beta)*cos(gamma_s - gamma_w)
        Clamped to [0.0, 1.0].

    Parameters:
        solar_zenith_deg (float): Solar zenith angle from vertical (0° = directly overhead, 90° = horizon).
        surface_tilt_deg (float): Surface tilt from horizontal (0° = flat roof, 90° = vertical wall).
        surface_azimuth_deg (float): Wall orientation azimuth (180° = South).
        solar_azimuth_deg (float): Sun position azimuth (180° = South).

    Returns:
        float: Incidence factor between 0.0 and 1.0.

    Assumptions:
        Standard spherical trigonometry projection (Duffie & Beckman Solar Engineering).

    Raises:
        ValueError: If angles are out of range [0, 180] or [0, 360].
    """
    if not (0.0 <= solar_zenith_deg <= 180.0):
        raise ValueError(f"Solar zenith must be between 0° and 180°, got {solar_zenith_deg}")
    if not (0.0 <= surface_tilt_deg <= 180.0):
        raise ValueError(f"Surface tilt must be between 0° and 180°, got {surface_tilt_deg}")

    # If the sun is below horizon (zenith > 90°), incidence factor is 0
    if solar_zenith_deg >= 90.0:
        return 0.0

    z_rad = math.radians(solar_zenith_deg)
    b_rad = math.radians(surface_tilt_deg)
    d_az_rad = math.radians(solar_azimuth_deg - surface_azimuth_deg)

    cos_theta = math.cos(z_rad) * math.cos(b_rad) + math.sin(z_rad) * math.sin(b_rad) * math.cos(d_az_rad)
    return float(max(0.0, min(1.0, cos_theta)))
