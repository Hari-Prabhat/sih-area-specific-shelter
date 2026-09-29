# ThermoShelter AI â€” Member 2 Integration & Handoff Guide

**Target Audience**: Member 5 (Integration + QA) & Entire ThermoShelter Engineering Team
**Author**: Member 2 (Parametric Geometry, Material & Envelope, Passive Systems)
**Status**: Verified, 127/127 Tests Passing, Self-Contained

---

## ðŸŒŸ Primary Architectural Statement

> [!IMPORTANT]
> **The primary integration boundary for downstream modules is ShelterDesign.**

All geometric, multi-layer envelope, glazing, fenestration, thermal mass, and passive strategy decisions are encapsulated within the canonical `ShelterDesign` digital twin artifact.

Downstream systems should consume `ShelterDesign` directly:
- **Member 3 (Thermal Simulation & Optimizer)** extracts:
  - Envelope U-values: `design.wall_assembly.u_value`, `design.roof_assembly.u_value`, `design.floor_assembly.u_value`
  - Total UA product and heat loss coefficient: $H = \sum U_i A_i$
  - Surface areas: `design.geometry.gross_wall_area_m2`, `design.geometry.net_wall_area_m2`, `design.geometry.roof_area_m2`, `design.geometry.floor_area_m2`
  - Glazing fenestration: `design.glazing.u_value`, `design.glazing.shgc`, window areas by orientation facade
  - Enclosed volume: `design.geometry.volume_m3`
  - Sensible thermal storage capacitance: $\sum \text{element.thermal_capacity_j_per_k}$ from `design.thermal_mass_elements`
  - Passive ventilation parameters: `design.passive_strategies` (e.g. night flushing ACH, baseline ACH)
- **Member 4 (Frontend, 3D & 2D Blueprints)** extracts:
  - Footprint dimensions: `design.geometry.length_m`, `design.geometry.width_m`, `design.geometry.height_m`
  - Roof shape: `design.geometry.roof_type`, `design.geometry.roof_pitch_deg`, `design.geometry.ridge_height_m`
  - Spatial zones: `design.geometry.zones` (living, solar sunspace, airlock, buffer)
  - Aperture placements: `design.geometry.openings` (widths, heights, facade azimuths, overhangs)
  - Materials palette: `design.wall_assembly.layers`, `design.roof_assembly.layers`

---

## 1. Files Created by Member 2

The entire subsystem is organized cleanly under `services/shelter/`, `data/mock/`, `docs/`, and `tests/`:

| File Path | Description |
| :--- | :--- |
| `services/shelter/__init__.py` | Unified public package interface, convenience factory functions, and re-exports |
| `services/shelter/models.py` | Canonical domain data contracts (`ShelterRequirements`, `ShelterGeometry`, `MaterialAssembly`, `MaterialLayer`, `OpeningDefinition`, `ZoneDefinition`, `ThermalMassDefinition`, `GlazingDefinition`, `PassiveStrategy`, `ShelterDesign`) with full JSON serialization |
| `services/shelter/geometry_engine.py` | Parametric generators (rectangular, compact, elongated, pitched/gable, flat, custom), boundary metric calculations, azimuth normalization, and physical validation |
| `services/shelter/envelope_engine.py` | Multi-layer composite assembly engine conforming to ISO 6946 / IS 3792, materials database bridge, lumped thermal mass capacitance, and glazing specifications |
| `services/shelter/passive_systems.py` | Structured passive strategy catalog and management for cold-region, hot-dry, hot-humid, and seasonal climates |
| `services/shelter/builder.py` | `ShelterDesignBuilder`, preset factories (`build_leh_ladakh_design`, `build_hot_dry_design`), and JSON disk persistence helpers |
| `data/mock/README.md` | Documentation for independent mock dataset layer |
| `data/mock/mock_shelter_requirements.json` | Standalone mock requirements file |
| `data/mock/mock_shelter_geometry.json` | Standalone mock geometry file |
| `data/mock/mock_material_assembly.json` | Standalone mock multilayer assemblies file |
| `data/mock/mock_passive_strategy.json` | Standalone mock passive strategies list |
| `data/mock/mock_shelter_design_leh.json` | Complete serializable mock `ShelterDesign` for Leh/Ladakh extreme cold climate |
| `data/mock/mock_shelter_design_hot_dry.json` | Complete serializable mock `ShelterDesign` for Jaisalmer hot-dry climate |
| `tests/test_member2_subsystem.py` | Comprehensive test suite (31 new test cases) covering geometry, envelope, openings, passive systems, builder, and serialization |
| `docs/member2_specification.md` | Full engineering specifications, mathematical derivations, data dictionary, and units |
| `docs/integration/member2-integration.md` | This integration and handoff document |

