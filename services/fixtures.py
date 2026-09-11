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


# =====================================================================
# 4. THERMOCORE-LADAKH-GOLDEN — Deterministic Engineering Integration Fixture
# =====================================================================

def get_golden_ladakh_scenario(
    hours: int = 168,
) -> Tuple[ClimateProfile, ShelterDesign]:
    """
    THERMOCORE-LADAKH-GOLDEN: Deterministic cold high-altitude integration fixture.

    DATA PROVENANCE NOTE:
      All values in this fixture are ESTIMATED / USER_DEFINED for engineering
      testing purposes. They are NOT measured field data. Do not cite them
      as validated or certified.

    Climate (ESTIMATED):
      - Location: Leh, Ladakh (34.1526°N, 77.5771°E, 3500m ASL)
      - Cold high-altitude winter: mean -8°C, diurnal swing ±6°C
      - High-altitude clear-sky solar: peak DNI 800 W/m², DHI 160 W/m²
      - Dry mountain air: RH ~30%, wind 2.5 m/s
      - Cloud cover: ~0.15 (clear), Precipitation: 0 mm

    Shelter (USER_DEFINED):
      - 4 occupants, permanent use
      - Compact geometry: 4.0m × 3.5m × 2.8m (14.0 m² floor, 39.2 m³ volume)
      - South-oriented (180°) for passive solar harvesting
      - High-performance envelope:
          Wall: stone (300mm, k=1.5) + PUF insulation (100mm, k=0.025)
          Roof: concrete deck (150mm, k=1.40) + PUF insulation (120mm, k=0.025)
          Floor: concrete slab (150mm, k=1.40)
      - Triple low-E glazing (argon), 2.0 m² window area, SHGC=0.45
      - Controlled ventilation: ACH=0.4 (tight envelope with airlock)
      - Thermal mass: Trombe wall (stone, 200mm, 4 m², south-facing)
      - Passive strategies: solar collection, thermal mass storage
    """
    from services.shelter.models import (
        DataProvenance,
        GlazingDefinition,
        MaterialAssembly,
        MaterialLayer,
        OpeningDefinition,
        PassiveStrategy as ShelterPassiveStrategy,
        ShelterDesign,
        ShelterGeometry,
        ShelterRequirements,
        ThermalMassDefinition,
        STANDARD_GLAZING_PRESETS,
    )

    # ── Climate synthesis (ESTIMATED from statistical data) ──
    t_series: List[float] = []
    dni_series: List[float] = []
    dhi_series: List[float] = []
    ws_series: List[float] = []
    rh_series: List[float] = []
    cc_series: List[float] = []
    pr_series: List[float] = []
    ts_series: List[str] = []

    for h in range(hours):
        hour_of_day = h % 24
        day_num = h // 24

        # Temperature: cold with diurnal cycle
        t = -8.0 + 6.0 * math.sin((hour_of_day - 8) * math.pi / 12.0)
        t_series.append(round(t, 2))

        # Solar: high altitude clear sky
        if 7 <= hour_of_day <= 17:
            solar_frac = math.sin((hour_of_day - 7) * math.pi / 10.0)
            dni_series.append(round(max(0.0, 800.0 * solar_frac), 1))
            dhi_series.append(round(max(0.0, 160.0 * solar_frac), 1))
        else:
            dni_series.append(0.0)
            dhi_series.append(0.0)

        ws_series.append(2.5)
        rh_series.append(30.0)
        cc_series.append(0.15)
        pr_series.append(0.0)
        ts_series.append(f"2026-01-{1 + day_num:02d}T{hour_of_day:02d}:00:00+05:30")

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
        elevation_m=3500.0,
        timezone_offset_hours=5.5,
        hourly_cloud_cover=cc_series,
        hourly_precipitation=pr_series,
        timestamps=ts_series,
        data_source="THERMOCORE_GOLDEN_FIXTURE",
        data_provenance="estimated",
        data_confidence=0.70,
    )

    # ── Shelter design (USER_DEFINED engineering fixture) ──
    requirements = ShelterRequirements(
        occupants=4,
        shelter_purpose="high_altitude_post",
        permanence="permanent",
        mobility="permanent",
        priorities=["thermal_comfort", "energy_efficiency", "structural_integrity"],
        available_resources=["local_stone", "concrete", "puf_insulation"],
        energy_sources=["passive_solar", "biomass"],
        constraints={"ach": 0.4, "heat_per_person": 80.0},
        provenance="user_defined",
    )

    openings = [
        OpeningDefinition(
            id="win_south_primary",
            name="South Primary Window",
            opening_type="window",
            width_m=1.6,
            height_m=1.25,
            area_m2=2.0,
            facade="south",
            orientation_deg=180.0,
            shading_factor=1.0,
            is_operable=False,
            ventilation_role="none",
        ),
    ]

    geometry = ShelterGeometry(
        geometry_type="rectangular",
        length_m=4.0,
        width_m=3.5,
        height_m=2.8,
        roof_type="flat",
        roof_pitch_deg=0.0,
        orientation_deg=180.0,
        openings=openings,
    )

    # Wall: stone + PUF insulation
    wall_assembly = MaterialAssembly(
        assembly_id="golden_wall",
        name="Stone + PUF Wall Assembly",
        category="wall",
        layers=[
            MaterialLayer(
                material_id="stone",
                name="Local Stone Masonry",
                thickness_m=0.30,
                conductivity_w_mk=1.50,
                density_kg_m3=2400.0,
                specific_heat_j_kgk=840.0,
            ),
            MaterialLayer(
                material_id="puf_insulation",
                name="PUF Insulation Board",
                thickness_m=0.10,
                conductivity_w_mk=0.025,
                density_kg_m3=35.0,
                specific_heat_j_kgk=1400.0,
            ),
        ],
    )

    # Roof: concrete + PUF insulation
    roof_assembly = MaterialAssembly(
        assembly_id="golden_roof",
        name="Concrete + PUF Roof Assembly",
        category="roof",
        layers=[
            MaterialLayer(
                material_id="concrete_deck",
                name="Reinforced Concrete Deck",
                thickness_m=0.15,
                conductivity_w_mk=1.40,
                density_kg_m3=2300.0,
                specific_heat_j_kgk=880.0,
            ),
            MaterialLayer(
                material_id="puf_insulation",
                name="PUF Roof Insulation",
                thickness_m=0.12,
                conductivity_w_mk=0.025,
                density_kg_m3=35.0,
                specific_heat_j_kgk=1400.0,
            ),
        ],
    )

    # Floor: concrete slab
    floor_assembly = MaterialAssembly(
        assembly_id="golden_floor",
        name="Ground Floor Slab",
        category="floor",
        layers=[
            MaterialLayer(
                material_id="concrete_slab",
                name="Concrete Ground Slab",
                thickness_m=0.15,
                conductivity_w_mk=1.40,
                density_kg_m3=2300.0,
                specific_heat_j_kgk=880.0,
            ),
        ],
    )

    # Triple low-E glazing
    glazing = STANDARD_GLAZING_PRESETS["triple_low_e"]

    # Thermal mass: Trombe wall
    thermal_mass_elements = [
        ThermalMassDefinition(
            id="trombe_south",
            name="South Trombe Wall (Stone)",
            material_id="stone",
            thickness_m=0.20,
            area_m2=4.0,
            density_kg_m3=2400.0,
            specific_heat_j_kgk=840.0,
            location="trombe_wall",
            provenance="user_defined",
        ),
    ]

    # Passive strategies
    passive_strategies = [
        ShelterPassiveStrategy(
            id="solar_collection",
            name="South Solar Collection",
            category="cold_region",
            climate_applicability=["cold", "extreme_cold"],
            parameters={"orientation": "south", "window_area_m2": 2.0, "shgc": 0.45},
            affected_openings=["win_south_primary"],
            affected_surfaces=["south_wall"],
            notes="Maximizes passive solar gains through south-facing triple-glazed aperture",
            assumptions="Northern hemisphere winter; minimal shading obstructions",
            provenance="user_defined",
        ),
        ShelterPassiveStrategy(
            id="thermal_mass_storage",
            name="Trombe Wall Thermal Mass Storage",
            category="cold_region",
            climate_applicability=["cold", "extreme_cold"],
            parameters={"mass_kg": 384.0, "capacity_j_k": 322560.0},
            affected_surfaces=["south_wall"],
            notes="Stone Trombe wall absorbs daytime solar energy and releases it during night",
            assumptions="Effective only with high solar availability and clear sky conditions",
            provenance="user_defined",
        ),
    ]

    design = ShelterDesign(
        design_id="THERMOCORE-LADAKH-GOLDEN",
        name="Golden Ladakh High-Altitude Permanent Shelter",
        requirements=requirements,
        geometry=geometry,
        wall_assembly=wall_assembly,
        roof_assembly=roof_assembly,
        floor_assembly=floor_assembly,
        glazing=glazing,
        openings=openings,
        thermal_mass_elements=thermal_mass_elements,
        passive_strategies=passive_strategies,
        version="2.0.0",
        created_at="2026-01-01T00:00:00+00:00",
        metadata={
            "wall_material": "stone",
            "wall_thickness_m": 0.30,
            "roof_thickness_m": 0.15,
            "shelter_model": "compact_shelter",
            "heat_per_person": 80.0,
            "ach": 0.4,
            "orientation": "south",
            "insulation_thickness_m": 0.10,
            "insulation_conductivity": 0.025,
            "roof_insulation_m": 0.12,
            "roof_conductivity": 1.40,
            "shelter_type": "Permanent",
        },
        provenance="user_defined",
    )

    return climate, design
