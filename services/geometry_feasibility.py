"""
THERMOSHELTER - Geometry feasibility boundaries (D5-A)
=====================================================

Pure, deterministic validation helpers over the EXISTING canonical geometry
engine (services/geometry.py remains the single authority for areas and
volumes - this module recomputes nothing).

Purpose (D5-A Phase, contract preparation only):
    Isolate the opening-feasibility boundary that D5-B geometry optimization
    will enforce BEFORE candidate evaluation. Rationale (D5 audit): the
    simulation engine silently clamps over-sized openings to the gross wall
    area (simulation_service.py window/door area clamps). If the optimizer
    relied on those clamps, a candidate could be ranked on clamped physics
    while consumers (Apply Candidate, Blueprint, 3D, Report) displayed the
    UNCLAMPED design - an inconsistency. D5-B must REJECT infeasible
    candidates instead; these helpers define that rejection boundary.

Engineering honesty:
    - NO numeric facade margins, minimum openings, or aspect ratios are
      invented here. Facade-margins are an engineering/product decision and
      remain absent until explicitly approved (flagged for D5-B).
    - All thresholds are expressed as engine-derived quantities (gross wall
      area, opening areas from the canonical design).

These helpers are not yet called by the optimizer (D5-A scope); they are
unit-tested so D5-B can consume them without redesign.
"""

from typing import Any, Dict, Optional, Tuple

from services.geometry import calculate_wall_area


def openings_fit_within_envelope(
    length: float,
    width: float,
    height: float,
    window_area: float,
    door_area: float,
) -> Dict[str, Any]:
    """
    Deterministic opening-feasibility boundary for a rectangular envelope.

    Checks (mathematical basis only, no invented margins):
      1. All inputs finite and strictly positive where dimensionally required.
      2. Total opening area (windows + doors) must not exceed the gross wall
         area derived by the canonical geometry engine.

    This mirrors the physical requirement enforced by
    ``services.geometry.calculate_net_wall_area`` (net wall area must remain
    non-negative) but returns a machine-readable verdict instead of raising,
    so D5-B can prune infeasible candidates without exception-driven control
    flow inside the Optuna objective.

    Args:
        length: Interior length in meters.
        width: Interior width in meters.
        height: Clear interior height in meters.
        window_area: Total window opening area in m^2.
        door_area: Total door opening area in m^2.

    Returns:
        Dict with:
            feasible (bool): True when openings fit within the gross wall area.
            gross_wall_area_m2 (float): Canonical engine gross wall area.
            total_openings_m2 (float): window_area + door_area.
            reason (str | None): Human-readable rejection reason when infeasible.
    """
    dims = (length, width, height)
    if any(not isinstance(d, (int, float)) or d != d or d in (float("inf"), float("-inf")) for d in dims):
        return {
            "feasible": False,
            "gross_wall_area_m2": None,
            "total_openings_m2": None,
            "reason": "Geometry dimensions must be finite numbers.",
        }
    if any(d <= 0.0 for d in dims):
        return {
            "feasible": False,
            "gross_wall_area_m2": None,
            "total_openings_m2": None,
            "reason": "Geometry dimensions must be strictly positive (> 0).",
        }
    if window_area < 0.0 or door_area < 0.0:
        return {
            "feasible": False,
            "gross_wall_area_m2": None,
            "total_openings_m2": None,
            "reason": "Opening areas cannot be negative.",
        }

    gross_wall_area = float(calculate_wall_area(length, width, height))
    total_openings = float(window_area) + float(door_area)

    if total_openings > gross_wall_area:
        return {
            "feasible": False,
            "gross_wall_area_m2": gross_wall_area,
            "total_openings_m2": total_openings,
            "reason": (
                f"Total openings area ({total_openings:.2f} m^2) exceeds gross "
                f"wall area ({gross_wall_area:.2f} m^2)."
            ),
        }

    return {
        "feasible": True,
        "gross_wall_area_m2": gross_wall_area,
        "total_openings_m2": total_openings,
        "reason": None,
    }


