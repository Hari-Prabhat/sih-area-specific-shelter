"""
THERMOSHELTER AI — Canonical Data Contracts (Member 2)
======================================================
Authoritative domain models and shared contracts for geometry, multi-layer
envelope assemblies, thermal mass, glazing, openings, passive strategies,
and the composite ShelterDesign digital twin.

All models conform to explicit SI units, physical sanity bounds, and full
round-trip JSON serialization.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from services.formula_constants import (
    DEFAULT_ACH,
    DEFAULT_OCCUPANT_HEAT_GAIN,
)


# =====================================================================
# DATA PROVENANCE
# =====================================================================

class DataProvenance:
    """Canonical enumeration of data origin and measurement confidence level."""
    USER_DEFINED = "user_defined"
    DATABASE = "database"
    ESTIMATED = "estimated"
    HISTORICAL = "historical"
    MEASURED = "measured"
    SIMULATED = "simulated"
    OPTIMIZED = "optimized"

    @classmethod
    def all_values(cls) -> set[str]:
        return {
            cls.USER_DEFINED,
            cls.DATABASE,
            cls.ESTIMATED,
            cls.HISTORICAL,
            cls.MEASURED,
            cls.SIMULATED,
            cls.OPTIMIZED,
        }


# =====================================================================
# 1. SHELTER REQUIREMENTS
# =====================================================================

@dataclass
class ShelterRequirements:
    """
    High-level operational, occupant, and contextual requirements for the shelter.

    SI Units:
        occupants: integer count (persons, strictly > 0)
        duration_days: days (or None for permanent, strictly > 0 if specified)
    """
    occupants: int
    shelter_purpose: str  # e.g. "emergency_relief", "high_altitude_post", "field_station", "residence", "permanent_passive_shelter"
    duration_days: Optional[int] = None
    permanence: str = "permanent"  # "temporary", "semi_permanent", "permanent"
    mobility: str = "permanent"  # "mobile", "demountable", "permanent"
    priorities: List[str] = field(default_factory=list)  # e.g. ["thermal_comfort", "speed_of_assembly"]
    available_resources: List[str] = field(default_factory=list)  # e.g. ["local_stone", "mud", "timber"]
    energy_sources: List[str] = field(default_factory=list)  # e.g. ["passive_solar", "biomass"]
    constraints: Dict[str, Any] = field(default_factory=dict)
    provenance: str = DataProvenance.USER_DEFINED

    def __post_init__(self) -> None:
        if self.occupants <= 0:
            raise ValueError(f"Occupants must be strictly positive (> 0), got {self.occupants}")
        if self.duration_days is not None and self.duration_days <= 0:
            raise ValueError(f"Duration days must be > 0 when specified, got {self.duration_days}")
        valid_permanence = {"temporary", "semi_permanent", "permanent"}
        if self.permanence.lower() not in valid_permanence:
            raise ValueError(f"Invalid permanence '{self.permanence}'. Must be one of {valid_permanence}")
        valid_mobility = {"mobile", "demountable", "permanent"}
        if self.mobility.lower() not in valid_mobility:
            raise ValueError(f"Invalid mobility '{self.mobility}'. Must be one of {valid_mobility}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShelterRequirements:
        return cls(
            occupants=int(data["occupants"]),
            shelter_purpose=str(data.get("shelter_purpose", "general")),
            duration_days=int(data["duration_days"]) if data.get("duration_days") is not None else None,
            permanence=str(data.get("permanence", "permanent")),
            mobility=str(data.get("mobility", "permanent")),
            priorities=list(data.get("priorities", [])),
            available_resources=list(data.get("available_resources", [])),
            energy_sources=list(data.get("energy_sources", [])),
            constraints=dict(data.get("constraints", {})),
            provenance=str(data.get("provenance", DataProvenance.USER_DEFINED)),
        )


# =====================================================================
# 2. OPENINGS & ZONES
# =====================================================================

@dataclass
class OpeningDefinition:
    """
    Physical fenestration or aperture in the building envelope.

    SI Units:
        width_m: meters (m)
        height_m: meters (m)
        area_m2: square meters (m²)
        orientation_deg: azimuth degrees (0°=N, 90°=E, 180°=S, 270°=W)
        overhang_depth_m: meters (m)
        shading_factor: dimensionless fraction [0.0, 1.0] (1.0 = unshaded)
    """
    id: str
    name: str
    opening_type: str  # "window", "door", "vent", "inlet", "outlet"
    width_m: float
    height_m: float
    area_m2: float
    facade: str  # "north", "south", "east", "west", "roof"
    orientation_deg: float  # 0.0 to 360.0
    is_operable: bool = False
    glazing_id: Optional[str] = None
    shading_factor: float = 1.0  # 0.0 to 1.0
    overhang_depth_m: float = 0.0
    ventilation_role: str = "none"  # "inlet", "outlet", "bypass", "night_purge", "none"
    provenance: str = DataProvenance.USER_DEFINED

    def __post_init__(self) -> None:
        if self.width_m <= 0.0 or self.height_m <= 0.0:
            raise ValueError(f"Opening dimensions must be strictly positive, got {self.width_m}x{self.height_m}")
        if self.area_m2 <= 0.0:
            raise ValueError(f"Opening area must be strictly positive, got {self.area_m2}")
        if not (0.0 <= self.orientation_deg <= 360.0):
            raise ValueError(f"Orientation must be within [0, 360] degrees, got {self.orientation_deg}")
        if not (0.0 <= self.shading_factor <= 1.0):
            raise ValueError(f"Shading factor must be between 0.0 and 1.0, got {self.shading_factor}")
        if self.overhang_depth_m < 0.0:
            raise ValueError(f"Overhang depth cannot be negative, got {self.overhang_depth_m}")
        valid_types = {"window", "door", "vent", "inlet", "outlet"}
        if self.opening_type.lower() not in valid_types:
            raise ValueError(f"Invalid opening type '{self.opening_type}'. Must be one of {valid_types}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OpeningDefinition:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            opening_type=str(data.get("opening_type", "window")),
            width_m=float(data["width_m"]),
            height_m=float(data["height_m"]),
            area_m2=float(data.get("area_m2", float(data["width_m"]) * float(data["height_m"]))),
            facade=str(data.get("facade", "south")).lower(),
            orientation_deg=float(data.get("orientation_deg", 180.0)),
            is_operable=bool(data.get("is_operable", False)),
            glazing_id=str(data["glazing_id"]) if data.get("glazing_id") else None,
            shading_factor=float(data.get("shading_factor", 1.0)),
            overhang_depth_m=float(data.get("overhang_depth_m", 0.0)),
            ventilation_role=str(data.get("ventilation_role", "none")).lower(),
            provenance=str(data.get("provenance", DataProvenance.USER_DEFINED)),
        )


@dataclass
class ZoneDefinition:
    """
    Sub-divided spatial functional zone within the shelter envelope.

    SI Units:
        floor_area_m2: m²
        volume_m3: m³
        length_m, width_m, height_m: m
    """
    id: str
    name: str
    zone_type: str  # "occupied", "solar", "thermal_mass_core", "buffer", "airlock"
    floor_area_m2: float
    volume_m3: float
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    temperature_control_required: bool = True
    notes: str = ""
    provenance: str = DataProvenance.USER_DEFINED

    def __post_init__(self) -> None:
        if self.floor_area_m2 <= 0.0:
            raise ValueError(f"Zone floor area must be strictly positive, got {self.floor_area_m2}")
        if self.volume_m3 <= 0.0:
            raise ValueError(f"Zone volume must be strictly positive, got {self.volume_m3}")
        valid_types = {"occupied", "solar", "thermal_mass_core", "buffer", "airlock"}
        if self.zone_type.lower() not in valid_types:
            raise ValueError(f"Invalid zone type '{self.zone_type}'. Must be one of {valid_types}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ZoneDefinition:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            zone_type=str(data.get("zone_type", "occupied")),
            floor_area_m2=float(data["floor_area_m2"]),
            volume_m3=float(data["volume_m3"]),
            length_m=float(data["length_m"]) if data.get("length_m") is not None else None,
            width_m=float(data["width_m"]) if data.get("width_m") is not None else None,
            height_m=float(data["height_m"]) if data.get("height_m") is not None else None,
            temperature_control_required=bool(data.get("temperature_control_required", True)),
            notes=str(data.get("notes", "")),
            provenance=str(data.get("provenance", DataProvenance.USER_DEFINED)),
        )


# =====================================================================
# 3. SHELTER GEOMETRY
# =====================================================================

@dataclass
class ShelterGeometry:
    """
    Complete geometric definition and derived boundary metrics for a shelter.

    SI Units:
        length_m, width_m, height_m: meters (m, strictly > 0)
        orientation_deg: degrees azimuth (0°=North, 90°=East, 180°=South, 270°=West)
        roof_pitch_deg: slope angle in degrees [0, 90)
        floor_area_m2, roof_area_m2, gross_wall_area_m2, net_wall_area_m2: m²
        volume_m3: m³
        surface_to_volume_ratio: 1/m (m²/m³)
        window_to_wall_ratio: dimensionless fraction [0, 1]
        ridge_height_m: meters (m)
    """
    geometry_type: str  # "rectangular", "compact", "elongated", "custom"
    length_m: float
    width_m: float
    height_m: float
    roof_type: str = "flat"  # "flat", "pitched", "shed", "gable"
    roof_pitch_deg: float = 0.0
    orientation_deg: float = 180.0
    floor_area_m2: float = 0.0
    volume_m3: float = 0.0
    gross_wall_area_m2: float = 0.0
    net_wall_area_m2: float = 0.0
    facade_wall_areas: Dict[str, float] = field(default_factory=dict)
    roof_area_m2: float = 0.0
    total_envelope_area_m2: float = 0.0
    surface_to_volume_ratio: float = 0.0
    window_to_wall_ratio: float = 0.0
    ridge_height_m: float = 0.0
    openings: List[OpeningDefinition] = field(default_factory=list)
    zones: List[ZoneDefinition] = field(default_factory=list)
    provenance: str = DataProvenance.USER_DEFINED

    def __post_init__(self) -> None:
        if self.length_m <= 0.0 or self.width_m <= 0.0 or self.height_m <= 0.0:
            raise ValueError(
                f"Shelter dimensions must be strictly positive, got "
                f"L={self.length_m}, W={self.width_m}, H={self.height_m}"
            )
        if not (0.0 <= self.orientation_deg <= 360.0):
            raise ValueError(f"Orientation must be within [0, 360] degrees, got {self.orientation_deg}")
        if not (0.0 <= self.roof_pitch_deg < 90.0):
            raise ValueError(f"Roof pitch must be >= 0 and < 90 degrees, got {self.roof_pitch_deg}")

        # Derive boundary metrics if omitted
        if self.floor_area_m2 <= 0.0:
            self.floor_area_m2 = round(self.length_m * self.width_m, 4)
        if self.volume_m3 <= 0.0:
            self.volume_m3 = round(self.floor_area_m2 * self.height_m, 4)
        if self.gross_wall_area_m2 <= 0.0:
            self.gross_wall_area_m2 = round(2.0 * (self.length_m + self.width_m) * self.height_m, 4)
        if self.roof_area_m2 <= 0.0:
            if self.roof_pitch_deg > 0.0:
                rad = math.radians(self.roof_pitch_deg)
                self.roof_area_m2 = round(self.floor_area_m2 / math.cos(rad), 4)
            else:
                self.roof_area_m2 = self.floor_area_m2
        if self.total_envelope_area_m2 <= 0.0:
            self.total_envelope_area_m2 = round(self.gross_wall_area_m2 + self.roof_area_m2 + self.floor_area_m2, 4)
        if self.surface_to_volume_ratio <= 0.0 and self.volume_m3 > 0.0:
            self.surface_to_volume_ratio = round(self.total_envelope_area_m2 / self.volume_m3, 4)

        if self.openings:
            total_openings_area = sum(o.area_m2 for o in self.openings)
            wall_area = self.gross_wall_area_m2 if self.gross_wall_area_m2 > 0.0 else 2.0 * (self.length_m + self.width_m) * self.height_m
            if total_openings_area > wall_area:
                raise ValueError(
                    f"Total opening area ({total_openings_area} m²) cannot exceed total wall area ({wall_area:.2f} m²)"
                )
            self.net_wall_area_m2 = max(0.0, round(wall_area - total_openings_area, 4))
            self.window_to_wall_ratio = round(total_openings_area / wall_area, 4) if wall_area > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["openings"] = [o.to_dict() if hasattr(o, "to_dict") else o for o in self.openings]
        d["zones"] = [z.to_dict() if hasattr(z, "to_dict") else z for z in self.zones]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShelterGeometry:
        openings = [OpeningDefinition.from_dict(o) for o in data.get("openings", [])]
        zones = [ZoneDefinition.from_dict(z) for z in data.get("zones", [])]
        return cls(
            geometry_type=str(data.get("geometry_type", "rectangular")),
            length_m=float(data["length_m"]),
            width_m=float(data["width_m"]),
            height_m=float(data["height_m"]),
            roof_type=str(data.get("roof_type", "flat")),
            roof_pitch_deg=float(data.get("roof_pitch_deg", 0.0)),
            orientation_deg=float(data.get("orientation_deg", 180.0)),
            floor_area_m2=float(data.get("floor_area_m2", 0.0)),
            volume_m3=float(data.get("volume_m3", 0.0)),
            gross_wall_area_m2=float(data.get("gross_wall_area_m2", 0.0)),
            net_wall_area_m2=float(data.get("net_wall_area_m2", 0.0)),
            facade_wall_areas=dict(data.get("facade_wall_areas", {})),
            roof_area_m2=float(data.get("roof_area_m2", 0.0)),
            total_envelope_area_m2=float(data.get("total_envelope_area_m2", 0.0)),
            surface_to_volume_ratio=float(data.get("surface_to_volume_ratio", 0.0)),
            window_to_wall_ratio=float(data.get("window_to_wall_ratio", 0.0)),
            ridge_height_m=float(data.get("ridge_height_m", 0.0)),
            openings=openings,
            zones=zones,
            provenance=str(data.get("provenance", DataProvenance.USER_DEFINED)),
        )


# =====================================================================
# 4. MATERIALS & MULTILAYER ENVELOPE (ISO 6946)
# =====================================================================

@dataclass
class MaterialLayer:
    """
    Homogeneous material layer in a series composite assembly.

    SI Units:
        thickness_m: meters (m, strictly > 0)
        conductivity_w_mk: W/(m·K) (strictly > 0)
        density_kg_m3: kg/m³ (strictly > 0)
        specific_heat_j_kgk: J/(kg·K) (strictly > 0)
        emissivity, solar_absorptivity: dimensionless fraction [0.0, 1.0]
        cost_estimate_usd: USD/m² or USD/m³ (>= 0.0)
    """
    material_id: str
    name: str
    thickness_m: float
    conductivity_w_mk: float
    density_kg_m3: float
    specific_heat_j_kgk: float
    emissivity: float = 0.90
    solar_absorptivity: float = 0.70
    cost_estimate_usd: float = 0.0
    data_status: str = "literature/reference"  # "measured", "literature/reference", "estimated", "user-defined"
    source: str = ""
    provenance: str = DataProvenance.DATABASE

    def __post_init__(self) -> None:
        if self.thickness_m <= 0.0:
            raise ValueError(f"Layer thickness must be strictly positive, got {self.thickness_m} m")
        if self.conductivity_w_mk <= 0.0:
            raise ValueError(f"Conductivity must be strictly positive, got {self.conductivity_w_mk} W/(m·K)")
        if self.density_kg_m3 <= 0.0:
            raise ValueError(f"Density must be strictly positive, got {self.density_kg_m3} kg/m³")
        if self.specific_heat_j_kgk <= 0.0:
            raise ValueError(f"Specific heat must be strictly positive, got {self.specific_heat_j_kgk} J/(kg·K)")
        if not (0.0 <= self.emissivity <= 1.0):
            raise ValueError(f"Emissivity must be between 0.0 and 1.0, got {self.emissivity}")
        if not (0.0 <= self.solar_absorptivity <= 1.0):
            raise ValueError(f"Solar absorptivity must be between 0.0 and 1.0, got {self.solar_absorptivity}")
        if self.cost_estimate_usd < 0.0:
            raise ValueError(f"Cost estimate cannot be negative, got {self.cost_estimate_usd}")

    @property
    def resistance_m2_k_w(self) -> float:
        """1D conductive thermal resistance: R = d / k [m²·K/W]."""
        return self.thickness_m / self.conductivity_w_mk

    @property
    def mass_per_m2_kg(self) -> float:
        """Areal mass density: m_area = rho * d [kg/m²]."""
        return self.density_kg_m3 * self.thickness_m

    @property
    def heat_capacity_per_m2_j_k(self) -> float:
        """Areal thermal capacitance: C_area = rho * d * c_p [J/(m²·K)]."""
        return self.density_kg_m3 * self.thickness_m * self.specific_heat_j_kgk

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["resistance_m2_k_w"] = round(self.resistance_m2_k_w, 4)
        d["mass_per_m2_kg"] = round(self.mass_per_m2_kg, 2)
        d["heat_capacity_per_m2_j_k"] = round(self.heat_capacity_per_m2_j_k, 2)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MaterialLayer:
        return cls(
            material_id=str(data["material_id"]),
            name=str(data.get("name", data["material_id"])),
            thickness_m=float(data["thickness_m"]),
            conductivity_w_mk=float(data["conductivity_w_mk"]),
            density_kg_m3=float(data["density_kg_m3"]),
            specific_heat_j_kgk=float(data["specific_heat_j_kgk"]),
            emissivity=float(data.get("emissivity", 0.90)),
            solar_absorptivity=float(data.get("solar_absorptivity", 0.70)),
            cost_estimate_usd=float(data.get("cost_estimate_usd", 0.0)),
            data_status=str(data.get("data_status", "literature/reference")),
            source=str(data.get("source", "")),
            provenance=str(data.get("provenance", DataProvenance.DATABASE)),
        )


@dataclass
class MaterialAssembly:
    """
    Multi-layer composite assembly for wall, roof, floor, or door.
    Layers are ordered from Interior to Exterior.

    SI Units:
        resistances (r_inside, r_outside, r_layers, r_total): m²·K/W
        u_value: W/(m²·K)
        total_thickness_m: meters (m)
        total_mass_per_m2: kg/m²
        heat_capacity_per_m2: J/(m²·K)
    """
    assembly_id: str
    name: str
    category: str  # "wall", "roof", "floor", "door"
    layers: List[MaterialLayer] = field(default_factory=list)
    r_inside: float = 0.13  # ISO 6946 interior surface film resistance (m²·K/W)
    r_outside: float = 0.04  # ISO 6946 exterior surface film resistance (m²·K/W)
    r_layers: float = 0.0
    r_total: float = 0.0
    u_value: float = 0.0
    total_thickness_m: float = 0.0
    total_mass_per_m2: float = 0.0
    heat_capacity_per_m2: float = 0.0
    provenance: str = DataProvenance.DATABASE

    def __post_init__(self) -> None:
        if self.r_inside < 0.0 or self.r_outside < 0.0:
            raise ValueError("Film resistances cannot be negative.")
        valid_cats = {"wall", "roof", "floor", "door"}
        if self.category.lower() not in valid_cats:
            raise ValueError(f"Invalid assembly category '{self.category}'. Must be one of {valid_cats}")

        # Compute ISO 6946 properties if layers are supplied and metrics not pre-computed
        if self.layers and self.u_value <= 0.0:
            self.r_layers = sum(l.resistance_m2_k_w for l in self.layers)
            self.r_total = self.r_inside + self.r_layers + self.r_outside
            self.u_value = round(1.0 / self.r_total, 4) if self.r_total > 0 else 0.0
            self.total_thickness_m = round(sum(l.thickness_m for l in self.layers), 4)
            self.total_mass_per_m2 = round(sum(l.mass_per_m2_kg for l in self.layers), 2)
            self.heat_capacity_per_m2 = round(sum(l.heat_capacity_per_m2_j_k for l in self.layers), 2)
            self.r_layers = round(self.r_layers, 4)
            self.r_total = round(self.r_total, 4)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["layers"] = [layer.to_dict() for layer in self.layers]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MaterialAssembly:
        layers = [MaterialLayer.from_dict(l) for l in data.get("layers", [])]
        return cls(
            assembly_id=str(data["assembly_id"]),
            name=str(data.get("name", data["assembly_id"])),
            category=str(data.get("category", "wall")),
            layers=layers,
            r_inside=float(data.get("r_inside", 0.13)),
            r_outside=float(data.get("r_outside", 0.04)),
            r_layers=float(data.get("r_layers", 0.0)),
            r_total=float(data.get("r_total", 0.0)),
            u_value=float(data.get("u_value", 0.0)),
            total_thickness_m=float(data.get("total_thickness_m", 0.0)),
            total_mass_per_m2=float(data.get("total_mass_per_m2", 0.0)),
            heat_capacity_per_m2=float(data.get("heat_capacity_per_m2", 0.0)),
            provenance=str(data.get("provenance", DataProvenance.DATABASE)),
        )


# =====================================================================
# 5. THERMAL MASS & GLAZING
# =====================================================================

@dataclass
class ThermalMassDefinition:
    """
    Dedicated sensible thermal storage mass element (e.g. Trombe wall, floor slab, water wall).

    SI Units:
        thickness_m: meters (m, strictly > 0)
        area_m2: square meters (m², strictly > 0)
        volume_m3: cubic meters (m³)
        density_kg_m3: kg/m³ (strictly > 0)
        specific_heat_j_kgk: J/(kg·K) (strictly > 0)
        mass_kg: kilograms (kg)
        thermal_capacity_j_per_k: Joules per Kelvin (J/K)
    """
    id: str
    name: str
    material_id: str
    thickness_m: float
    area_m2: float
    volume_m3: float = 0.0
    density_kg_m3: float = 2300.0
    specific_heat_j_kgk: float = 880.0
    mass_kg: float = 0.0
    thermal_capacity_j_per_k: float = 0.0
    location: str = "floor_slab"  # "floor_slab", "trombe_wall", "internal_wall", "core"
    provenance: str = DataProvenance.DATABASE

    def __post_init__(self) -> None:
        if self.area_m2 <= 0.0 or self.thickness_m <= 0.0:
            raise ValueError("Thermal mass area and thickness must be strictly positive.")
        if self.density_kg_m3 <= 0.0 or self.specific_heat_j_kgk <= 0.0:
            raise ValueError("Thermal mass density and specific heat must be strictly positive.")
        if self.volume_m3 <= 0.0:
            self.volume_m3 = round(self.area_m2 * self.thickness_m, 4)
        if self.mass_kg <= 0.0:
            self.mass_kg = round(self.volume_m3 * self.density_kg_m3, 2)
        if self.thermal_capacity_j_per_k <= 0.0:
            self.thermal_capacity_j_per_k = round(self.mass_kg * self.specific_heat_j_kgk, 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThermalMassDefinition:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            material_id=str(data["material_id"]),
            thickness_m=float(data["thickness_m"]),
            area_m2=float(data["area_m2"]),
            volume_m3=float(data.get("volume_m3", 0.0)),
            density_kg_m3=float(data.get("density_kg_m3", 2300.0)),
            specific_heat_j_kgk=float(data.get("specific_heat_j_kgk", 880.0)),
            mass_kg=float(data.get("mass_kg", 0.0)),
            thermal_capacity_j_per_k=float(data.get("thermal_capacity_j_per_k", 0.0)),
            location=str(data.get("location", "floor_slab")),
            provenance=str(data.get("provenance", DataProvenance.DATABASE)),
        )


@dataclass
class GlazingDefinition:
    """
    Optical and thermal transmittance specification for fenestration.

    SI Units:
        u_value: W/(m²·K) (strictly > 0)
        shgc: dimensionless fraction [0.0, 1.0]
        thickness_m: meters (m, strictly > 0)
        visible_transmittance: dimensionless fraction [0.0, 1.0]
    """
    id: str
    name: str
    u_value: float
    shgc: float
    thickness_m: float
    visible_transmittance: float = 0.80
    is_argon_filled: bool = False
    panes_count: int = 2
    source: str = ""
    notes: str = ""
    provenance: str = DataProvenance.DATABASE

    def __post_init__(self) -> None:
        if self.u_value <= 0.0:
            raise ValueError(f"Glazing U-value must be strictly positive, got {self.u_value}")
        if not (0.0 <= self.shgc <= 1.0):
            raise ValueError(f"SHGC must be between 0.0 and 1.0, got {self.shgc}")
        if not (0.0 <= self.visible_transmittance <= 1.0):
            raise ValueError(f"Visible transmittance must be within [0, 1], got {self.visible_transmittance}")
        if self.thickness_m <= 0.0:
            raise ValueError(f"Glazing thickness must be strictly positive, got {self.thickness_m}")

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.id.lower() == other.lower() or self.name.lower() == other.lower()
        if isinstance(other, GlazingDefinition):
            return self.id == other.id and abs(self.u_value - other.u_value) < 1e-4 and abs(self.shgc - other.shgc) < 1e-4
        return False

    def __str__(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GlazingDefinition:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            u_value=float(data["u_value"]),
            shgc=float(data["shgc"]),
            thickness_m=float(data.get("thickness_m", 0.02)),
            visible_transmittance=float(data.get("visible_transmittance", 0.80)),
            is_argon_filled=bool(data.get("is_argon_filled", False)),
            panes_count=int(data.get("panes_count", 2)),
            source=str(data.get("source", "")),
            notes=str(data.get("notes", "")),
            provenance=str(data.get("provenance", DataProvenance.DATABASE)),
        )


# Standard glazing registry presets
STANDARD_GLAZING_PRESETS: Dict[str, GlazingDefinition] = {
    "single_clear": GlazingDefinition(
        id="single_clear",
        name="Single Clear Float Glass (4mm)",
        u_value=5.8,
        shgc=0.85,
        thickness_m=0.004,
        visible_transmittance=0.90,
    ),
    "double_clear": GlazingDefinition(
        id="double_clear",
        name="Double Glazed Clear (4-12-4 Air)",
        u_value=2.8,
        shgc=0.76,
        thickness_m=0.020,
        visible_transmittance=0.81,
    ),
    "double_low_e": GlazingDefinition(
        id="double_low_e",
        name="Low-E Double Glazing (Argon Gas)",
        u_value=1.8,
        shgc=0.60,
        thickness_m=0.020,
        visible_transmittance=0.75,
        is_argon_filled=True,
    ),
    "triple_low_e": GlazingDefinition(
        id="triple_low_e",
        name="Triple Low-E Glazing (Argon Gas)",
        u_value=0.9,
        shgc=0.45,
        thickness_m=0.036,
        visible_transmittance=0.65,
        is_argon_filled=True,
        panes_count=3,
    ),
}


# =====================================================================
# 6. PASSIVE STRATEGY
# =====================================================================

@dataclass
class PassiveStrategy:
    """
    Architectural passive system specification for heating, cooling, or ventilation.

    Categories:
        - cold_region: solar capture, thermal mass, high insulation, airlock, buffer zones, controlled ventilation
        - hot_dry: night-time cool-air flushing and thermal-mass pre-cooling, shading, reduced solar gain
        - hot_humid: cross ventilation, stack ventilation, shading, high openable area
        - variable_seasonal: adaptive openings, adjustable shading, reversible ventilation
    """
    id: str
    name: str
    category: str  # "cold_region", "hot_dry", "hot_humid", "variable_seasonal"
    climate_applicability: List[str] = field(default_factory=list)
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    affected_openings: List[str] = field(default_factory=list)
    affected_surfaces: List[str] = field(default_factory=list)
    notes: str = ""
    assumptions: str = ""
    provenance: str = DataProvenance.OPTIMIZED

    def __post_init__(self) -> None:
        valid_cats = {"cold_region", "hot_dry", "hot_humid", "variable_seasonal"}
        if self.category.lower() not in valid_cats:
            raise ValueError(f"Invalid strategy category '{self.category}'. Must be one of {valid_cats}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PassiveStrategy:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            category=str(data.get("category", "cold_region")),
            climate_applicability=list(data.get("climate_applicability", [])),
            enabled=bool(data.get("enabled", True)),
            parameters=dict(data.get("parameters", {})),
            affected_openings=list(data.get("affected_openings", [])),
            affected_surfaces=list(data.get("affected_surfaces", [])),
            notes=str(data.get("notes", "")),
            assumptions=str(data.get("assumptions", "")),
            provenance=str(data.get("provenance", DataProvenance.OPTIMIZED)),
        )


# =====================================================================
# 7. SHELTER DESIGN (AUTHORITATIVE CANONICAL DIGITAL TWIN)
# =====================================================================

@dataclass(init=False)
class ShelterDesign:
    """
    Authoritative Canonical Digital Twin Specification for ThermoShelter.
    ====================================================================
    Represents ONE physical shelter design combining:
    - Operational & Occupant Requirements
    - Parametric Geometry & Boundary Metrics
    - Multilayer Wall, Roof, Floor, Door Composite Assemblies (ISO 6946)
    - Glazing & Fenestration Openings
    - Dedicated Sensible Thermal Mass Storage Elements
    - Regional Passive Strategies
    - Spatial Functional Zones

    This model serves as the single source of truth across all subsystems:
    - Member 1 (Climate) -> Target boundary conditions
    - Member 2 (Shelter Design) -> Canonical model authoring
    - Member 3 (Simulation & Optimization) -> Thermal engine input via SimulationAdapter
    - Member 4 (Visualization) -> 3D model & 2D architectural blueprint rendering
    - Member 5 (Integration & QA) -> Full lifecycle compliance
    """
    design_id: str
    name: str
    requirements: ShelterRequirements
    geometry: ShelterGeometry
    wall_assembly: MaterialAssembly
    roof_assembly: MaterialAssembly
    floor_assembly: MaterialAssembly
    glazing: GlazingDefinition
    door_assembly: Optional[MaterialAssembly] = None
    openings: List[OpeningDefinition] = field(default_factory=list)
    zones: List[ZoneDefinition] = field(default_factory=list)
    thermal_mass_elements: List[ThermalMassDefinition] = field(default_factory=list)
    passive_strategies: List[PassiveStrategy] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: str = DataProvenance.USER_DEFINED

    def __init__(
        self,
        design_id: Optional[str] = None,
        name: Optional[str] = None,
        requirements: Optional[ShelterRequirements] = None,
        geometry: Optional[ShelterGeometry] = None,
        wall_assembly: Optional[MaterialAssembly] = None,
        roof_assembly: Optional[MaterialAssembly] = None,
        floor_assembly: Optional[MaterialAssembly] = None,
        glazing: Optional[Union[GlazingDefinition, str]] = None,
        door_assembly: Optional[MaterialAssembly] = None,
        openings: Optional[List[OpeningDefinition]] = None,
        zones: Optional[List[ZoneDefinition]] = None,
        thermal_mass_elements: Optional[List[ThermalMassDefinition]] = None,
        passive_strategies: Optional[List[PassiveStrategy]] = None,
        version: str = "1.0.0",
        created_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provenance: str = DataProvenance.USER_DEFINED,
        **kwargs: Any,
    ) -> None:
        """
        Supports both canonical hierarchical instantiation and legacy flat keyword instantiation.
        """
        # 1. Canonical instantiation path
        if (
            requirements is not None
            and geometry is not None
            and wall_assembly is not None
            and roof_assembly is not None
            and floor_assembly is not None
        ):
            self.design_id = str(design_id or "shelter_canonical_001")
            self.name = str(name or "Canonical Shelter Design")
            self.requirements = requirements
            self.geometry = geometry
            self.wall_assembly = wall_assembly
            self.roof_assembly = roof_assembly
            self.floor_assembly = floor_assembly
            self.door_assembly = door_assembly

            # Resolve glazing
            if isinstance(glazing, GlazingDefinition):
                self.glazing = glazing
            elif isinstance(glazing, str):
                self.glazing = STANDARD_GLAZING_PRESETS.get(
                    glazing.lower(),
                    GlazingDefinition(id=glazing, name=glazing, u_value=2.8, shgc=0.76, thickness_m=0.02)
                )
            else:
                self.glazing = STANDARD_GLAZING_PRESETS["double_clear"]

            self.openings = list(openings if openings is not None else geometry.openings)
            self.zones = list(zones if zones is not None else geometry.zones)
            self.thermal_mass_elements = list(thermal_mass_elements or [])
            self.passive_strategies = list(passive_strategies or [])
            self.version = str(version)
            self.created_at = str(created_at or datetime.now(timezone.utc).isoformat())
            self.metadata = dict(metadata or {})
            self.provenance = str(provenance)

        # 2. Legacy flat keyword synthesis path
        else:
            length = float(kwargs.get("length", 4.0))
            width = float(kwargs.get("width", 3.0))
            height = float(kwargs.get("height", 2.8))
            if length <= 0.0:
                raise ValueError(f"Shelter length must be strictly positive, got {length} m")
            if width <= 0.0:
                raise ValueError(f"Shelter width must be strictly positive, got {width} m")
            if height <= 0.0:
                raise ValueError(f"Shelter height must be strictly positive, got {height} m")

            shelter_type = str(kwargs.get("shelter_type", kwargs.get("home_type", "Permanent")))
            if shelter_type.lower() not in {"permanent", "temporary"}:
                raise ValueError(f"shelter_type must be 'Permanent' or 'Temporary', got '{shelter_type}'")

            gross_wall = 2.0 * (length + width) * height
            window_area = float(kwargs.get("window_area", kwargs.get("window_area_m2", 2.0)))
            if window_area < 0.0:
                raise ValueError(f"Window area cannot be negative, got {window_area} m²")
            if window_area > gross_wall:
                raise ValueError(
                    f"Window area ({window_area} m²) cannot exceed total wall area ({gross_wall:.2f} m²)"
                )

            wall_thickness_m = float(kwargs.get("wall_thickness_m", 0.23))
            if wall_thickness_m < 0.0:
                raise ValueError(f"Wall thickness cannot be negative, got {wall_thickness_m} m")

            insulation_thickness_m = float(kwargs.get("insulation_thickness_m", 0.0))
            if insulation_thickness_m < 0.0:
                raise ValueError(f"Insulation thickness cannot be negative, got {insulation_thickness_m} m")

            insulation_conductivity = float(kwargs.get("insulation_conductivity", 0.025))
            if insulation_conductivity <= 0.0:
                raise ValueError(f"Insulation conductivity must be > 0, got {insulation_conductivity} W/m·K")

            roof_thickness_m = float(kwargs.get("roof_thickness_m", 0.15))
            if roof_thickness_m < 0.0:
                raise ValueError(f"Roof thickness cannot be negative, got {roof_thickness_m} m")

            roof_conductivity = float(kwargs.get("roof_conductivity", 0.50))
            if roof_conductivity <= 0.0:
                raise ValueError(f"Roof conductivity must be > 0, got {roof_conductivity} W/m·K")

            roof_insulation_m = float(kwargs.get("roof_insulation_m", 0.0))
            if roof_insulation_m < 0.0:
                raise ValueError(f"Roof insulation cannot be negative, got {roof_insulation_m} m")

            roof_type = str(kwargs.get("roof_type", "flat"))
            pitch_angle_deg = float(kwargs.get("pitch_angle_deg", 30.0 if roof_type.lower() == "pitched" else 0.0))
            if not (0.0 <= pitch_angle_deg < 90.0):
                raise ValueError(f"Roof pitch angle must be in [0, 90) degrees, got {pitch_angle_deg}")

            shgc_val = float(kwargs["shgc"]) if kwargs.get("shgc") is not None else None
            if shgc_val is not None and not (0.0 <= shgc_val <= 1.0):
                raise ValueError(f"SHGC must be between 0.0 and 1.0, got {shgc_val}")

            ach_val = float(kwargs.get("ach", DEFAULT_ACH))
            if ach_val < 0.0:
                raise ValueError(f"ACH cannot be negative, got {ach_val}")

            occupants_val = int(kwargs.get("occupants", 2))
            if occupants_val < 0:
                raise ValueError(f"Occupants cannot be negative, got {occupants_val}")

            heat_per_person_val = float(kwargs.get("heat_per_person", DEFAULT_OCCUPANT_HEAT_GAIN))
            if heat_per_person_val < 0.0:
                raise ValueError(f"Heat per person cannot be negative, got {heat_per_person_val} W")

            # Orientation normalization
            ori_raw = kwargs.get("orientation", "south")
            if isinstance(ori_raw, (int, float)):
                ori_deg = float(ori_raw) % 360.0
            else:
                deg_map = {"north": 0.0, "east": 90.0, "south": 180.0, "west": 270.0}
                ori_deg = deg_map.get(str(ori_raw).lower(), 180.0)

            # Build constituent components
            req = ShelterRequirements(
                occupants=max(1, occupants_val),
                shelter_purpose="general",
                permanence=shelter_type.lower(),
                constraints={"ach": ach_val, "heat_per_person": heat_per_person_val},
            )

            # Openings
            openings_synth: List[OpeningDefinition] = []
            if window_area > 0.0:
                w_win = round(math.sqrt(window_area * 1.25), 2)
                h_win = round(window_area / w_win, 2)
                openings_synth.append(
                    OpeningDefinition(
                        id="win_primary",
                        name="Primary Fenestration",
                        opening_type="window",
                        width_m=w_win,
                        height_m=h_win,
                        area_m2=window_area,
                        facade="south" if ori_deg == 180.0 else "facade",
                        orientation_deg=ori_deg,
                        shading_factor=1.0,
                    )
                )

            geom = ShelterGeometry(
                geometry_type="rectangular",
                length_m=length,
                width_m=width,
                height_m=height,
                roof_type=roof_type,
                roof_pitch_deg=pitch_angle_deg,
                orientation_deg=ori_deg,
                openings=openings_synth,
            )

            # Glazing
            glaze_arg = kwargs.get("glazing", glazing or "double_clear")
            if isinstance(glaze_arg, GlazingDefinition):
                glaze_def = glaze_arg
            elif isinstance(glaze_arg, str):
                base_glaze = STANDARD_GLAZING_PRESETS.get(glaze_arg.lower(), STANDARD_GLAZING_PRESETS["double_clear"])
                if shgc_val is not None:
                    glaze_def = GlazingDefinition(
                        id=base_glaze.id,
                        name=base_glaze.name,
                        u_value=base_glaze.u_value,
                        shgc=shgc_val,
                        thickness_m=base_glaze.thickness_m,
                    )
                else:
                    glaze_def = base_glaze
            else:
                glaze_def = STANDARD_GLAZING_PRESETS["double_clear"]

            # Wall Assembly
            wall_mat = str(kwargs.get("wall_material", kwargs.get("wall_material_name", "brick")))
            mat_k = 0.72 if "brick" in wall_mat.lower() else (0.13 if "timber" in wall_mat.lower() else 0.50)
            wall_layers = [
                MaterialLayer(
                    material_id=wall_mat,
                    name=wall_mat.title(),
                    thickness_m=max(0.01, wall_thickness_m),
                    conductivity_w_mk=mat_k,
                    density_kg_m3=1800.0,
                    specific_heat_j_kgk=900.0,
                )
            ]
            if insulation_thickness_m > 0.0:
                wall_layers.append(
                    MaterialLayer(
                        material_id="puf_insulation",
                        name="PUF Insulation Board",
                        thickness_m=insulation_thickness_m,
                        conductivity_w_mk=insulation_conductivity,
                        density_kg_m3=35.0,
                        specific_heat_j_kgk=1400.0,
                    )
                )
            wall_asm = MaterialAssembly(
                assembly_id="wall_asm",
                name="Wall Assembly",
                category="wall",
                layers=wall_layers,
            )

            # Roof Assembly
            roof_layers = [
                MaterialLayer(
                    material_id="roof_structure",
                    name="Roof Deck",
                    thickness_m=max(0.01, roof_thickness_m),
                    conductivity_w_mk=roof_conductivity,
                    density_kg_m3=1400.0,
                    specific_heat_j_kgk=1000.0,
                )
            ]
            if roof_insulation_m > 0.0:
                roof_layers.append(
                    MaterialLayer(
                        material_id="roof_insulation",
                        name="Roof Insulation Board",
                        thickness_m=roof_insulation_m,
                        conductivity_w_mk=insulation_conductivity,
                        density_kg_m3=35.0,
                        specific_heat_j_kgk=1400.0,
                    )
                )
            roof_asm = MaterialAssembly(
                assembly_id="roof_asm",
                name="Roof Assembly",
                category="roof",
                layers=roof_layers,
            )

            # Floor Assembly
            floor_asm = MaterialAssembly(
                assembly_id="floor_asm",
                name="Floor Slab",
                category="floor",
                layers=[
                    MaterialLayer(
                        material_id="concrete_slab",
                        name="Ground Slab",
                        thickness_m=0.15,
                        conductivity_w_mk=1.40,
                        density_kg_m3=2300.0,
                        specific_heat_j_kgk=880.0,
                    )
                ],
            )

            self.design_id = str(design_id or "synthesized_design")
            self.name = str(name or f"{shelter_type} Shelter Design")
            self.requirements = req
            self.geometry = geom
            self.wall_assembly = wall_asm
            self.roof_assembly = roof_asm
            self.floor_assembly = floor_asm
            self.door_assembly = None
            self.glazing = glaze_def
            self.openings = openings_synth
            self.zones = []
            self.thermal_mass_elements = []
            self.passive_strategies = []
            self.version = str(version)
            self.created_at = str(created_at or "2026-01-01T00:00:00+00:00")
            self.provenance = str(provenance)
            self.metadata = {
                "wall_material": wall_mat,
                "wall_thickness_m": wall_thickness_m,
                "roof_thickness_m": roof_thickness_m,
                "shelter_model": kwargs.get("shelter_model", f"rectangular_{roof_type}"),
                "heat_per_person": heat_per_person_val,
                "ach": ach_val,
                "orientation": ori_raw,
                "insulation_thickness_m": insulation_thickness_m,
                "insulation_conductivity": insulation_conductivity,
                "roof_insulation_m": roof_insulation_m,
                "roof_conductivity": roof_conductivity,
                "shelter_type": shelter_type,
            }

    # =================================================================
    # BACKWARD COMPATIBILITY PROPERTIES & CONVENIENCE ACCESSORS
    # =================================================================

    @property
    def length(self) -> float:
        return self.geometry.length_m

    @property
    def width(self) -> float:
        return self.geometry.width_m

    @property
    def height(self) -> float:
        return self.geometry.height_m

    @property
    def wall_material(self) -> str:
        if "wall_material" in self.metadata:
            return str(self.metadata["wall_material"])
        if self.wall_assembly and self.wall_assembly.layers:
            return self.wall_assembly.layers[0].material_id
        return "brick"

    @property
    def wall_thickness_m(self) -> float:
        if "wall_thickness_m" in self.metadata:
            return float(self.metadata["wall_thickness_m"])
        if self.wall_assembly and self.wall_assembly.layers:
            return self.wall_assembly.layers[0].thickness_m
        return self.wall_assembly.total_thickness_m

    @property
    def insulation_thickness_m(self) -> float:
        if "insulation_thickness_m" in self.metadata:
            return float(self.metadata["insulation_thickness_m"])
        if self.wall_assembly and len(self.wall_assembly.layers) > 1:
            for layer in self.wall_assembly.layers[1:]:
                if any(k in layer.material_id.lower() for k in ("insul", "puf", "eps", "xps", "wool", "cork")):
                    return layer.thickness_m
            return self.wall_assembly.layers[1].thickness_m
        return 0.0

    @property
    def insulation_conductivity(self) -> float:
        if "insulation_conductivity" in self.metadata:
            return float(self.metadata["insulation_conductivity"])
        if self.wall_assembly and len(self.wall_assembly.layers) > 1:
            for layer in self.wall_assembly.layers[1:]:
                if any(k in layer.material_id.lower() for k in ("insul", "puf", "eps", "xps", "wool", "cork")):
                    return layer.conductivity_w_mk
            return self.wall_assembly.layers[1].conductivity_w_mk
        return 0.025

    @property
    def roof_type(self) -> str:
        return self.geometry.roof_type

    @property
    def pitch_angle_deg(self) -> float:
        return self.geometry.roof_pitch_deg

    @property
    def roof_thickness_m(self) -> float:
        if "roof_thickness_m" in self.metadata:
            return float(self.metadata["roof_thickness_m"])
        if self.roof_assembly and self.roof_assembly.layers:
            return self.roof_assembly.layers[0].thickness_m
        return self.roof_assembly.total_thickness_m

    @property
    def roof_conductivity(self) -> float:
        if "roof_conductivity" in self.metadata:
            return float(self.metadata["roof_conductivity"])
        if self.roof_assembly and self.roof_assembly.layers:
            return self.roof_assembly.layers[0].conductivity_w_mk
        return 0.50

    @property
    def roof_insulation_m(self) -> float:
        if "roof_insulation_m" in self.metadata:
            return float(self.metadata["roof_insulation_m"])
        if self.roof_assembly and len(self.roof_assembly.layers) > 1:
            for layer in self.roof_assembly.layers[1:]:
                if any(k in layer.material_id.lower() for k in ("insul", "puf", "eps", "xps", "wool", "cork")):
                    return layer.thickness_m
        return 0.0

    @property
    def window_area(self) -> float:
        if self.openings:
            w_area = sum(o.area_m2 for o in self.openings if o.opening_type == "window")
            if w_area > 0.0:
                return round(w_area, 4)
        if "window_area" in self.metadata:
            return float(self.metadata["window_area"])
        return 0.0

    @property
    def shgc(self) -> float:
        return self.glazing.shgc

    @property
    def orientation(self) -> Union[str, float]:
        if "orientation" in self.metadata and isinstance(self.metadata["orientation"], str):
            return self.metadata["orientation"]
        deg = self.geometry.orientation_deg
        deg_map = {0.0: "north", 90.0: "east", 180.0: "south", 270.0: "west", 360.0: "north"}
        return deg_map.get(round(deg, 1), deg)

    @property
    def ach(self) -> float:
        if "ach" in self.metadata:
            return float(self.metadata["ach"])
        if "ach" in self.requirements.constraints:
            return float(self.requirements.constraints["ach"])
        return DEFAULT_ACH

    @property
    def occupants(self) -> int:
        return self.requirements.occupants

    @property
    def shelter_type(self) -> str:
        if "shelter_type" in self.metadata:
            return str(self.metadata["shelter_type"])
        return self.requirements.permanence.capitalize()

    @property
    def shelter_model(self) -> Optional[str]:
        if "shelter_model" in self.metadata:
            return str(self.metadata["shelter_model"])
        return f"{self.geometry.geometry_type}_{self.geometry.roof_type}"

    @property
    def heat_per_person(self) -> float:
        return float(self.metadata.get("heat_per_person", DEFAULT_OCCUPANT_HEAT_GAIN))

    # =================================================================
    # SERIALIZATION
    # =================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire canonical design tree into a JSON-compliant Python dict."""
        return {
            "design_id": self.design_id,
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "provenance": self.provenance,
            "requirements": self.requirements.to_dict(),
            "geometry": self.geometry.to_dict(),
            "wall_assembly": self.wall_assembly.to_dict(),
            "roof_assembly": self.roof_assembly.to_dict(),
            "floor_assembly": self.floor_assembly.to_dict(),
            "door_assembly": self.door_assembly.to_dict() if self.door_assembly else None,
            "glazing": self.glazing.to_dict(),
            "openings": [o.to_dict() for o in self.openings],
            "zones": [z.to_dict() for z in self.zones],
            "thermal_mass_elements": [t.to_dict() for t in self.thermal_mass_elements],
            "passive_strategies": [p.to_dict() for p in self.passive_strategies],
            "metadata": self.metadata,
            # Top-level legacy aliases for seamless backward compatibility
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "wall_material": self.wall_material,
            "wall_thickness_m": self.wall_thickness_m,
            "insulation_thickness_m": self.insulation_thickness_m,
            "insulation_conductivity": self.insulation_conductivity,
            "roof_type": self.roof_type,
            "pitch_angle_deg": self.pitch_angle_deg,
            "roof_thickness_m": self.roof_thickness_m,
            "roof_conductivity": self.roof_conductivity,
            "roof_insulation_m": self.roof_insulation_m,
            "window_area": self.window_area,
            "glazing_type": self.glazing.id,
            "shgc": self.shgc,
            "orientation": self.orientation,
            "ach": self.ach,
            "occupants": self.occupants,
            "shelter_type": self.shelter_type,
            "heat_per_person": self.heat_per_person,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes ShelterDesign to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShelterDesign:
        """Deserializes a dictionary into a validated ShelterDesign domain model."""
        if "requirements" in data and "geometry" in data and "wall_assembly" in data:
            requirements = ShelterRequirements.from_dict(data["requirements"])
            geometry = ShelterGeometry.from_dict(data["geometry"])
            wall_assembly = MaterialAssembly.from_dict(data["wall_assembly"])
            roof_assembly = MaterialAssembly.from_dict(data["roof_assembly"])
            floor_assembly = MaterialAssembly.from_dict(data["floor_assembly"])
            door_assembly = (
                MaterialAssembly.from_dict(data["door_assembly"])
                if data.get("door_assembly")
                else None
            )
            glazing_raw = data.get("glazing", {})
            if isinstance(glazing_raw, dict):
                glazing = GlazingDefinition.from_dict(glazing_raw)
            elif isinstance(glazing_raw, str):
                glazing = STANDARD_GLAZING_PRESETS.get(
                    glazing_raw.lower(),
                    GlazingDefinition(id=glazing_raw, name=glazing_raw, u_value=2.8, shgc=0.76, thickness_m=0.02)
                )
            else:
                glazing = STANDARD_GLAZING_PRESETS["double_clear"]

            openings = [OpeningDefinition.from_dict(o) for o in data.get("openings", [])]
            zones = [ZoneDefinition.from_dict(z) for z in data.get("zones", [])]
            thermal_mass = [ThermalMassDefinition.from_dict(t) for t in data.get("thermal_mass_elements", [])]
            passive_strategies = [PassiveStrategy.from_dict(p) for p in data.get("passive_strategies", [])]

            return cls(
                design_id=str(data.get("design_id", "shelter_canonical_001")),
                name=str(data.get("name", data.get("design_id", "Canonical Shelter"))),
                requirements=requirements,
                geometry=geometry,
                wall_assembly=wall_assembly,
                roof_assembly=roof_assembly,
                floor_assembly=floor_assembly,
                glazing=glazing,
                door_assembly=door_assembly,
                openings=openings,
                zones=zones,
                thermal_mass_elements=thermal_mass,
                passive_strategies=passive_strategies,
                version=str(data.get("version", "1.0.0")),
                created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
                metadata=dict(data.get("metadata", {})),
                provenance=str(data.get("provenance", DataProvenance.USER_DEFINED)),
            )
        else:
            return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> ShelterDesign:
        """Parses a JSON string and creates a ShelterDesign instance."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_simulation_parameters(self) -> Dict[str, Any]:
        """Extracts equivalent lumped thermal parameters for numerical simulation."""
        gross_wall = self.geometry.gross_wall_area_m2 or (2.0 * (self.geometry.length_m + self.geometry.width_m) * self.geometry.height_m)
        roof_area = self.geometry.roof_area_m2 or (self.geometry.length_m * self.geometry.width_m)
        floor_area = self.geometry.floor_area_m2 or (self.geometry.length_m * self.geometry.width_m)
        vol = self.geometry.volume_m3 or (floor_area * self.geometry.height_m)

        c_wall = self.wall_assembly.heat_capacity_per_m2 * gross_wall
        c_roof = self.roof_assembly.heat_capacity_per_m2 * roof_area
        c_floor = self.floor_assembly.heat_capacity_per_m2 * floor_area
        c_mass = sum(tm.thermal_capacity_j_per_k for tm in self.thermal_mass_elements)
        total_capacity = c_wall + c_roof + c_floor + c_mass
        if total_capacity <= 0.0:
            total_capacity = 1.0e7

        return {
            "wall_u_value": self.wall_assembly.u_value,
            "roof_u_value": self.roof_assembly.u_value,
            "floor_u_value": self.floor_assembly.u_value,
            "window_u_value": self.glazing.u_value,
            "window_shgc": self.glazing.shgc,
            "window_area_m2": self.window_area,
            "gross_wall_area_m2": gross_wall,
            "roof_area_m2": roof_area,
            "floor_area_m2": floor_area,
            "volume_m3": vol,
            "effective_thermal_capacity_j_k": total_capacity,
            "orientation_deg": self.geometry.orientation_deg,
            "ach": self.ach,
            "occupants": self.occupants,
            "heat_per_person": self.heat_per_person,
            "roof_type": self.roof_type,
            "pitch_angle_deg": self.pitch_angle_deg,
        }
