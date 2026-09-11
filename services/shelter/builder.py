"""
THERMOSHELTER AI — Shelter Design Builder & Archetype Factory (Member 2)
========================================================================
Assembles requirements, parametric geometry, multi-layer assemblies, fenestrations,
thermal mass, and passive systems into a unified, validated ShelterDesign digital twin.

Includes:
- Fluent ShelterDesignBuilder
- Hero demo preset: Leh/Ladakh Extreme Cold High-Performance Passive Shelter
- Hot-Dry & Hot-Humid regional benchmark presets
- Clean JSON file persistence (save/load)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from services.shelter.models import (
    GlazingDefinition,
    MaterialAssembly,
    MaterialLayer,
    OpeningDefinition,
    PassiveStrategy,
    ShelterDesign,
    ShelterGeometry,
    ShelterRequirements,
    ThermalMassDefinition,
    ZoneDefinition,
)
from services.shelter.geometry_engine import (
    create_compact_geometry,
    create_elongated_geometry,
    create_pitched_roof_geometry,
    create_rectangular_geometry,
    validate_geometry,
)
from services.shelter.envelope_engine import (
    create_glazing,
    create_material_assembly,
    create_material_layer,
    create_thermal_mass,
)
from services.shelter.passive_systems import (
    get_default_cold_region_strategies,
    get_default_hot_dry_strategies,
    get_default_hot_humid_strategies,
    create_passive_strategy,
)


class ShelterDesignBuildError(ValueError):
    """Raised when mandatory design components are missing or physically invalid."""
    pass


class ShelterDesignBuilder:
    """
    Fluent builder for constructing validated ShelterDesign digital twins.
    """

    def __init__(self, design_id: str, name: str) -> None:
        self.design_id = design_id
        self.name = name
        self.version = "1.0.0"
        self._requirements: Optional[ShelterRequirements] = None
        self._geometry: Optional[ShelterGeometry] = None
        self._wall_assembly: Optional[MaterialAssembly] = None
        self._roof_assembly: Optional[MaterialAssembly] = None
        self._floor_assembly: Optional[MaterialAssembly] = None
        self._door_assembly: Optional[MaterialAssembly] = None
        self._glazing: Optional[GlazingDefinition] = None
        self._openings: List[OpeningDefinition] = []
        self._zones: List[ZoneDefinition] = []
        self._thermal_mass_elements: List[ThermalMassDefinition] = []
        self._passive_strategies: List[PassiveStrategy] = []
        self._metadata: Dict[str, Any] = {}

    def set_requirements(self, requirements: ShelterRequirements) -> ShelterDesignBuilder:
        self._requirements = requirements
        return self

    def set_geometry(self, geometry: ShelterGeometry) -> ShelterDesignBuilder:
        self._geometry = geometry
        return self

    def set_wall_assembly(self, assembly: MaterialAssembly) -> ShelterDesignBuilder:
        self._wall_assembly = assembly
        return self

    def set_roof_assembly(self, assembly: MaterialAssembly) -> ShelterDesignBuilder:
        self._roof_assembly = assembly
        return self

    def set_floor_assembly(self, assembly: MaterialAssembly) -> ShelterDesignBuilder:
        self._floor_assembly = assembly
        return self

    def set_door_assembly(self, assembly: MaterialAssembly) -> ShelterDesignBuilder:
        self._door_assembly = assembly
        return self

    def set_glazing(self, glazing: GlazingDefinition) -> ShelterDesignBuilder:
        self._glazing = glazing
        return self

    def add_opening(self, opening: OpeningDefinition) -> ShelterDesignBuilder:
        self._openings.append(opening)
        return self

    def set_openings(self, openings: List[OpeningDefinition]) -> ShelterDesignBuilder:
        self._openings = list(openings)
        return self

    def add_zone(self, zone: ZoneDefinition) -> ShelterDesignBuilder:
        self._zones.append(zone)
        return self

    def set_zones(self, zones: List[ZoneDefinition]) -> ShelterDesignBuilder:
        self._zones = list(zones)
        return self

    def add_thermal_mass(self, thermal_mass: ThermalMassDefinition) -> ShelterDesignBuilder:
        self._thermal_mass_elements.append(thermal_mass)
        return self

    def set_thermal_mass_elements(self, elements: List[ThermalMassDefinition]) -> ShelterDesignBuilder:
        self._thermal_mass_elements = list(elements)
        return self

    def add_passive_strategy(self, strategy: PassiveStrategy) -> ShelterDesignBuilder:
        self._passive_strategies.append(strategy)
        return self

    def set_passive_strategies(self, strategies: List[PassiveStrategy]) -> ShelterDesignBuilder:
        self._passive_strategies = list(strategies)
        return self

    def set_metadata(self, metadata: Dict[str, Any]) -> ShelterDesignBuilder:
        self._metadata = dict(metadata)
        return self

    def build(self) -> ShelterDesign:
        """
        Validates all constraints and returns the complete ShelterDesign object.
        """
        if not self._requirements:
            raise ShelterDesignBuildError("ShelterRequirements must be specified.")
        if not self._geometry:
            raise ShelterDesignBuildError("ShelterGeometry must be specified.")
        if not self._wall_assembly:
            raise ShelterDesignBuildError("Wall MaterialAssembly must be specified.")
        if not self._roof_assembly:
            raise ShelterDesignBuildError("Roof MaterialAssembly must be specified.")
        if not self._floor_assembly:
            raise ShelterDesignBuildError("Floor MaterialAssembly must be specified.")
        if not self._glazing:
            raise ShelterDesignBuildError("GlazingDefinition must be specified.")

        # Sync openings and zones with geometry if they were added to builder
        if self._openings and not self._geometry.openings:
            self._geometry.openings = list(self._openings)
        elif self._geometry.openings and not self._openings:
            self._openings = list(self._geometry.openings)

        if self._zones and not self._geometry.zones:
            self._geometry.zones = list(self._zones)
        elif self._geometry.zones and not self._zones:
            self._zones = list(self._geometry.zones)

        validate_geometry(self._geometry)

        design = ShelterDesign(
            design_id=self.design_id,
            name=self.name,
            requirements=self._requirements,
            geometry=self._geometry,
            wall_assembly=self._wall_assembly,
            roof_assembly=self._roof_assembly,
            floor_assembly=self._floor_assembly,
            door_assembly=self._door_assembly,
            glazing=self._glazing,
            openings=self._openings,
            zones=self._zones,
            thermal_mass_elements=self._thermal_mass_elements,
            passive_strategies=self._passive_strategies,
            version=self.version,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=self._metadata,
        )

        return design


# =====================================================================
# PRESET FACTORIES
# =====================================================================

def build_leh_ladakh_design() -> ShelterDesign:
    """
    Constructs the canonical Hero design:
    - Location: Leh/Ladakh (High-Altitude Cold Desert)
    - Occupants: 4
    - Purpose: Permanent shelter / Guard & Field Post
    - Climate Strategy: Extreme Cold (Passive Solar Heating & High Retention)
    - Geometry: Compact rectangular (5.0m x 4.0m x 2.7m)
    - Envelope: Multilayer mud brick + polyurethane insulation + external timber rainscreen
    - Passive Systems: South aperture, thermal mass core, entry airlock, controlled low ACH
    """
    # 1. Requirements
    requirements = ShelterRequirements(
        occupants=4,
        shelter_purpose="permanent_passive_shelter",
        duration_days=None,  # Permanent
        permanence="permanent",
        mobility="permanent",
        priorities=["maximum_heat_retention", "thermal_comfort", "local_materials"],
        available_resources=["mud_brick", "local_stone", "poplar_willow_timber", "puf_boards"],
        energy_sources=["passive_solar", "biomass_backup"],
        constraints={"min_indoor_temp_c": 15.0, "design_outdoor_winter_temp_c": -20.0},
    )

    # 2. Openings & Zones
    south_window = OpeningDefinition(
        id="win_south_solar",
        name="South Solar Harvesting Window",
        opening_type="window",
        width_m=2.5,
        height_m=1.6,
        area_m2=4.0,
        facade="south",
        orientation_deg=180.0,
        is_operable=True,
        glazing_id="double_low_e_argon_16mm",
        shading_factor=0.95,
        overhang_depth_m=0.3,
        ventilation_role="inlet",
    )
    east_window = OpeningDefinition(
        id="win_east_daylight",
        name="East Morning Daylight Window",
        opening_type="window",
        width_m=1.0,
        height_m=1.0,
        area_m2=1.0,
        facade="east",
        orientation_deg=90.0,
        is_operable=True,
        glazing_id="double_low_e_argon_16mm",
        shading_factor=1.0,
        overhang_depth_m=0.2,
        ventilation_role="outlet",
    )
    airlock_outer_door = OpeningDefinition(
        id="door_airlock_outer",
        name="Airlock Outer Weather Door",
        opening_type="door",
        width_m=0.9,
        height_m=2.0,
        area_m2=1.8,
        facade="south",
        orientation_deg=180.0,
        is_operable=True,
        ventilation_role="none",
    )
    openings = [south_window, east_window, airlock_outer_door]

    living_zone = ZoneDefinition(
        id="zone_living",
        name="Main Heated Living Zone",
        zone_type="occupied",
        floor_area_m2=14.0,
        volume_m3=37.8,
        length_m=3.5,
        width_m=4.0,
        height_m=2.7,
        temperature_control_required=True,
        notes="Primary living and sleeping quarters coupled to solar aperture and thermal mass.",
    )
    solar_zone = ZoneDefinition(
        id="zone_sunspace",
        name="Direct Solar Gain Sun Zone",
        zone_type="solar",
        floor_area_m2=3.0,
        volume_m3=8.1,
        length_m=1.5,
        width_m=2.0,
        height_m=2.7,
        temperature_control_required=False,
        notes="South-facing direct solar gain area buffering interior.",
    )
    airlock_zone = ZoneDefinition(
        id="zone_airlock",
        name="Entry Airlock Vestibule",
        zone_type="airlock",
        floor_area_m2=2.5,
        volume_m3=6.75,
        length_m=1.5,
        width_m=1.67,
        height_m=2.7,
        temperature_control_required=False,
        notes="Dual-door buffer preventing cold air drafts upon entry.",
    )
    zones = [living_zone, solar_zone, airlock_zone]

    # 3. Geometry (Compact 5.0m x 4.0m x 2.7m, South Azimuth)
    geometry = create_compact_geometry(
        length_m=5.0,
        width_m=4.0,
        height_m=2.7,
        roof_type="flat",
        roof_pitch_deg=0.0,
        orientation_deg=180.0,
        openings=openings,
        zones=zones,
    )

    # 4. Multilayer Envelope Assemblies
    # Wall: Interior plaster (0.02m) -> Mud Brick structural core (0.25m) -> PUF Insulation (0.08m) -> Wood cladding (0.02m)
    wall_layers = [
        create_material_layer("mud_brick", thickness_m=0.02, name="Interior Earth Plaster", conductivity_w_mk=0.50),
        create_material_layer("mud_brick", thickness_m=0.25, name="Structural Mud Brick Core"),
        create_material_layer("polyurethane_foam", thickness_m=0.08, name="Rigid PUF Insulation"),
        create_material_layer("wood_timber_pine", thickness_m=0.02, name="Exterior Timber Protective Facing"),
    ]
    wall_assembly = create_material_assembly("wall_leh_composite", "Leh High-Performance Mud-PUF Wall", "wall", wall_layers)

    # Roof: Ceiling lining (0.02m wood) -> PUF Insulation (0.12m) -> Timber joists (0.10m) -> Waterproofing/Mud cap (0.05m)
    roof_layers = [
        create_material_layer("wood_timber_pine", thickness_m=0.02, name="Interior Ceiling Wood Planking"),
        create_material_layer("polyurethane_foam", thickness_m=0.12, name="Roof PUF Continuous Thermal Barrier"),
        create_material_layer("wood_timber_pine", thickness_m=0.10, name="Poplar Structural Roof Rafters"),
        create_material_layer("mud_brick", thickness_m=0.05, name="Traditional Compacted Earth Roof Cap"),
    ]
    roof_assembly = create_material_assembly("roof_leh_composite", "Leh Insulated Timber-Earth Roof", "roof", roof_layers)

    # Floor: Timber floorboard (0.03m) -> XPS Insulation (0.08m) -> Stone sub-base (0.20m) -> Ground
    floor_layers = [
        create_material_layer("wood_timber_pine", thickness_m=0.03, name="Interior Timber Floor Planks"),
        create_material_layer("xps_insulation", thickness_m=0.08, name="Sub-Floor XPS High-Density Insulation"),
        create_material_layer("stone_granite", thickness_m=0.20, name="Rubble Stone Capillary Bed"),
    ]
    floor_assembly = create_material_assembly("floor_leh_composite", "Leh Insulated Ground Floor", "floor", floor_layers)

    # Door: Heavy insulated timber airlock door
    door_layers = [
        create_material_layer("wood_timber_pine", thickness_m=0.02, name="Interior Door Face"),
        create_material_layer("polyurethane_foam", thickness_m=0.04, name="PUF Insulating Door Core"),
        create_material_layer("wood_timber_pine", thickness_m=0.02, name="Exterior Weatherproof Face"),
    ]
    door_assembly = create_material_assembly("door_leh_insulated", "Insulated Weatherproof Door", "door", door_layers)

    # 5. Glazing
    glazing = create_glazing("double_low_e_argon_16mm")

    # 6. Thermal Mass Elements
    # Trombe wall / internal heat bank (4.0m length, 1.2m height, 0.30m thick granite stone mass)
    internal_stone_mass = create_thermal_mass(
        id="mass_internal_stone_bank",
        name="Internal Granite Stone Heat Bank",
        material_id="stone_granite",
        thickness_m=0.30,
        area_m2=4.8,
        location="internal_wall",
    )
    mud_brick_wall_mass = create_thermal_mass(
        id="mass_mud_brick_core",
        name="Mud Brick Structural Thermal Storage",
        material_id="mud_brick",
        thickness_m=0.25,
        area_m2=12.0,
        location="core",
    )
    thermal_masses = [internal_stone_mass, mud_brick_wall_mass]

    # 7. Passive Strategies
    strategies = get_default_cold_region_strategies()

    builder = ShelterDesignBuilder(
        design_id="shelter_leh_ladakh_hero",
        name="ThermoShelter Leh/Ladakh High-Altitude Cold Passive Twin",
    )
    builder.set_requirements(requirements)
    builder.set_geometry(geometry)
    builder.set_wall_assembly(wall_assembly)
    builder.set_roof_assembly(roof_assembly)
    builder.set_floor_assembly(floor_assembly)
    builder.set_door_assembly(door_assembly)
    builder.set_glazing(glazing)
    builder.set_openings(openings)
    builder.set_zones(zones)
    builder.set_thermal_mass_elements(thermal_masses)
    builder.set_passive_strategies(strategies)
    builder.set_metadata({
        "location": "Leh, Ladakh, India",
        "elevation_m": 3500,
        "climate_classification": "BWk (Cold Arid High-Altitude)",
        "target_season": "Winter extreme heating",
    })

    return builder.build()


def build_hot_dry_design() -> ShelterDesign:
    """
    Constructs a benchmark hot-dry passive shelter (e.g. Jaisalmer/Thar Desert):
    - Massive rammed earth envelope
    - Night-time cool-air flushing and thermal-mass pre-cooling
    - Deep external solar shading overhangs
    """
    requirements = ShelterRequirements(
        occupants=4,
        shelter_purpose="field_station",
        permanence="permanent",
        mobility="permanent",
        priorities=["cooling_reduction", "thermal_inertia", "local_materials"],
        available_resources=["rammed_earth", "sandstone", "lime_plaster"],
        energy_sources=["passive_solar", "night_sky_cooling"],
    )

    openings = [
        OpeningDefinition(
            id="win_north_inlet",
            name="North Night Flushing Inlet",
            opening_type="window",
            width_m=1.8,
            height_m=1.2,
            area_m2=2.16,
            facade="north",
            orientation_deg=0.0,
            is_operable=True,
            glazing_id="double_clear_air_12mm",
            shading_factor=0.4,
            overhang_depth_m=0.8,
            ventilation_role="inlet",
        ),
        OpeningDefinition(
            id="win_south_shaded",
            name="South Shaded Aperture",
            opening_type="window",
            width_m=1.2,
            height_m=1.0,
            area_m2=1.2,
            facade="south",
            orientation_deg=180.0,
            is_operable=True,
            glazing_id="double_clear_air_12mm",
            shading_factor=0.3,
            overhang_depth_m=1.0,
            ventilation_role="outlet",
        ),
    ]

    geometry = create_rectangular_geometry(
        length_m=6.0,
        width_m=3.5,
        height_m=3.0,
        roof_type="flat",
        orientation_deg=180.0,
        openings=openings,
    )

    # Thick massive rammed earth walls
    wall_layers = [
        create_material_layer("mud_brick", thickness_m=0.02, name="Interior Lime Plaster"),
        create_material_layer("rammed_earth", thickness_m=0.35, name="Heavy Rammed Earth Core"),
        create_material_layer("mud_brick", thickness_m=0.02, name="Exterior Reflective Lime Wash"),
    ]
    wall_assembly = create_material_assembly("wall_hot_dry_earth", "Massive Rammed Earth Wall", "wall", wall_layers)

    roof_layers = [
        create_material_layer("wood_timber_pine", thickness_m=0.03, name="Wood Decking"),
        create_material_layer("eps_insulation", thickness_m=0.08, name="EPS Roof Insulation"),
        create_material_layer("concrete_standard", thickness_m=0.10, name="Reflective Concrete Roof Slab"),
    ]
    roof_assembly = create_material_assembly("roof_hot_dry_slab", "Insulated Concrete Roof Slab", "roof", roof_layers)

    floor_layers = [
        create_material_layer("stone_granite", thickness_m=0.05, name="Sandstone Floor Tiles"),
        create_material_layer("concrete_standard", thickness_m=0.15, name="Earth-Coupled Thermal Slab"),
    ]
    floor_assembly = create_material_assembly("floor_hot_dry_slab", "Earth-Coupled Cooling Floor", "floor", floor_layers)

    glazing = create_glazing("double_clear_air_12mm")
    floor_mass = create_thermal_mass("mass_floor_slab", "Ground-Coupled Floor Mass", "concrete_standard", 0.15, 21.0, location="floor_slab")

    strategies = get_default_hot_dry_strategies()

    builder = ShelterDesignBuilder("shelter_hot_dry_benchmark", "ThermoShelter Hot-Dry Desert Passive Twin")
    builder.set_requirements(requirements)
    builder.set_geometry(geometry)
    builder.set_wall_assembly(wall_assembly)
    builder.set_roof_assembly(roof_assembly)
    builder.set_floor_assembly(floor_assembly)
    builder.set_glazing(glazing)
    builder.set_openings(openings)
    builder.set_thermal_mass_elements([floor_mass])
    builder.set_passive_strategies(strategies)
    builder.set_metadata({"location": "Jaisalmer, Rajasthan, India", "climate_type": "Hot-Dry Desert"})

    return builder.build()


# =====================================================================
# PERSISTENCE HELPERS
# =====================================================================

def save_shelter_design_to_file(design: ShelterDesign, file_path: str) -> None:
    """Saves a ShelterDesign instance as a formatted JSON document."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(design.to_json(indent=2))


def load_shelter_design_from_file(file_path: str) -> ShelterDesign:
    """Loads and reconstructs a ShelterDesign instance from a JSON document."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return ShelterDesign.from_json(content)
