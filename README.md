# 🌡️ ThermoShelter AI
### Area-Specific Passive Shelter Design & Thermal Simulation Platform

> **Explore climate-specific shelter designs before building them.**

ThermoShelter AI is an **engineering design studio prototype** for early-stage passive shelter design exploration. It combines a climate/weather intelligence pipeline, a reduced-order thermal simulation engine, rule-based passive-strategy guidance, Optuna optimization, parametric 2D blueprint drawings, an illustrative 3D digital twin, and an auto-generated engineering report — presented through a React design studio backed by a FastAPI physics service.

> **Important:** The current repository does **not** contain a trained AI/ML model, physical sensor validation, or ANSYS/CFD integration. The name "AI" refers to the intended intelligent design workflow; the current recommendation system is rule-based and optimization-driven. ANSYS (or other high-fidelity FEA/CFD verification) is a **future validation pathway**, not a current feature.

---

## 🎯 Problem Statement

Shelters can behave very differently under different climates. Choosing the right geometry, insulation, materials, glazing, orientation and ventilation assumptions is difficult when design decisions are made using generic shelter templates or disconnected calculations.

ThermoShelter AI addresses this early-stage design problem by connecting:

**Climate → Shelter Design → Passive Strategy → Thermal Simulation → Optimization → Blueprint / 3D / Report**

---

## 🚀 Key Features

- 🌍 **Location-resolved climate profiles** via the Open-Meteo pipeline (live / forecast / historical-reanalysis modes) with honest provenance labelling (`MODEL ANALYSIS`, `FORECAST`, `HISTORICAL REANALYSIS`, `DESIGN`, `FALLBACK` — never "measured")
- 🧭 **Climate-derived passive strategy** (e.g. EXTREME COLD solar-capture strategy for Leh, HOT DRY thermal-mass/nocturnal-flush strategy for Jaisalmer) with an annual-classification basis and read-only design comparison
- 🏠 **Parametric shelter design**: rectangular/cylindrical/dome/pyramid geometry (rectangular is physics-backed; other shapes are visualization-only), orientation, roof pitch, envelope layers, openings, glazing
- 🌡️ **168-hour transient thermal simulation** (Python 1D Forward Euler + ISO 6946 envelope U-values, authoritative backend)
- ☀️ **Solar-gain and heat-flow breakdown** (wall/roof/floor/window/door/ventilation/radiation, incident vs useful solar energy)
- 🤖 **Optuna TPE optimization** over a weighted multi-objective score (comfort / envelope efficiency / solar) across insulation, window area, wall material, glazing, orientation and thermal mass — plus optional **geometry + envelope search** with explicit prototype bounds and deterministic pre-simulation feasibility rejection
- 📊 **Real baseline vs candidate comparison** (the baseline is an actual simulation of the current canonical design, auto-run when missing or stale)
- 📐 **ISO 6946-style engineering blueprint** (floor plan, section, elevation, envelope detail — parametric SVG from the canonical design)
- 🧊 **Illustrative 3D digital twin** (Three.js / react-three-fiber, parameter-driven — an engineering visualization, not CFD/FEM output)
- 📄 **Auto-generated engineering report** with provenance, simulated/predicted labelling, honesty limitations section, and native print-to-PDF (A4)

---

## 🧮 Thermal Model

The engine is a **reduced-order, single-zone thermal model** (`services/simulation_service.py`). The shelter is one thermal node with heat entering and leaving through simplified pathways:

```text
Net Heat = Solar Gain + Internal Heat
           - Conduction - Ventilation - Radiation

Indoor Temperature
        ↓
   updated over time (forward Euler)
```

The implementation uses thermal resistance/U-values (ISO 6946 layer methodology), conduction, simplified solar glazing gain, ventilation heat exchange (ACH), internal gains, longwave radiation and lumped thermal capacitance with forward-Euler time stepping.

The comfort model is a simple **18–24 °C temperature band**. It is not PMV/PPD, CFD, or a humidity-coupled comfort model.

**All thermal outputs are simulated/predicted values — none are field measurements.**

---

## 🏛️ Architecture

Two-process architecture:

```text
React Design Studio (thermoshelter-design-studio, Vite dev server, port 5173)
        │  /api proxy (vite.config.js → http://127.0.0.1:8000)
        ↓
FastAPI Backend (backend/main.py, port 8000)
        │
        ├── backend/climate_routes.py        → location → weather → ClimateProfile → passive strategy
        ├── backend/simulation_routes.py     → canonical simulation (Forward Euler + ISO 6946)
        └── backend/optimization_routes.py   → Optuna TPE search + candidate feasibility
        │
        └── services/ (physics, climate, geometry, contracts, optimization engines)
```

Canonical data flow (single source of truth — the `ShelterDesign` contract):

```text
ShelterDesign → Simulation → Optimization → Candidate → Apply
             → Blueprint → 3D Twin → Engineering Report
```