---

## 2. Existing Files Modified

Only one existing file was minimally touched to provide seamless backward-compatible re-exports:
- **`services/__init__.py`**: Re-exported `ShelterRequirements`, `ShelterGeometry`, `MaterialAssembly`, `PassiveStrategy`, `ShelterDesign`, `build_shelter_design`, and `build_leh_ladakh_design`. All existing 96 baseline tests remain completely passing with zero regressions.

---

## 3. Files That Should NOT Be Modified During Integration

To protect verified scientific calculations and maintain compatibility:
- `services/geometry.py` (working baseline formulas reused by geometry engine)
- `services/thermal.py` (working 1D heat conduction and Euler formulas)
- `services/formulas.py` (central mathematical formula registry)
- `services/material_service.py` (materials database accessor)
- `data/materials/materials.json` (authoritative materials dataset)
- `data/materials/glazing.json` (authoritative glazing dataset)
- `data/shelters/templates.json` (archetype templates)

---

## 4. Dependencies

Member 2's implementation is intentionally **zero-external-dependency** on non-standard libraries:
- Standard Python libraries used: `math`, `json`, `dataclasses`, `datetime`, `typing`, `pathlib`, `os`
- Repository dependencies: `services.formula_constants`, `services.material_service`, `services.thermal`, `data_loader`
- Test runner: `pytest`

---

## 5. How Downstream Modules Import and Consume

### 5.1 Basic Import
```python
from services.shelter import (
    ShelterDesign,
    ShelterRequirements,
    ShelterGeometry,
    MaterialAssembly,
    PassiveStrategy,
    build_leh_ladakh_design,
    build_hot_dry_design,
    load_shelter_design_from_file,
)
```

### 5.2 Loading Pre-Built Designs
```python
# Programmatically construct hero Ladakh design
design = build_leh_ladakh_design()

# Or load from saved JSON disk artifact
design_from_file = load_shelter_design_from_file("data/mock/mock_shelter_design_leh.json")
```

### 5.3 Extracting Inputs for Member 3 (Simulation Engine)
```python
design = build_leh_ladakh_design()

# Conduction UA components
wall_u = design.wall_assembly.u_value          # W/mÂ²Â·K
roof_u = design.roof_assembly.u_value          # W/mÂ²Â·K
floor_u = design.floor_assembly.u_value        # W/mÂ²Â·K
wall_area = design.geometry.net_wall_area_m2   # mÂ²
roof_area = design.geometry.roof_area_m2       # mÂ²
floor_area = design.geometry.floor_area_m2     # mÂ²

# Total aggregate UA (W/K)
ua_envelope = (wall_u * wall_area) + (roof_u * roof_area) + (floor_u * floor_area)

# Glazing solar gains
window_area = sum(op.area_m2 for op in design.openings if op.opening_type == "window")
shgc = design.glazing.shgc

# Thermal capacitance (J/K)
total_thermal_capacity = sum(tm.thermal_capacity_j_per_k for tm in design.thermal_mass_elements)

# Air volume for ACH ventilation (mÂ³)
volume = design.geometry.volume_m3
```

### 5.4 Extracting Inputs for Member 4 (3D & Blueprint Visualization)
```python
design = build_leh_ladakh_design()

# Dimensions & envelope form
length = design.geometry.length_m
width = design.geometry.width_m
height = design.geometry.height_m
roof_type = design.geometry.roof_type          # "flat", "pitched", etc.
ridge_height = design.geometry.ridge_height_m  # Extra height for pitched roof

# Openings placement
for op in design.openings:
    print(f"Opening {op.id} on {op.facade} facade: {op.width_m}x{op.height_m} m, overhang={op.overhang_depth_m}m")

# Functional zones
for zone in design.zones:
    print(f"Zone {zone.name} ({zone.zone_type}): {zone.floor_area_m2} mÂ²")
```

