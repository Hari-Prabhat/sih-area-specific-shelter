"""
THERMOSHELTER AI - Deterministic Scenario Test Fixtures
========================================================
Provides deterministic, physically representative test fixtures for the three
core SIH validation scenarios:
  1. LEH (Cold / High-Altitude / Permanent Shelter)
  2. JAISALMER (Hot-Dry / High Solar Radiation)
  3. CHENNAI (Hot-Humid / High Humidity)

NOTE:
  These fixtures are designated for TEST AND INDEPENDENT DEVELOPMENT ONLY.
  They provide deterministic, reproducible boundary conditions for Member 3
  while Member 1 (Climate) and Member 2 (Design) work on their respective branches.
"""

import math
from typing import List, Tuple
from services.contracts import ClimateProfile, ShelterDesign


# =====================================================================
# 1. LEH, LADAKH SCENARIO FIXTURE (Cold / High Altitude)
# =====================================================================

def get_leh_scenario(
    hours: int = 168,
    occupants: int = 4,
    shelter_type: str = "Permanent"
) -> Tuple[ClimateProfile, ShelterDesign]:
    """
    Returns deterministic (ClimateProfile, ShelterDesign) for Leh, Ladakh.

    Climate Characteristics:
      - Extreme cold winter conditions: mean temp -5.0°C, diurnal swing ±7.5°C (-12.5°C to +2.5°C).
      - High altitude clear sky solar radiation: peak direct solar 750 W/m².
      - Dry mountain air: relative humidity ~35%, wind speed ~3.0 m/s.

    Shelter Design (Golden Scenario):
      - 4 Occupants, Permanent shelter.
      - Dimensions: 4.5m x 3.2m x 2.8m (Floor Area: 14.4 m², Volume: 40.32 m³).
      - Double-glazed Low-E fenestration facing South (solar passive harvesting).
      - Heavy thermal envelope (fired clay brick, 230mm base + 80mm PUF insulation).
    """
    t_series: List[float] = []
    dni_series: List[float] = []
    dhi_series: List[float] = []
    ws_series: List[float] = []
    rh_series: List[float] = []

    for h in range(hours):
        hour_of_day = h % 24
        # Cold temperature diurnal wave: minimum at 05:00, maximum at 14:00
        t = -5.0 + 7.5 * math.sin((hour_of_day - 8) * math.pi / 12.0)
        t_series.append(round(t, 2))

        # Strong high-altitude solar irradiance
        if 7 <= hour_of_day <= 17:
            solar_frac = math.sin((hour_of_day - 7) * math.pi / 10.0)
            dni = max(0.0, 750.0 * solar_frac)
            dhi = max(0.0, 150.0 * solar_frac)
        else:
            dni = 0.0
            dhi = 0.0

        dni_series.append(round(dni, 1))
        dhi_series.append(round(dhi, 1))
        ws_series.append(3.0)
        rh_series.append(35.0)

    climate = ClimateProfile(
        city="leh",
        latitude=34.1526,
        longitude=77.5771,
        hourly_temperature=t_series,
        hourly_direct_solar=dni_series,
        hourly_diffuse_solar=dhi_series,
        hourly_wind_speed=ws_series,
        hourly_humidity=rh_series,
        climate_zone="cold",
    )

    design = ShelterDesign(
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        wall_thickness_m=0.23,
        insulation_thickness_m=0.08,
        insulation_conductivity=0.025,
        roof_type="pitched",
        pitch_angle_deg=30.0,
        roof_thickness_m=0.15,
        roof_conductivity=0.50,
        roof_insulation_m=0.08,
        window_area=2.5,
        glazing="double_low_e",
        orientation="south",
        ach=0.5,
        occupants=occupants,
        shelter_type=shelter_type,
        shelter_model="rectangular_pitched",
        heat_per_person=80.0,
    )

    return climate, design


# =====================================================================
# 2. JAISALMER SCENARIO FIXTURE (Hot-Dry / Desert)
# =====================================================================

