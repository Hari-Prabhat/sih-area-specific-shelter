# ThermoShelter AI — Problem Statement & Proposed Solution

**Project:** ThermoShelter AI  
**Team:** Rocket  
**Competition:** Smart India Hackathon 2026  
**Project Theme:** Area-Specific Passive Shelter Design & Thermal Simulation

---

## 1. Executive Summary

ThermoShelter AI is a Python and Streamlit prototype for **early-stage, climate-specific passive shelter design exploration**. The platform connects local climate conditions with shelter geometry, envelope materials, glazing, orientation, thermal simulation, optimization, comparison, and visualization.

The central engineering premise is that a shelter that performs acceptably in one region cannot automatically be expected to perform similarly in another. Outdoor temperature, solar exposure, wind, humidity, geometry, envelope resistance, openings, and thermal mass interact to determine the modeled indoor thermal response.

ThermoShelter therefore follows a design workflow in which the **location is treated as a first-class design input** rather than merely a weather-chart selection.

> **Climate → Requirements → Design → Thermal Simulation → Optimization → Comparison → Visualization**

The current implementation is intentionally an early-stage design and decision-support tool. It uses a reduced-order, single-zone thermal model and deterministic climate recommendations rather than a trained machine-learning model or high-fidelity CFD/building simulation.

---

## 2. Problem Statement

### 2.1 Engineering Problem

Generic shelter designs often use common dimensions, materials, openings, and envelope assumptions without sufficiently accounting for the thermal conditions of the deployment region.

For area-specific shelter planning, important design variables include:

- local outdoor temperature patterns;
- solar irradiance;
- wind and humidity conditions;
- shelter occupancy;
- temporary versus permanent use;
- shelter geometry and volume;
- wall and roof thermal resistance;
- insulation thickness;
- window area and glazing performance;
- orientation and solar exposure;
- ventilation assumptions; and
- thermal mass.

These variables are coupled. Changing one parameter can alter several thermal pathways simultaneously.

For example, increasing glazing may improve useful solar gain under a favorable orientation but also increase conductive transmission through the window. Increasing insulation can reduce conductive heat transfer but does not by itself resolve solar overheating or ventilation-related heat exchange.

A practical early-stage design workflow therefore needs to support **rapid, explainable comparison of multiple shelter configurations under different climate conditions**.

---

## 3. Why Area-Specific Design Matters

The repository currently supports five active climate locations:

| Location | Climate classification used by recommendation engine | Design emphasis |
|---|---|---|
| Leh | Cold / severe cold | Insulation, solar capture, thermal inertia |
| Jaisalmer | Hot-dry | Shading, thermal mass, solar rejection, night cooling |
| Chennai | Hot-humid | Ventilation, shading, solar rejection |
| Delhi | Composite | Balanced seasonal performance |
| Bengaluru | Moderate | Moderate envelope and passive strategies |

The classification is implemented in `services/recommender.py`. The platform uses these categories to select deterministic design recommendations and explanations.

This means that the platform is intended to demonstrate a key principle:

> **Changing the location should change the recommended design strategy, not merely change the temperature graph.**

---

## 4. Proposed Solution

ThermoShelter AI integrates the major early-stage design steps into one workflow.

```text
                    USER
                     │
                     ▼
          Location + Requirements
                     │
                     ▼
            Climate Characterization
                     │
                     ▼
       Auto-Sizing + Climate Recommendations
                     │
                     ▼
     Geometry + Materials + Glazing + Orientation
                     │
                     ▼
          Reduced-Order Thermal Model
                     │
                     ▼
       Comfort + Heat-Flow + Energy Metrics
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     Optimization           Comparison
          │                     │
          └──────────┬──────────┘
                     ▼
              2D / 3D Visualization
```

The implementation is not a single black-box prediction model. Instead, it combines:

1. **Local EPW climate data**
2. **Rule-based climate recommendations**
3. **Deterministic geometry and material calculations**
4. **Reduced-order transient thermal simulation**
5. **Optuna TPE optimization**
6. **Baseline-versus-optimized comparison**
7. **Interactive 2D and 3D visualization**

This structure makes the design process more transparent and allows individual engineering assumptions to be inspected.

---

## 5. End-to-End Design Workflow

### Step 1 — Select the deployment location

The user selects one of the currently supported locations. The climate service loads the corresponding local EPW weather file from:

```text
data/weather/
├── leh.epw
├── jaisalmer.epw
├── delhi.epw
├── chennai.epw
└── bengaluru.epw
```

The climate service extracts hourly:

- air temperature;
- direct normal irradiance;
- diffuse horizontal irradiance;
- wind speed; and
- relative humidity.

The active simulation uses temperature and solar irradiance directly in its thermal calculations.

### Step 2 — Define shelter requirements

The interface accepts requirements including:

- location;
- occupant count;
- temporary/permanent shelter type; and
- design-related dimensions or configuration depending on the selected feature studio.

The recommendation engine can auto-size a baseline shelter using occupancy and permanence.

### Step 3 — Generate climate-aware design guidance

`services/recommender.py` classifies the selected location and generates deterministic recommendations for:

- wall/envelope material;
- roof approach;
- insulation type;
- glazing;
- orientation;
- shading; and
- permanence-related design rationale.

### Step 4 — Configure the shelter

The simulation supports:

- rectangular flat-roof shelters;
- rectangular pitched-roof shelters;
- compact shelters;
- elongated shelters; and
- custom dimensions.

The user can vary envelope and fenestration characteristics such as wall material, insulation thickness, window area, glazing, and orientation.

### Step 5 — Simulate thermal response