# =====================================================================
# D5-B: full pre-simulation geometry feasibility evaluation.
#
# Deterministic rejection boundary for geometry-optimized candidates.
# The simulation engine's 85% window / 15% door gross-wall clamps are
# ENGINE-INTERNAL PHYSICS GUARDS and are deliberately NOT the feasibility
# model: relying on them would rank candidates on clamped physics while
# consumers displayed the unclamped design. D5-B rejects infeasible
# candidates BEFORE simulation instead.
#
# Facade-usable-area percentages/margins are deliberately ABSENT: any
# such margin would be an invented numeric constraint. The per-facade
# checks below use full facade bands (100% usable) - purely mathematical.
#
# The opening layout derivation (window counts, 70/30 south/north area
# split, aspect-derived dimensions) mirrors the frontend
# thermoshelter-design-studio/src/services/openingLayout.ts EXACTLY -
# the single deterministic layout authority shared by Blueprint, 3D,
# and now feasibility.
# =====================================================================

SOUTH_GLAZING_SHARE = 0.7
NORTH_GLAZING_SHARE = 0.3


def _derive_opening_dims(window_area: float, door_area: float) -> Dict[str, float]:
    """
    Mirrors services/openingLayout.ts (D4-C): south = 2 windows sharing 70%
    of the design window area; north = 1 window with 30%; single south door.
    Dimension clamps are the SAME values the viewers use, so a candidate
    that passes here is exactly what Blueprint/3D will draw.
    """
    r2 = lambda v: round(v * 100) / 100  # noqa: E731 - mirrors ts r2()

    def clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    south_total = window_area * SOUTH_GLAZING_SHARE
    north_total = window_area * NORTH_GLAZING_SHARE

    south_each = max(0.3, south_total / 2.0)
    south_w = clamp(r2((south_each * 1.3) ** 0.5), 0.6, 2.4)
    south_h = clamp(r2(south_each / south_w), 0.6, 2.0)

    north_each = north_total
    north_w = clamp(r2((north_each * 1.2) ** 0.5), 0.5, 1.8)
    north_h = clamp(r2(north_each / north_w), 0.5, 1.6)

    door_clamped = clamp(door_area if door_area and door_area > 0 else 2.0, 0.8, 5.0)
    door_w = clamp(r2((door_clamped / 2.2) ** 0.5), 0.8, 1.8)
    door_h = clamp(r2(door_clamped / door_w), 1.9, 2.5)

    return {
        "south_window_w": south_w,
        "south_window_h": south_h,
        "north_window_w": north_w,
        "north_window_h": north_h,
        "door_w": door_w,
        "door_h": door_h,
    }


