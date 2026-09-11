# ThermoShelter AI — Frontend & Backend Integration Architecture

This document provides a comprehensive technical reference for the **ThermoShelter AI** architectural engineering platform, detailing the connection between the **React + TypeScript frontend** and the **FastAPI + Python engineering backend**, the exact numerical data payloads passed between them, and how outputs, 3D geometry, and climate regions are derived.

---

## 1. System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               REACT + TYPESCRIPT FRONTEND                              │
│                                                                                        │
│  [UI Pages & Workstations]                                                             │
│    • OverviewPage         • ClimatePage          • DesignStudioPage (Hero 3D Studio)   │
│    • SimulationPage       • OptimizationPage     • ComparisonPage (Baseline vs Opt)    │
│    • MaterialsPage        • SensitivityPage      • DigitalTwinPage                     │
│    • FloorplanPage        • ValidationPage       • ReportPage                          │
│                                                                                        │
│  [State Management]                                                                    │
│    Zustand Global Store (frontend/src/store/designStore.ts)                            │
│                                                                                        │
│  [API Client]                                                                          │
│    Typed Fetch Client (frontend/src/api/client.ts)                                     │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │  HTTP / JSON (Vite Proxy: /api/*)
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND (api.py)                                  │
│                                                                                        │
│  REST API Router (Port 8000)                                                           │
│    • /api/climate/{city}        • /api/simulation           • /api/optimization        │
│    • /api/comparison            • /api/material-comparison  • /api/sensitivity         │
│    • /api/validation            • /api/export/markdown      • /api/export/json         │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │  Native Python Service Calls
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          AUTHORITATIVE PHYSICS BACKEND (services/*)                    │
│                                                                                        │
│  • climate_service.py     : 8,760-hour EPW meteorological weather reader (IMD/NREL)   │
│  • simulation_service.py  : 168-hr transient Forward Euler solver (dt = 60s)          │
│  • formulas.py            : ISO 6946 multi-layer U-value & thermal resistance solvers  │
│  • optimize.py            : Optuna TPE multi-objective Bayesian design optimizer      │
│  • recommender.py         : Area-specific auto-sizing & material heuristic rules       │
│  • material_service.py    : Database of physical material properties (k, ρ, cp, ε)     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. How the Frontend Connects to the Backend

### A. Network Routing via Vite Reverse Proxy
The frontend runs on `http://localhost:5173`, and the FastAPI backend runs on `http://127.0.0.1:8000`.
To avoid Cross-Origin Resource Sharing (CORS) blocks and IPv4/IPv6 address mismatches, Vite is configured with an internal reverse proxy in [`frontend/vite.config.ts`](file:///D:/SIH/frontend/vite.config.ts):

```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
```
When the frontend makes a request to `/api/simulation`, Vite forwards it directly to `http://127.0.0.1:8000/api/simulation`.

### B. Typed Client Layer
The frontend API client is located in [`frontend/src/api/client.ts`](file:///D:/SIH/frontend/src/api/client.ts). It enforces strict TypeScript typing for every request and response payload.

### C. State Management with Zustand
The application state is centralized in [`frontend/src/store/designStore.ts`](file:///D:/SIH/frontend/src/store/designStore.ts):
- **User Inputs**: Selected climate region, occupancy count, permanence mode (`Temporary` vs `Permanent`), length, width, height, roof profile, wall material, insulation thickness, and window area.
- **Backend Cache**: Holds the latest `climateData`, `simulationResult`, `optimizationResult`, and `comparisonResult`.
- **Reactive Updates**: When the user changes a parameter and clicks `[ SIMULATE ]`, the store calls the backend, updates the cache, and triggers instant re-renders of the 3D model, Recharts graphs, and telemetry cards.

---

## 3. Climate Regions Supported by the Backend

The platform supports 5 distinct Indian climatic zones derived from authentic EnergyPlus Weather (EPW), Indian Meteorological Department (IMD), and NREL NSRDB datasets:

| Region Key | Display Name | Climatic Classification | Elevation | Winter Design Temp | Summer Peak Temp | Annual Solar GHI | HDD (Base 18°C) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`leh`** | Leh, Ladakh | Alpine Severe Cold | 3,524 m | -18.5 °C | 25.0 °C | 2,100 kWh/m² | 4,850 HDD |
| **`jaisalmer`** | Jaisalmer, Thar | Hot & Arid Desert | 225 m | 7.0 °C | 46.0 °C | 2,250 kWh/m² | 850 HDD |
| **`chennai`** | Chennai Coast | Warm & Humid Tropical | 6 m | 20.0 °C | 38.0 °C | 1,950 kWh/m² | 120 HDD |
| **`delhi`** | Delhi NCR | Subtropical Composite | 216 m | 5.0 °C | 44.0 °C | 1,900 kWh/m² | 1,200 HDD |
| **`bengaluru`** | Bengaluru | Temperate Moderate Plateau | 920 m | 15.0 °C | 34.0 °C | 1,850 kWh/m² | 450 HDD |

### Climate Data Returned by Backend (`GET /api/climate/{city}`)
```json
{
  "city": "leh",
  "latitude": 34.15,
  "longitude": 77.58,
  "climate_type": "cold",
  "climate_description": "Alpine Severe Cold",
  "hourly_temperature": [-12.4, -13.1, -14.0, ...],   // 8,760 hours of outdoor ambient dry-bulb (°C)
  "hourly_direct_solar": [0.0, 0.0, 185.2, ...],      // 8,760 hours of direct beam solar flux (W/m²)
  "hourly_diffuse_solar": [0.0, 0.0, 62.1, ...],       // 8,760 hours of diffuse sky radiation (W/m²)
  "hourly_wind_speed": [2.1, 1.8, 2.5, ...],           // 8,760 hours of wind velocity (m/s)
  "hourly_humidity": [42.0, 44.5, 38.0, ...],          // 8,760 hours of relative humidity (%)
  "metadata": {
    "elevation": "3,524 m",
    "solar_ghi": "2,100 kWh/m²",
    "hdd": 4850,
    "source": "IMD Leh Station & NREL NSRDB / ASHRAE EPW Reference"
  }
}
```

---

## 4. What Values the Backend Gives to Output

When the user selects a climate and clicks `[ SIMULATE ]`, the frontend sends a `POST /api/simulation` request:

### Input Payload Sent to Backend:
```json
{
  "city": "leh",
  "length": 4.5,
  "width": 3.2,
  "height": 2.8,
  "wall_material": "brick",
  "insulation_thickness_m": 0.06,
  "window_area": 2.5,
  "glazing": "double_clear",
  "orientation": "south",
  "roof_type": "pitched",
  "occupants": 4,
  "hours_to_simulate": 168
}
```

### Full Output Values Returned by Backend:

The backend returns a comprehensive physical telemetry dictionary containing over 40 computed variables:

#### 1. Thermal Comfort Metrics (`comfort_metrics`, `comfort_hours`, `comfort_percentage`)
- `comfort_percentage`: Percentage of 168 hours the interior air temperature stays inside the ASHRAE 55 comfort band (18.0 °C to 24.0 °C). E.g., `78.5%`.
- `comfort_hours`: Total hours within 18–24 °C. E.g., `132.0 / 168 h`.
- `discomfort_degree_hours`: Cumulative degree-hours outside the comfort threshold ($\int |T_{\text{in}} - T_{\text{target}}| \, dt$). E.g., `412.5 °C·h`.
- `comfort_metrics.avg`: 168-hour mean interior air temperature. E.g., `19.8 °C`.
- `comfort_metrics.min_t`: Minimum recorded indoor temperature across the week. E.g., `14.2 °C`.
- `comfort_metrics.max_t`: Maximum recorded indoor temperature across the week. E.g., `23.9 °C`.
- `comfort_status`: Evaluated state: `"optimal"` | `"heating_required"` | `"cooling_required"`.

#### 2. Envelope Thermal Properties (`u_values`)
Computed according to ISO 6946 multi-layer conduction:
- `u_values.wall_u`: Total wall assembly heat transmission coefficient ($W/m^2K$). E.g., `0.380 W/m²K`.
- `u_values.roof_u`: Total roof assembly heat transmission coefficient ($W/m^2K$). E.g., `0.290 W/m²K`.
- `u_values.glass_u`: Glazing U-value. E.g., `2.800 W/m²K` (Double Clear).
- `u_values.wall_r_total`: Total thermal resistance ($m^2K/W$). E.g., `2.63 m²K/W`.
- `u_values.roof_r_total`: Total roof thermal resistance ($m^2K/W$). E.g., `3.45 m²K/W`.

#### 3. Energy Balance & Heat Losses (`component_heat_loss_kwh`, `total_heat_loss_kwh`)
Weekly cumulative energy exchange in kilowatt-hours (kWh):
- `total_heat_loss_kwh`: Cumulative thermal energy lost through all paths over 168 hours. E.g., `148.2 kWh`.
- `component_heat_loss_kwh.wall_loss_kwh`: Conduction through vertical walls. E.g., `42.5 kWh`.
- `component_heat_loss_kwh.roof_loss_kwh`: Conduction through ceiling / roof. E.g., `38.1 kWh`.
- `component_heat_loss_kwh.floor_loss_kwh`: Conduction to ground substrate. E.g., `18.4 kWh`.
- `component_heat_loss_kwh.window_loss_kwh`: Conduction through fenestration glass. E.g., `24.6 kWh`.
- `component_heat_loss_kwh.vent_loss_kwh`: Enthalpy loss due to air infiltration/ventilation. E.g., `24.6 kWh`.
- `integrated_solar_energy_kwh`: Total useful natural solar thermal energy admitted into the shelter through the glazed aperture. E.g., `86.4 kWh`.
- `integrated_incident_solar_kwh`: Total incident radiation hitting the aperture. E.g., `124.0 kWh`.

#### 4. 168-Hour Time-Series Arrays (for Recharts Graphs)
- `indoor_temperature`: Array of 168 floats representing indoor air temperature at each hour ($T_1, T_2, \dots, T_{168}$).
- `outdoor_temperature`: Array of 168 floats representing ambient temperature.
- `solar_thermal_gain`: Array of 168 floats of admitted solar heat flow in Watts ($W$).
- `solar_power`: Array of 168 floats of incident aperture power in Watts ($W$).
- `wall_heat_flow`: Hourly conduction loss through walls ($W$).
- `roof_heat_flow`: Hourly conduction loss through roof ($W$).
- `window_heat_flow`: Hourly conduction loss through glazing ($W$).
- `ventilation_heat_flow`: Hourly air exchange loss ($W$).

---

## 5. What Values the Backend Gives to the 3D Digital Twin

The 3D viewer ([`frontend/src/components/shelter/ShelterModel3D.tsx`](file:///D:/SIH/frontend/src/components/shelter/ShelterModel3D.tsx)) is built with **Three.js** and WebGL. It derives its visual geometry from the backend design and geometry models:

```typescript
<ShelterModel3D
  length={design.length}
  width={design.width}
  height={design.height}
  roofType={design.roofType}
  wallMaterial={design.wallMaterial}
  windowArea={design.windowArea}
  orientation={design.orientation}
/>
```

### Exact Mapping of Backend Data to 3D Geometry:

| Backend Parameter | Type | 3D Rendering Implementation |
| :--- | :--- | :--- |
| **`length`** | `float` (m) | Scales the 3D shelter along the **X-axis**. Substrate concrete slab is rendered with an offset: `BoxGeometry(length + 0.4, 0.2, width + 0.4)`. |
| **`width`** | `float` (m) | Scales the 3D shelter along the **Z-axis**. |
| **`height`** | `float` (m) | Sets the vertical height of exterior walls on the **Y-axis**: `BoxGeometry(length, height, width)`. |
| **`roof_type`** | `"pitched"` \| `"flat"` | **If `"pitched"`**: Generates a 30° gabled roof triangular prism using `THREE.ExtrudeGeometry` spanning the entire length with realistic eaves overhang (`0.25m`), plus front and rear triangular gable walls.<br>**If `"flat"`**: Renders a modular composite roof slab with a horizontal overhang (`0.20m`). |
| **`wall_material`** | `string` | Customizes Three.js shader material: color, roughness, and metalness.<br>• `brick`: Terracotta `#b45309`, roughness 0.85<br>• `stone`: Slate gray `#64748b`, roughness 0.90<br>• `concrete`: Industrial gray `#94a3b8`, roughness 0.80<br>• `puf_insulation`: Cyan insulated panel `#38bdf8`, roughness 0.40<br>• `wood`: Pine timber brown `#92400e`, roughness 0.70<br>• `mud`: Vernacular adobe brown `#78350f`, roughness 0.95 |
| **`window_area`** | `float` ($m^2$) | Calculates aperture dimensions: $\text{width} = \sqrt{\text{window\_area} \times 1.2}$, $\text{height} = \frac{\text{window\_area}}{\text{width}}$. Renders a physical glass panel with refraction, transmission (0.75), transparency, and dark aluminum frame. |
| **`orientation`** | `"south"` \| `"north"` \| ... | Places the glazed aperture on the corresponding facade. A 3D **North Arrow compass** (`THREE.ArrowHelper`) is rendered on the ground plane to illustrate orientation relative to solar azimuth. |

---

## 6. Optimization Values Returned to Frontend (`POST /api/optimization`)

When the user triggers Bayesian Optimization, Optuna executes TPE (Tree-structured Parzen Estimator) parameter sweeps in Python. The backend returns:

1. **`optimal_insulation_mm`**: Optimal PUF insulation thickness in millimeters. E.g., `120 mm`.
2. **`optimal_window_area_m2`**: Optimal south-facing window aperture in square meters. E.g., `3.2 m²`.
3. **`optimal_wall_material`**: Best performing wall assembly for the climate. E.g., `"brick"` (high thermal mass).
4. **`optimal_glazing`**: Optimal glazing type. E.g., `"double_low_e"`.
5. **`discomfort_score`**: Objective score minimized by Optuna.
6. **`ranked_designs`**: Array of the top 3 Pareto candidate designs with individual comfort, heat loss, and solar sub-scores.
7. **`explanation`**: Natural language engineering rationale explaining why this configuration was recommended based on climate physics.

Clicking **`[ APPLY RECOMMENDED DESIGN ]`** in the frontend immediately transfers these parameters into the active design state and updates the 3D model and simulation.

---

## 7. Verification & Health Checks

- **Backend Health Check**:
  `GET http://127.0.0.1:8000/api/health` → `{"status": "ok", "service": "ThermoShelter AI"}`
- **Automated Backend Test Suite**:
  Run `python -m pytest -q` in `D:\SIH` → **242 tests passing**.
- **Frontend Production Build**:
  Run `npm run build` in `D:\SIH\frontend` → **0 errors**.
- **Start All Services with One Click**:
  Double-click [`D:\SIH\start.bat`](file:///D:/SIH/start.bat) to launch both the FastAPI backend and Vite frontend together.
