# ThermoShelter AI — Assumptions & Limitations

**Purpose:** Define the current modelling boundaries clearly so that project claims remain technically defensible.

---

## 1. Model Scope

ThermoShelter is an **early-stage passive shelter design and optimization prototype**.

The current model is designed for:

- rapid comparison;
- climate-specific screening;
- material/geometry exploration;
- thermal trend analysis; and
- optimization of defined design variables.

It is not intended to replace detailed building simulation, CFD, structural analysis, or physical testing.

---

## 2. Thermal Model Assumptions

The current simulation uses a **reduced-order single-zone thermal representation**.

Key assumptions include:

- one primary indoor temperature state;
- simplified envelope heat transfer;
- lumped effective thermal capacity;
- hourly weather boundary conditions;
- sub-hour forward-Euler integration;
- simplified solar-gain modelling;
- simplified longwave radiation;
- sensible ventilation heat exchange.

---

## 3. Comfort Model

The current screening comfort band is:

$$
18^\circ C \leq T_{in} \leq 24^\circ C
$$

This provides simple:

- comfortable;
- too-cold; and
- too-hot

classification.

It is **not** a PMV/PPD, adaptive-comfort, or humidity-coupled comfort model.

---

## 4. Solar and Orientation Simplifications

The current model uses simplified orientation factors rather than a complete facade-by-facade solar-position calculation.

Therefore:

- orientation effects are comparative;
- shading is simplified;
- glazing solar gain is represented using SHGC and a simplified exposure factor;
- the model does not reproduce a full annual solar geometry calculation.

These assumptions are suitable for rapid design exploration but should be refined for final engineering analysis.

---

## 5. Ventilation and Humidity

The ventilation model represents sensible heat exchange using ACH.

The current model does not fully simulate:

- latent heat;
- moisture transport;
- condensation;
- indoor humidity generation;
- detailed natural-ventilation airflow;
- CFD-scale air movement.

This is especially relevant for hot-humid climates such as Chennai.

---

## 6. Thermal Mass

Thermal inertia is represented through a simplified effective thermal capacity.

The current prototype does not perform detailed transient heat diffusion through every wall/roof material layer.

Therefore, material “thermal mass” comparisons should be interpreted as **modelled comparative behaviour**, not a full finite-difference wall-temperature simulation.

---

## 7. Weather Data

The active simulation uses bundled local EPW profiles for five locations.

Limitations:

- no live weather API;
- no dynamic site-specific weather generation;
- no real-time weather adaptation;
- no field-measured boundary conditions.

The repository's metadata contains additional locations, but those are not automatically equivalent to active simulation support.

---

## 8. Material Data

Material properties are reference/database inputs.

They may vary in practice due to:

- manufacturing;
- moisture;
- density;
- workmanship;
- temperature;
- aging;
- local sourcing; and
- installation quality.

The current database should therefore not be presented as a laboratory-measured material catalogue.

---

## 9. Optimization Limitations

The optimizer searches a defined design space rather than every possible shelter configuration.

Current variables include:

- insulation thickness;
- window area;
- wall material;
- glazing;
- orientation.

The result is optimal **within the selected model, constraints and objective**, not universally optimal for every real-world criterion.

A lower discomfort score does not automatically imply:

- lower cost;
- lower embodied carbon;
- better structural performance;
- better constructability;
- better logistics; or
- better occupant acceptance.

---

## 10. Visualization Limitations

The 2D and 3D outputs are design-communication and visualization tools.

They should not be interpreted as:

- construction-ready CAD drawings;
- structural drawings;
- certified architectural plans;
- fabrication drawings.

---

## 11. AI Claim Boundary

The repository explicitly states that the current version does **not contain a trained AI/ML model**.

The current “AI” workflow is better described as:

```text
Climate Rules
      +
Physics-Based Simulation
      +
Optimization
      +
Explainable Recommendation
```

The system should therefore not claim that a neural network or machine-learning predictor is currently producing the temperature predictions.

---

## 12. Validation Boundary

Software tests and analytical benchmarks establish implementation correctness for defined cases.

They do not establish:

- field accuracy;
- annual energy-prediction accuracy;
- structural safety;
- construction performance;
- universal climate suitability.

Physical testing and measured-field calibration are future validation stages.

---

## 13. Recommended Technical Claim

For SIH presentations, a defensible statement is:

> **ThermoShelter is a rapid, explainable, physics-based early-stage design and optimization platform that helps compare climate-specific passive shelter configurations before detailed engineering verification.**

Avoid unsupported claims such as:

> “The system perfectly predicts real indoor temperature.”

or:

> “The optimized design guarantees a specific percentage of energy savings.”

Any percentage shown during judging should specify its simulation scenario, baseline, assumptions, and metric.

---

## 14. Future Scope

The current limitations define a clear engineering roadmap:

```text
Reduced-Order Model
        ↓
More Detailed Thermal Model
        ↓
Humidity / Adaptive Comfort
        ↓
Detailed Solar & Ventilation Models
        ↓
Annual / Seasonal Simulation
        ↓
High-Fidelity CFD / Building Simulation
        ↓
Physical Test
        ↓
Field Calibration
```

Additional future improvements include:

- live climate-data integration;
- multi-objective optimization;
- cost and embodied-carbon optimization;
- local-material availability;
- CAD/BIM export;
- uncertainty analysis; and
- measured-performance calibration.

---

## 15. Conclusion

The current prototype is strongest when positioned as a **fast design-screening and decision-support layer**.

Its engineering value comes from connecting climate data, explicit physical relationships, material/geometry choices, optimization, and visualization in one workflow while clearly identifying where detailed engineering verification is still required.
