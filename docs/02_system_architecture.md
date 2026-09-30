# ThermoShelter AI — System Architecture

**Project:** ThermoShelter AI  
**Architecture Type:** Streamlit application with modular Python services  
**Primary Language:** Python  
**Deployment Model:** Prototype / early-stage design exploration

---

## 1. Architecture Overview

ThermoShelter AI is implemented as a modular Python application whose user interface is built with **Streamlit**.

The architecture separates:

- user-interface components;
- climate and data access;
- design recommendations;
- geometry calculations;
- material handling;
- thermal and energy calculations;
- simulation orchestration;
- optimization;
- visualization; and
- validation/testing.

The central application orchestrator is `app.py`.

Unlike an API-first architecture, the current repository **does not contain a FastAPI or other standalone backend service**. Streamlit calls the Python component/service layer directly.

---

## 2. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                         USER / DESIGNER                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                       │
│                         app.py                              │
│                                                             │
│  Requirements │ Feature Studios │ Comparison │ Visualization│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    COMPONENT LAYER                          │
│                                                             │
│ inputs.py       feature_studio.py      comparison.py        │
│ dashboard.py    charts.py              export.py            │
│ recommendations.py                    shelter_3d.py         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┼────────────────┐
                │              │                │
                ▼              ▼                ▼
┌─────────────────────┐ ┌───────────────┐ ┌──────────────────┐
│ CLIMATE / DATA      │ │ DESIGN LOGIC  │ │ SIMULATION       │
│                     │ │               │ │                  │
│ climate_service.py  │ │ recommender   │ │ simulation       │
│ data_loader.py      │ │ geometry.py   │ │ thermal.py       │
│ EPW / JSON / CSV    │ │ material svc  │ │ solar.py         │
└──────────┬──────────┘ └───────┬───────┘ │ ventilation.py   │
           │                    │         │ comfort.py       │
           └────────────┬───────┘ └──────┴────────┬─────────┘
                        │                          │
                        ▼                          ▼
               ┌────────────────────────────────────────┐
               │          FORMULA / ENGINE LAYER        │
               │                                        │
               │ formulas.py │ thermal.py │ solar.py   │
               │ geometry.py │ ventilation │ comfort    │
               └────────────────────┬───────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ SIMULATION RESULTS   │
                         │                      │
                         │ Temperature          │
                         │ Heat flow            │
                         │ Solar gain            │
                         │ Comfort               │
                         │ U-values              │
                         │ Energy metrics        │
                         └──────────┬───────────┘
                                    │
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
             ┌─────────────────┐         ┌─────────────────┐
             │ OPTIMIZATION    │         │ VISUALIZATION   │
             │                 │         │                 │
             │ optimize.py     │         │ Plotly charts   │
             │ Optuna TPE      │         │ 2D floor plan   │
             │                 │         │ 3D shelter      │
             └────────┬────────┘         └────────┬────────┘
                      │                           │
                      └─────────────┬─────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ DESIGNER / JUDGE     │
                         │                      │
                         │ Compare → Interpret  │
                         │ → Select design      │
                         └──────────────────────┘
```

---

## 3. Application Entry Point

### `app.py`

`app.py` is the main application orchestrator.

It:

1. configures the Streamlit page;
2. sets the application layout/theme;
3. renders the requirements input section;
4. provides feature-studio navigation;
5. dispatches the selected workflow to the corresponding component.

The current feature studios are:

- **Shelter Designer**
- **Baseline vs Optimized**
- **Material Comparison Studio**
- **Multiple Shelter Models**
- **Sensitivity Analysis Studio**

The application does not place the thermal equations directly inside the UI. Instead, UI components invoke reusable service modules.

---

## 4. Component Layer

The `components/` directory provides the presentation and workflow layer.

### Major components

| Component | Responsibility |
|---|---|
| `inputs.py` | Collect shelter requirements and user constraints |
| `feature_studio.py` | Coordinate major design/exploration studios |
| `comparison.py` | Baseline versus optimized design presentation |
| `charts.py` | Plotting and result visualization |
| `chart_theme.py` | Visualization styling |
| `dashboard.py` | Dashboard-oriented presentation |
| `shelter_3d.py` | 3D shelter visualization |
| `export.py` | Export-related UI functionality |
| `recommendations.py` | Recommendation presentation |

This layer should primarily handle **interaction and presentation**, while reusable engineering calculations remain in `services/`.

---

## 5. Climate and Data Layer

### `services/climate_service.py`

The climate service loads local EPW files using `pvlib`.

The active weather directory is:

```text
data/weather/
├── leh.epw
├── jaisalmer.epw
├── delhi.epw
├── chennai.epw
└── bengaluru.epw
```

The service exposes:

- location identifier;
- latitude;
- longitude;
- hourly air temperature;
- hourly direct solar irradiance;
- hourly diffuse solar irradiance;
- hourly wind speed; and
- hourly relative humidity.

The current simulation uses bundled weather files rather than a live weather API.

### Supporting data

```text
data/
├── climate/
│   ├── locations.json
│   └── weather.csv
├── materials/
│   ├── materials.json
│   └── glazing.json
└── shelters/
    └── templates.json
