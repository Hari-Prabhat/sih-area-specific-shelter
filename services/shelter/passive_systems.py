"""
THERMOSHELTER AI — Passive Systems Engine (Member 2)
=====================================================
Structured representation of architectural passive solar, thermal mass,
ventilation, shading, airlock, and buffer zone strategies.

Defines passive strategies as explicit physical and geometric configurations
for downstream simulation engines (Member 3) without directly simulating
temperatures here.

Supported Climatic Frameworks:
- Cold-region: High insulation, direct solar capture, south solar aperture,
  thermal mass storage, entry airlock/vestibule, buffer zones, controlled ventilation.
- Hot/dry: Night-time cool-air flushing and thermal-mass pre-cooling, external shading,
  reduced daytime solar gain, controlled openings.
- Hot/humid: Cross-ventilation pathways, stack ventilation, shading, high openable area.
- Variable/seasonal: Adaptive operable openings, adjustable shading, reversible ventilation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.shelter.models import PassiveStrategy


class PassiveStrategyValidationError(ValueError):
    """Raised when passive strategy configuration or parameters are invalid."""
    pass


# =====================================================================
# STANDARD CATALOG OF STRATEGIES
# =====================================================================

STRATEGY_CATALOG: Dict[str, Dict[str, Any]] = {
    # ------------------ COLD REGION STRATEGIES ------------------
    "high_performance_insulation": {
        "name": "High-Performance Continuous Envelope Insulation",
        "category": "cold_region",
        "climate_applicability": ["extreme_cold", "cold", "high_altitude_desert"],
        "default_parameters": {
            "target_wall_u_value": 0.25,
            "target_roof_u_value": 0.18,
            "target_floor_u_value": 0.30,
            "thermal_bridging_factor": 0.05,
        },
        "notes": "Minimizes conductive heat loss across extreme temperature differentials (e.g. -20°C in Ladakh).",
        "assumptions": "Continuous insulation layer without uninsulated structural thermal bridges.",
    },
    "direct_solar_gain_south_aperture": {
        "name": "South-Oriented Direct Solar Aperture",
        "category": "cold_region",
        "climate_applicability": ["extreme_cold", "cold", "high_altitude_desert"],
        "default_parameters": {
            "south_window_to_wall_ratio": 0.25,
            "north_window_to_wall_ratio": 0.05,
            "glazing_shgc": 0.65,
            "nighttime_movable_insulation_r": 1.0,
        },
        "notes": "Captures abundant winter horizontal and vertical solar radiation at high altitude.",
        "assumptions": "South facade has unobstructed solar exposure between 09:00 and 15:00 solar time.",
    },
    "sensible_thermal_mass_storage": {
        "name": "Sensible Thermal Mass Storage Core",
        "category": "cold_region",
        "climate_applicability": ["extreme_cold", "cold", "high_altitude_desert", "hot_dry"],
        "default_parameters": {
            "mass_material": "mud_brick",
            "thickness_m": 0.30,
            "minimum_capacitance_j_per_k": 5000000.0,
            "solar_radiation_coupling_fraction": 0.70,
        },
        "notes": "Absorbs diurnal solar peaks and re-radiates heat during sub-zero nights.",
        "assumptions": "Thermal mass is coupled directly to solar gain zone and interior air volume.",
    },
    "entry_airlock_vestibule": {
        "name": "Airlock Vestibule (Dual-Door Entrance Buffer)",
        "category": "cold_region",
        "climate_applicability": ["extreme_cold", "cold", "high_altitude_desert"],
        "default_parameters": {
            "airlock_depth_m": 1.5,
            "airlock_area_m2": 3.0,
            "door_seal_infiltration_reduction_factor": 0.65,
        },
        "notes": "Prevents catastrophic cold air gushes upon ingress/egress in sub-zero windy environments.",
        "assumptions": "Two sequential doors are operated independently so both are never open simultaneously.",
    },
    "buffer_zone_layout": {
        "name": "Thermal Buffer Zone Layout",
        "category": "cold_region",
        "climate_applicability": ["extreme_cold", "cold", "composite"],
        "default_parameters": {
            "buffer_facade": "north",
            "buffer_use": "storage_or_latrine",
            "buffer_temp_delta_c": 5.0,
        },
        "notes": "Places non-habitable or secondary spaces along the harsh north/windward boundary.",
        "assumptions": "Buffer zone has unheated boundary walls serving as an intermediate thermal step.",
    },
    "controlled_low_rate_ventilation": {
        "name": "Controlled Minimum Fresh-Air Ventilation",
        "category": "cold_region",
        "climate_applicability": ["extreme_cold", "cold"],
        "default_parameters": {
            "ach_baseline": 0.35,
            "air_preheat_solar_collector": False,
            "heat_recovery_efficiency": 0.0,
        },
        "notes": "Maintains occupant air quality (CO2 management) while severely restricting cold air infiltration.",
        "assumptions": "Envelope is well-caulked to limit uncontrolled leakage.",
    },

    # ------------------ HOT/DRY STRATEGIES ------------------
    "night_cooling_and_mass_precooling": {
        "name": "Night-Time Cool-Air Flushing and Thermal-Mass Pre-Cooling",
        "category": "hot_dry",
        "climate_applicability": ["hot_dry", "desert"],
        "default_parameters": {
            "night_flush_ach": 4.0,
            "flush_start_hour": 22,
            "flush_end_hour": 6,
            "daytime_sealed_ach": 0.3,
        },
        "notes": "Harnesses large diurnal temperature swings to evacuate heat and chill internal mass overnight.",
        "assumptions": "Night ambient temperature drops below comfort threshold (diurnal swing > 12°C).",
    },
    "solar_rejection_and_overhang_shading": {
        "name": "Solar Rejection and Exterior Overhang Shading",
        "category": "hot_dry",
        "climate_applicability": ["hot_dry", "hot_humid", "composite"],
        "default_parameters": {
            "overhang_depth_m": 0.8,
            "roof_solar_reflectance": 0.75,
            "exterior_shading_factor": 0.35,
        },
        "notes": "Rejects high-angle direct summer solar radiation from opaque roof and glazing surfaces.",
        "assumptions": "Overhang geometry is sized to shade high summer sun while admitting low winter sun.",
    },
    "controlled_daytime_openings": {
        "name": "Controlled Daytime Openings Closure",
        "category": "hot_dry",
        "climate_applicability": ["hot_dry"],
        "default_parameters": {
            "daytime_aperture_closure_pct": 90.0,
            "inlet_filtration": True,
        },
        "notes": "Restricts ingress of hot, dusty daytime exterior air into the shelter core.",
        "assumptions": "Occupants maintain closed fenestrations during daytime heat hours.",
    },

    # ------------------ HOT/HUMID STRATEGIES ------------------
    "natural_cross_ventilation": {
        "name": "Natural Cross-Ventilation System",
        "category": "hot_humid",
        "climate_applicability": ["hot_humid", "warm_marine"],
        "default_parameters": {
            "inlet_to_outlet_ratio": 1.0,
            "windward_facade": "south",
            "leeward_facade": "north",
            "effective_air_velocity_m_s": 0.8,
            "min_openable_wwr": 0.30,
        },
        "notes": "Enhances indoor air movement to maximize physiological evaporative cooling in humid air.",
        "assumptions": "Aligns apertures with prevailing daytime breeze directions.",
    },
    "stack_ventilation_induced_exhaust": {
        "name": "Stack-Effect Induced Thermal Chimney Ventilation",
        "category": "hot_humid",
        "climate_applicability": ["hot_humid", "composite"],
        "default_parameters": {
            "stack_height_m": 2.5,
            "exhaust_vent_area_m2": 0.6,
            "inlet_vent_area_m2": 0.8,
        },
        "notes": "Uses thermal buoyancy to draw warm stale air out through elevated ridge/roof vents.",
        "assumptions": "Vertical height differential between low inlet and high exhaust is maintained.",
    },

    # ------------------ VARIABLE / SEASONAL STRATEGIES ------------------
    "adaptive_seasonal_shading": {
        "name": "Adaptive Seasonal Glazing Shading",
        "category": "variable_seasonal",
        "climate_applicability": ["composite", "variable_seasonal"],
        "default_parameters": {
            "summer_shading_factor": 0.30,
            "winter_shading_factor": 0.95,
            "mechanism": "movable_exterior_louvers",
        },
        "notes": "Allows full winter solar heat gain while blocking harsh summer solar gains.",
        "assumptions": "Manual or automated adjustment between cooling and heating seasons.",
    },
    "reversible_seasonal_ventilation": {
        "name": "Reversible Seasonal Ventilation Mode",
        "category": "variable_seasonal",
        "climate_applicability": ["composite", "variable_seasonal"],
        "default_parameters": {
            "winter_ach": 0.3,
            "summer_ach": 3.5,
        },
        "notes": "Switches between tightly sealed winter heat-retention and open summer air-flushing.",
        "assumptions": "Operable vents and sash windows can be tightly latched with weather-stripping.",
    },
}


# =====================================================================
# STRATEGY FACTORY & MANAGEMENT FUNCTIONS
# =====================================================================

def get_strategy_catalog() -> Dict[str, Dict[str, Any]]:
    """Returns the full master catalog of supported passive design strategies."""
    return dict(STRATEGY_CATALOG)


def create_passive_strategy(
    strategy_id: str,
    enabled: bool = True,
    name: Optional[str] = None,
    category: Optional[str] = None,
    climate_applicability: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    affected_openings: Optional[List[str]] = None,
    affected_surfaces: Optional[List[str]] = None,
    notes: Optional[str] = None,
    assumptions: Optional[str] = None,
) -> PassiveStrategy:
    """
    Constructs a validated PassiveStrategy instance.
    If strategy_id matches a known catalog entry, standard defaults are populated.
    """
    catalog_entry = STRATEGY_CATALOG.get(strategy_id)
    if catalog_entry:
        strat_name = name or catalog_entry["name"]
        strat_cat = category or catalog_entry["category"]
        strat_climates = climate_applicability or list(catalog_entry["climate_applicability"])
        merged_params = dict(catalog_entry["default_parameters"])
        if parameters:
            merged_params.update(parameters)
        strat_notes = notes or catalog_entry["notes"]
        strat_assump = assumptions or catalog_entry["assumptions"]
    else:
        if not category:
            raise PassiveStrategyValidationError(
                f"Custom strategy '{strategy_id}' must specify category "
                f"('cold_region', 'hot_dry', 'hot_humid', 'variable_seasonal')."
            )
        strat_name = name or strategy_id.replace("_", " ").title()
        strat_cat = category
        strat_climates = climate_applicability or ["general"]
        merged_params = parameters or {}
        strat_notes = notes or "User-defined passive strategy"
        strat_assump = assumptions or ""

    strategy = PassiveStrategy(
        id=strategy_id,
        name=strat_name,
        category=strat_cat,
        climate_applicability=strat_climates,
        enabled=enabled,
        parameters=merged_params,
        affected_openings=affected_openings or [],
        affected_surfaces=affected_surfaces or [],
        notes=strat_notes,
        assumptions=strat_assump,
    )

    validate_passive_strategy(strategy)
    return strategy


def validate_passive_strategy(strategy: PassiveStrategy) -> None:
    """
    Validates passive strategy configuration and parameter bounds.
    """
    valid_categories = {"cold_region", "hot_dry", "hot_humid", "variable_seasonal"}
    if strategy.category.lower() not in valid_categories:
        raise PassiveStrategyValidationError(
            f"Invalid strategy category '{strategy.category}'. Must be one of {valid_categories}"
        )

    # Validate specific numeric parameters
    params = strategy.parameters
    if "night_flush_ach" in params:
        val = float(params["night_flush_ach"])
        if val <= 0.0:
            raise PassiveStrategyValidationError(f"night_flush_ach must be > 0, got {val}")
    if "ach_baseline" in params:
        val = float(params["ach_baseline"])
        if val <= 0.0:
            raise PassiveStrategyValidationError(f"ach_baseline must be > 0, got {val}")
    if "south_window_to_wall_ratio" in params:
        val = float(params["south_window_to_wall_ratio"])
        if not (0.0 <= val <= 1.0):
            raise PassiveStrategyValidationError(f"south_window_to_wall_ratio must be in [0, 1], got {val}")
    if "overhang_depth_m" in params:
        val = float(params["overhang_depth_m"])
        if val < 0.0:
            raise PassiveStrategyValidationError(f"overhang_depth_m cannot be negative, got {val}")


def get_default_cold_region_strategies() -> List[PassiveStrategy]:
    """Returns standard recommended passive strategies for extreme cold climates (e.g. Leh/Ladakh)."""
    return [
        create_passive_strategy("high_performance_insulation", enabled=True),
        create_passive_strategy("direct_solar_gain_south_aperture", enabled=True, affected_surfaces=["south"]),
        create_passive_strategy("sensible_thermal_mass_storage", enabled=True),
        create_passive_strategy("entry_airlock_vestibule", enabled=True),
        create_passive_strategy("buffer_zone_layout", enabled=True, affected_surfaces=["north"]),
        create_passive_strategy("controlled_low_rate_ventilation", enabled=True),
    ]


def get_default_hot_dry_strategies() -> List[PassiveStrategy]:
    """Returns standard recommended passive strategies for hot-dry climates (e.g. Jaisalmer)."""
    return [
        create_passive_strategy("night_cooling_and_mass_precooling", enabled=True),
        create_passive_strategy("sensible_thermal_mass_storage", enabled=True),
        create_passive_strategy("solar_rejection_and_overhang_shading", enabled=True, affected_surfaces=["roof", "south", "west"]),
        create_passive_strategy("controlled_daytime_openings", enabled=True),
    ]


def get_default_hot_humid_strategies() -> List[PassiveStrategy]:
    """Returns standard recommended passive strategies for hot-humid climates (e.g. Chennai)."""
    return [
        create_passive_strategy("natural_cross_ventilation", enabled=True, affected_surfaces=["south", "north"]),
        create_passive_strategy("stack_ventilation_induced_exhaust", enabled=True, affected_surfaces=["roof"]),
        create_passive_strategy("solar_rejection_and_overhang_shading", enabled=True, affected_surfaces=["roof", "south", "east", "west"]),
    ]
