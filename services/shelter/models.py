"""
THERMOSHELTER AI — Canonical Data Contracts (Member 2)
======================================================
Formal domain models and shared contracts for geometry, multi-layer envelope
assemblies, thermal mass, glazing, openings, passive strategies, and the
composite ShelterDesign object.

All models are serializable to/from JSON and Python dictionaries with complete
field validation and SI units.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


# =====================================================================
# 1. SHELTER REQUIREMENTS
# =====================================================================

@dataclass
class ShelterRequirements:
    """
    High-level operational, occupant, and contextual requirements for the shelter.

    Units:
        occupants: integer count (persons)
        duration_days: days (or None for permanent)
    """
    occupants: int
    shelter_purpose: str  # e.g. "emergency_relief", "high_altitude_post", "field_station", "residence"
    duration_days: Optional[int] = None
    permanence: str = "permanent"  # "temporary", "semi_permanent", "permanent"
    mobility: str = "permanent"  # "mobile", "demountable", "permanent"
    priorities: List[str] = field(default_factory=list)  # e.g. ["thermal_comfort", "speed_of_assembly"]
    available_resources: List[str] = field(default_factory=list)  # e.g. ["local_stone", "mud", "timber"]
    energy_sources: List[str] = field(default_factory=list)  # e.g. ["passive_solar", "biomass"]
    constraints: Dict[str, Any] = field(default_factory=dict)

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
        )


# =====================================================================
# 2. OPENINGS & ZONES
# =====================================================================

@dataclass
class OpeningDefinition:
    """
    Physical fenestration or aperture in the building envelope.

    Units:
        width_m, height_m: meters (m)
        area_m2: square meters (m²)
        orientation_deg: azimuth degrees (0°=N, 90°=E, 180°=S, 270°=W)
        overhang_depth_m: meters (m)
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
    shading_factor: float = 1.0  # 0.0 to 1.0 (1.0 = unshaded)
    overhang_depth_m: float = 0.0
    ventilation_role: str = "none"  # "inlet", "outlet", "bypass", "night_purge", "none"

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
        )


@dataclass
class ZoneDefinition:
    """
    Sub-divided spatial functional zone within the shelter envelope.

    Units:
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
        )


# =====================================================================
# 3. SHELTER GEOMETRY
# =====================================================================

@dataclass
class ShelterGeometry:
    """
    Complete geometric definition and derived boundary metrics for a shelter.

    Units:
        length_m, width_m, height_m: m
        orientation_deg: degrees azimuth (0°=North, 90°=East, 180°=South, 270°=West)
        roof_pitch_deg: slope angle in degrees
        areas: m²
        volume_m3: m³
        surface_to_volume_ratio: 1/m (m²/m³)
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

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
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
        )


# =====================================================================
# 4. MATERIALS & MULTILAYER ENVELOPE
# =====================================================================

