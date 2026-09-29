# WP1 — FastAPI + React Foundation Architecture & Integration Report

**Target Branch:** `integration-react-final`  
**Status:** COMPLETE & VERIFIED  
**Work Package:** WP1 — FastAPI Backend + React Design Studio Recovery & Integration

---

## 1. Executive Summary

Work Package 1 establishes the official, production-ready decoupled architecture of the **ThermoShelter AI** platform:
- **Presentation & Interaction (Member 4):** Recovered React 18 + Vite + Tailwind CSS + Three.js application in `thermoshelter-design-studio/`.
- **API & Orchestration Layer:** FastAPI REST backend in `backend/` (`backend/main.py`) with strict Pydantic v2 validation, CORS configuration, and normalized JSON responses.
- **Scientific Source of Truth (Members 1, 2, 3):** Authoritative Python thermal physics engine, ISO 6946 multi-layer conduction solver, forward Euler numerical integrator, and canonical engineering contracts (`services/contracts.py`, `services/shelter/models.py`, `services/simulation_adapter.py`).

```mermaid
flowchart TD
    subgraph Client ["React Frontend (thermoshelter-design-studio)"]
        UI_STUDIO[Design Studio / Manual Designer]
        API_CLIENT[src/services/api.ts]
        UI_RESULTS[SimulationResults / 3D Visualization]
    end

    subgraph API ["FastAPI Backend (backend/)"]
        FASTAPI[backend/main.py]
        ROUTER_SIM[/api/simulation/run]
        ROUTER_CLIM[/api/climate/*]
        ROUTER_HLT[/api/health]
    end

    subgraph ScientificCore ["Authoritative Python Scientific Core"]
        CANON_DES[services/shelter/models.py: ShelterDesign]
        CANON_CLM[services/contracts.py: ClimateProfile]
        ADAPTER[services/simulation_adapter.py: SimulationAdapter]
        ENGINE[services/simulation_service.py: run_simulation]
        RESULT[services/contracts.py: SimulationResult]
    end

    UI_STUDIO -->|Trigger Simulation| API_CLIENT
    API_CLIENT -->|POST /api/simulation/run| ROUTER_SIM
    ROUTER_SIM -->|Validate & Adapt| CANON_DES
    ROUTER_SIM -->|Resolve Weather| CANON_CLM
    CANON_DES --> ADAPTER
    CANON_CLM --> ADAPTER
    ADAPTER -->|1D Forward Euler + ISO 6946| ENGINE
    ENGINE -->|Typed Result| RESULT
    RESULT -->|JSON| ROUTER_SIM
    ROUTER_SIM -->|HTTP 200 JSON| API_CLIENT
    API_CLIENT -->|Render Real Results| UI_RESULTS
```

---

## 2. FastAPI Architecture & Entry Point

### Entry Point
- **File:** `backend/main.py`
- **Application Instance:** `app = FastAPI(...)`
- **Port / Server:** `uvicorn backend.main:app --reload --port 8000`

### CORS Configuration
Configured strictly for local development origins without wildcard security hazards:
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173`
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8000` (FastAPI Swagger / OpenAPI docs)
- `http://127.0.0.1:8000`
- Configurable via `CORS_ALLOWED_ORIGINS` environment variable.

### Error Handling
Global exception handlers return clean JSON structures, eliminating raw stack traces from API responses:
- `ValueError` $\rightarrow$ `HTTP 422 Unprocessable Entity`: `{"error": "Validation Error", "detail": "..."}`
- `TypeError` $\rightarrow$ `HTTP 400 Bad Request`: `{"error": "Type Error", "detail": "..."}`
- `HTTPException` $\rightarrow$ Appropriate HTTP status codes with structured details.

---

## 3. Canonical Endpoints

### 1. System Health
- **Route:** `GET /api/health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "ThermoShelter AI",
    "version": "1.0.0",
    "canonical_contracts": true,
    "physics_engine": "Python 1D Forward Euler + ISO 6946 (Authoritative)",
    "subsystems": {
      "member1_climate": "active",
      "member2_shelter_design": "active",
      "member3_simulation": "active"
    }
  }
  ```

### 2. Thermal Simulation Execution
- **Route:** `POST /api/simulation/run`
- **Input Contract:** `SimulationRunRequest`
  - Accepts canonical `design` (`ShelterDesign` dict or flat parameters).
  - Accepts canonical `climate` (`ClimateProfile` dict, Pydantic backend model, or `city` name string).
  - Configurable `hours_to_simulate` (default: 168), `substeps` (default: 60), `initial_indoor_temp` (default: 20.0°C).
- **Execution Pipeline:**
  1. Input validation via Pydantic v2.
  2. Resolves canonical `ClimateProfile` (preserving historical/estimated/measured provenance).
  3. Resolves canonical `ShelterDesign` (preserving physical bounds, materials, and geometries).
  4. Passes through `SimulationAdapter.to_simulation_input()`.
  5. Executes authoritative Python solver `simulation_service.run_simulation()`.
  6. Returns full canonical `SimulationResult.to_dict()`.

### 3. Climate Intelligence Routes (Member 1)
- `POST /api/climate/location`: Resolves place name or coordinates to `Location`.
- `POST /api/climate/profile`: Synthesizes climatological normal profile.
- `POST /api/climate/classify`: Classifies location into one of 6 canonical zones.
- `POST /api/climate/strategy`: Generates evidence-based passive architectural strategies.
- `POST /api/climate/analyze`: End-to-end analysis pipeline.

---

## 4. React Frontend Recovery & Client Layer

### Recovery
The React frontend previously stripped in commit `716c86a` was recovered from historical commit `bb2161d` into `thermoshelter-design-studio/`.

### Legacy TypeScript Thermal Engine Status
- **File:** `thermoshelter-design-studio/src/utils/thermalEngine.ts`
- **Classification:** **LEGACY CLIENT-SIDE PROTOTYPE (NON-AUTHORITATIVE)**
- A comprehensive deprecation disclaimer was added to the header.
- The React application is rewired so that all simulation requests route through `src/services/api.ts` to the Python FastAPI backend.
- The client-side TypeScript calculations are retained solely as an offline fallback if the API server is unreachable.

### React API Client
- **File:** `thermoshelter-design-studio/src/services/api.ts`
- **Functions:**
  - `checkApiHealth()`: Queries `/api/health`.
  - `buildCanonicalSimulationPayload(...)`: Serializes UI entities into the canonical request payload.
  - `adaptCanonicalToUiResult(...)`: Translates canonical Python timeseries and metrics into UI chart data while preserving the complete raw `canonical` object.
  - `runSimulationViaApi(...)`: Dispatches asynchronous POST request to `/api/simulation/run`.

### Vite Development Proxy
`vite.config.js` was updated with an upstream proxy:
```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
}
```

---

## 5. Development Startup Instructions

### 1. Start the FastAPI Backend
From project root:
```powershell
# Activate Python environment
$env:PYTHONPATH="."
python -m uvicorn backend.main:app --reload --port 8000
```
- API will be accessible at: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Start the React Frontend
In a separate terminal:
```powershell
cd thermoshelter-design-studio
npm run dev
```
- Web Application will be accessible at: `http://localhost:5173`
- Requests to `/api/*` will automatically proxy to `http://localhost:8000/api/*`.

---

## 6. Known Limitations & Next Steps

1. **Vite Build Dependencies:** In this work package, only the core simulation and climate paths are hooked up. Advanced 3D interaction, blueprint generation, and Bayesian optimization UI are deferred to subsequent work packages per instructions.
2. **Offline Mode:** If FastAPI is offline, the frontend falls back with a console warning to the client-side demo calculation.
