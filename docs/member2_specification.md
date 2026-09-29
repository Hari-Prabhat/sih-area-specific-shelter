# ThermoShelter AI — Member 2 Technical Specification

## Subsystem: Parametric Geometry, Multilayer Envelope & Passive Systems Engines

**Author**: Member 2 (Geometry, Envelope & Passive Systems)
**Status**: Production-Ready / Fully Tested
**Test Coverage**: 127/127 tests passing

---

## 1. Architectural Scope & Subsystem Boundary

Member 2 is responsible for the digital twin physical representation layer:
1. **Parametric Shelter Geometry Engine** (`services/shelter/geometry_engine.py`)
2. **Material & Multilayer Envelope Engine** (`services/shelter/envelope_engine.py`)
3. **Passive Systems Engine** (`services/shelter/passive_systems.py`)
4. **Canonical Digital Twin Models & Builder** (`services/shelter/models.py`, `services/shelter/builder.py`, `services/shelter/__init__.py`)

This subsystem does **not** perform transient thermal simulations, weather API ingestion, frontend rendering, 3D graphics, or Bayesian optimization. Instead, it provides the clean physical domain models and mathematical property derivations required by those downstream modules.

```
┌─────────────────────────────────────────────────────────────┐
│                    ShelterRequirements                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                       ShelterDesign                         │
├─────────────────────────────────────────────────────────────┤
│ ├── ShelterGeometry (Dimensions, S/V, Zones, Openings)      │
│ ├── Wall Assembly (ISO 6946 Multilayer, R_total, U_val)     │
│ ├── Roof Assembly (ISO 6946 Horizontal Air Film, U_val)     │
│ ├── Floor Assembly (Subfloor Ground Coupling, U_val)        │
│ ├── Glazing Definition (U_val, SHGC, Transmittance)         │
│ ├── Openings List (Windows, Doors, Vents, Roles, Shading)   │
│ ├── Zones List (Occupied, Solar Sunspace, Airlock, Core)    │
│ ├── Thermal Mass Elements (Explicit m, C = m * cp)          │
│ └── Passive Strategies (Cold, Hot-Dry, Humid Configurations)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       Member 3 (Simulation)         Member 4 (3D/Blueprints)
```

---

## 2. Standardized Physical Units

All internal computations and canonical data models strictly adhere to SI metric units:

| Physical Property | SI Unit | Symbol |
| :--- | :--- | :--- |
| Length, Width, Height, Thickness | Meters | `m` |
| Surface Area, Floor Area, Opening Area | Square Meters | `m²` |
| Enclosed Air Volume, Material Volume | Cubic Meters | `m³` |
| Thermal Conductivity ($k$) | Watts per meter-Kelvin | `W/(m·K)` |
| Density ($\rho$) | Kilograms per cubic meter | `kg/m³` |
| Specific Heat Capacity ($c_p$) | Joules per kilogram-Kelvin | `J/(kg·K)` |
| Thermal Resistance ($R$) | Square meter-Kelvins per Watt | `m²·K/W` |
| Thermal Transmittance ($U$) | Watts per square meter-Kelvin | `W/(m²·K)` |
| Mass ($m$) | Kilograms | `kg` |
| Lumped Thermal Capacitance ($C$) | Joules per Kelvin | `J/K` |
| Orientation Azimuth | Degrees | `°` ($0^\circ = \text{North}, 180^\circ = \text{South}$) |
| Solar Absorptivity ($\alpha$), Emissivity ($\epsilon$), SHGC | Dimensionless fraction | $0.0 - 1.0$ |

---

## 3. Parametric Geometry Engine

### 3.1 Supported Geometry Types
- **Rectangular**: Standard 4-facade shelter with user-defined $L, W, H$.
- **Compact**: Near 1:1 square aspect ratio minimizing envelope surface-to-volume ratio ($S/V$) for cold climates (e.g., Leh/Ladakh).
- **Elongated**: High aspect ratio ($L/W \ge 2.0$) aligned along the East-West axis to maximize south solar aperture or facilitate cross-ventilation.
- **Pitched / Gabled Roof**: Computes dual-slope roof area, ridge height $H_{\text{ridge}} = (W/2)\tan(\theta)$, triangular gable areas, and enclosed attic air volume.
- **Flat Roof**: Horizontal roof where $A_{\text{roof}} = L \times W$.
- **Custom Geometry**: Programmatic dimensioning for non-standard modular units.