Every stage renders from the same canonical design object; no stage invents conflicting geometry, material, or opening values.

---

## 📁 Project Structure

```text
sih-area-specific-shelter/
├── backend/                  # FastAPI application and route modules
├── services/                 # Physics/climate/geometry/optimization engines
├── data/
│   ├── climate/
│   ├── materials/            # materials.json, glazing.json
│   ├── shelters/
│   └── weather/              # bundled EPW benchmark files (leh, jaisalmer, delhi, …)
├── tests/                    # pytest suite (backend + contracts)
├── scripts/
│   ├── start-dev.ps1         # two-process dev launcher (Windows)
│   └── validate_data.py
├── docs/                     # equations.md, data_dictionary.md, engine specs
└── thermoshelter-design-studio/   # React + TypeScript + Vite + Tailwind frontend
    └── src/
        ├── components/       # stage UIs (design, simulation, blueprint, 3D, report…)
        ├── services/         # typed API client, report model, artifact capture
        ├── store/            # canonical studio state
        └── report/           # A4 print stylesheet
```

---

## 💻 Installation & Run

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Frontend dependencies

```bash
cd thermoshelter-design-studio
npm install
```

### 3. Start the backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 4. Start the frontend (in a second terminal)

```bash
cd thermoshelter-design-studio
npm run dev
```

Then open **http://localhost:5173**.

### One-command launcher (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-dev.ps1
```

### 5. API health check

```bash
curl http://127.0.0.1:8000/api/health
```

The frontend also shows live backend status in its context strip ("Backend" indicator).

---

## 🧪 Testing

Backend (pytest, from the repository root):

```bash
python -m pytest
```

Frontend (Vitest + TypeScript check + production build):

```bash
cd thermoshelter-design-studio
npm test
npx tsc --noEmit
npm run build
```

Dataset validation:

```bash
python scripts/validate_data.py
```

No unsupported accuracy or performance percentage is claimed here.

---

## ⚠️ Current Limitations

The current prototype is intentionally simplified:

- single-zone reduced-order thermal model (1D Forward Euler)
- 168-hour simulation horizon in the main workflows
- simplified radiation, solar and ventilation/infiltration modelling
- simple 18–24 °C comfort band (not PMV/PPD)
- rectangular shape is physics-backed; cylindrical/dome/pyramid shapes are **visualization-only** (they do not reach the thermal engine)
- geometry search uses **proposed prototype optimization bounds** (4–10 m length, 3–6 m width, 2.4–4.0 m clear height, aspect ratio ≤ 3.0) — these are prototype assumptions, not DRDO/regulatory/ISO requirements
- shape optimization and continuous geometry optimization are **not currently implemented**
- weather is model-derived (Open-Meteo NWP analysis / forecast / historical reanalysis / bundled design data) — **not measured on-site sensor data**
- **no ANSYS/CFD/FEM integration** and no physical sensor validation; ANSYS-class high-fidelity verification remains a future pathway
- no field calibration

Therefore, ThermoShelter AI is for **early-stage design exploration and decision support**, not final engineering certification or construction approval.

---

## 🚧 Future Scope

Planned upgrades include:

- annual/seasonal simulation
- more climate locations
- improved solar and thermal-mass modelling
- humidity and adaptive comfort modelling
- high-fidelity verification (e.g. ANSYS/CFD) and measured-field calibration
- CAD/BIM export

These are **future capabilities**, not current features.

---

## 👥 Team Rocket

| Member | Role |
|---|---|
| **M. Yagneshwar** | Team Leader |
| **Hari Prabhat Kumar** | Team Member |
| **Shaik Sohail** | Team Member |
| **K. M. Shanthan** | Team Member |
| **Syed Abid Ali** | Team Member |
| **K. Trishathi** | Team Member |

---

## 🏆 Smart India Hackathon 2026

**Project:** ThermoShelter AI  
**Team:** Rocket  
**Theme:** Area-Specific Passive Shelter Design & Thermal Simulation

The repository documents the current prototype implementation. Official challenge IDs and other competition metadata are intentionally omitted unless verified from the official project information.

---

## 📚 References

Technical references used by the repository include:

- ISO 6946 — Thermal resistance and transmittance
- IS 3792 — Thermal performance of buildings
- ASHRAE Handbook — Fundamentals
- ASHRAE Standard 55 — Thermal comfort
- EN 673 — Glass thermal performance
- NFRC 100 / 200 — Fenestration performance
- BIPM SI Brochure — SI units
- CODATA physical constants

Project-specific equations and data definitions are documented in `docs/equations.md` and `docs/data_dictionary.md`.

---

## ⚖️ Disclaimer

ThermoShelter AI provides **simulation-based estimates for early-stage design exploration**. Results depend on model assumptions and supplied data and should not be treated as structural, HVAC, fire-safety, building-code, or professional engineering certification.

---

### ThermoShelter AI
**Climate-aware design. Physics-based exploration. Transparent optimization.**