@dataclass
class MaterialLayer:
    """
    Homogeneous material layer in a series composite assembly.

    Units:
        thickness_m: m
        conductivity_w_mk: W/(m·K)
        density_kg_m3: kg/m³
        specific_heat_j_kgk: J/(kg·K)
        emissivity, solar_absorptivity: dimensionless fraction (0.0 to 1.0)
        cost_estimate_usd: USD per m³ (or USD/m² if thin)
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

    def __post_init__(self) -> None:
        if self.thickness_m <= 0.0:
            raise ValueError(f"Layer thickness must be strictly positive, got {self.thickness_m}")
        if self.conductivity_w_mk <= 0.0:
            raise ValueError(f"Conductivity must be strictly positive, got {self.conductivity_w_mk}")
        if self.density_kg_m3 <= 0.0:
            raise ValueError(f"Density must be strictly positive, got {self.density_kg_m3}")
        if self.specific_heat_j_kgk <= 0.0:
            raise ValueError(f"Specific heat must be strictly positive, got {self.specific_heat_j_kgk}")
        if not (0.0 <= self.emissivity <= 1.0):
            raise ValueError(f"Emissivity must be between 0.0 and 1.0, got {self.emissivity}")
        if not (0.0 <= self.solar_absorptivity <= 1.0):
            raise ValueError(f"Solar absorptivity must be between 0.0 and 1.0, got {self.solar_absorptivity}")

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
        )


@dataclass
class MaterialAssembly:
    """
    Multi-layer composite assembly for wall, roof, floor, or door.
    Layers are ordered from Interior to Exterior.

    Units:
        resistances: m²·K/W
        u_value: W/(m²·K)
        total_thickness_m: m
        total_mass_per_m2: kg/m²
        heat_capacity_per_m2: J/(m²·K)
    """
    assembly_id: str
    name: str
    category: str  # "wall", "roof", "floor", "door"
    layers: List[MaterialLayer] = field(default_factory=list)
    r_inside: float = 0.13  # ISO 6946 interior surface film resistance
    r_outside: float = 0.04  # ISO 6946 exterior surface film resistance
    r_layers: float = 0.0
    r_total: float = 0.0
    u_value: float = 0.0
    total_thickness_m: float = 0.0
    total_mass_per_m2: float = 0.0
    heat_capacity_per_m2: float = 0.0

    def __post_init__(self) -> None:
        if self.r_inside < 0.0 or self.r_outside < 0.0:
            raise ValueError("Film resistances cannot be negative.")
        valid_cats = {"wall", "roof", "floor", "door"}
        if self.category.lower() not in valid_cats:
            raise ValueError(f"Invalid assembly category '{self.category}'. Must be one of {valid_cats}")

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
        )


# =====================================================================
# 5. THERMAL MASS & GLAZING
# =====================================================================

@dataclass
class ThermalMassDefinition:
    """
    Dedicated sensible thermal storage mass element (e.g. Trombe wall, floor slab, water wall).

    Units:
        thickness_m: m
        area_m2: m²
        volume_m3: m³
        density_kg_m3: kg/m³
        specific_heat_j_kgk: J/(kg·K)
        mass_kg: kg
        thermal_capacity_j_per_k: J/K
    """
    id: str
    name: str
    material_id: str
    thickness_m: float
    area_m2: float
    volume_m3: float
    density_kg_m3: float
    specific_heat_j_kgk: float
    mass_kg: float
    thermal_capacity_j_per_k: float
    location: str = "floor_slab"  # "floor_slab", "trombe_wall", "internal_wall", "core"

    def __post_init__(self) -> None:
        if self.area_m2 <= 0.0 or self.thickness_m <= 0.0:
            raise ValueError("Thermal mass area and thickness must be strictly positive.")
        if self.density_kg_m3 <= 0.0 or self.specific_heat_j_kgk <= 0.0:
            raise ValueError("Thermal mass density and specific heat must be strictly positive.")

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
            volume_m3=float(data.get("volume_m3", float(data["area_m2"]) * float(data["thickness_m"]))),
            density_kg_m3=float(data["density_kg_m3"]),
            specific_heat_j_kgk=float(data["specific_heat_j_kgk"]),
            mass_kg=float(data.get("mass_kg", 0.0)),
            thermal_capacity_j_per_k=float(data.get("thermal_capacity_j_per_k", 0.0)),
            location=str(data.get("location", "floor_slab")),
        )


@dataclass
class GlazingDefinition:
    """
    Optical and thermal transmittance specification for fenestration.

    Units:
        u_value: W/(m²·K)
        shgc: dimensionless fraction (0.0 to 1.0)
        thickness_m: m
        visible_transmittance: dimensionless fraction (0.0 to 1.0)
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

    def __post_init__(self) -> None:
        if self.u_value <= 0.0:
            raise ValueError(f"Glazing U-value must be strictly positive, got {self.u_value}")
        if not (0.0 <= self.shgc <= 1.0):
            raise ValueError(f"SHGC must be between 0.0 and 1.0, got {self.shgc}")
        if not (0.0 <= self.visible_transmittance <= 1.0):
            raise ValueError(f"Visible transmittance must be within [0, 1], got {self.visible_transmittance}")
        if self.thickness_m <= 0.0:
            raise ValueError(f"Glazing thickness must be strictly positive, got {self.thickness_m}")

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
        )


# =====================================================================
# 6. PASSIVE STRATEGY
# =====================================================================

@dataclass
class PassiveStrategy:
    """
    Architectural passive system specification for heating, cooling, or ventilation.

    Categories:
        - cold_region: solar capture, thermal mass, high insulation, airlock, buffer zones, controlled ventilation
        - hot_dry: night-time cool-air flushing and thermal-mass pre-cooling, shading, reduced solar gain, controlled openings
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
        )


# =====================================================================
# 7. SHELTER DESIGN (CANONICAL COMPOSITE ARTIFACT)
# =====================================================================

@dataclass
class ShelterDesign:
    """
    Primary canonical digital twin specification combining:
    - Requirements
    - Parametric Geometry
    - Multilayer Wall, Roof, Floor, Door Assemblies
    - Glazing & Openings
    - Thermal Mass Elements
    - Passive Strategies
    - Functional Zones

    This is the primary integration contract consumed by:
    - Member 3: Thermal digital twin & optimization simulation
    - Member 4: 3D visualizer & 2D architectural blueprint generator
    - Member 5: System integration & QA validation
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

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire design tree into a JSON-compliant Python dict."""
        return {
            "design_id": self.design_id,
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
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
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes ShelterDesign to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShelterDesign:
        """Deserializes a dictionary into a validated ShelterDesign domain model."""
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
        glazing = GlazingDefinition.from_dict(data["glazing"])
        openings = [OpeningDefinition.from_dict(o) for o in data.get("openings", [])]
        zones = [ZoneDefinition.from_dict(z) for z in data.get("zones", [])]
        thermal_mass = [ThermalMassDefinition.from_dict(t) for t in data.get("thermal_mass_elements", [])]
        passive_strategies = [PassiveStrategy.from_dict(p) for p in data.get("passive_strategies", [])]

        return cls(
            design_id=str(data["design_id"]),
            name=str(data.get("name", data["design_id"])),
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
        )

    @classmethod
    def from_json(cls, json_str: str) -> ShelterDesign:
        """Parses a JSON string and creates a ShelterDesign instance."""
        data = json.loads(json_str)
        return cls.from_dict(data)
