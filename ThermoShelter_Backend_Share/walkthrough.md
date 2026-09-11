# ThermoShelter AI — React + TypeScript + FastAPI Workstation Walkthrough

## Summary of Completed Migration

Successfully migrated ThermoShelter from Streamlit to a **React + TypeScript + Three.js + Recharts architectural engineering workstation** backed by a **FastAPI JSON API layer**.

The Python physics engine remains the authoritative calculation bedrock. Zero thermal formulas or fake data were introduced to React.

---

## 1. Architecture

```
React 19 + TypeScript + Vite + Tailwind CSS + Three.js + Recharts + Zustand
                                ↓  HTTP / REST JSON
                      FastAPI (D:\SIH\api.py)
                                ↓  Native Python
               Existing Services (D:\SIH\services\*)
    (climate_service, simulation_service, optimize, recommender, etc.)
                                ↓
                Engineering Physics & Solvers
```

- **Backend Authority**: All transient heat transfer (Forward Euler 168-hr Δt=60s), ISO 6946 multi-layer conduction, and Optuna TPE Bayesian optimization execute strictly in Python.
- **Frontend Presentation**: Dedicated high-performance engineering UI inspired by architectural CAD and building physics simulation software.

---

## 2. Frontend Pages Created

All pages reside in `D:\SIH\frontend\src\pages\`:

1. **`OverviewPage.tsx`**:
   - High-impact mission banner displaying active climate, outdoor temperature, solar irradiation, and design workflow.
   - 4 Hero KPI metric cards (Comfort Zone %, Mean Indoor Temp, Weekly Heat Loss, Solar Harvest).
   - Interactive 3D Digital Twin live preview coupled with real-time envelope specifications and Bayesian status.
   - Primary Call to Action: `Design Shelter`.

2. **`ClimatePage.tsx`**:
   - Location details, elevation, winter design temperature, solar GHI, heating degree days (HDD), and data provenance.
   - 24-hour and 168-hour dual-axis meteorological charts (ambient temperature and direct solar flux) using Recharts.
   - *"WHAT THIS MEANS FOR YOUR SHELTER"* engineering section with physical implications for Leh, Jaisalmer, and Chennai.

3. **`DesignStudioPage.tsx`** (*Hero Feature*):
   - Split-screen workstation: Left column parametric engineering controls (Geometry, Materials, Glazing, Passive systems); Right column large interactive 3D digital twin.
   - Real-time 3D geometry deformation upon modifying length, width, height, and pitched/flat roof types.
   - Primary action buttons: `[ SIMULATE ENVELOPE ]` and `[ OPTIMIZE ENVELOPE ]`.

4. **`SimulationPage.tsx`**:
   - 4 Hero metrics: Indoor Temperature, Comfort Target Hours, Total Envelope Loss, and Solar Heat Admitted.
   - 4 Analytical visualization tabs:
     - 🌡️ Temperature: 168-hour indoor vs outdoor ambient with green ASHRAE 55 18–24°C comfort band.
     - ☀️ Solar Dynamics: Incident aperture flux vs admitted useful thermal gain.
     - ⚡ Component Heat Flows: Dynamic wall, roof, glazing, floor, and ventilation losses in Watts.
     - 📊 Energy Balance: Weekly cumulative energy loss and solar gain in kWh.
   - Concise physical engineering interpretation generated directly from numerical results.

5. **`OptimizationPage.tsx`**:
   - Visual display of Bayesian optimization progress, discomfort score, and multi-objective Pareto trade-offs.
   - Full specification of Candidate #1 Recommended Design.
   - Primary CTA: `[ APPLY RECOMMENDED DESIGN ]` (updates active design state across the entire workstation).
   - Top-ranked candidate designs table (#1, #2, #3) with explicit sub-scores.

6. **`ComparisonPage.tsx`**:
   - Side-by-side comparative panels: Baseline Uninsulated vs AI-Optimized Design.
   - Mini 3D models, assembly U-values, insulation thickness, and comfort hours for each design.
   - Delta improvement metrics (+comfort %, -discomfort DH, -heat loss cut).
   - 168-hour overlaid thermal response curve.

7. **`MaterialsPage.tsx`**:
   - Visual material cards with thermal conductivity (k), density, assembly U-value, comfort percentage, and heat loss.
   - Ability to select any material and immediately update the design and simulation.
   - 168-hour multi-material indoor temperature progression curves.

8. **`SensitivityPage.tsx`**:
   - Parametric sweep charts for Insulation Thickness (0–200mm) and Window Aperture Area (0.5–6.0m²).
   - Dual-axis curve showing Comfort % and Weekly Heat Loss with vertical reference line indicating the *Current Design* marker.
   - Physics explanation of diminishing marginal returns in insulation and solar aperture sizing.

9. **`DigitalTwinPage.tsx`**:
   - Large immersive Three.js WebGL canvas with mouse orbit, zoom, pan, and compass north arrow.
   - Parametric geometry sliders for length, width, height, and flat/pitched roof profiles with instant 3D feedback.

10. **`FloorplanPage.tsx`**:
    - Architectural 2D blueprint drafting rendered via precision SVG.
    - Wall thickness (230mm), window aperture placement, door swing arc, dimension annotations, and usable floor area.

11. **`ValidationPage.tsx`**:
    - Analytical ISO 6946 steady-state multi-layer conduction benchmark (MAE < 0.0001 W, 0.0000% error, PASS).
    - Transient lumped capacitance energy conservation benchmark (ΔT=0.720 K exact match, PASS).
    - Physical model governing equations and assumptions.

12. **`ReportPage.tsx`**:
    - Official Engineering Specification Report document preview.
    - `[ DOWNLOAD MARKDOWN (.MD) ]` and `[ DOWNLOAD JSON TELEMETRY ]` buttons powered by the Python export services.

---

## 3. Persistent Shell & Components Created

- **`frontend/src/components/layout/Sidebar.tsx`**: Exact requested navigation hierarchy:
  - `PROJECT`: Overview
  - `DESIGN`: Climate, Shelter Designer
  - `ANALYZE`: Simulation, Optimization, Compare, Materials, Sensitivity
  - `VISUALIZE`: 3D Digital Twin, Floorplan
  - `VERIFY`: Validation
  - `DELIVER`: Engineering Report
  - Bottom status: Active climate (e.g. `LEH`), design dimensions, and real-time simulation status.
- **`frontend/src/components/layout/AppShell.tsx`**: Top command bar with global climate selector, occupancy input, permanence toggle (Temporary vs Permanent), and quick-trigger SIMULATE / OPTIMIZE buttons.
- **`frontend/src/components/shelter/ShelterModel3D.tsx`**: Three.js WebGL digital twin rendering concrete slab, walls with material-tinted shaders, aligned pitched or flat roof, glass window panel, door, and North arrow.
- **`frontend/src/components/common/MetricCard.tsx`**: High-contrast engineering KPI card with deltas and status badges.
- **`frontend/src/store/designStore.ts`**: Single authoritative Zustand global state store managing active design parameters and caching simulation/optimization results.
- **`frontend/src/api/client.ts`**: Typed asynchronous client calling FastAPI endpoints.

---

## 4. FastAPI Endpoints Created (`api.py`)

- `GET  /api/health`
- `GET  /api/climate/cities`
- `GET  /api/climate/{city}`
- `GET  /api/materials`
- `GET  /api/materials/{material_id}`
- `GET  /api/shelter-models`
- `GET  /api/glazing`
- `GET  /api/orientations`
- `POST /api/auto-size`
- `POST /api/recommend-materials`
- `POST /api/simulation`
- `POST /api/optimization`
- `POST /api/comparison`
- `POST /api/material-comparison`
- `POST /api/archetype-comparison`
- `POST /api/sensitivity`
- `GET  /api/validation`
- `POST /api/export/markdown`
- `POST /api/export/json`

---

## 5. Verification & Tests

### A. Python Backend Tests
```bash
python -m pytest -q
```
- **Result**: **242 passed** (all 230 original baseline tests preserved + 12 automated API endpoint tests).
- 0 tests failed, 0 tests deleted.

### B. Frontend Production Build
```bash
cd frontend && npm run build
```
- **Result**: **Clean compilation** (`tsc -b && vite build` completed with 0 errors).

### C. Live End-to-End Testing (Leh, Jaisalmer, Chennai)
Verified via live HTTP requests to `http://127.0.0.1:8000`:
- **Leh**: Alpine cold, 8760h EPW data, baseline average temperature -4.2°C, 0% uninsulated comfort, optimized to 125mm PUF insulation and 3,335 DH.
- **Jaisalmer**: Hot-arid desert, 8760h EPW data, baseline average temperature 19.9°C, 54.2% comfort.
- **Chennai**: Warm-humid coastal, 8760h EPW data, baseline average temperature 30.7°C, 4.8% comfort.
- **Analytical Validation**: Steady-state relative error 0.0000% (PASS), transient energy conservation exact match (PASS).
- **Export**: Markdown report (3,082 bytes) and JSON telemetry generated and downloaded directly from backend.