### 3.2 Orientation Convention
Azimuth angle $\theta_{\text{orient}} \in [0^\circ, 360^\circ)$:
- $0^\circ$ = North
- $90^\circ$ = East
- $180^\circ$ = South (maximum solar harvesting in Northern Hemisphere)
- $270^\circ$ = West

### 3.3 Derived Geometric Equations
$$\text{Floor Area: } A_{\text{floor}} = L \times W$$
$$\text{Flat Roof Area: } A_{\text{roof}} = L \times W$$
$$\text{Pitched Roof Area: } A_{\text{roof,pitched}} = \frac{L \times W}{\cos(\theta)}$$
$$\text{Attic Volume: } V_{\text{attic}} = \frac{1}{2} \times W \times \left( \frac{W}{2}\tan(\theta) \right) \times L$$
$$\text{Total Volume: } V = (L \times W \times H) + V_{\text{attic}}$$
$$\text{Gross Wall Area: } A_{\text{wall,gross}} = 2(L + W)H + 2 A_{\text{gable}}$$
$$\text{Net Wall Area: } A_{\text{wall,net}} = A_{\text{wall,gross}} - \sum A_{\text{openings}}$$
$$\text{Total Envelope Area: } A_{\text{envelope}} = A_{\text{floor}} + A_{\text{roof}} + A_{\text{wall,gross}}$$
$$\text{Surface-to-Volume Ratio: } S/V = \frac{A_{\text{envelope}}}{V}$$
$$\text{Window-to-Wall Ratio (WWR): } \text{WWR} = \frac{\sum A_{\text{windows}}}{A_{\text{wall,gross}}}$$

### 3.4 Multi-Zone Spatial Partitioning
The geometry engine supports architectural functional zoning:
- **`occupied`**: Main living/working spaces requiring thermal comfort control.
- **`solar`**: Sunspace or direct solar gain conservatory.
- **`thermal_mass_core`**: Internal zone hosting storage mass walls/banks.
- **`buffer`**: Unconditioned northern or service spaces (storage, latrines).
- **`airlock`**: Dual-door entry vestibule preventing infiltration drafts.

---

## 4. Material & Multilayer Envelope Engine

### 4.1 Database Provenance & Status Tracking
Every material property maintains a strict provenance status:
- `measured`: Lab or in-situ testing.
- `literature/reference`: Curated international or national standard (IS 3792, ASHRAE Fundamentals, ISO 10456, TERI).
- `estimated`: Engineering approximation from related materials.
- `user-defined`: Explicitly supplied by project engineer.

### 4.2 Layer Conductive Resistance
For any homogeneous planar layer $i$:
$$R_i = \frac{d_i}{k_i} \quad [\text{m}^2\cdot\text{K}/\text{W}]$$
$$\text{Areal Mass: } m_{\text{area},i} = \rho_i \times d_i \quad [\text{kg}/\text{m}^2]$$
$$\text{Areal Heat Capacity: } C_{\text{area},i} = \rho_i \times d_i \times c_{p,i} \quad [\text{J}/(\text{m}^2\cdot\text{K})]$$

### 4.3 Composite Assembly Thermal Transmittance (ISO 6946)
$$R_{\text{layers}} = \sum_{i=1}^n R_i$$
$$R_{\text{total}} = R_{\text{inside}} + R_{\text{layers}} + R_{\text{outside}}$$
$$U = \frac{1}{R_{\text{total}}} \quad [\text{W}/(\text{m}^2\cdot\text{K})]$$

