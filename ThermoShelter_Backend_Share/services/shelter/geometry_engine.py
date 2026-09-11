"""
THERMOSHELTER AI — Parametric Shelter Geometry Engine (Member 2)
================================================================
Comprehensive parametric generation, dimensional validation, multi-zone
partitioning, fenestration placement, and boundary surface-to-volume metrics.

Supports:
- Rectangular baseline
- Compact (minimum surface area for cold climates)
- Elongated (solar capture & cross-ventilation)
- Pitched roof (gabled/shed with attic volume & ridge height)
- Flat roof
- Custom programmatic dimensions
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import services.geometry as legacy_geom
from services.shelter.models import OpeningDefinition, ShelterGeometry, ZoneDefinition


class GeometryValidationError(ValueError):
    """Raised when geometric or architectural constraints are violated."""
    pass


# Orientation constants
NORTH_AZIMUTH: float = 0.0
EAST_AZIMUTH: float = 90.0
SOUTH_AZIMUTH: float = 180.0
WEST_AZIMUTH: float = 270.0


def normalize_azimuth(azimuth_deg: float) -> float:
    """
    Normalizes an orientation azimuth to [0.0, 360.0).
    0° = North, 90° = East, 180° = South, 270° = West.
    """
    az = float(azimuth_deg) % 360.0
    if az < 0.0:
        az += 360.0
    return az


def calculate_geometry_metrics(
    length_m: float,
    width_m: float,
    height_m: float,
    roof_type: str = "flat",
    roof_pitch_deg: float = 0.0,
    openings: Optional[List[OpeningDefinition]] = None,
    gable_on: str = "east_west",  # "east_west" or "north_south"
) -> Dict[str, float]:
    """
    Computes rigorous surface areas, enclosed volume, envelope boundary,
    and surface-to-volume ratio for rectangular/pitched shelters.

    Parameters:
        length_m: Shelter length in meters (along East-West by default).
        width_m: Shelter width in meters (along North-South by default).
        height_m: Eave or ceiling height in meters.
        roof_type: "flat", "pitched", "gable", "shed".
        roof_pitch_deg: Roof slope in degrees (0 for flat).
        openings: List of openings to calculate net opaque wall areas.
        gable_on: Facade pair carrying triangular gables ("east_west" or "north_south").

    Returns:
        Dict of computed quantities in SI units.
    """
    if length_m <= 0.0 or width_m <= 0.0 or height_m <= 0.0:
        raise GeometryValidationError(
            f"All shelter dimensions must be strictly positive (>0), got "
            f"L={length_m}, W={width_m}, H={height_m}"
        )
    if not (0.0 <= roof_pitch_deg < 90.0):
        raise GeometryValidationError(
            f"Roof pitch angle must be within [0, 90) degrees, got {roof_pitch_deg}"
        )

    floor_area = float(length_m * width_m)
    openings_list = openings or []

    is_pitched = roof_type.lower() in {"pitched", "gable", "shed"} and roof_pitch_deg > 0.0

    if is_pitched:
        rad = math.radians(roof_pitch_deg)
        if gable_on == "east_west":
            span = width_m
            length_along = length_m
        else:
            span = length_m
            length_along = width_m

        ridge_height = (span / 2.0) * math.tan(rad)
        roof_area = (length_m * width_m) / math.cos(rad)
        gable_area_each = 0.5 * span * ridge_height
        total_gable_area = 2.0 * gable_area_each
        attic_volume = 0.5 * span * ridge_height * length_along
        volume = (length_m * width_m * height_m) + attic_volume
    else:
        ridge_height = 0.0
        roof_area = floor_area
        total_gable_area = 0.0
        volume = length_m * width_m * height_m

    base_perimeter_wall = 2.0 * (length_m + width_m) * height_m
    gross_wall_area = base_perimeter_wall + total_gable_area

    # Facade gross areas (assuming length is East-West, width is North-South)
    # North & South facades have length_m width; East & West have width_m width.
    north_gross = length_m * height_m
    south_gross = length_m * height_m
    east_gross = width_m * height_m
    west_gross = width_m * height_m

    if is_pitched:
        if gable_on == "east_west":
            east_gross += total_gable_area / 2.0
            west_gross += total_gable_area / 2.0
        else:
            north_gross += total_gable_area / 2.0
            south_gross += total_gable_area / 2.0

    # Total openings area and validation
    total_window_area = sum(o.area_m2 for o in openings_list if o.opening_type.lower() == "window")
    total_door_area = sum(o.area_m2 for o in openings_list if o.opening_type.lower() == "door")
    total_opening_area = sum(o.area_m2 for o in openings_list)

    if total_opening_area > gross_wall_area:
        raise GeometryValidationError(
            f"Total opening area ({total_opening_area:.2f} m²) exceeds gross wall area "
            f"({gross_wall_area:.2f} m²)."
        )

    net_wall_area = gross_wall_area - total_opening_area
    total_envelope_area = floor_area + roof_area + gross_wall_area
    sv_ratio = total_envelope_area / volume if volume > 0 else 0.0
    wwr = total_window_area / gross_wall_area if gross_wall_area > 0 else 0.0

    return {
        "floor_area_m2": round(floor_area, 4),
        "volume_m3": round(volume, 4),
        "gross_wall_area_m2": round(gross_wall_area, 4),
        "net_wall_area_m2": round(net_wall_area, 4),
        "roof_area_m2": round(roof_area, 4),
        "ridge_height_m": round(ridge_height, 4),
        "total_envelope_area_m2": round(total_envelope_area, 4),
        "surface_to_volume_ratio": round(sv_ratio, 4),
        "window_to_wall_ratio": round(wwr, 4),
        "north_wall_area_m2": round(north_gross, 4),
        "south_wall_area_m2": round(south_gross, 4),
        "east_wall_area_m2": round(east_gross, 4),
        "west_wall_area_m2": round(west_gross, 4),
    }


def validate_geometry(geometry: ShelterGeometry) -> None:
    """
    Enforces strict physical, architectural, and geometric validity.

    Raises:
        GeometryValidationError: If any physical constraint is violated.
    """
    if geometry.length_m <= 0.0:
        raise GeometryValidationError(f"Length must be strictly positive, got {geometry.length_m} m")
    if geometry.width_m <= 0.0:
        raise GeometryValidationError(f"Width must be strictly positive, got {geometry.width_m} m")
    if geometry.height_m <= 0.0:
        raise GeometryValidationError(f"Height must be strictly positive, got {geometry.height_m} m")
    if not (0.0 <= geometry.orientation_deg <= 360.0):
        raise GeometryValidationError(
            f"Orientation azimuth must be in range [0, 360] degrees, got {geometry.orientation_deg}"
        )
    if not (0.0 <= geometry.roof_pitch_deg < 90.0):
        raise GeometryValidationError(
            f"Roof pitch must be >= 0 and < 90 degrees, got {geometry.roof_pitch_deg}"
        )

    # Validate individual openings
    facade_openings: Dict[str, float] = {"north": 0.0, "south": 0.0, "east": 0.0, "west": 0.0, "roof": 0.0}
    for op in geometry.openings:
        if op.width_m <= 0.0 or op.height_m <= 0.0:
            raise GeometryValidationError(
                f"Opening '{op.id}' has non-positive dimensions ({op.width_m}x{op.height_m} m)"
            )
        if op.area_m2 <= 0.0:
            raise GeometryValidationError(
                f"Opening '{op.id}' has non-positive area ({op.area_m2} m²)"
            )
        facade_key = op.facade.lower()
        if facade_key in facade_openings:
            facade_openings[facade_key] += op.area_m2

    # Verify openings do not exceed respective facade areas
    if geometry.facade_wall_areas:
        for facade, op_area in facade_openings.items():
            if facade == "roof":
                if op_area > geometry.roof_area_m2:
                    raise GeometryValidationError(
                        f"Roof openings ({op_area} m²) exceed roof area ({geometry.roof_area_m2} m²)"
                    )
            elif facade in geometry.facade_wall_areas:
                wall_limit = geometry.facade_wall_areas[facade]
                if op_area > wall_limit:
                    raise GeometryValidationError(
                        f"{facade.title()} facade openings ({op_area:.2f} m²) exceed available "
                        f"wall area ({wall_limit:.2f} m²)"
                    )

    # Validate net wall area
    total_opening_area = sum(op.area_m2 for op in geometry.openings)
    if total_opening_area > geometry.gross_wall_area_m2:
        raise GeometryValidationError(
            f"Total openings ({total_opening_area:.2f} m²) exceed gross wall area "
            f"({geometry.gross_wall_area_m2:.2f} m²)"
        )

    # Validate zones
    if geometry.zones:
        total_zone_area = sum(z.floor_area_m2 for z in geometry.zones)
        if total_zone_area > geometry.floor_area_m2 * 1.05:  # Allow 5% tolerance for internal partition overlap
            raise GeometryValidationError(
                f"Sum of internal zone floor areas ({total_zone_area:.2f} m²) exceeds "
                f"shelter net floor area ({geometry.floor_area_m2:.2f} m²)"
            )


def create_rectangular_geometry(
    length_m: float,
    width_m: float,
    height_m: float,
    roof_type: str = "flat",
    roof_pitch_deg: float = 0.0,
    orientation_deg: float = SOUTH_AZIMUTH,
    openings: Optional[List[OpeningDefinition]] = None,
    zones: Optional[List[ZoneDefinition]] = None,
) -> ShelterGeometry:
    """
    Builds a standard rectangular shelter geometry with derived metrics and validation.
    """
    metrics = calculate_geometry_metrics(
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        roof_type=roof_type,
        roof_pitch_deg=roof_pitch_deg,
        openings=openings,
    )

    facade_areas = {
        "north": metrics["north_wall_area_m2"],
        "south": metrics["south_wall_area_m2"],
        "east": metrics["east_wall_area_m2"],
        "west": metrics["west_wall_area_m2"],
    }

    geom = ShelterGeometry(
        geometry_type="rectangular",
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        roof_type=roof_type,
        roof_pitch_deg=roof_pitch_deg,
        orientation_deg=normalize_azimuth(orientation_deg),
        floor_area_m2=metrics["floor_area_m2"],
        volume_m3=metrics["volume_m3"],
        gross_wall_area_m2=metrics["gross_wall_area_m2"],
        net_wall_area_m2=metrics["net_wall_area_m2"],
        facade_wall_areas=facade_areas,
        roof_area_m2=metrics["roof_area_m2"],
        total_envelope_area_m2=metrics["total_envelope_area_m2"],
        surface_to_volume_ratio=metrics["surface_to_volume_ratio"],
        window_to_wall_ratio=metrics["window_to_wall_ratio"],
        ridge_height_m=metrics["ridge_height_m"],
        openings=openings or [],
        zones=zones or [],
    )

    validate_geometry(geom)
    return geom


def create_compact_geometry(
    floor_area_m2: Optional[float] = None,
    length_m: Optional[float] = None,
    width_m: Optional[float] = None,
    height_m: float = 2.7,
    roof_type: str = "flat",
    roof_pitch_deg: float = 0.0,
    orientation_deg: float = SOUTH_AZIMUTH,
    openings: Optional[List[OpeningDefinition]] = None,
    zones: Optional[List[ZoneDefinition]] = None,
) -> ShelterGeometry:
    """
    Creates a compact (near-square 1:1 aspect ratio) shelter designed to minimize
    exposed surface-to-volume ratio for cold climates (e.g. Leh/Ladakh).
    """
    if floor_area_m2 is not None and floor_area_m2 > 0:
        side = math.sqrt(floor_area_m2)
        l = round(side, 3)
        w = round(side, 3)
    elif length_m is not None and width_m is not None:
        l = length_m
        w = width_m
    else:
        # Standard default compact 16 m² cold shelter
        l = 4.0
        w = 4.0

    geom = create_rectangular_geometry(
        length_m=l,
        width_m=w,
        height_m=height_m,
        roof_type=roof_type,
        roof_pitch_deg=roof_pitch_deg,
        orientation_deg=orientation_deg,
        openings=openings,
        zones=zones,
    )
    geom.geometry_type = "compact"
    return geom


def create_elongated_geometry(
    floor_area_m2: Optional[float] = None,
    length_m: Optional[float] = None,
    width_m: Optional[float] = None,
    height_m: float = 2.7,
    aspect_ratio: float = 2.2,  # Length / Width ratio
    roof_type: str = "flat",
    roof_pitch_deg: float = 0.0,
    orientation_deg: float = SOUTH_AZIMUTH,
    openings: Optional[List[OpeningDefinition]] = None,
    zones: Optional[List[ZoneDefinition]] = None,
) -> ShelterGeometry:
    """
    Creates an elongated shelter with a high aspect ratio (Length:Width ~ 2:1 or higher)
    aligned along the East-West axis to maximize south solar exposure or facilitate
    cross-ventilation in hot climates.
    """
    if floor_area_m2 is not None and floor_area_m2 > 0:
        if aspect_ratio <= 0.0:
            raise GeometryValidationError(f"Aspect ratio must be > 0, got {aspect_ratio}")
        w = math.sqrt(floor_area_m2 / aspect_ratio)
        l = w * aspect_ratio
        l = round(l, 3)
        w = round(w, 3)
    elif length_m is not None and width_m is not None:
        l = length_m
        w = width_m
    else:
        # Default elongated 24 m² shelter (6.0m x 2.7m)
        l = 6.6
        w = 3.0

    geom = create_rectangular_geometry(
        length_m=l,
        width_m=w,
        height_m=height_m,
        roof_type=roof_type,
        roof_pitch_deg=roof_pitch_deg,
        orientation_deg=orientation_deg,
        openings=openings,
        zones=zones,
    )
    geom.geometry_type = "elongated"
    return geom


def create_pitched_roof_geometry(
    length_m: float,
    width_m: float,
    height_m: float,
    roof_pitch_deg: float = 30.0,
    orientation_deg: float = SOUTH_AZIMUTH,
    openings: Optional[List[OpeningDefinition]] = None,
    zones: Optional[List[ZoneDefinition]] = None,
) -> ShelterGeometry:
    """
    Creates a gabled pitched roof shelter with explicitly modeled attic volume,
    gable wall areas, and ridge height.
    """
    geom = create_rectangular_geometry(
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        roof_type="pitched",
        roof_pitch_deg=roof_pitch_deg,
        orientation_deg=orientation_deg,
        openings=openings,
        zones=zones,
    )
    return geom


def create_custom_geometry(
    length_m: float,
    width_m: float,
    height_m: float,
    roof_type: str = "flat",
    roof_pitch_deg: float = 0.0,
    orientation_deg: float = SOUTH_AZIMUTH,
    openings: Optional[List[OpeningDefinition]] = None,
    zones: Optional[List[ZoneDefinition]] = None,
) -> ShelterGeometry:
    """
    Programmatic creator for arbitrary user-specified shelter geometries.
    """
    geom = create_rectangular_geometry(
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        roof_type=roof_type,
        roof_pitch_deg=roof_pitch_deg,
        orientation_deg=orientation_deg,
        openings=openings,
        zones=zones,
    )
    geom.geometry_type = "custom"
    return geom
