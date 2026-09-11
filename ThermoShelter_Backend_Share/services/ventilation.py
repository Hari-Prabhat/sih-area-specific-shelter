"""
THERMOSHELTER AI - Ventilation & Infiltration Heat Transfer
===========================================================
Formulas for volumetric air exchange, infiltration airflow,
and sensible heat losses caused by air exchange.
"""

from services.formula_constants import (
    AIR_DENSITY_DEFAULT,
    AIR_SPECIFIC_HEAT,
    SECONDS_PER_HOUR,
)


def calculate_airflow_from_ach(ach: float, volume: float) -> float:
    """
    Calculates volumetric airflow rate in cubic meters per second (m³/s) from Air Changes per Hour (ACH).

    Formula:
        V_dot = (ACH * volume) / 3600

    Parameters:
        ach (float): Air exchange rate in air changes per hour (1/h). Must be >= 0.
        volume (float): Enclosed internal air volume in cubic meters (m³). Must be > 0.

    Returns:
        float: Volumetric airflow rate in m³/s.

    Raises:
        ValueError: If ach < 0 or volume <= 0.
    """
    if ach < 0.0:
        raise ValueError(f"ACH cannot be negative, got {ach}")
    if volume <= 0.0:
        raise ValueError(f"Volume must be strictly positive (> 0), got {volume}")

    return float((ach * volume) / SECONDS_PER_HOUR)


def calculate_ventilation_heat_loss(
    air_density: float,
    airflow: float,
    air_specific_heat: float,
    indoor_temperature: float,
    outdoor_temperature: float
) -> float:
    """
    Calculates sensible heat loss rate due to ventilation or infiltration.

    Formula:
        Q_vent = rho * V_dot * c_p * (T_in - T_out)

    Parameters:
        air_density (float): Air density in kilograms per cubic meter (kg/m³). Must be > 0.
        airflow (float): Volumetric airflow rate in cubic meters per second (m³/s). Must be >= 0.
        air_specific_heat (float): Air specific heat capacity in Joules per kilogram-Kelvin (J/(kg·K)). Must be > 0.
        indoor_temperature (float): Indoor air temperature in degrees Celsius (°C).
        outdoor_temperature (float): Outdoor ambient air temperature in degrees Celsius (°C).

    Returns:
        float: Sensible ventilation/infiltration heat transfer in Watts (W).
               Positive (+) indicates heat loss to the outside when Tin > Tout.
               Negative (-) indicates heat gain from hot outdoor air when Tin < Tout.

    Assumptions:
        Sensible heat exchange only; moisture/latent enthalpy neglected for dry cold climates (Ladakh).

    Raises:
        ValueError: If air_density <= 0, airflow < 0, or air_specific_heat <= 0.
    """
    if air_density <= 0.0:
        raise ValueError(f"Air density must be positive, got {air_density}")
    if airflow < 0.0:
        raise ValueError(f"Airflow cannot be negative, got {airflow}")
    if air_specific_heat <= 0.0:
        raise ValueError(f"Air specific heat must be positive, got {air_specific_heat}")

    delta_t = indoor_temperature - outdoor_temperature
    return float(air_density * airflow * air_specific_heat * delta_t)


def calculate_ventilation_loss_from_ach(
    ach: float,
    volume: float,
    indoor_temperature: float,
    outdoor_temperature: float,
    air_density: float = AIR_DENSITY_DEFAULT,
    air_specific_heat: float = AIR_SPECIFIC_HEAT
) -> float:
    """
    Convenience function that calculates ventilation heat loss directly from ACH and shelter volume.

    Formula:
        V_dot = (ACH * volume) / 3600
        Q_vent = rho * V_dot * c_p * (T_in - T_out)

    Parameters:
        ach (float): Air changes per hour (1/h).
        volume (float): Internal air volume in m³.
        indoor_temperature (float): Indoor temperature in °C.
        outdoor_temperature (float): Outdoor ambient temperature in °C.
        air_density (float): Air density in kg/m³. Default is 1.225 kg/m³.
        air_specific_heat (float): Specific heat of air in J/(kg·K). Default is 1005.0 J/(kg·K).

    Returns:
        float: Ventilation heat loss rate in Watts (W).
    """
    airflow = calculate_airflow_from_ach(ach, volume)
    return calculate_ventilation_heat_loss(
        air_density=air_density,
        airflow=airflow,
        air_specific_heat=air_specific_heat,
        indoor_temperature=indoor_temperature,
        outdoor_temperature=outdoor_temperature
    )
