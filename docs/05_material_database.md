# ThermoShelter AI — Material & Engineering Database

**Purpose:** Document the material, glazing, and shelter-template datasets used by the prototype.

---

## 1. Material Database Overview

The primary material database is:

```text
data/materials/materials.json
```

It currently contains **19 material records**.

Supported material categories include:

- wall;
- roof;
- floor;
- insulation; and
- thermal mass.

The database is loaded and normalized through:

```text
services/material_service.py
```

---

## 2. Material Properties

Each material record can contain:

| Property | Unit | Purpose |
|---|---|---|
| Density | kg/m³ | Mass / thermal inertia calculations |
| Thermal conductivity | W/m·K | Conductive resistance |
| Specific heat | J/kg·K | Thermal storage |
| Emissivity | — | Longwave radiation |
| Solar absorptivity | — | Solar surface response |
| Cost estimate | USD/m³ in source data | Indicative comparison |
| Source | — | Data provenance |
| Notes | — | Engineering context |

The database also stores typical, minimum, and maximum values for many physical properties.

---

## 3. Example Materials

The repository includes materials such as:

- Mud Brick / Adobe;
- Rammed Earth;
- Granite Stone Masonry;
- insulation materials;
- masonry/concrete alternatives; and
- other envelope materials.

For example, the Mud Brick record identifies:

- density;
- conductivity;
- specific heat;
- emissivity;
- solar absorptivity;
- indicative cost; and
- literature/reference sources.

The material database therefore supports both **thermal calculations** and **design comparison**.

---

## 4. How Material Properties Enter the Model

The most important property for steady-state envelope transmission is thermal conductivity:

$$
R=\frac{L}{k}
$$

The resulting layer resistances are combined with surface-film resistances:

$$
R_{total}=R_{inside}+\sum R_i+R_{outside}
$$

and:

$$
U=\frac{1}{R_{total}}
$$

The U-value is then used in conductive heat-flow calculations.

Density and specific heat provide additional physical information for thermal-mass treatment, while emissivity and solar absorptivity support radiation/solar calculations.

---

## 5. Glazing Database

The glazing reference dataset is:

```text
data/materials/glazing.json
```

It contains **7 glazing records**.

Typical properties include:

- U-value;
- SHGC;
- thickness;
- visible transmittance;
- source; and
- notes.

Examples include:

| Glazing | Typical U-value | Typical SHGC |
|---|---:|---:|
| Single clear | 5.8 W/m²·K | 0.85 |
| Double clear | 2.8 W/m²·K | 0.76 |
| Double low-E | 1.8 W/m²·K | 0.60 |

The runtime simulation exposes simplified glazing presets for its active workflows.

---

## 6. Material Selection by Climate

The recommendation engine does not select materials randomly. It uses explicit climate rules.

Examples:

| Climate | General strategy |
|---|---|
| Cold | High resistance + thermal inertia + controlled solar gain |
| Hot-dry | Thermal mass + solar rejection + shading |
| Hot-humid | Lightweight envelope + ventilation + shading |
| Composite | Balanced seasonal envelope |
| Moderate | Moderate insulation + passive daylight/ventilation |

Temporary and permanent shelters can receive different recommendations.

For example, in cold conditions the current rules distinguish lightweight PUF-insulated modular construction for temporary deployment from heavier masonry-oriented construction for permanent use.

---

## 7. Temporary vs Permanent Design

The recommender differentiates shelter permanence through:

- geometry;
- height;
- material selection;
- permanence rationale; and
- optimization constraints.

The current auto-sizing logic uses:

```text
Minimum floor area = max(12 m², occupants × 4.5 m²)

Aspect ratio ≈ 1.3 : 1

Temporary height = 2.6 m
Permanent height = 2.8 m
```

This allows the documentation to show that “temporary” and “permanent” are not simply two labels in the interface.

---

## 8. Data Quality Checks

`validate_data.py` checks:

- required fields;
- duplicate IDs;
- valid material categories;
- positive physical-property values;
- minimum/maximum consistency;
- positive glazing U-values;
- SHGC within 0–1;
- positive glazing thickness; and
- valid shelter-template dimensions.

The current validation run reports:

```text
Materials: 19
Glazing:   7
Shelters:  4
Errors:    0
```

---

## 9. Important Data Qualification

Material values in the repository are **reference/database values**, not measurements performed by the ThermoShelter team.

Therefore the project should describe them as:

> Literature/reference-based engineering inputs used for comparative modelling.

Do not describe the database as experimentally validated unless physical testing has actually been performed.

---

## 10. Future Extension

A mature material subsystem can add:

- region-specific local materials;
- embodied-carbon metrics;
- lifecycle cost;
- availability/logistics;
- measured thermal properties;
- uncertainty ranges;
- moisture behaviour; and
- supplier/manufacturer data.

This would allow optimization to move beyond thermal comfort alone toward **cost + performance + sustainability + availability**.