---

## 6. Example `ShelterDesign` JSON Structure

Below is an abbreviated excerpt of the JSON format outputted by `design.to_json()`:

```json
{
  "design_id": "shelter_leh_ladakh_hero",
  "name": "ThermoShelter Leh/Ladakh High-Altitude Cold Passive Twin",
  "version": "1.0.0",
  "requirements": {
    "occupants": 4,
    "shelter_purpose": "permanent_passive_shelter",
    "permanence": "permanent",
    "mobility": "permanent",
    "priorities": ["maximum_heat_retention", "thermal_comfort", "local_materials"]
  },
  "geometry": {
    "geometry_type": "compact",
    "length_m": 5.0,
    "width_m": 4.0,
    "height_m": 2.7,
    "roof_type": "flat",
    "floor_area_m2": 20.0,
    "volume_m3": 54.0,
    "gross_wall_area_m2": 48.6,
    "net_wall_area_m2": 41.8,
    "roof_area_m2": 20.0,
    "total_envelope_area_m2": 88.6,
    "surface_to_volume_ratio": 1.6407,
    "orientation_deg": 180.0
  },
  "wall_assembly": {
    "assembly_id": "wall_leh_composite",
    "category": "wall",
    "r_total": 4.1133,
    "u_value": 0.2431,
    "total_thickness_m": 0.37,
    "layers": [
      {
        "material_id": "mud_brick",
        "name": "Structural Mud Brick Core",
        "thickness_m": 0.25,
        "conductivity_w_mk": 0.6,
        "density_kg_m3": 1600.0,
        "resistance_m2_k_w": 0.4167
      },
      {
        "material_id": "polyurethane_foam",
        "name": "Rigid PUF Insulation",
        "thickness_m": 0.08,
        "conductivity_w_mk": 0.024,
        "resistance_m2_k_w": 3.3333
      }
    ]
  },
  "glazing": {
    "id": "double_low_e_argon_16mm",
    "u_value": 1.2,
    "shgc": 0.55,
    "visible_transmittance": 0.72,
    "is_argon_filled": true
  },
  "passive_strategies": [
    {
      "id": "direct_solar_gain_south_aperture",
      "name": "South-Oriented Direct Solar Aperture",
      "category": "cold_region",
      "enabled": true
    },
    {
      "id": "sensible_thermal_mass_storage",
      "name": "Sensible Thermal Mass Storage Core",
      "category": "cold_region",
      "enabled": true
    },
    {
      "id": "entry_airlock_vestibule",
      "name": "Airlock Vestibule (Dual-Door Entrance Buffer)",
      "category": "cold_region",
      "enabled": true
    }
  ]
}
```

---

## 7. QA & Testing Instructions for Member 5

Execute the unified test suite:
```bash
python -m pytest tests/ services/tests/ -v
```

Expected result:
- **Total Tests**: 127
- **Passed**: 127
- **Failures**: 0
- **Execution Time**: ~4 seconds

---

## 8. Known Assumptions & Limitations

1. **One-Dimensional Conduction**: Multi-layer assembly $U$-values follow standard ISO 6946 1D steady-state heat conduction assuming planar series layers. Two-dimensional or three-dimensional thermal bridging (e.g. corner junctions) is treated as a percentage factor in passive strategy parameters if modeled.
2. **Lumped Thermal Mass**: Thermal capacitance $C_{\text{thermal}} = \sum m_i c_{p,i}$ is calculated as an lumped sensible property. The transient heat penetration depth and diurnal damping factor are solved by Member 3's time-step differential equation engine.
3. **Rectangular and Pitched Geometry Primitives**: Geometry generators currently model rectangular, compact, elongated, and pitched (gable/shed) primitives. Curved or geodesic dome structures should be approximated via equivalent surface-to-volume parameters in `create_custom_geometry(...)`.