The simulation service models the shelter as a **single thermal node** with lumped thermal capacity.

The model tracks heat exchange through:

- walls;
- roof;
- floor;
- windows;
- ventilation;
- longwave radiation;
- solar gain; and
- internal occupant/equipment gains.

The default main workflow simulates **168 hours** with sub-hour forward-Euler integration.

### Step 6 — Evaluate performance

The application reports modeled metrics including:

- indoor temperature series;
- outdoor temperature;
- average/minimum/maximum indoor temperature;
- comfort hours;
- comfort percentage;
- discomfort degree-hours;
- solar gain;
- wall/roof/floor/window heat flow;
- ventilation and radiation heat flow;
- integrated solar energy;
- total modeled heat-loss components;
- envelope U-values; and
- geometry metrics.

### Step 7 — Optimize

The optimization service uses **Optuna's Tree-structured Parzen Estimator (TPE) sampler**.

The current optimization search can vary:

- insulation thickness;
- window area;
- wall material;
- glazing; and
- orientation.

The optimization objective is to minimize simulated **discomfort degree-hours** for the selected scenario.

### Step 8 — Compare and visualize

The platform provides feature studios for:

- shelter design;
- baseline versus optimized comparison;
- material comparison;
- multiple shelter-model comparison; and
- sensitivity analysis.

The repository also contains interactive Plotly-based 2D/3D visualization components.

---

## 6. Mapping the Proposed Solution to the Core Requirements

| Design requirement | ThermoShelter implementation |
|---|---|
| Area-specific design | Local climate profile + climate classification |
| Indoor temperature prediction | Reduced-order transient thermal simulation |
| Solar thermal analysis | Solar irradiance + glazing solar-gain model |
| Heat-flow details | Component-level thermal balance tracking |
| Material exploration | Material database + material comparison |
| Geometry exploration | Geometry service + multiple shelter models |
| Orientation exploration | Orientation factors |
| Design optimization | Optuna TPE optimization |
| Temporary/permanent differentiation | Auto-sizing and climate recommendation rules |
| Visual design exploration | Interactive 2D/3D components |

---

## 7. Engineering Basis

The platform uses established engineering relationships rather than an opaque learned model.

The core calculations include:

- thermal resistance and U-value;
- conductive heat transfer;
- solar gain through glazing;
- sensible ventilation heat exchange;
- longwave radiative heat transfer;
- thermal capacitance;
- transient indoor-temperature updating; and
- temperature-band comfort evaluation.

The detailed equations and assumptions are maintained separately in:

```text
docs/equations.md
```

The project therefore separates the **engineering calculation layer** from the user-interface layer.

---

## 8. What Makes the Approach Distinct

ThermoShelter's intended differentiator is not simply that it calculates indoor temperature.

It combines:

> **Climate-aware recommendations + physics-based screening + optimization + material/geometry comparison + visual design exploration**

This provides a rapid screening workflow before detailed professional engineering analysis.

The emphasis is on **speed, transparency, explainability, and comparative design exploration**.

---

## 9. Current Scope and Important Boundary

The current repository should be represented accurately during SIH evaluation.

### Implemented in the current prototype

- Python + Streamlit application;
- five bundled climate locations;
- local EPW weather data;
- deterministic climate recommendations;
- occupancy-based auto-sizing;
- material and glazing databases;
- geometry calculations;
- reduced-order transient thermal simulation;
- 168-hour main simulation horizon;
- thermal comfort statistics;
- component heat-flow tracking;
- Optuna TPE optimization;
- baseline/optimized comparison;
- multiple shelter models;
- sensitivity analysis components;
- interactive visualization;
- automated tests and data validation.

### Not currently implemented as production/high-fidelity capabilities

- trained machine-learning prediction model;
- live climate API integration;
- full CFD;
- full EnergyPlus/ANSYS simulation;
- field-calibrated thermal prediction;
- structural certification;
- construction approval.

The repository README explicitly describes the current system as a prototype and states that the present recommendation layer is rule-based and optimization-driven.

---

## 10. Intended Impact

The project aims to make climate-responsive passive shelter exploration faster and more accessible during the early design stage.

Potential benefits include:

- earlier identification of climate-appropriate envelope strategies;
- faster comparison of materials and geometries;
- improved understanding of thermal trade-offs;
- reduced dependence on disconnected manual calculations during early screening;
- support for temporary and permanent shelter scenarios; and
- a structured path from climate data to an explainable design concept.

No measured field energy-savings percentage is claimed by the current implementation.

---

## 11. Future Engineering Direction

The repository identifies several future extensions:

- annual and seasonal simulation;
- additional climate locations;
- improved solar and thermal-mass modelling;
- humidity and adaptive comfort modelling;
- multi-objective optimization;
- measured-field calibration;
- high-fidelity simulation verification;
- live climate-data integration; and
- CAD/BIM/report-export integration.

The intended long-term progression is:

```text
Climate Data
     ↓
Rapid Design Screening
     ↓
Optimization
     ↓
High-Fidelity Verification
     ↓
Field Validation
     ↓
Climate-Specific Shelter Design Guidance
```

---

## 12. Conclusion

ThermoShelter AI addresses the early-stage challenge of designing shelters that respond to the conditions of their deployment area.

Rather than treating shelter design as a fixed template, the platform links **climate, requirements, geometry, materials, glazing, orientation, thermal behaviour, optimization, and visualization** into a single workflow.

The current prototype is deliberately positioned as a **rapid, explainable design-screening and decision-support system**. Its value lies in helping users explore and compare climate-specific concepts before progressing to detailed engineering verification.