#### Boundary Surface Film Resistances ($R_{\text{si}}, R_{\text{se}}$):
- **Vertical Walls**: $R_{\text{in}} = 0.13\,\text{m}^2\cdot\text{K}/\text{W}$, $R_{\text{out}} = 0.04\,\text{m}^2\cdot\text{K}/\text{W}$
- **Horizontal Roof (Heat Flow Upward)**: $R_{\text{in}} = 0.10\,\text{m}^2\cdot\text{K}/\text{W}$, $R_{\text{out}} = 0.04\,\text{m}^2\cdot\text{K}/\text{W}$
- **Ground / Subfloor (Heat Flow Downward)**: $R_{\text{in}} = 0.17\,\text{m}^2\cdot\text{K}/\text{W}$, $R_{\text{out}} = 0.04\,\text{m}^2\cdot\text{K}/\text{W}$

### 4.4 Sensible Thermal Mass Storage
Thermal mass elements (Trombe walls, internal stone banks, concrete floor slabs) are modeled explicitly:
$$V = A \times d \quad [\text{m}^3]$$
$$m = \rho \times V \quad [\text{kg}]$$
$$C_{\text{thermal}} = m \times c_p = \rho \times V \times c_p \quad [\text{J}/\text{K}]$$

---

## 5. Passive Systems Engine

Passive systems are defined as explicit physical configurations rather than hard-coded temperatures:

### 5.1 Cold-Region Strategies (e.g. Leh/Ladakh)
1. **High-Performance Continuous Insulation**: Target wall $U \le 0.25\,\text{W}/\text{m}^2\text{K}$, roof $U \le 0.18\,\text{W}/\text{m}^2\text{K}$.
2. **South-Oriented Direct Solar Aperture**: Maximizes winter solar harvesting.
3. **Sensible Thermal Mass Storage Core**: Absorbs daytime solar peaks and re-radiates heat during sub-zero nights.
4. **Entry Airlock Vestibule**: Dual-door airlock reducing cold-air infiltration drafts by >65%.
5. **Thermal Buffer Zone Layout**: Locates secondary/storage spaces on the northern facade.
6. **Controlled Minimum Fresh-Air Ventilation**: Limits baseline air infiltration to $0.35\,\text{ACH}$.

### 5.2 Hot-Dry Strategies (e.g. Jaisalmer)
1. **Night-Time Cool-Air Flushing and Thermal-Mass Pre-Cooling**:
   - *Technical Nomenclature Requirement*: Uses nocturnal air flushing ($4.0\,\text{ACH}$) to evacuate heat and pre-cool structural mass for daytime damping.
2. **Solar Rejection and Exterior Overhang Shading**: Deep eaves ($0.8 - 1.0\,\text{m}$) and high-albedo roof finishes.
3. **Controlled Daytime Openings Closure**: Seals openings during peak heat hours.

### 5.3 Hot-Humid Strategies (e.g. Chennai)
1. **Natural Cross-Ventilation System**: Aligns operable apertures with prevailing breeze.
2. **Stack-Effect Induced Thermal Chimney Ventilation**: High roof/ridge vents evacuating buoyant warm air.

---

## 6. Public Python API Quick Reference

```python
from services.shelter import (
    create_geometry,
    create_material_layer,
    create_material_assembly,
    create_thermal_mass,
    create_glazing,
    create_opening,
    create_passive_strategy,
    build_shelter_design,
    build_leh_ladakh_design,
    save_shelter_design_to_file,
    load_shelter_design_from_file,
)

# 1. Build canonical Leh hero design
leh_design = build_leh_ladakh_design()
print(f"Design: {leh_design.name}")
print(f"Wall U-value: {leh_design.wall_assembly.u_value:.4f} W/m²K")
print(f"Roof U-value: {leh_design.roof_assembly.u_value:.4f} W/m²K")

# 2. Serialize to JSON string or save to file
json_str = leh_design.to_json(indent=2)
save_shelter_design_to_file(leh_design, "my_shelter.json")

# 3. Reload from JSON
loaded = load_shelter_design_from_file("my_shelter.json")
assert loaded.design_id == leh_design.design_id
```
