"""
THERMOSHELTER AI — Area-Specific Passive Shelter Engineering Package (Member 2)
================================================================================
Public API exposing:
- Parametric Shelter Geometry Engine
- Material & Multilayer Envelope Engine
- Passive Systems Engine
- Canonical ShelterDesign digital twin builder & JSON serialization
"""

from typing import Optional


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
    GeometryValidationError,
    calculate_geometry_metrics,
    create_compact_geometry,
    create_custom_geometry,
    create_elongated_geometry,
    create_pitched_roof_geometry,
    create_rectangular_geometry,
    normalize_azimuth,
    validate_geometry,
)

from services.shelter.envelope_engine import (
    calculate_assembly_metrics,
    calculate_thermal_capacity,
    create_glazing,
    create_material_assembly,
    create_material_layer,
    create_thermal_mass,
)

from services.shelter.passive_systems import (
    PassiveStrategyValidationError,
    create_passive_strategy,
    get_default_cold_region_strategies,
    get_default_hot_dry_strategies,
    get_default_hot_humid_strategies,
    get_strategy_catalog,
    validate_passive_strategy,
)

from services.shelter.builder import (
    ShelterDesignBuildError,
    ShelterDesignBuilder,
    build_hot_dry_design,
    build_leh_ladakh_design,
    load_shelter_design_from_file,
    save_shelter_design_to_file,
)


# Convenience API aliases matching Section 22 specification
def create_geometry(
    length_m: float,
    width_m: float,
    height_m: float,
    geometry_type: str = "rectangular",
    roof_type: str = "flat",
    roof_pitch_deg: float = 0.0,
    orientation_deg: float = 180.0,
    **kwargs,
) -> ShelterGeometry:
    """Convenience factory for parametric geometry generation."""
    gtype = geometry_type.lower()
    if gtype == "compact":
        return create_compact_geometry(
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            roof_type=roof_type,
            roof_pitch_deg=roof_pitch_deg,
            orientation_deg=orientation_deg,
            **kwargs,
        )
    elif gtype == "elongated":
        return create_elongated_geometry(
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            roof_type=roof_type,
            roof_pitch_deg=roof_pitch_deg,
            orientation_deg=orientation_deg,
            **kwargs,
        )
    elif gtype in {"pitched", "gable"} or roof_pitch_deg > 0.0:
        return create_pitched_roof_geometry(
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            roof_pitch_deg=roof_pitch_deg,
            orientation_deg=orientation_deg,
            **kwargs,
        )
    elif gtype == "custom":
        return create_custom_geometry(
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            roof_type=roof_type,
            roof_pitch_deg=roof_pitch_deg,
            orientation_deg=orientation_deg,
            **kwargs,
        )
    else:
        return create_rectangular_geometry(
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            roof_type=roof_type,
            roof_pitch_deg=roof_pitch_deg,
            orientation_deg=orientation_deg,
            **kwargs,
        )


def calculate_assembly_r_value(assembly: MaterialAssembly) -> float:
    """Returns the total thermal resistance (R_total) of an assembly."""
    return assembly.r_total


def calculate_assembly_u_value(assembly: MaterialAssembly) -> float:
    """Returns the overall thermal transmittance (U-value) of an assembly."""
    return assembly.u_value


def create_opening(
    id: str,
    width_m: float,
    height_m: float,
    opening_type: str = "window",
    facade: str = "south",
    orientation_deg: float = 180.0,
    name: Optional[str] = None,
    is_operable: bool = False,
    glazing_id: Optional[str] = None,
    shading_factor: float = 1.0,
    overhang_depth_m: float = 0.0,
    ventilation_role: str = "none",
) -> OpeningDefinition:
    """Convenience factory for fenestration apertures."""
    return OpeningDefinition(
        id=id,
        name=name or id,
        opening_type=opening_type,
        width_m=width_m,
        height_m=height_m,
        area_m2=round(width_m * height_m, 4),
        facade=facade,
        orientation_deg=orientation_deg,
        is_operable=is_operable,
        glazing_id=glazing_id,
        shading_factor=shading_factor,
        overhang_depth_m=overhang_depth_m,
        ventilation_role=ventilation_role,
    )


def build_shelter_design(
    design_id: str,
    name: str,
    requirements: ShelterRequirements,
    geometry: ShelterGeometry,
    wall_assembly: MaterialAssembly,
    roof_assembly: MaterialAssembly,
    floor_assembly: MaterialAssembly,
    glazing: GlazingDefinition,
    door_assembly: Optional[MaterialAssembly] = None,
    openings: Optional[list] = None,
    zones: Optional[list] = None,
    thermal_mass_elements: Optional[list] = None,
    passive_strategies: Optional[list] = None,
    metadata: Optional[dict] = None,
) -> ShelterDesign:
    """Direct factory constructing a validated ShelterDesign."""
    builder = ShelterDesignBuilder(design_id=design_id, name=name)
    builder.set_requirements(requirements)
    builder.set_geometry(geometry)
    builder.set_wall_assembly(wall_assembly)
    builder.set_roof_assembly(roof_assembly)
    builder.set_floor_assembly(floor_assembly)
    builder.set_glazing(glazing)
    if door_assembly:
        builder.set_door_assembly(door_assembly)
    if openings:
        builder.set_openings(openings)
    if zones:
        builder.set_zones(zones)
    if thermal_mass_elements:
        builder.set_thermal_mass_elements(thermal_mass_elements)
    if passive_strategies:
        builder.set_passive_strategies(passive_strategies)
    if metadata:
        builder.set_metadata(metadata)
    return builder.build()


__all__ = [
    # Canonical Domain Models
    "ShelterRequirements",
    "ShelterGeometry",
    "OpeningDefinition",
    "ZoneDefinition",
    "MaterialLayer",
    "MaterialAssembly",
    "ThermalMassDefinition",
    "GlazingDefinition",
    "PassiveStrategy",
    "ShelterDesign",
    # Geometry API
    "create_geometry",
    "create_rectangular_geometry",
    "create_compact_geometry",
    "create_elongated_geometry",
    "create_pitched_roof_geometry",
    "create_custom_geometry",
    "validate_geometry",
    "calculate_geometry_metrics",
    "GeometryValidationError",
    "normalize_azimuth",
    # Envelope API
    "create_material_layer",
    "create_material_assembly",
    "calculate_assembly_metrics",
    "calculate_assembly_r_value",
    "calculate_assembly_u_value",
    "calculate_thermal_capacity",
    "create_thermal_mass",
    "create_glazing",
    # Fenestration API
    "create_opening",
    # Passive Systems API
    "create_passive_strategy",
    "validate_passive_strategy",
    "get_strategy_catalog",
    "get_default_cold_region_strategies",
    "get_default_hot_dry_strategies",
    "get_default_hot_humid_strategies",
    "PassiveStrategyValidationError",
    # Builder & Persistence
    "ShelterDesignBuilder",
    "ShelterDesignBuildError",
    "build_shelter_design",
    "build_leh_ladakh_design",
    "build_hot_dry_design",
    "save_shelter_design_to_file",
    "load_shelter_design_from_file",
]
