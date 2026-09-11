# Phase 2 — Integration Plan: Canonical Design + Climate → Thermal Simulation

## Current Data Flow (Traced)

```
ClimateProfile (services/contracts.py)
    + ShelterDesign (services/shelter/models.py)
        ↓
SimulationAdapter.to_simulation_input()
    → adapt_to_climate_profile() / adapt_to_shelter_design()
    → extract_envelope_parameters()
        ↓
SimulationInput (climate + design + envelope_parameters)
        ↓
SimulationAdapter.run_simulation_from_input()
    → maps design flat properties to run_simulation() kwargs
        ↓
run_simulation() [services/simulation_service.py]
    → independently re-computes U-values, geometry, thermal mass
    → forward Euler transient solver (substeps per hour)
    → returns raw Dict[str, Any]
        ↓
adapt_simulation_result() → SimulationResult
```

## Key Findings

1. **ClimateProfile created:** via `create_mock_climate_profile()` or scenario fixtures in `services/fixtures.py`
2. **ShelterDesign created:** via legacy flat kwargs or canonical composite instantiation
3. **SimulationInput created:** by `SimulationAdapter.to_simulation_input()`
4. **SimulationEnvelopeParameters populated:** by `extract_envelope_parameters()` — but **not consumed** by `run_simulation()`
5. **Thermal engine:** `run_simulation()` in `simulation_service.py` — it independently computes everything from flat parameters
6. **Consumed fields:** length, width, height, wall_material, wall_thickness_m, insulation_thickness_m, insulation_conductivity, window_area, glazing, orientation, roof_type, pitch_angle_deg, shelter_model, roof_thickness_m, roof_conductivity, roof_insulation_m, shgc, ach, occupants, heat_per_person, hourly_temperatures, hourly_direct_solar, hourly_diffuse_solar
7. **Ignored canonical fields:** thermal_mass_elements (dedicated Trombe/water walls), passive_strategies, door_assembly, zones, openings (individual), floor assembly layers
8. **No duplicate physics:** No TypeScript thermal engine exists. Python is authoritative.
9. **Backend climate schema:** `backend/climate/schemas.py` has a separate Pydantic ClimateProfile (structured with Location, ClimateMetrics, SolarData, etc.) — structurally different from `services.contracts.ClimateProfile`. Needs mapping adapter.

## Implementation Plan

### 1. Climate Integration
- Add `adapt_backend_climate_profile()` function in `services/contracts.py` that maps `backend.climate.schemas.ClimateProfile` → `services.contracts.ClimateProfile`
- Preserve all available data: location, elevation, solar, wind, humidity, provenance

### 2. Simulation Adapter Enhancement
- The adapter already correctly maps all fields that the thermal engine supports
- Document which canonical fields are unsupported by the current engine
- No structural changes needed to the adapter

### 3. Sensitivity Tests (tests/test_phase2_sensitivity.py)
- A: Insulation sensitivity
- B: Window area sensitivity
- C: Orientation sensitivity
- D: Ventilation/ACH sensitivity
- E: Thermal mass sensitivity
- F: Geometry sensitivity
- G: Material sensitivity
- H: Climate sensitivity
- I: Occupancy sensitivity

### 4. Golden Engineering Scenario
- THERMOCORE-LADAKH-GOLDEN fixture in `services/fixtures.py`
- Cold high-altitude, 4 occupants, permanent, south-oriented, high-performance envelope
- Runs through real thermal simulation, asserts comprehensive result structure

### 5. Heat-Flow Accounting Verification
- Verify SimulationResult exposes all required dashboard categories
- Document supported vs unsupported categories

### 6. Documentation
- `docs/integration/phase-2-integration.md` with full architecture, mappings, and results
