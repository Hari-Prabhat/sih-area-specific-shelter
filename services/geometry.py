"""
THERMOSHELTER AI - Geometric Calculation Formulas
==================================================
Deterministic, pure mathematical functions for shelter surface areas,
internal volumes, net wall areas, and envelope boundary metrics.
"""

from typing import Optional

def calculate_floor_area(length: float, width: float) -> float:
    """
    Calculates the interior floor area of a rectangular shelter.

    Formula:
        A_floor = length * width

    Parameters:
        length (float): Length of the shelter in meters (m). Must be > 0.
        width (float): Width of the shelter in meters (m). Must be > 0.

    Returns:
        float: Net floor area in square meters (m²).

    Assumptions:
        Physically rigorous for rectangular plan geometries.

    Raises:
        ValueError: If length <= 0 or width <= 0.
    """
    if length <= 0.0:
        raise ValueError(f"Length must be strictly positive (> 0), got {length}")
    if width <= 0.0:
        raise ValueError(f"Width must be strictly positive (> 0), got {width}")
    return float(length * width)


def calculate_volume(length: float, width: float, height: float) -> float:
    """
    Calculates the internal enclosed air volume of a rectangular shelter.

    Formula:
        V = length * width * height

    Parameters:
        length (float): Length of the shelter in meters (m). Must be > 0.
        width (float): Width of the shelter in meters (m). Must be > 0.
        height (float): Mean internal ceiling height in meters (m). Must be > 0.

    Returns:
        float: Total enclosed air volume in cubic meters (m³).

    Assumptions:
        Assumes flat ceiling or mean effective volume for low-slope roof forms.

    Raises:
        ValueError: If length, width, or height is <= 0.
    """
    if length <= 0.0:
        raise ValueError(f"Length must be strictly positive (> 0), got {length}")
    if width <= 0.0:
        raise ValueError(f"Width must be strictly positive (> 0), got {width}")
    if height <= 0.0:
        raise ValueError(f"Height must be strictly positive (> 0), got {height}")
    return float(length * width * height)


def calculate_wall_area(length: float, width: float, height: float) -> float:
    """
    Calculates the gross total vertical perimeter wall area for a 4-walled rectangular shelter.

    Formula:
        A_wall = 2 * (length + width) * height

    Parameters:
        length (float): Length of the shelter in meters (m). Must be > 0.
        width (float): Width of the shelter in meters (m). Must be > 0.
        height (float): Eave/wall height in meters (m). Must be > 0.

    Returns:
        float: Gross exterior wall surface area in square meters (m²).

    Assumptions:
        Uniform wall height across all four perimeter facades.

    Raises:
        ValueError: If length, width, or height is <= 0.
    """
    if length <= 0.0:
        raise ValueError(f"Length must be strictly positive (> 0), got {length}")
    if width <= 0.0:
        raise ValueError(f"Width must be strictly positive (> 0), got {width}")
    if height <= 0.0:
        raise ValueError(f"Height must be strictly positive (> 0), got {height}")
    return float(2.0 * (length + width) * height)


def calculate_roof_area_flat(length: float, width: float) -> float:
    """
    Calculates the surface area of a flat horizontal roof.

    Formula:
        A_roof = length * width

    Parameters:
        length (float): Roof length in meters (m). Must be > 0.
        width (float): Roof width in meters (m). Must be > 0.

    Returns:
        float: Roof surface area in square meters (m²).

    Raises:
        ValueError: If length <= 0 or width <= 0.
    """
    if length <= 0.0:
        raise ValueError(f"Length must be strictly positive (> 0), got {length}")
    if width <= 0.0:
        raise ValueError(f"Width must be strictly positive (> 0), got {width}")
    return float(length * width)


def calculate_total_envelope_area(
    length: float,
    width: float,
    height: float,
    roof_area: Optional[float] = None,
    floor_area: Optional[float] = None
) -> float:
    """
    Calculates total exterior envelope surface area (floor + roof + gross walls).

    Formula:
        A_total = A_floor + A_roof + A_gross_wall

    Parameters:
        length (float): Length in meters (m). Must be > 0.
        width (float): Width in meters (m). Must be > 0.
        height (float): Wall height in meters (m). Must be > 0.
        roof_area (Optional[float]): Custom roof area (e.g. pitched/sloped). Defaults to length * width.
        floor_area (Optional[float]): Custom floor area. Defaults to length * width.

    Returns:
        float: Total envelope surface area in square meters (m²).

    Raises:
        ValueError: If dimensions or custom areas are invalid.
    """
    w_area = calculate_wall_area(length, width, height)
    f_area = floor_area if floor_area is not None else calculate_floor_area(length, width)
    r_area = roof_area if roof_area is not None else calculate_roof_area_flat(length, width)

    if f_area <= 0.0:
        raise ValueError(f"Floor area must be strictly positive, got {f_area}")
    if r_area <= 0.0:
        raise ValueError(f"Roof area must be strictly positive, got {r_area}")

    return float(w_area + f_area + r_area)