```

These datasets support location metadata, material properties, glazing metadata, shelter templates, and related application data.

---

## 6. Material Subsystem

### `services/material_service.py`

The material service loads and normalizes material records from:

```text
data/materials/materials.json
```

Material records can include:

- thermal conductivity;
- density;
- specific heat;
- emissivity;
- solar absorptivity;
- indicative cost;
- source; and
- notes.

The service also provides material lookup by identifier/alias.

### Glazing

Runtime glazing presets are defined in `services/simulation_service.py`.

The active presets include:

- single clear;
- double clear;
- double low-E; and
- triple low-E.

Each preset contains a modeled U-value and SHGC.

---

## 7. Climate Recommendation Subsystem

### `services/recommender.py`

The recommendation subsystem is deterministic and climate-rule based.

Current mapping:

```text
Leh        → cold
Jaisalmer  → hot_dry
Chennai    → hot_humid
Delhi      → composite
Bengaluru  → moderate
```

The recommendation layer provides climate-specific guidance concerning:

- envelope materials;
- insulation;
- roof strategy;
- glazing;
- orientation;
- shading; and
- temporary/permanent shelter rationale.

The same module also performs occupancy-based auto-sizing.

### Important architectural boundary

This subsystem is **not a trained machine-learning inference service**.

The repository's current intelligence layer is:

```text
Climate classification
        +
Deterministic design rules
        +
Physics-based simulation
        +
Optimization
```

---

## 8. Geometry Subsystem

### `services/geometry.py`

The geometry service contains deterministic functions for:

- floor area;
- enclosed volume;
- gross wall area;
- flat roof area;
- total envelope area;
- net wall area; and
- pitched roof geometry.

The pitched-roof calculation can derive:

- roof area;
- gable area;
- gross wall area;
- volume;
- ridge height; and
- total height.

These calculations are reused by the simulation and visualization layers.

---

## 9. Thermal Calculation Layer

### `services/thermal.py`

This module provides reusable thermal calculations including:

- layer thermal resistance;
- total thermal resistance;
- U-value;
- conductive heat flow;
- heat-loss coefficients;
- thermal capacity;
- stored thermal energy;
- radiative heat transfer;
- internal heat gains;
- net heat flow; and
- temperature updating.

### `services/formulas.py`

`formulas.py` acts as the centralized formula interface and re-exports the major geometry, solar, ventilation, comfort, and thermal functions.

This reduces duplication and gives the simulation layer a common engineering calculation interface.

---

## 10. Central Simulation Service

### `services/simulation_service.py`

This is the authoritative simulation orchestration layer.

The high-level dependency is:

```text
app.py / feature components
            │
            ▼
simulation_service.py
            │
            ├── climate_service.py
            ├── material_service.py
            ├── geometry.py
            ├── thermal.py
            ├── solar.py
            ├── ventilation.py
            └── comfort.py
```

The simulation performs:

1. weather loading;
2. geometry calculation;
3. wall/roof/floor U-value calculation;
4. glazing parameter selection;
5. orientation-factor selection;
6. thermal-capacity setup;
7. sub-hour numerical integration;
8. component heat-flow tracking;
9. comfort evaluation; and
10. energy aggregation.

---

## 11. Thermal Simulation Data Flow

```text
EPW Weather
    │
    ├── Outdoor Temperature
    ├── Direct Solar
    └── Diffuse Solar
             │
             ▼
      Simulation Inputs
             │
             ├── Geometry
             ├── Materials
             ├── Insulation
             ├── Windows / Glazing
             ├── Orientation
             ├── ACH
             └── Occupants
             │
             ▼
       Envelope U-values
             │
             ▼
      Thermal Coefficients
             │
             ▼
      Hour-by-Hour Loop
             │
             ├── Solar Gain
             ├── Internal Gain
             ├── Wall Loss
             ├── Roof Loss
             ├── Floor Loss
             ├── Window Loss
             ├── Ventilation
             └── Radiation
             │
             ▼
        Net Heat Flow
             │
             ▼
      Indoor Temperature
             │
             ▼
     Comfort + Energy Metrics
```

---

## 12. Numerical Integration

The simulation uses explicit forward-Euler time integration.

The main UI workflow uses:

- a 168-hour simulation horizon;
- hourly weather inputs; and
- sub-hour integration controlled by the `substeps` parameter.

The implementation defaults to 60 substeps per hour in the main simulation function, while optimization calls use a reduced substep count to speed up repeated candidate evaluation.

This separation is important:

```text
Detailed simulation
        ↓
Higher temporal resolution

Optimization loop
        ↓