def get_jaisalmer_scenario(
    hours: int = 168,
    occupants: int = 4,
    shelter_type: str = "Permanent"
) -> Tuple[ClimateProfile, ShelterDesign]:
    """
    Returns deterministic (ClimateProfile, ShelterDesign) for Jaisalmer.

    Climate Characteristics:
      - Hot-dry desert climate: mean temp 36.0°C, diurnal swing ±8.0°C (28.0°C to 44.0°C).
      - Very high direct solar radiation: peak direct solar 850 W/m².
      - Arid atmosphere: relative humidity ~20%, wind speed ~4.0 m/s.

    Shelter Design:
      - 4 Occupants.
      - High thermal mass (mud/stone 300mm), shaded window aperture facing North.
    """
    t_series: List[float] = []
    dni_series: List[float] = []
    dhi_series: List[float] = []
    ws_series: List[float] = []
    rh_series: List[float] = []

    for h in range(hours):
        hour_of_day = h % 24
        t = 36.0 + 8.0 * math.sin((hour_of_day - 8) * math.pi / 12.0)
        t_series.append(round(t, 2))

        if 6 <= hour_of_day <= 18:
            solar_frac = math.sin((hour_of_day - 6) * math.pi / 12.0)
            dni = max(0.0, 850.0 * solar_frac)
            dhi = max(0.0, 180.0 * solar_frac)
        else:
            dni = 0.0
            dhi = 0.0

        dni_series.append(round(dni, 1))
        dhi_series.append(round(dhi, 1))
        ws_series.append(4.0)
        rh_series.append(20.0)

    climate = ClimateProfile(
        city="jaisalmer",
        latitude=26.9157,
        longitude=70.9083,
        hourly_temperature=t_series,
        hourly_direct_solar=dni_series,
        hourly_diffuse_solar=dhi_series,
        hourly_wind_speed=ws_series,
        hourly_humidity=rh_series,
        climate_zone="hot_dry",
    )

    design = ShelterDesign(
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="mud",
        wall_thickness_m=0.30,
        insulation_thickness_m=0.03,
        insulation_conductivity=0.025,
        roof_type="flat",
        pitch_angle_deg=0.0,
        roof_thickness_m=0.20,
        roof_conductivity=0.60,
        roof_insulation_m=0.04,
        window_area=1.5,
        glazing="double_clear",
        orientation="north",
        ach=0.8,
        occupants=occupants,
        shelter_type=shelter_type,
        shelter_model="compact_shelter",
        heat_per_person=80.0,
    )

    return climate, design


# =====================================================================
# 3. CHENNAI SCENARIO FIXTURE (Hot-Humid / Coastal)
# =====================================================================

def get_chennai_scenario(
    hours: int = 168,
    occupants: int = 4,
    shelter_type: str = "Permanent"
) -> Tuple[ClimateProfile, ShelterDesign]:
    """
    Returns deterministic (ClimateProfile, ShelterDesign) for Chennai.

    Climate Characteristics:
      - Hot-humid coastal climate: mean temp 31.0°C, narrow diurnal swing ±4.0°C (27.0°C to 35.0°C).
      - Moderate direct / high diffuse solar radiation: peak DNI 600 W/m², DHI 250 W/m².
      - High relative humidity: ~80%, sea breeze ~3.5 m/s.

    Shelter Design:
      - 4 Occupants.
      - Cross-ventilation optimized (higher ACH), moderate insulation, East/West solar shading.
    """
    t_series: List[float] = []
    dni_series: List[float] = []
    dhi_series: List[float] = []
    ws_series: List[float] = []
    rh_series: List[float] = []

    for h in range(hours):
        hour_of_day = h % 24
        t = 31.0 + 4.0 * math.sin((hour_of_day - 8) * math.pi / 12.0)
        t_series.append(round(t, 2))

        if 6 <= hour_of_day <= 18:
            solar_frac = math.sin((hour_of_day - 6) * math.pi / 12.0)
            dni = max(0.0, 600.0 * solar_frac)
            dhi = max(0.0, 250.0 * solar_frac)
        else:
            dni = 0.0
            dhi = 0.0

        dni_series.append(round(dni, 1))
        dhi_series.append(round(dhi, 1))
        ws_series.append(3.5)
        rh_series.append(80.0)

    climate = ClimateProfile(
        city="chennai",
        latitude=13.0827,
        longitude=80.2707,
        hourly_temperature=t_series,
        hourly_direct_solar=dni_series,
        hourly_diffuse_solar=dhi_series,
        hourly_wind_speed=ws_series,
        hourly_humidity=rh_series,
        climate_zone="hot_humid",
    )

    design = ShelterDesign(
        length=5.0,
        width=2.8,
        height=2.8,
        wall_material="brick",
        wall_thickness_m=0.20,
        insulation_thickness_m=0.02,
        insulation_conductivity=0.025,
        roof_type="flat",
        pitch_angle_deg=0.0,
        roof_thickness_m=0.15,
        roof_conductivity=0.50,
        roof_insulation_m=0.03,
        window_area=3.0,
        glazing="double_clear",
        orientation="east",
        ach=1.5,
        occupants=occupants,
        shelter_type=shelter_type,
        shelter_model="elongated_shelter",
        heat_per_person=80.0,
    )

    return climate, design
