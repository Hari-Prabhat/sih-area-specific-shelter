# WP3-A — Optimization Backend Integration & API Specification

**Target Branch:** `integration-react-final`  
**Status:** COMPLETE & VERIFIED  
**Work Package:** WP3-A — Optimization Backend Integration & Canonical API

---

## 1. Executive Summary

Work Package 3-A establishes the integration between the existing Python Bayesian design optimization engine (`services/optimize.py`) and the canonical engineering digital twin architecture (`services/shelter/models.py`, `services/contracts.py`, `services/simulation_adapter.py`). It exposes a single, high-performance REST endpoint for multi-objective optimization:

`POST /api/optimization/run`

The endpoint validates input geometries and boundary climates, bridges canonical `ShelterDesign` specifications into structured `OptimizationInput` contracts via `OptimizationAdapter`, executes Optuna TPE (Tree-structured Parzen Estimator) numerical evaluations over candidate configurations, and returns ranked candidates (#1, #2, #3) serialized as canonical digital twin designs.

---

## 2. Existing Optimizer Architecture & Trace

| Aspect | Implementation Details |
|---|---|
| **Entry Point** | `services.optimize.optimize_shelter(opt_input: OptimizationInput) -> OptimizationResult` |
| **Adapter Interface** | `OptimizationAdapter.from_shelter_design()`, `OptimizationAdapter.candidate_to_shelter_design()`, `OptimizationAdapter.run_optimization_from_input()` |
| **Input Contract** | `services.contracts.OptimizationInput` |
| **Output Contract** | `services.contracts.OptimizationResult` containing `List[OptimizationCandidate]` |
| **Sampling Algorithm** | Optuna TPE (`optuna.samplers.TPESampler(seed=42)`) |
| **Trial Simulation** | `services.simulation_service.run_simulation` (1D Forward Euler solver) |

### Supported Optimization Variables
The optimizer varies only parameters physically consumed by the thermal physics engine:
1. **Envelope Insulation Thickness ($m$):** Continuous float between `min_insulation_m` and `max_insulation_m` (default: $0.0 - 0.20\text{ m}$, step $5\text{ mm}$).
2. **Window Aperture Area ($m^2$):** Continuous float bounded by physical facade area constraints ($0.5\text{ m}^2$ up to $40\%$ gross wall area).
3. **Glazing Assembly:** Categorical choice among `single_clear`, `double_clear`, `double_low_e`, `triple_low_e`.
4. **Orientation Azimuth:** Categorical facade alignment (`south`, `north`, `east`, `west`).
5. **Structural Wall Material:** Categorical selection tailored by shelter permanence:
   - *Temporary:* Lightweight portable prefab panels (`puf_insulation`, `eps_insulation`, `wood`, `brick`).
   - *Permanent:* Heavy sensible thermal mass substrates (`brick`, `mud`, `stone`, `concrete`, `puf_insulation`).

---

## 3. Multi-Objective Function Formulation

The optimizer preserves the existing physical objective formulations:

### Default Mode
- **Permanent Shelters:** Minimizes lifecycle discomfort degree hours while heavily weighting total heat loss to promote envelope thermal resistance and passive inertia:
  $$\text{Score} = \text{DDH} + 0.35 \times Q_{\text{loss, total}}$$
- **Temporary Shelters:** Prioritizes immediate thermal protection while penalizing heavy material density to maintain modular portability and rapid field transportability:
  $$\text{Score} = \text{DDH} + 0.15 \times Q_{\text{loss, total}} + \text{Penalty}_{\text{density}}$$

### Weighted Multi-Objective Mode
When custom `weights` are provided (`comfort`, `efficiency`, `solar` summing to $1.0$):
$$\text{Utility} = w_{\text{comfort}} \times S_{\text{comfort}} + w_{\text{efficiency}} \times S_{\text{efficiency}} + w_{\text{solar}} \times S_{\text{solar}}$$
$$\text{Score} = 100.0 - \text{Utility}$$

---

## 4. REST API Specification

### Endpoint: `POST /api/optimization/run`

#### Request Payload Schema
```json
{
  "city": "leh",
  "home_type": "Permanent",
  "design": {
    "length": 4.5,
    "width": 3.2,
    "height": 2.8,
    "wall_material": "brick",
    "insulation_thickness_m": 0.0,
    "window_area": 2.0,
    "glazing": "single_clear",
    "occupants": 3
  },
  "n_trials": 20,
  "substeps": 15,
  "hours_to_simulate": 168,
  "weights": {
    "comfort": 0.50,
    "efficiency": 0.35,
    "solar": 0.15
  },
  "min_insulation_m": 0.0,
  "max_insulation_m": 0.20
}
```

#### Response Structure
```json
{
  "city": "leh",
  "home_type": "Permanent",
  "insulation_thickness_m": 0.085,
  "insulation_mm": 85.0,
  "window_area_m2": 2.4,
  "wall_material": "stone",
  "glazing": "double_low_e",
  "glazing_name": "Double Glazed Low-E",
  "orientation": "south",
  "discomfort_score": 12.4,
  "simulation_result": { "...": "Full 168h simulation breakdown" },
  "ranked_designs": [
    {
      "rank": 1,
      "label": "Design #1",
      "rationale": "Optimal Multi-Criteria Balance",
      "overall_score": 88.4,
      "sub_scores": { "comfort": 92.0, "efficiency": 84.5, "solar": 86.0 },
      "insulation_mm": 85.0,
      "window_area_m2": 2.4,
      "wall_material": "stone",
      "glazing": "double_low_e",
      "orientation": "south",
      "comfort_percentage": 89.3,
      "total_heat_loss_kwh": 94.2,
      "solar_gain_kwh": 52.1,
      "u_values": { "wall_u": 0.26, "roof_u": 0.32, "floor_u": 0.40, "window_u": 1.8 },
      "canonical_design": { "...": "Complete ShelterDesign digital twin" }
    }
  ],
  "recommended_design": { "...": "Direct reference to Design #1" },
  "n_trials": 20,
  "explanation": "Optimized Permanent shelter configuration for Leh..."
}
```

---

## 5. Candidate Digital Twin Representation

Each candidate is mapped back into a canonical `ShelterDesign` via:
`OptimizationAdapter.candidate_to_shelter_design(candidate, base_design)`

This preserves:
- The base shelter's core dimensions ($L \times W \times H$)
- Structural roof pitch and geometry type
- Infiltration (ACH) and occupancy constraints
- Sets `provenance = DataProvenance.OPTIMIZED`

---

## 6. Verification & Test Strategy

| Test Suite | File | Tests | Result |
|---|---|---|---|
| **Optimization API & Adapter Tests** | `tests/test_optimization_api.py` | 7 | **7 PASSED** (2.32s) |
| **Existing Optimization Unit Tests** | `services/tests/test_optimization.py` | 16 | **16 PASSED** |
| **Recommender Integration Tests** | `tests/test_optimization_and_recommender.py` | 4 | **4 PASSED** |
| **FastAPI Core Endpoints** | `tests/test_fastapi_endpoints.py` | 10 | **10 PASSED** |
| **Full Python Test Suite** | `pytest services/tests/ tests/` | 297 | **297 PASSED** (5.79s) |
| **React Build Verification** | `npm run build` | - | **0 errors, bundle complete** (8.26s) |

---

## 7. Performance & Guardrails

- **Default API Trials:** Bound to $n=20$ trials with $15$ integration substeps/hour for interactive HTTP responsiveness ($< 5\text{ seconds}$).
- **Validation Guardrails:** Rejects non-positive geometries, invalid climate names, and mismatched weight sums with standard HTTP 422 JSON error messages.
- **Quota Discipline:** Integration tests utilize small trial counts ($n=2-5$ trials) to ensure fast CI/CD execution without degrading Optuna numerical fidelity.
