"""
THERMOSHELTER AI - Central Building Simulation Service
======================================================
Single authoritative simulation engine for full timeseries thermal modeling,
envelope U-value derivation, component heat balance tracking, and thermal
comfort assessment.

Architecture:
app.py / optimize.py -> simulation_service.py -> thermal.py -> formulas.py
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

# Ensure services package is discoverable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from services.climate_service import get_climate_data
from services.material_service import get_material
import services.formulas as f
from services.formula_constants import (
    AIR_DENSITY_DEFAULT,
    AIR_SPECIFIC_HEAT,
    DEFAULT_ACH,
    DEFAULT_COMFORT_MAX,
    DEFAULT_COMFORT_MIN,
    DEFAULT_OCCUPANT_HEAT_GAIN,
    DEFAULT_R_INSIDE_HORIZONTAL,
    DEFAULT_R_INSIDE_VERTICAL,
    DEFAULT_R_OUTSIDE_HORIZONTAL,
    DEFAULT_R_OUTSIDE_VERTICAL,
    SECONDS_PER_HOUR,
)


# =====================================================================
# GLAZING & ORIENTATION SPECIFICATIONS
# =====================================================================
GLAZING_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "single_clear": {
        "name": "Single Glazed Clear (6mm)",
        "u_value": 5.80,
        "shgc": 0.82,
        "description": "Standard 6mm single float glass",
    },
    "double_clear": {
        "name": "Double Glazed Clear (4-12-4 Air)",
        "u_value": 2.80,
        "shgc": 0.70,
        "description": "Standard double glazing with 12mm air cavity",
    },
    "double_low_e": {
        "name": "Double Low-E Glazing (Argon Gas)",
        "u_value": 1.80,
        "shgc": 0.50,
        "description": "High performance low-emissivity coating with Argon cavity",
    },
    "triple_low_e": {
        "name": "Triple Low-E Glazing (Argon Gas)",
        "u_value": 1.00,
        "shgc": 0.35,
        "description": "Ultra high-performance triple glazing for extreme cold",
    },
}

ORIENTATION_FACTORS: Dict[str, float] = {
    "south": 1.00,  # Maximum passive solar harvesting in winter (Northern Hemisphere)
    "north": 0.45,  # Diffuse ambient daylight
    "east": 0.70,   # Morning solar gain
    "west": 0.75,   # Afternoon solar gain
}

SHELTER_MODELS: Dict[str, Dict[str, Any]] = {
    "rectangular_flat": {
        "name": "Rectangular (Flat Roof)",
        "description": "Standard rectangular plan with flat composite roof. Highly cost effective and modular.",
        "roof_type": "flat",
        "default_dimensions": {"length": 4.5, "width": 3.2, "height": 2.8},
    },
    "rectangular_pitched": {
        "name": "Rectangular (Pitched Roof)",
        "description": "Gabled pitched roof (30° slope) with increased attic buffer, excellent snow and rain runoff.",
        "roof_type": "pitched",
        "default_dimensions": {"length": 4.5, "width": 3.2, "height": 2.8},
    },
    "compact_shelter": {
        "name": "Compact Shelter (Low S/V Ratio)",
        "description": "Square footprint maximizing interior volume while minimizing external surface exposure.",
        "roof_type": "flat",
        "default_dimensions": {"length": 3.8, "width": 3.8, "height": 2.8},
    },
    "elongated_shelter": {
        "name": "Elongated Shelter (Solar/Vent Oriented)",
        "description": "High aspect-ratio footprint (2.5:1) maximizing south solar aperture or cross-ventilation.",
        "roof_type": "flat",
        "default_dimensions": {"length": 6.0, "width": 2.4, "height": 2.8},
    },
    "custom_dimensions": {
        "name": "Custom Dimensions",
        "description": "User-defined custom length, width, height, and roof profile.",
        "roof_type": "custom",
        "default_dimensions": {"length": 4.0, "width": 3.0, "height": 2.8},
    },
}


def calculate_assembly_u_value(
    base_material: Union[str, Dict[str, Any]],
    base_thickness_m: float,
    insulation_thickness_m: float = 0.0,
    insulation_conductivity: float = 0.025,
    is_horizontal: bool = False,
    r_inside: Optional[float] = None,
    r_outside: Optional[float] = None,
) -> Dict[str, float]:
    """
    Computes ISO 6946 total thermal resistance and U-value for a composite wall or roof assembly.

    Parameters:
        base_material: Material key (str) or material dictionary.
        base_thickness_m: Thickness of the structural substrate in meters.
        insulation_thickness_m: Added insulation layer thickness in meters.
        insulation_conductivity: Thermal conductivity of insulation (W/mK). Default 0.025 (PUF).
        is_horizontal: If True, uses standard horizontal ceiling film resistances.
        r_inside: Custom inside film resistance (m²K/W).
        r_outside: Custom outside film resistance (m²K/W).

    Returns:
        Dict with "R_total", "U_value", "base_R", "insulation_R".
    """
    if r_inside is None:
        r_inside = DEFAULT_R_INSIDE_HORIZONTAL if is_horizontal else DEFAULT_R_INSIDE_VERTICAL
    if r_outside is None:
        r_outside = DEFAULT_R_OUTSIDE_HORIZONTAL if is_horizontal else DEFAULT_R_OUTSIDE_VERTICAL

    # Resolve base material conductivity
    if isinstance(base_material, str):
        mat_dict = get_material(base_material)
        if "error" in mat_dict:
            k_base = 0.72  # Default brick fallback
        else:
            k_base = float(mat_dict.get("thermal_conductivity", 0.72))
    elif isinstance(base_material, dict):
        k_base = float(base_material.get("thermal_conductivity", 0.72))
    else:
        k_base = 0.72

    layers: List[Tuple[float, float]] = []
    base_r = 0.0
    if base_thickness_m > 0:
        base_r = f.calculate_layer_resistance(base_thickness_m, k_base)
        layers.append((base_thickness_m, k_base))

    ins_r = 0.0
    if insulation_thickness_m > 0:
        ins_r = f.calculate_layer_resistance(insulation_thickness_m, insulation_conductivity)
        layers.append((insulation_thickness_m, insulation_conductivity))

    if not layers:
        # Fallback if both thicknesses are 0
        layers.append((0.20, k_base))
        base_r = 0.20 / k_base

    r_total = f.calculate_total_resistance(r_inside, layers, r_outside)
    u_val = f.calculate_u_value(r_total)

    return {
        "R_total": round(float(r_total), 4),
        "U_value": round(float(u_val), 4),
        "base_R": round(float(base_r), 4),
        "insulation_R": round(float(ins_r), 4),
    }


def run_simulation(
    city: str,
    length: float = 4.0,
    width: float = 3.0,
    height: float = 2.8,
    wall_material: Union[str, Dict[str, Any]] = "brick",
    wall_thickness_m: float = 0.23,
    insulation_thickness_m: float = 0.0,
    insulation_conductivity: float = 0.025,
    window_area: float = 2.0,
    glazing: str = "double_clear",
    orientation: Union[str, float] = "south",
    roof_type: str = "flat",
    pitch_angle_deg: float = 30.0,
    shelter_model: Optional[str] = None,
    roof_thickness_m: float = 0.15,
    roof_conductivity: float = 0.50,
    roof_insulation_m: float = 0.0,
    glass_thickness_m: float = 0.006,
    glass_conductivity: float = 1.00,
    shgc: Optional[float] = None,
    ach: float = DEFAULT_ACH,
    occupants: int = 2,
    heat_per_person: float = DEFAULT_OCCUPANT_HEAT_GAIN,
    initial_indoor_temp: float = 20.0,
    hours_to_simulate: int = 168,
    substeps: int = 60,
) -> Dict[str, Any]:
    """
    Authoritative physical simulation runner for shelter thermal response.

    Features:
      - Multi-layer ISO 6946 U-values for walls, roof, and fenestration.
      - Support for glazing types (single_clear, double_clear, double_low_e, triple_low_e).
      - Support for multiple shelter models (rectangular flat/pitched, compact, elongated, custom).
      - Orientation solar harvesting factors (south, north, east, west).
      - Sub-hour explicit forward Euler numerical integration (dt = 3600 / substeps).
      - Hourly component heat flow balance tracking (solar, internal, walls, roof, floor, glass, vent, radiation).
      - Cumulative energy metrics (kWh) and thermal comfort statistics.
    """
    # 1. Fetch Weather Data
    weather = get_climate_data(city)
    if "error" in weather:
        return {"error": weather["error"]}

    outdoor_temps = weather["hourly_temperature"]
    direct_solar = weather["hourly_direct_solar"]
    diffuse_solar = weather["hourly_diffuse_solar"]

    available_hours = min(len(outdoor_temps), hours_to_simulate)
    if available_hours <= 0:
        return {"error": f"No weather data available for city: {city}"}

    # 2. Geometric Calculations via services/geometry.py
    floor_area = f.calculate_floor_area(length, width)

    # Determine roof type from model if provided
    effective_roof_type = roof_type
    if shelter_model == "rectangular_pitched":
        effective_roof_type = "pitched"
    elif shelter_model in ("rectangular_flat", "compact_shelter", "elongated_shelter"):
        effective_roof_type = "flat"

    if effective_roof_type == "pitched":
        p_geo = f.calculate_pitched_roof_geometry(length, width, height, pitch_angle_deg)
        roof_area = p_geo["roof_area"]
        gross_wall_area = p_geo["gross_wall_area"]
        volume = p_geo["volume"]
    else:
        volume = f.calculate_volume(length, width, height)
        roof_area = f.calculate_roof_area_flat(length, width)
        gross_wall_area = f.calculate_wall_area(length, width, height)

    window_area_clamped = min(window_area, gross_wall_area * 0.85)
    solid_wall_area = f.calculate_net_wall_area(gross_wall_area, window_area_clamped, 0.0)


    # 3. Envelope U-values via ISO 6946 multi-layer formulation
    wall_u_data = calculate_assembly_u_value(
        base_material=wall_material,
        base_thickness_m=wall_thickness_m,
        insulation_thickness_m=insulation_thickness_m,
        insulation_conductivity=insulation_conductivity,
        is_horizontal=False,
    )
    roof_u_data = calculate_assembly_u_value(
        base_material={"thermal_conductivity": roof_conductivity},
        base_thickness_m=roof_thickness_m,
        insulation_thickness_m=roof_insulation_m,
        insulation_conductivity=insulation_conductivity,
        is_horizontal=True,
    )
    floor_u_data = calculate_assembly_u_value(
        base_material={"thermal_conductivity": 1.20},
        base_thickness_m=0.15,
        is_horizontal=True,
    )

    # Resolve glazing parameters
    if glazing in GLAZING_PROPERTIES:
        glaze_spec = GLAZING_PROPERTIES[glazing]
        u_glass = float(glaze_spec["u_value"])
        effective_shgc = float(glaze_spec["shgc"]) if shgc is None else float(shgc)
    else:
        # Fallback to single/custom glass
        r_glass_film = DEFAULT_R_INSIDE_VERTICAL + (glass_thickness_m / glass_conductivity) + DEFAULT_R_OUTSIDE_VERTICAL
        u_glass = float(1.0 / r_glass_film)
        effective_shgc = 0.80 if shgc is None else float(shgc)

    # Resolve orientation factor
    if isinstance(orientation, str):
        orient_factor = ORIENTATION_FACTORS.get(orientation.lower(), 1.0)
    elif isinstance(orientation, (int, float)):
        orient_factor = float(max(0.0, min(1.0, orientation)))
    else:
        orient_factor = 1.0

    u_wall = wall_u_data["U_value"]
    u_roof = roof_u_data["U_value"]
    u_floor = floor_u_data["U_value"]

    # 4. Thermal Mass (Air mass + interior multiplier)
    air_mass = volume * AIR_DENSITY_DEFAULT
    total_thermal_mass = (air_mass * AIR_SPECIFIC_HEAT) * 3.0

    # 5. Simulation Time-stepping
    dt = SECONDS_PER_HOUR / substeps
    t_in = float(initial_indoor_temp)

    indoor_temps: List[float] = []
    hourly_solar_irradiance: List[float] = []
    hourly_solar_power: List[float] = []
    hourly_solar_gain: List[float] = []
    hourly_q_internal: List[float] = []
    hourly_q_walls: List[float] = []
    hourly_q_roof: List[float] = []
    hourly_q_floor: List[float] = []
    hourly_q_windows: List[float] = []
    hourly_q_vent: List[float] = []
    hourly_q_rad: List[float] = []
    hourly_q_net: List[float] = []
    comfort_status_series: List[str] = []

    # Internal occupant gain
    q_internal_base = f.calculate_internal_heat_gain(occupants, heat_per_person)
    # Add modest base equipment/lighting (approx 40W)
    q_internal_total = q_internal_base + 40.0

    for hour in range(available_hours):
        t_out = float(outdoor_temps[hour])
        solar_flux = float(direct_solar[hour] + diffuse_solar[hour])
        p_solar_incident = float(solar_flux * window_area_clamped)

        # Step useful solar gain through windows (with glazing SHGC and orientation scaling)
        q_sol = f.calculate_glazing_solar_gain(
            solar_irradiance=solar_flux,
            window_area=window_area_clamped,
            shgc=effective_shgc,
            shading_factor=orient_factor
        )

        hour_q_walls = 0.0
        hour_q_roof = 0.0
        hour_q_floor = 0.0
        hour_q_windows = 0.0
        hour_q_vent = 0.0
        hour_q_rad = 0.0
        hour_q_net = 0.0

        for _ in range(substeps):
            q_walls = f.calculate_conduction_heat_loss(u_wall, solid_wall_area, t_in, t_out)
            q_roof = f.calculate_conduction_heat_loss(u_roof, roof_area, t_in, t_out)
            q_floor = f.calculate_conduction_heat_loss(u_floor, floor_area, t_in, t_out)
            q_windows = f.calculate_conduction_heat_loss(u_glass, window_area_clamped, t_in, t_out)
            q_vent = f.calculate_ventilation_loss_from_ach(ach, volume, t_in, t_out)
            q_rad = f.calculate_radiative_heat_transfer(
                emissivity=0.90,
                area=roof_area,
                surface_temperature_c=t_in,
                surrounding_temperature_c=t_out
            )

            q_cond = q_walls + q_roof + q_floor + q_windows
            q_net = f.calculate_net_heat_flow(
                solar_gain=q_sol,
                internal_gain=q_internal_total,
                conduction_loss=q_cond,
                ventilation_loss=q_vent,
                radiation_loss=q_rad
            )
            t_in = f.calculate_temperature_update(
                current_temperature=t_in,
                net_heat_flow=q_net,
                thermal_capacity=total_thermal_mass,
                time_step_seconds=dt
            )

            hour_q_walls += q_walls
            hour_q_roof += q_roof
            hour_q_floor += q_floor
            hour_q_windows += q_windows
            hour_q_vent += q_vent
            hour_q_rad += q_rad
            hour_q_net += q_net

        indoor_temps.append(round(float(t_in), 4))
        hourly_solar_irradiance.append(round(float(solar_flux), 2))
        hourly_solar_power.append(round(float(p_solar_incident), 2))
        hourly_solar_gain.append(round(float(q_sol), 2))
        hourly_q_internal.append(round(float(q_internal_total), 2))
        hourly_q_walls.append(round(float(hour_q_walls / substeps), 2))
        hourly_q_roof.append(round(float(hour_q_roof / substeps), 2))
        hourly_q_floor.append(round(float(hour_q_floor / substeps), 2))
        hourly_q_windows.append(round(float(hour_q_windows / substeps), 2))
        hourly_q_vent.append(round(float(hour_q_vent / substeps), 2))
        hourly_q_rad.append(round(float(hour_q_rad / substeps), 2))
        hourly_q_net.append(round(float(hour_q_net / substeps), 2))
        comfort_status_series.append(f.calculate_comfort_status(t_in, DEFAULT_COMFORT_MIN, DEFAULT_COMFORT_MAX))

    # 6. Thermal Comfort Indicators via services/comfort.py
    avg_t = round(f.calculate_average_temperature(indoor_temps), 2)
    min_t = round(f.calculate_min_temperature(indoor_temps), 2)
    max_t = round(f.calculate_max_temperature(indoor_temps), 2)
    comfort_hrs = f.calculate_comfort_hours(indoor_temps, DEFAULT_COMFORT_MIN, DEFAULT_COMFORT_MAX)
    comfort_pct = f.calculate_comfort_percentage(comfort_hrs, float(len(indoor_temps)))

    # Discomfort degree-hours calculation
    discomfort_dh = 0.0
    for t in indoor_temps:
        if t < DEFAULT_COMFORT_MIN:
            discomfort_dh += (DEFAULT_COMFORT_MIN - t)
        elif t > DEFAULT_COMFORT_MAX:
            discomfort_dh += (t - DEFAULT_COMFORT_MAX)

    if comfort_pct >= 75.0:
        overall_comfort_status = "Comfortable"
    elif avg_t < DEFAULT_COMFORT_MIN:
        overall_comfort_status = "Cold-Dominated (Underheating)"
    else:
        overall_comfort_status = "Heat-Dominated (Overheating)"

    comfort_metrics = {
        "avg": avg_t,
        "min_t": min_t,
        "max_t": max_t,
        "comfort_pct": round(comfort_pct, 2),
        "discomfort_dh": round(float(discomfort_dh), 2),
        "comfort_hours": comfort_hrs,
        "status": overall_comfort_status,
    }

    # 7. Energy Totals in kWh
    total_solar_kwh = round(f.calculate_total_solar_energy(hourly_solar_gain), 2)
    total_incident_solar_kwh = round(f.calculate_total_solar_energy(hourly_solar_power), 2)
    total_internal_kwh = round(sum(hourly_q_internal) / 1000.0, 2)
    total_wall_loss_kwh = round(f.calculate_total_heat_loss(hourly_q_walls), 2)
    total_roof_loss_kwh = round(f.calculate_total_heat_loss(hourly_q_roof), 2)
    total_floor_loss_kwh = round(f.calculate_total_heat_loss(hourly_q_floor), 2)
    total_window_loss_kwh = round(f.calculate_total_heat_loss(hourly_q_windows), 2)
    total_vent_loss_kwh = round(f.calculate_total_heat_loss(hourly_q_vent), 2)
    total_rad_loss_kwh = round(f.calculate_total_heat_loss(hourly_q_rad), 2)

    total_component_loss_kwh = round(
        total_wall_loss_kwh + total_roof_loss_kwh + total_floor_loss_kwh +
        total_window_loss_kwh + total_vent_loss_kwh + total_rad_loss_kwh, 2
    )

    component_heat_loss = {
        "wall_loss_kwh": total_wall_loss_kwh,
        "roof_loss_kwh": total_roof_loss_kwh,
        "floor_loss_kwh": total_floor_loss_kwh,
        "window_loss_kwh": total_window_loss_kwh,
        "ventilation_loss_kwh": total_vent_loss_kwh,
        "radiation_loss_kwh": total_rad_loss_kwh,
    }

    energy_totals = {
        "solar_gain_kwh": total_solar_kwh,
        "incident_solar_kwh": total_incident_solar_kwh,
        "internal_gain_kwh": total_internal_kwh,
        "wall_loss_kwh": total_wall_loss_kwh,
        "roof_loss_kwh": total_roof_loss_kwh,
        "floor_loss_kwh": total_floor_loss_kwh,
        "window_loss_kwh": total_window_loss_kwh,
        "vent_loss_kwh": total_vent_loss_kwh,
        "radiation_loss_kwh": total_rad_loss_kwh,
        "total_heat_loss_kwh": total_component_loss_kwh,
        "total_envelope_loss_kwh": round(total_wall_loss_kwh + total_roof_loss_kwh + total_floor_loss_kwh + total_window_loss_kwh, 2),
    }

    return {
        "city": city,
        # SIH Core Outputs
        "indoor_temperature": indoor_temps,
        "indoor_temperatures": indoor_temps,
        "outdoor_temperature": outdoor_temps[:available_hours],
        "outdoor_temperatures": outdoor_temps[:available_hours],
        "solar_irradiance": hourly_solar_irradiance,
        "solar_power": hourly_solar_power,
        "solar_thermal_gain": hourly_solar_gain,
        "hourly_solar_gain": hourly_solar_gain,
        "hourly_internal_gain": hourly_q_internal,
        "wall_heat_flow": hourly_q_walls,
        "hourly_wall_loss": hourly_q_walls,
        "roof_heat_flow": hourly_q_roof,
        "hourly_roof_loss": hourly_q_roof,
        "floor_heat_flow": hourly_q_floor,
        "window_heat_flow": hourly_q_windows,
        "hourly_window_loss": hourly_q_windows,
        "ventilation_heat_flow": hourly_q_vent,
        "hourly_vent_loss": hourly_q_vent,
        "radiation_heat_flow": hourly_q_rad,
        "net_heat_flow": hourly_q_net,

        "comfort_status": overall_comfort_status,
        "comfort_status_series": comfort_status_series,
        "comfort_hours": comfort_hrs,
        "comfort_percentage": round(comfort_pct, 2),
        "discomfort_degree_hours": round(float(discomfort_dh), 2),
        "integrated_solar_energy_kwh": total_solar_kwh,
        "integrated_incident_solar_kwh": total_incident_solar_kwh,
        "component_heat_loss_kwh": component_heat_loss,
        "total_heat_loss_kwh": total_component_loss_kwh,
        "comfort_metrics": comfort_metrics,
        "energy_totals_kwh": energy_totals,
        "u_values": {
            "wall_u": u_wall,
            "roof_u": u_roof,
            "floor_u": u_floor,
            "glass_u": round(u_glass, 4),
            "wall_r_total": wall_u_data["R_total"],
            "roof_r_total": roof_u_data["R_total"],
            "floor_r_total": floor_u_data["R_total"],
        },
        "geometry": {
            "floor_area_m2": round(floor_area, 2),
            "volume_m3": round(volume, 2),
            "solid_wall_area_m2": round(solid_wall_area, 2),
            "roof_area_m2": round(roof_area, 2),
            "window_area_m2": round(window_area_clamped, 2),
            "roof_type": effective_roof_type,
            "shelter_model": shelter_model or ("rectangular_pitched" if effective_roof_type == "pitched" else "rectangular_flat"),
        },
        "specs": {
            "wall_material": wall_material if isinstance(wall_material, str) else "custom",
            "insulation_thickness_m": insulation_thickness_m,
            "window_area_m2": window_area_clamped,
            "glazing": glazing,
            "orientation": orientation,
            "roof_type": effective_roof_type,
            "shelter_model": shelter_model or ("rectangular_pitched" if effective_roof_type == "pitched" else "rectangular_flat"),
            "occupants": occupants,
        }
    }


def simulate_shelter(

    city: str,
    length: float,
    width: float,
    height: float,
    wall_material_name: str,
    window_area: float,
    insulation_thickness_m: float = 0.0,
    glazing: str = "double_clear",
    orientation: Union[str, float] = "south",
    occupants: int = 2,
    substeps: int = 60,
    return_full_dict: bool = False,
) -> Union[List[float], Dict[str, Any]]:
    """
    Standard interface function providing drop-in compatibility for simulate_shelter.

    If return_full_dict is False: returns List[float] of indoor temperatures.
    If return_full_dict is True: returns the full detailed results dictionary.
    """
    result = run_simulation(
        city=city,
        length=length,
        width=width,
        height=height,
        wall_material=wall_material_name,
        insulation_thickness_m=insulation_thickness_m,
        window_area=window_area,
        glazing=glazing,
        orientation=orientation,
        occupants=occupants,
        substeps=substeps,
    )
    if "error" in result:
        return result

    if return_full_dict:
        return result
    return result["indoor_temperatures"]