def evaluate_geometry_feasibility(
    length: float,
    width: float,
    height: float,
    window_area: float,
    door_area: float,
    min_aspect_ratio: Optional[float] = None,
    max_aspect_ratio: Optional[float] = None,
    bounds: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Dict[str, Any]:
    """
    Deterministic D5-B feasibility verdict for one candidate geometry.

    Checks, in order (all mathematical; NO invented margins):
      1. Trial dimension bounds (redundant-by-construction defense: the
         Optuna sampling bounds produce in-range values, but this guards
         against future call sites).
      2. Orientation-independent aspect ratio
         ``max(L/W, W/L)`` against supplied bounds (when given).
      3. Per-facade opening fit: the derived south-facade openings
         (70% of windows + door) must fit the L x H south band; the north
         windows (30%) must fit the L x H north band; each derived opening's
         width must fit the facade length and height must fit clear height.
      4. Total-opening gross-wall backstop (openings_fit_within_envelope,
         rectangular gross wall - conservative for pitched roofs whose
         gable area only increases the real gross wall).

    Returns:
        Dict with ``feasible`` (bool), ``reason`` (str | None) and
        ``checks`` (detail per rule) - machine-readable for TrialPruned.
    """
    checks: Dict[str, Any] = {}

    # 0. Basic numeric sanity (mirrors the helper above).
    dims = (length, width, height)
    if any(not isinstance(d, (int, float)) or d != d or d in (float("inf"), float("-inf")) for d in dims):
        return {"feasible": False, "reason": "Geometry dimensions must be finite numbers.", "checks": {}}
    if any(d <= 0.0 for d in dims):
        return {"feasible": False, "reason": "Geometry dimensions must be strictly positive (> 0).", "checks": {}}
    if window_area < 0.0 or door_area < 0.0:
        return {"feasible": False, "reason": "Opening areas cannot be negative.", "checks": {}}

    # 1. Trial dimension bounds (optional explicit defense).
    if bounds:
        for dim, value in (("length", length), ("width", width), ("height", height)):
            if dim in bounds:
                lo, hi = bounds[dim]
                if not (lo <= value <= hi):
                    checks["dimension_bounds"] = False
                    return {
                        "feasible": False,
                        "reason": f"{dim} ({value} m) outside bounds [{lo}, {hi}] m.",
                        "checks": checks,
                    }
        checks["dimension_bounds"] = True

    # 2. Orientation-independent aspect ratio.
    aspect_ratio = max(length / width, width / length)
    checks["aspect_ratio"] = aspect_ratio
    if min_aspect_ratio is not None and aspect_ratio < min_aspect_ratio:
        return {
            "feasible": False,
            "reason": f"Aspect ratio {aspect_ratio:.3f} below minimum {min_aspect_ratio}.",
            "checks": checks,
        }
    if max_aspect_ratio is not None and aspect_ratio > max_aspect_ratio:
        return {
            "feasible": False,
            "reason": f"Aspect ratio {aspect_ratio:.3f} exceeds maximum {max_aspect_ratio}.",
            "checks": checks,
        }

    # 3. Per-facade opening fit (openingLayout.ts derivation).
    o = _derive_opening_dims(window_area, door_area)
    south_band = length * height
    south_needed = window_area * SOUTH_GLAZING_SHARE + max(0.0, min(door_area, door_area if door_area > 0 else 2.0))
    north_needed = window_area * NORTH_GLAZING_SHARE
    checks["south_facade_demand_m2"] = round(south_needed, 3)
    checks["north_facade_demand_m2"] = round(north_needed, 3)
    if south_needed > south_band + 1e-9:
        return {
            "feasible": False,
            "reason": (
                f"South facade openings ({south_needed:.2f} m2: 70% windows + door) "
                f"exceed the {length:g} x {height:g} m facade band ({south_band:.2f} m2)."
            ),
            "checks": checks,
        }
    if north_needed > south_band + 1e-9:
        return {
            "feasible": False,
            "reason": (
                f"North facade windows ({north_needed:.2f} m2) exceed the "
                f"{length:g} x {height:g} m facade band ({south_band:.2f} m2)."
            ),
            "checks": checks,
        }
    # Per-opening dimensional fit (same clamped dims the viewers draw).
    if o["south_window_h"] > height + 1e-9 or o["north_window_h"] > height + 1e-9 or o["door_h"] > height + 1e-9:
        return {
            "feasible": False,
            "reason": f"Derived opening height exceeds clear height {height:g} m.",
            "checks": checks,
        }
    if o["south_window_w"] > length + 1e-9 or o["north_window_w"] > length + 1e-9 or o["door_w"] > length + 1e-9:
        return {
            "feasible": False,
            "reason": f"Derived opening width exceeds facade length {length:g} m.",
            "checks": checks,
        }
    checks["facade_fit"] = True

    # 4. Gross-wall backstop (rectangular gross wall - conservative).
    gross = float(calculate_wall_area(length, width, height))
    total_openings = float(window_area) + float(door_area)
    checks["gross_wall_area_m2"] = gross
    if total_openings > gross + 1e-9:
        return {
            "feasible": False,
            "reason": (
                f"Total openings ({total_openings:.2f} m2) exceed gross wall "
                f"area ({gross:.2f} m2)."
            ),
            "checks": checks,
        }
    checks["gross_wall_backstop"] = True

    return {"feasible": True, "reason": None, "checks": checks}
