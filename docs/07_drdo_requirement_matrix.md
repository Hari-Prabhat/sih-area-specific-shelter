# ThermoShelter AI — Requirement Traceability Matrix

**Purpose:** Map the requested engineering capabilities to the corresponding implementation and evidence available in the repository.

---

## 1. Requirement Mapping

| Requirement / Capability | Current Implementation | Evidence |
|---|---|---|
| Area-specific shelter design | Climate classification + local weather profiles | Leh/Jaisalmer/Delhi/Chennai/Bengaluru workflows |
| User-defined shelter requirements | Streamlit input layer | `components/inputs.py` |
| Occupancy-based sizing | `auto_size_shelter()` | `services/recommender.py` |
| Temporary vs permanent shelter | Separate sizing/material/recommendation logic | `tests/test_temporary_vs_permanent.py` |
| Indoor temperature prediction | 168-hour reduced-order thermal simulation | `services/simulation_service.py` |
| Solar thermal analysis | Solar irradiance + glazing gain | `services/solar.py` / simulation output |
| Heat-flow details | Component heat-flow tracking | Wall, roof, floor, window, ventilation, radiation |
| Material comparison | Material database + comparison studio | `data/materials/`, comparison workflow |
| Geometry comparison | Multiple shelter models + geometry service | `services/geometry.py` |
| Orientation comparison | Simplified orientation factors | Simulation + tests |
| Insulation exploration | Variable insulation thickness | Simulation + optimizer |
| Glazing exploration | Multiple glazing options | Glazing database + optimizer |
| Design optimization | Optuna TPE | `services/optimize.py` |
| Baseline vs optimized design | Comparison workflow | `components/comparison.py` |
| Climate-specific recommendations | Deterministic recommendation engine | `services/recommender.py` |
| 2D design visualization | Interactive floor plan | `components/charts.py` |
| 3D design visualization | Plotly shelter visualization | `services/visual3d.py`, `components/shelter_3d.py` |
| Sensitivity analysis | Sensitivity curves/workflow | Feature studio + chart functions |
| Engineering equations | Central formula documentation | `docs/equations.md` |
| Dataset validation | Dedicated validator | `scripts/validate_data.py` |
| Automated software testing | pytest suite | `tests/`, `services/tests/` |

---

## 2. Climate Coverage

The current active recommendation/simulation workflow covers:

```text
Leh        → Cold
Jaisalmer  → Hot-Dry
Delhi      → Composite
Chennai    → Hot-Humid
Bengaluru  → Moderate
```

The metadata layer additionally contains Kargil, Srinagar and Mumbai.

---

## 3. Simulation Outputs

The simulation exposes the core evidence required for thermal analysis:

### Temperature

- indoor temperature;
- outdoor temperature;
- average/min/max;
- comfort status.

### Solar

- solar irradiance;
- solar power;
- solar thermal gain;
- integrated solar energy;
- incident solar energy.

### Heat flow

- wall;
- roof;
- floor;
- window;
- ventilation;
- radiation;
- net heat flow.

### Summary metrics

- U-values;
- comfort hours;
- comfort percentage;
- discomfort degree-hours;
- component heat-loss energy;
- geometry metrics.

---

## 4. Optimization Traceability

The optimizer evaluates combinations of:

```text
Insulation thickness
Window area
Wall material
Glazing
Orientation
```

The principal optimization objective is modeled discomfort degree-hours.

The repository also calculates multi-criteria design scores using comfort, energy, heat-loss retention and solar-harvesting components for candidate ranking.

---

## 5. Evidence Status

### Implemented and test-covered

- climate loading;
- material loading;
- geometry;
- thermal calculations;
- simulation;
- optimization;
- recommendations;
- temporary/permanent distinction;
- visualization;
- dataset validation.

### Requires final SIH evidence capture

- final baseline/optimized numerical results;
- final climate-to-climate comparison;
- final screenshots;
- final test-run output;
- final demo scenario.

---

## 6. Important Claim Boundary

The current repository supports:

> **Rapid, explainable, physics-based early-stage shelter design exploration and optimization.**

It does not support a claim that the current prototype is:

- a full CFD solver;
- a structural-analysis platform;
- a field-calibrated digital twin;
- a trained machine-learning predictor; or
- a replacement for detailed professional engineering analysis.

---

## 7. Judge-Facing Traceability Flow

```text
Requirement
    ↓
Repository Module
    ↓
Calculation / Logic
    ↓
Simulation Result
    ↓
Visualization
    ↓
Test / Validation Evidence
```

This structure allows the team to answer:

> “Where is this requirement implemented?”

with a specific module and demonstrable output rather than a presentation-only claim.
