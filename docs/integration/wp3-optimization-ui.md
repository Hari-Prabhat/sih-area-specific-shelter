# WP3-B — Optimization + Design Comparison React UI Integration

## 1. Overview & Architecture
WP3-B bridges the backend multi-objective Bayesian optimization engine (`/api/optimization/run` backed by Optuna TPE and 1D forward Euler simulation) with the frontend React interface (`thermoshelter-design-studio`).

### Canonical Flow
```
User inputs parameters & weights (Comfort, Efficiency, Solar)
           │
           ▼
[POST /api/optimization/run]
           │
           ├─ Optuna TPE generates trials within parameter bounds
           ├─ 1D Forward Euler simulation evaluates each candidate (168h / 7d)
           └─ Multi-objective scoring ranks candidates #1..#N
           │
           ▼
Frontend receives CanonicalOptimizationResult
           │
           ├─ Displays Recommended Design & Top Ranked Candidates
           ├─ Baseline vs. Optimized delta comparison (Comfort, Heating Demand, Heat Loss)
           ├─ Visual comparison charts (Comfort vs. Efficiency vs. Solar, U-values, Demand)
           ├─ Inspect Candidate in 3D Preview (ShelterModel3D)
           └─ "Apply to Design Studio" updates authoritative ShelterDesign state
```

## 2. Key UI Capabilities Added
1. **Optimization Controls:**
   - Multi-objective weight sliders (Thermal Comfort, Heating Efficiency, Solar Gain) normalizing automatically.
   - Trials selector (10, 20, 30, 50 trials) with estimated runtime indicators.
   - Shelter permanence selector (`Permanent` vs `Temporary`).
   - One-click "Run Bayesian Optimization" button from both Design Studio and Compare tabs.

2. **Multi-Candidate Comparison:**
   - Detailed candidate cards showing Rank, Rationale badge, Score, Comfort %, Total Heat Loss, Heating Demand, U-values, Glazing, Wall Material, and Orientation.
   - Direct Delta Metrics vs Baseline:
     - $\Delta$ Comfort Percentage ($+X\%$)
     - $\Delta$ Annual/Weekly Heating Demand ($-Y\text{ kWh}$)
     - $\Delta$ Heat Loss Reduction ($-Z\text{ kWh}$)
   - Grouped Bar Charts comparing Baseline vs Candidates for Comfort, Demand, and U-values.

3. **Candidate Inspection & Application:**
   - Interactive candidate 3D visualization preview.
   - "Apply Design to Studio" button: transfers the candidate's wall material, insulation thickness/type, glazing, and orientation to the canonical `ShelterDesign` state.
   - Design provenance indicators showing that physics and optimization were evaluated by Python Optuna & ISO 6946 Euler models.