def calculate_net_wall_area(
    gross_wall_area: float,
    window_area: float,
    door_area: float = 0.0
) -> float:
    """
    Calculates net opaque wall area by subtracting fenestrations and door openings.

    Formula:
        A_net = gross_wall_area - window_area - door_area

    Parameters:
        gross_wall_area (float): Total gross wall area in square meters (m²). Must be >= 0.
        window_area (float): Total window opening area in square meters (m²). Must be >= 0.
        door_area (float): Total door opening area in square meters (m²). Must be >= 0.

    Returns:
        float: Net opaque wall area in square meters (m²).

    Raises:
        ValueError: If any input is negative, or if openings exceed gross wall area.
    """
    if gross_wall_area < 0.0:
        raise ValueError(f"Gross wall area cannot be negative, got {gross_wall_area}")
    if window_area < 0.0:
        raise ValueError(f"Window area cannot be negative, got {window_area}")
    if door_area < 0.0:
        raise ValueError(f"Door area cannot be negative, got {door_area}")

    openings = window_area + door_area
    if openings > gross_wall_area:
        raise ValueError(
            f"Total openings area ({openings} m²) exceeds gross wall area ({gross_wall_area} m²)"
        )

    return float(gross_wall_area - openings)


def calculate_pitched_roof_geometry(
    length: float,
    width: float,
    height: float,
    pitch_angle_deg: float = 30.0
) -> dict:
    """
    Calculates detailed roof area, gable wall area, and volume for a pitched/gabled shelter.

    Parameters:
        length: Shelter length in meters.
        width: Shelter width in meters (gable span).
        height: Eave height in meters.
        pitch_angle_deg: Roof slope angle in degrees (default 30.0°).

    Returns:
        Dict with "roof_area", "gable_area", "gross_wall_area", "volume", "ridge_height", "total_height".
    """
    import math
    if length <= 0.0 or width <= 0.0 or height <= 0.0:
        raise ValueError("Dimensions must be strictly positive.")

    rad = math.radians(pitch_angle_deg)
    ridge_height = (width / 2.0) * math.tan(rad)
    roof_area = (length * width) / math.cos(rad)
    gable_area = 2.0 * (0.5 * width * ridge_height)
    gross_wall = calculate_wall_area(length, width, height) + gable_area
    volume = calculate_volume(length, width, height) + (0.5 * width * ridge_height * length)

    return {
        "roof_area": round(float(roof_area), 3),
        "gable_area": round(float(gable_area), 3),
        "gross_wall_area": round(float(gross_wall), 3),
        "volume": round(float(volume), 3),
        "ridge_height": round(float(ridge_height), 3),
        "total_height": round(float(height + ridge_height), 3),
    }



# =====================================================================
# CANONICAL MULTI-SHAPE GEOMETRY (product-hardening pass)
# =====================================================================
# Shape-specific derived metrics for the four shelter forms exposed by the
# Design stage. Every formula is closed-form analytic; no values here are
# engineering assumptions beyond the documented mathematical model. The
# thermal engine consumes these derived areas/volumes so a Dome is simulated
# AS a dome — never silently converted back to a rectangular box.

import math as _math


