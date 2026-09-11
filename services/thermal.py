"""
THERMOSHELTER AI - Thermal Energy & Heat Transfer Formulas
===========================================================
Formulas for multi-layer thermal resistance, U-values, conductive heat loss,
lumped thermal capacitance, longwave radiation exchange, internal gains,
and transient energy-balance temperature updates.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from services.formula_constants import (
    CELSIUS_TO_KELVIN,
    DEFAULT_OCCUPANT_HEAT_GAIN,
    DEFAULT_R_INSIDE_VERTICAL,
    DEFAULT_R_OUTSIDE_VERTICAL,
    STEFAN_BOLTZMANN,
)


def celsius_to_kelvin(t_c: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Converts temperature from Celsius (°C) to absolute Kelvin (K).

    Formula:
        T_K = T_C + 273.15
    """
    return t_c + CELSIUS_TO_KELVIN


def kelvin_to_celsius(t_k: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Converts absolute temperature from Kelvin (K) to Celsius (°C).

    Formula:
        T_C = T_K - 273.15

    Raises:
        ValueError: If T_K is strictly negative (< 0 K).
    """
    if isinstance(t_k, (int, float)) and t_k < 0.0:
        raise ValueError(f"Absolute temperature in Kelvin cannot be negative, got {t_k} K")
    elif isinstance(t_k, np.ndarray) and np.any(t_k < 0.0):
        raise ValueError("Absolute temperature array contains negative Kelvin values.")
    return t_k - CELSIUS_TO_KELVIN


def calculate_layer_resistance(thickness: float, conductivity: float) -> float:
    """
    Calculates the 1D conductive thermal resistance (R-value) of a homogeneous material layer.

    Formula:
        R = thickness / conductivity

    Parameters:
        thickness (float): Layer thickness in meters (m). Must be > 0.
        conductivity (float): Thermal conductivity in Watts per meter-Kelvin (W/(m·K)). Must be > 0.

    Returns:
        float: Thermal resistance in square meter-Kelvins per Watt (m²·K/W).

    Assumptions:
        Physically rigorous 1D steady-state Fourier conduction.

    Raises:
        ValueError: If thickness <= 0 or conductivity <= 0.
    """
    if thickness <= 0.0:
        raise ValueError(f"Layer thickness must be strictly positive (> 0), got {thickness} m")
    if conductivity <= 0.0:
        raise ValueError(f"Thermal conductivity must be strictly positive (> 0), got {conductivity} W/m·K")

    return float(thickness / conductivity)


def calculate_total_resistance(
    inside_surface_resistance: float,
    layers: List[Tuple[float, float]],
    outside_surface_resistance: float
) -> float:
    """
    Calculates the total thermal resistance (R_total) of a multi-layer composite assembly.

    Formula:
        R_total = R_inside + sum(thickness_i / conductivity_i) + R_outside

    Parameters:
        inside_surface_resistance (float): Interior surface air film resistance in m²·K/W. Must be >= 0.
        layers (List[Tuple[float, float]]): Ordered list of (thickness_m, conductivity_W_mK) tuples.
        outside_surface_resistance (float): Exterior surface air film resistance in m²·K/W. Must be >= 0.

    Returns:
        float: Total composite thermal resistance in m²·K/W.

    Raises:
        ValueError: If film resistances are negative or any layer property is non-positive.
    """
    if inside_surface_resistance < 0.0:
        raise ValueError(f"Inside surface resistance cannot be negative, got {inside_surface_resistance}")
    if outside_surface_resistance < 0.0:
        raise ValueError(f"Outside surface resistance cannot be negative, got {outside_surface_resistance}")
    if not layers:
        raise ValueError("Layers list cannot be empty.")

    r_layers = 0.0
    for i, (thick, cond) in enumerate(layers):
        if thick <= 0.0:
            raise ValueError(f"Layer #{i} thickness must be > 0, got {thick}")
        if cond <= 0.0:
            raise ValueError(f"Layer #{i} conductivity must be > 0, got {cond}")
        r_layers += (thick / cond)

    return float(inside_surface_resistance + r_layers + outside_surface_resistance)


def calculate_u_value(total_resistance: float) -> float:
    """
    Calculates the overall heat transfer coefficient (U-value / thermal transmittance).

    Formula:
        U = 1 / R_total

    Parameters:
        total_resistance (float): Total thermal resistance in m²·K/W. Must be > 0.

    Returns:
        float: U-value in Watts per square meter-Kelvin (W/(m²·K)).

    Raises:
        ValueError: If total_resistance <= 0.
    """
    if total_resistance <= 0.0:
        raise ValueError(f"Total resistance must be strictly positive (> 0), got {total_resistance}")
    return float(1.0 / total_resistance)


def calculate_insulation_effect(
    existing_r: float,
    additional_thickness: float,
    insulation_conductivity: float
) -> Tuple[float, float]:
    """
    Calculates the updated R-value and corresponding U-value after adding an insulation layer.

    Parameters:
        existing_r (float): Baseline assembly R-value in m²·K/W. Must be > 0.
        additional_thickness (float): Added insulation thickness in meters (m). Must be >= 0.
        insulation_conductivity (float): Conductivity of the added insulation in W/(m·K). Must be > 0.

    Returns:
        Tuple[float, float]: (new_R_total, new_U_value).
    """
    if existing_r <= 0.0:
        raise ValueError(f"Existing R-value must be > 0, got {existing_r}")
    if additional_thickness < 0.0:
        raise ValueError(f"Additional thickness cannot be negative, got {additional_thickness}")
    if insulation_conductivity <= 0.0:
        raise ValueError(f"Insulation conductivity must be > 0, got {insulation_conductivity}")

    added_r = (additional_thickness / insulation_conductivity) if additional_thickness > 0 else 0.0
    new_r = existing_r + added_r
    new_u = 1.0 / new_r
    return float(new_r), float(new_u)


def calculate_conduction_heat_loss(
    u_value: float,
    area: float,
    indoor_temperature: float,
    outdoor_temperature: float
) -> float:
    """
    Calculates the rate of conductive heat transfer through a building envelope component.

    Formula:
        Q_conduction = U * A * (T_in - T_out)

    Parameters:
        u_value (float): Overall thermal transmittance in W/(m²·K). Must be >= 0.
        area (float): Net surface area in square meters (m²). Must be >= 0.
        indoor_temperature (float): Indoor zone temperature in °C.
        outdoor_temperature (float): Outdoor ambient temperature in °C.

    Returns:
        float: Conductive heat transfer rate in Watts (W).
               Sign convention:
               - Positive (+) denotes heat leaving the shelter (loss when Tin > Tout).
               - Negative (-) denotes heat entering the shelter (gain when Tin < Tout).

    Raises:
        ValueError: If u_value < 0 or area < 0.
    """
    if u_value < 0.0:
        raise ValueError(f"U-value cannot be negative, got {u_value}")
    if area < 0.0:
        raise ValueError(f"Area cannot be negative, got {area}")

    delta_t = indoor_temperature - outdoor_temperature
    return float(u_value * area * delta_t)


def calculate_heat_flow(
    u_value: float,
    area: float,
    temp_diff: float
) -> float:
    """
    Calculates steady conductive heat flow given a temperature differential.

    Formula:
        Q = U * A * delta_T
    """
    if u_value < 0.0:
        raise ValueError(f"U-value cannot be negative, got {u_value}")
    if area < 0.0:
        raise ValueError(f"Area cannot be negative, got {area}")
    return float(u_value * area * temp_diff)


def calculate_multilayer_heat_transfer(
    layers: List[Tuple[float, float]],
    area: float,
    indoor_temperature: float,
    outdoor_temperature: float,
    r_inside: float = DEFAULT_R_INSIDE_VERTICAL,
    r_outside: float = DEFAULT_R_OUTSIDE_VERTICAL
) -> Dict[str, float]:
    """
    Calculates total resistance, U-value, and conductive heat loss for a multi-layer wall or roof.

    Parameters:
        layers (List[Tuple[float, float]]): List of (thickness_m, conductivity_W_mK).
        area (float): Component surface area in m².
        indoor_temperature (float): Indoor temperature in °C.
        outdoor_temperature (float): Outdoor temperature in °C.
        r_inside (float): Inside film resistance (default: 0.13 m²·K/W).
        r_outside (float): Outside film resistance (default: 0.04 m²·K/W).

    Returns:
        Dict[str, float]: Dictionary with {"R_total": ..., "U_value": ..., "heat_loss_watts": ...}.
    """
    r_total = calculate_total_resistance(r_inside, layers, r_outside)
    u_val = calculate_u_value(r_total)
    q_loss = calculate_conduction_heat_loss(u_val, area, indoor_temperature, outdoor_temperature)
    return {
        "R_total": r_total,
        "U_value": u_val,
        "heat_loss_watts": q_loss
    }


def calculate_heat_loss_coefficient(u_value: float, area: float) -> float:
    """
    Calculates the building component heat loss coefficient (UA-value) in W/K.

    Formula:
        H = U * A
    """
    if u_value < 0.0 or area < 0.0:
        raise ValueError("U-value and area cannot be negative.")
    return float(u_value * area)


def calculate_total_heat_loss_coefficient(components: List[Tuple[float, float]]) -> float:
    """
    Calculates the aggregate building envelope heat loss coefficient (sum of UA products) in W/K.

    Formula:
        H_total = sum(U_i * A_i)

    Parameters:
        components (List[Tuple[float, float]]): List of (u_value, area) tuples.
    """
    h_total = 0.0
    for u, a in components:
        h_total += calculate_heat_loss_coefficient(u, a)
    return float(h_total)


def calculate_thermal_capacity(mass: float, specific_heat: float) -> float:
    """
    Calculates the lumped thermal capacitance (heat capacity) of a thermal storage mass.

    Formula:
        C = mass * specific_heat

    Parameters:
        mass (float): Mass of the element in kilograms (kg). Must be >= 0.
        specific_heat (float): Specific heat capacity in J/(kg·K). Must be > 0.

    Returns:
        float: Thermal capacity in Joules per Kelvin (J/K).

    Raises:
        ValueError: If mass < 0 or specific_heat <= 0.
    """
    if mass < 0.0:
        raise ValueError(f"Mass cannot be negative, got {mass}")
    if specific_heat <= 0.0:
        raise ValueError(f"Specific heat must be strictly positive, got {specific_heat}")
    return float(mass * specific_heat)


def calculate_temperature_change(energy_joules: float, thermal_capacity: float) -> float:
    """
    Calculates the temperature increment resulting from absorbed or lost thermal energy.

    Formula:
        delta_T = Q / C

    Parameters:
        energy_joules (float): Net thermal energy added (J).
        thermal_capacity (float): Thermal capacity in J/K. Must be > 0.

    Returns:
        float: Temperature change in Kelvin or °C (delta_T).

    Raises:
        ValueError: If thermal_capacity <= 0.
    """
    if thermal_capacity <= 0.0:
        raise ValueError(f"Thermal capacity must be strictly positive (> 0), got {thermal_capacity}")
    return float(energy_joules / thermal_capacity)


def calculate_stored_thermal_energy(mass: float, specific_heat: float, delta_temperature: float) -> float:
    """
    Calculates the sensible thermal energy stored in a mass across a temperature rise delta_T.

    Formula:
        Q = mass * specific_heat * delta_T
    """
    c = calculate_thermal_capacity(mass, specific_heat)
    return float(c * delta_temperature)


def calculate_radiative_heat_transfer(
    emissivity: float,
    area: float,
    surface_temperature_c: float,
    surrounding_temperature_c: float
) -> float:
    """
    Calculates net longwave radiative heat exchange using the Stefan-Boltzmann law.

    Formula:
        Q_rad = epsilon * sigma * A * (T_surface_K^4 - T_surroundings_K^4)

    Parameters:
        emissivity (float): Surface longwave emissivity (0.0 to 1.0).
        area (float): Radiating surface area in square meters (m²). Must be >= 0.
        surface_temperature_c (float): Surface temperature in °C.
        surrounding_temperature_c (float): Surrounding/Sky effective temperature in °C.

    Returns:
        float: Radiative heat loss rate in Watts (W).
               Positive (+) indicates net radiation loss to surroundings.

    Assumptions:
        Simplified gray-body radiation exchange with surrounding isothermal black enclosure.

    Raises:
        ValueError: If emissivity is not in [0, 1] or area < 0.
    """
    if not (0.0 <= emissivity <= 1.0):
        raise ValueError(f"Emissivity must be between 0.0 and 1.0, got {emissivity}")
    if area < 0.0:
        raise ValueError(f"Area cannot be negative, got {area}")

    t_s_k = celsius_to_kelvin(surface_temperature_c)
    t_surr_k = celsius_to_kelvin(surrounding_temperature_c)

    q_rad = emissivity * STEFAN_BOLTZMANN * area * (t_s_k**4 - t_surr_k**4)
    return float(q_rad)


def calculate_internal_heat_gain(
    occupants: int,
    heat_per_person: float = DEFAULT_OCCUPANT_HEAT_GAIN
) -> float:
    """
    Calculates internal sensible metabolic heat gain from human occupants.

    Formula:
        Q_internal = occupants * heat_per_person

    Parameters:
        occupants (int): Number of human occupants inside shelter. Must be >= 0.
        heat_per_person (float): Sensible heat output per person in Watts (W/person). Must be >= 0.

    Returns:
        float: Total internal sensible heat gain in Watts (W).

    Raises:
        ValueError: If occupants < 0 or heat_per_person < 0.
    """
    if occupants < 0:
        raise ValueError(f"Occupants cannot be negative, got {occupants}")
    if heat_per_person < 0.0:
        raise ValueError(f"Heat per person cannot be negative, got {heat_per_person}")
    return float(occupants * heat_per_person)


def calculate_net_heat_flow(
    solar_gain: float,
    internal_gain: float,
    conduction_loss: float,
    ventilation_loss: float,
    radiation_loss: float = 0.0
) -> float:
    """
    Calculates the instantaneous net thermal energy rate entering or leaving the indoor air node.

    Formula:
        Q_net = Q_solar + Q_internal - Q_conduction - Q_ventilation - Q_radiation

    Parameters:
        solar_gain (float): Useful solar thermal power admitted in Watts (W).
        internal_gain (float): Internal heat power from occupants/equipment in Watts (W).
        conduction_loss (float): Envelope conductive heat loss rate in Watts (W).
        ventilation_loss (float): Infiltration & ventilation heat loss rate in Watts (W).
        radiation_loss (float): Net longwave radiative loss rate in Watts (W). Default is 0.0.

    Returns:
        float: Net heat flow rate in Watts (W).
               Positive (+) = Net energy gain (causes indoor temperature to rise).
               Negative (-) = Net energy loss (causes indoor temperature to fall).
    """
    return float(solar_gain + internal_gain - conduction_loss - ventilation_loss - radiation_loss)


def calculate_temperature_update(
    current_temperature: float,
    net_heat_flow: float,
    thermal_capacity: float,
    time_step_seconds: float = 3600.0
) -> float:
    """
    Explicit forward Euler time-step integration for lumped indoor operative temperature.

    Formula:
        delta_T = (Q_net * delta_t) / C_thermal
        T_next = T_current + delta_T

    Parameters:
        current_temperature (float): Indoor air temperature at timestep t in °C.
        net_heat_flow (float): Net heat flow rate Q_net in Watts (W).
        thermal_capacity (float): Effective thermal capacitance in J/K. Must be > 0.
        time_step_seconds (float): Simulation timestep duration in seconds. Default is 3600.0s.

    Returns:
        float: Updated indoor temperature at timestep t + delta_t in °C.

    Assumptions:
        Single-node lumped thermal capacitance model with explicit Euler time integration.

    Raises:
        ValueError: If thermal_capacity <= 0 or time_step_seconds <= 0.
    """
    if thermal_capacity <= 0.0:
        raise ValueError(f"Thermal capacity must be strictly positive, got {thermal_capacity}")
    if time_step_seconds <= 0.0:
        raise ValueError(f"Timestep duration must be strictly positive, got {time_step_seconds}")

    delta_energy = net_heat_flow * time_step_seconds
    delta_t = delta_energy / thermal_capacity
    return float(current_temperature + delta_t)


def simulate_temperature_step(
    indoor_temperature: float,
    outdoor_temperature: float,
    solar_irradiance: float,
    window_area: float,
    shgc: float,
    envelope_ua: float,
    ach: float,
    volume: float,
    occupants: int,
    thermal_capacity: float,
    time_step_seconds: float = 3600.0,
    shading_factor: float = 1.0,
    heat_per_person: float = DEFAULT_OCCUPANT_HEAT_GAIN
) -> Dict[str, float]:
    """
    Executes one complete physics-based thermal simulation step for an enclosed shelter.

    Returns:
        Dict[str, float]: Detailed heat balance and updated temperature dictionary:
        {
            "indoor_temperature": next_T_c,
            "q_solar": q_sol,
            "q_internal": q_int,
            "q_conduction": q_cond,
            "q_ventilation": q_vent,
            "q_net": q_net,
            "delta_t": delta_t
        }
    """
    # 1. Solar gain
    from services.solar import calculate_glazing_solar_gain
    from services.ventilation import calculate_ventilation_loss_from_ach

    q_sol = calculate_glazing_solar_gain(solar_irradiance, window_area, shgc, shading_factor)

    # 2. Internal gain
    q_int = calculate_internal_heat_gain(occupants, heat_per_person)

    # 3. Conduction loss
    q_cond = calculate_heat_flow(envelope_ua, 1.0, indoor_temperature - outdoor_temperature)

    # 4. Ventilation loss
    q_vent = calculate_ventilation_loss_from_ach(ach, volume, indoor_temperature, outdoor_temperature)

    # 5. Net heat balance
    q_net = calculate_net_heat_flow(
        solar_gain=q_sol,
        internal_gain=q_int,
        conduction_loss=q_cond,
        ventilation_loss=q_vent,
        radiation_loss=0.0
    )

    # 6. Temperature update
    next_temp = calculate_temperature_update(
        current_temperature=indoor_temperature,
        net_heat_flow=q_net,
        thermal_capacity=thermal_capacity,
        time_step_seconds=time_step_seconds
    )

    return {
        "indoor_temperature": next_temp,
        "q_solar": q_sol,
        "q_internal": q_int,
        "q_conduction": q_cond,
        "q_ventilation": q_vent,
        "q_net": q_net,
        "delta_t": next_temp - indoor_temperature
    }


def calculate_heating_requirement(
    indoor_temperature: float,
    target_temperature: float,
    thermal_capacity: float,
    time_step_seconds: float = 3600.0
) -> float:
    """
    Calculates supplemental active heating power (Watts) required to raise temperature to target.

    Formula:
        If T_in < T_target:
            Q_heat = (thermal_capacity * (T_target - T_in)) / time_step_seconds
        Else:
            Q_heat = 0.0

    Parameters:
        indoor_temperature (float): Current simulated indoor temperature in °C.
        target_temperature (float): Desired indoor comfort setpoint in °C.
        thermal_capacity (float): Thermal capacity of the shelter node in J/K.
        time_step_seconds (float): Duration in seconds (s). Default is 3600.0s.

    Returns:
        float: Required auxiliary heating power in Watts (W).
    """
    if thermal_capacity <= 0.0:
        raise ValueError(f"Thermal capacity must be > 0, got {thermal_capacity}")
    if time_step_seconds <= 0.0:
        raise ValueError(f"Timestep must be > 0, got {time_step_seconds}")

    if indoor_temperature < target_temperature:
        needed_energy = thermal_capacity * (target_temperature - indoor_temperature)
        return float(needed_energy / time_step_seconds)
    return 0.0