Reduced resolution for faster search
```

The final optimized design is then evaluated using the authoritative 168-hour simulation.

---

## 13. Optimization Subsystem

### `services/optimize.py`

The optimization subsystem uses **Optuna** with a TPE sampler.

The search can explore:

- insulation thickness;
- window area;
- wall material;
- glazing; and
- orientation.

Conceptually:

```text
Design Space
     │
     ▼
Optuna Trial
     │
     ▼
Candidate Shelter
     │
     ▼
Thermal Simulation
     │
     ▼
Discomfort Degree-Hours
     │
     ▼
Objective Score
     │
     ▼
Next Candidate
     │
     └──────→ repeated search
                    │
                    ▼
              Best Design
```

The optimization direction is minimization of the modeled discomfort degree-hours.

---

## 14. Visualization Layer

The project contains Plotly-based visualization and 3D shelter components.

The visualization layer can present:

- indoor/outdoor temperature profiles;
- solar profiles;
- heat-flow breakdowns;
- comparison metrics;
- sensitivity results;
- 2D floor-plan representations; and
- 3D shelter geometry.

Visualization is therefore downstream of the engineering calculation layer.

```text
Engineering Result
       │
       ▼
Presentation Model
       │
       ├── Charts
       ├── Comparison
       ├── 2D Blueprint
       └── 3D Visualization
```

---

## 15. Validation and Testing Architecture

The repository includes tests for:

- formula calculations;
- thermal simulation;
- 3D visualization;
- chart/validation behavior;
- data loading;
- data validation;
- optimization/recommendation;
- temporary versus permanent shelter workflows.

A separate validation script is provided at:

```text
scripts/validate_data.py
```

This gives the project two complementary QA layers:

```text
Software tests
      +
Dataset validation
      +
Engineering sanity checks
```

The current repository does not claim that passing software tests constitutes real-world thermal validation.

---

## 16. Repository Architecture

```text
sih-area-specific-shelter/
│
├── app.py
├── data_loader.py
├── requirements.txt
│
├── components/
│   ├── charts.py
│   ├── chart_theme.py
│   ├── comparison.py
│   ├── dashboard.py
│   ├── export.py
│   ├── feature_studio.py
│   ├── inputs.py
│   ├── recommendations.py
│   └── shelter_3d.py
│
├── services/
│   ├── climate_service.py
│   ├── comfort.py
│   ├── formulas.py
│   ├── formula_constants.py
│   ├── geometry.py
│   ├── material_service.py
│   ├── optimize.py
│   ├── recommender.py
│   ├── simulation_service.py
│   ├── solar.py
│   ├── thermal.py
│   ├── thermal_engine.py
│   ├── ventilation.py
│   ├── visual3d.py
│   └── tests/
│
├── data/
│   ├── climate/
│   ├── materials/
│   ├── shelters/
│   └── weather/
│
├── docs/
│   ├── equations.md
│   └── data_dictionary.md
│
├── scripts/
│   └── validate_data.py
│
└── tests/
```

---

## 17. Architectural Principles

### Modularity

UI, engineering calculations, data access, optimization, and visualization are separated into modules.

### Reusability

Core calculations are implemented as reusable functions rather than being embedded only in UI code.

### Explainability

Recommendations are generated through explicit climate rules, while optimization evaluates explicit engineering simulation outputs.

### Data locality

The active climate simulation uses bundled EPW files, making the prototype reproducible without requiring a live weather API.

### Validation readiness

Engineering formulas, data validation, and software tests are organized as separate evidence layers.

---

## 18. Current Architectural Limitations

The current architecture is appropriate for an early-stage prototype but should not be described as a production digital-twin infrastructure.

Current limitations include:

- direct Streamlit-to-Python service calls;
- local/bundled climate datasets;
- reduced-order single-zone thermal modelling;
- simplified radiation and ventilation treatment;
- no dedicated external API layer;
- no high-fidelity CFD/FEA layer;
- no field-calibration service;
- no production database;
- no distributed optimization infrastructure.

These are natural candidates for later system evolution.

---

## 19. Future Architecture Direction

A future production-oriented architecture could evolve toward:

```text
                    Web / Mobile UI
                           │
                           ▼
                     API Gateway
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Climate API      Design API      Simulation API
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Simulation Engine
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
          Optimization          High-Fidelity
             Engine              Verification
                │                     │
                └──────────┬──────────┘
                           ▼
                     Results Store
                           │
                           ▼
                 Reports / CAD / BIM
```

This is a **future architectural direction**, not part of the current repository.

---

## 20. Summary

ThermoShelter AI follows a layered architecture:

> **Streamlit UI → Components → Data/Design Services → Engineering Calculation Layer → Simulation → Optimization → Visualization**

The architecture deliberately keeps the physics calculations separate from the interface and makes the main simulation service the central integration point.

This allows the prototype to remain explainable while supporting future expansion toward richer climate data, higher-fidelity simulation, advanced optimization, external APIs, and professional engineering workflows.