def calculate_shape_geometry(
    shape: str,
    length: float,
    width: float,
    height: float,
) -> dict:
    """
    Canonical shape-aware geometry for all four supported shelter forms.

    Mapping convention (keeps the canonical L/W/H contract intact):
      - rectangular: L x W footprint, H wall height (existing behavior).
      - cylindrical: length = DIAMETER, width = DIAMETER, height = wall height.
      - dome:        length = DIAMETER, width = DIAMETER, height = TOTAL height
                     (hemispherical cap on a cylindrical drum of height
                     max(0, H - radius)).
      - pyramid:     L x W base, H apex height.

    Derived metrics (SI):
      floor_area_m2:    floor footprint area
      volume_m3:        enclosed air volume
      gross_wall_area_m2: vertical exterior wall area (curved where applicable)
      roof_area_m2:     roof/envelope top area (curved cap where applicable)
      total_envelope_area_m2: gross_wall + roof (floor excluded, matching the
                          engine's envelope-loss convention)

    Dome volume uses the exact spherical-cap formula
        V = (pi * h_cap^2 / 3) * (3r - h_cap) + pi * r^2 * h_drum,
    with h_cap = H - h_drum. Dome envelope area uses the spherical-cap
    lateral area
        A = 2 * pi * r * h_cap (+ 2 * pi * r * h_drum drum wall),
    the standard surface-of-revolution approximation documented here.
    Pyramid envelope uses the exact sloped-face area from the true slant
    heights, not the rectangular wall formula.

    Raises:
        ValueError: on non-positive dimensions or unknown shape.
    """
    shape_norm = (shape or "rectangular").strip().lower()
    if shape_norm not in ("rectangular", "cylindrical", "dome", "pyramid"):
        raise ValueError(
            f"Unsupported shelter shape '{shape}'. Supported: rectangular, "
            "cylindrical, dome, pyramid."
        )
    if length <= 0.0 or width <= 0.0 or height <= 0.0:
        raise ValueError(
            f"Shelter dimensions must be strictly positive, got "
            f"L={length}, W={width}, H={height}"
        )

    if shape_norm == "rectangular":
        floor = float(length) * float(width)
        volume = floor * float(height)
        gross_wall = 2.0 * (float(length) + float(width)) * float(height)
        roof = floor
        return {
            "shape": "rectangular",
            "floor_area_m2": round(floor, 4),
            "volume_m3": round(volume, 4),
            "gross_wall_area_m2": round(gross_wall, 4),
            "roof_area_m2": round(roof, 4),
            "total_envelope_area_m2": round(gross_wall + roof, 4),
        }

    if shape_norm == "cylindrical":
        diameter = float(length)
        radius = diameter / 2.0
        floor = _math.pi * radius * radius
        volume = floor * float(height)
        wall = 2.0 * _math.pi * radius * float(height)  # cylinder lateral area
        roof = floor  # flat circular roof
        return {
            "shape": "cylindrical",
            "floor_area_m2": round(floor, 4),
            "volume_m3": round(volume, 4),
            "gross_wall_area_m2": round(wall, 4),
            "roof_area_m2": round(roof, 4),
            "total_envelope_area_m2": round(wall + roof, 4),
        }

    if shape_norm == "dome":
        diameter = float(length)
        radius = diameter / 2.0
        total_h = float(height)
        # Drum (vertical wall) height: the part of H that is cylindrical; the
        # remainder is the spherical cap. For H <= r the shelter is a pure cap
        # on the ground (drum height 0).
        drum_h = max(0.0, min(total_h - radius, total_h))
        cap_h = max(0.0, total_h - drum_h)
        floor = _math.pi * radius * radius
        drum_wall = 2.0 * _math.pi * radius * drum_h
        cap_area = 2.0 * _math.pi * radius * cap_h
        cap_volume = (_math.pi * cap_h * cap_h / 3.0) * (3.0 * radius - cap_h)
        volume = _math.pi * radius * radius * drum_h + cap_volume
        # Dome envelope = curved shell only (no separate flat roof).
        return {
            "shape": "dome",
            "floor_area_m2": round(floor, 4),
            "volume_m3": round(volume, 4),
            "gross_wall_area_m2": round(drum_wall, 4),
            "roof_area_m2": round(cap_area, 4),
            "total_envelope_area_m2": round(drum_wall + cap_area, 4),
        }

    # pyramid
    base_l = float(length)
    base_w = float(width)
    apex_h = float(height)
    floor = base_l * base_w
    volume = floor * apex_h / 3.0
    # Exact sloped-face areas from true slant heights.
    slant_l = _math.sqrt((base_w / 2.0) ** 2 + apex_h ** 2)  # faces meeting base L
    slant_w = _math.sqrt((base_l / 2.0) ** 2 + apex_h ** 2)  # faces meeting base W
    wall = base_l * slant_l + base_w * slant_w
    return {
        "shape": "pyramid",
        "floor_area_m2": round(floor, 4),
        "volume_m3": round(volume, 4),
        "gross_wall_area_m2": round(wall, 4),
        "roof_area_m2": 0.0,  # the sloped faces ARE the envelope; no flat roof
        "total_envelope_area_m2": round(wall, 4),
    }
