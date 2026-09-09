"""
THERMOSHELTER AI — Material & Envelope Engine (Member 2)
========================================================
Multilayer envelope assemblies, ISO 6946 thermal transmittance (U-value),
areal heat capacitance, material database bridge, sensible thermal mass storage,
and fenestration/glazing specifications.

Conforms to:
- ISO 6946 Building components and building elements — Thermal resistance and thermal transmittance
- IS 3792 Guide for heat insulation of buildings
- CODATA & ASHRAE Fundamentals thermophysical properties
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from services.formula_constants import (
    DEFAULT_R_INSIDE_HORIZONTAL,
    DEFAULT_R_INSIDE_VERTICAL,
    DEFAULT_R_OUTSIDE_HORIZONTAL,
    DEFAULT_R_OUTSIDE_VERTICAL,
)
import services.thermal as legacy_thermal
from services.material_service import get_material, load_all_materials
import data_loader
from services.shelter.models import (
    GlazingDefinition,
    MaterialAssembly,
    MaterialLayer,
    ThermalMassDefinition,
)

# Standard boundary film resistances (ISO 6946 / IS 3792) in m²·K/W
SURFACE_FILM_RESISTANCES: Dict[str, Tuple[float, float]] = {
    "wall": (DEFAULT_R_INSIDE_VERTICAL, DEFAULT_R_OUTSIDE_VERTICAL),       # 0.13, 0.04
    "roof": (DEFAULT_R_INSIDE_HORIZONTAL, DEFAULT_R_OUTSIDE_HORIZONTAL),   # 0.10, 0.04
    "floor": (0.17, 0.04),                                                 # 0.17 (downward), 0.04 (exterior/subfloor)
    "door": (DEFAULT_R_INSIDE_VERTICAL, DEFAULT_R_OUTSIDE_VERTICAL),       # 0.13, 0.04
}


def create_material_layer(
    material_id: str,
    thickness_m: float,
    name: Optional[str] = None,
    conductivity_w_mk: Optional[float] = None,
    density_kg_m3: Optional[float] = None,
    specific_heat_j_kgk: Optional[float] = None,
    emissivity: float = 0.90,
    solar_absorptivity: float = 0.70,
    cost_estimate_usd: float = 0.0,
    data_status: str = "literature/reference",
    source: str = "",
) -> MaterialLayer:
    """
    Creates a homogeneous material layer. If thermophysical properties are omitted,
    they are automatically queried and populated from the curated materials database.
    """
    if thickness_m <= 0.0:
        raise ValueError(f"Layer thickness must be strictly positive (>0), got {thickness_m} m")

    mat_record = get_material(material_id)
    if "error" not in mat_record:
        k = conductivity_w_mk if conductivity_w_mk is not None else float(mat_record.get("thermal_conductivity", 0.72))
        rho = density_kg_m3 if density_kg_m3 is not None else float(mat_record.get("density", 1800.0))
        cp = specific_heat_j_kgk if specific_heat_j_kgk is not None else float(mat_record.get("specific_heat", 900.0))
        eps = emissivity if emissivity != 0.90 else float(mat_record.get("emissivity", 0.90))
        alpha = solar_absorptivity if solar_absorptivity != 0.70 else float(mat_record.get("solar_absorptivity", 0.70))
        cost = cost_estimate_usd if cost_estimate_usd > 0 else float(mat_record.get("cost_estimate", 0.0))
        layer_name = name or mat_record.get("name", material_id.replace("_", " ").title())
        src = source or mat_record.get("source", "ThermoShelter Materials DB")
        status = data_status
    else:
        # Fallback to user-supplied parameters
        if conductivity_w_mk is None or density_kg_m3 is None or specific_heat_j_kgk is None:
            raise ValueError(
                f"Material '{material_id}' not found in database. Must supply "
                f"conductivity_w_mk, density_kg_m3, and specific_heat_j_kgk explicitly."
            )
        k = conductivity_w_mk
        rho = density_kg_m3
        cp = specific_heat_j_kgk
        eps = emissivity
        alpha = solar_absorptivity
        cost = cost_estimate_usd
        layer_name = name or material_id.replace("_", " ").title()
        src = source or "User-defined"
        status = "user-defined"

    return MaterialLayer(
        material_id=material_id,
        name=layer_name,
        thickness_m=thickness_m,
        conductivity_w_mk=k,
        density_kg_m3=rho,
        specific_heat_j_kgk=cp,
        emissivity=eps,
        solar_absorptivity=alpha,
        cost_estimate_usd=cost,
        data_status=status,
        source=src,
    )


def calculate_assembly_metrics(
    layers: List[MaterialLayer],
    category: str = "wall",
    r_inside: Optional[float] = None,
    r_outside: Optional[float] = None,
) -> Dict[str, float]:
    """
    Computes ISO 6946 multi-layer composite assembly performance metrics:
    - R_layers = sum(d_i / k_i)
    - R_total = R_in + R_layers + R_out
    - U_value = 1 / R_total
    - Total thickness, areal mass, areal heat capacity
    """
    if not layers:
        raise ValueError("Cannot calculate assembly metrics for an empty list of layers.")

    default_rin, default_rout = SURFACE_FILM_RESISTANCES.get(
        category.lower(), (DEFAULT_R_INSIDE_VERTICAL, DEFAULT_R_OUTSIDE_VERTICAL)
    )
    rin = r_inside if r_inside is not None else default_rin
    rout = r_outside if r_outside is not None else default_rout

    if rin < 0.0 or rout < 0.0:
        raise ValueError(f"Film resistances cannot be negative (R_in={rin}, R_out={rout})")

    r_layers = 0.0
    total_thickness = 0.0
    total_mass_per_m2 = 0.0
    heat_capacity_per_m2 = 0.0

    for layer in layers:
        r_layers += layer.resistance_m2_k_w
        total_thickness += layer.thickness_m
        total_mass_per_m2 += layer.mass_per_m2_kg
        heat_capacity_per_m2 += layer.heat_capacity_per_m2_j_k

    r_total = rin + r_layers + rout
    if r_total <= 0.0:
        raise ValueError("Total thermal resistance cannot be <= 0.")

    u_val = 1.0 / r_total

    return {
        "r_inside": round(rin, 4),
        "r_outside": round(rout, 4),
        "r_layers": round(r_layers, 4),
        "r_total": round(r_total, 4),
        "u_value": round(u_val, 4),
        "total_thickness_m": round(total_thickness, 4),
        "total_mass_per_m2": round(total_mass_per_m2, 2),
        "heat_capacity_per_m2": round(heat_capacity_per_m2, 2),
    }


def create_material_assembly(
    assembly_id: str,
    name: str,
    category: str,
    layers: List[MaterialLayer],
    r_inside: Optional[float] = None,
    r_outside: Optional[float] = None,
) -> MaterialAssembly:
    """
    Constructs a validated composite MaterialAssembly with all ISO 6946 metrics.
    """
    metrics = calculate_assembly_metrics(
        layers=layers,
        category=category,
        r_inside=r_inside,
        r_outside=r_outside,
    )

    return MaterialAssembly(
        assembly_id=assembly_id,
        name=name,
        category=category.lower(),
        layers=layers,
        r_inside=metrics["r_inside"],
        r_outside=metrics["r_outside"],
        r_layers=metrics["r_layers"],
        r_total=metrics["r_total"],
        u_value=metrics["u_value"],
        total_thickness_m=metrics["total_thickness_m"],
        total_mass_per_m2=metrics["total_mass_per_m2"],
        heat_capacity_per_m2=metrics["heat_capacity_per_m2"],
    )


def calculate_thermal_capacity(
    mass_kg: float,
    specific_heat_j_kgk: float,
) -> float:
    """
    Calculates lumped sensible thermal capacitance: C = m * c_p [J/K].
    """
    return legacy_thermal.calculate_thermal_capacity(mass_kg, specific_heat_j_kgk)


def create_thermal_mass(
    id: str,
    name: str,
    material_id: str,
    thickness_m: float,
    area_m2: float,
    location: str = "floor_slab",
    density_kg_m3: Optional[float] = None,
    specific_heat_j_kgk: Optional[float] = None,
) -> ThermalMassDefinition:
    """
    Constructs an explicitly defined sensible thermal storage mass element
    (e.g., stone floor slab, Trombe wall, rammed earth core).
    """
    if thickness_m <= 0.0 or area_m2 <= 0.0:
        raise ValueError(
            f"Thermal mass thickness and area must be strictly positive (>0), "
            f"got thickness={thickness_m}, area={area_m2}"
        )

    mat_record = get_material(material_id)
    if "error" not in mat_record:
        rho = density_kg_m3 if density_kg_m3 is not None else float(mat_record.get("density", 2000.0))
        cp = specific_heat_j_kgk if specific_heat_j_kgk is not None else float(mat_record.get("specific_heat", 900.0))
    else:
        if density_kg_m3 is None or specific_heat_j_kgk is None:
            raise ValueError(
                f"Material '{material_id}' not found. Must supply density and specific heat."
            )
        rho = density_kg_m3
        cp = specific_heat_j_kgk

    volume = area_m2 * thickness_m
    mass = rho * volume
    capacity = calculate_thermal_capacity(mass, cp)

    return ThermalMassDefinition(
        id=id,
        name=name,
        material_id=material_id,
        thickness_m=thickness_m,
        area_m2=area_m2,
        volume_m3=round(volume, 4),
        density_kg_m3=rho,
        specific_heat_j_kgk=cp,
        mass_kg=round(mass, 2),
        thermal_capacity_j_per_k=round(capacity, 2),
        location=location,
    )


def create_glazing(
    glazing_id: str,
    name: Optional[str] = None,
    u_value: Optional[float] = None,
    shgc: Optional[float] = None,
    thickness_m: Optional[float] = None,
    visible_transmittance: float = 0.80,
    is_argon_filled: bool = False,
    panes_count: int = 2,
    source: str = "",
    notes: str = "",
) -> GlazingDefinition:
    """
    Constructs a fenestration glazing specification, pulling default properties
    from data/materials/glazing.json when available.
    """
    try:
        g_spec = data_loader.get_glazing(glazing_id)
        u = u_value if u_value is not None else float(g_spec["U_value"]["typical_value"])
        s = shgc if shgc is not None else float(g_spec["SHGC"]["typical_value"])
        t = thickness_m if thickness_m is not None else float(g_spec["thickness"]["typical_value"])
        vt = float(g_spec.get("visible_transmittance", visible_transmittance))
        src = source or g_spec.get("source", "Glazing DB")
        g_name = name or g_spec.get("name", glazing_id.replace("_", " ").title())
        g_notes = notes or g_spec.get("notes", "")
    except Exception:
        if u_value is None or shgc is None:
            raise ValueError(
                f"Glazing '{glazing_id}' not found in database. Must supply u_value and shgc."
            )
        u = u_value
        s = shgc
        t = thickness_m if thickness_m is not None else 0.024
        vt = visible_transmittance
        src = source or "User-defined"
        g_name = name or glazing_id.replace("_", " ").title()
        g_notes = notes

    return GlazingDefinition(
        id=glazing_id,
        name=g_name,
        u_value=u,
        shgc=s,
        thickness_m=t,
        visible_transmittance=vt,
        is_argon_filled=is_argon_filled or ("argon" in glazing_id.lower()),
        panes_count=panes_count,
        source=src,
        notes=g_notes,
    )
