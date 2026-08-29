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
