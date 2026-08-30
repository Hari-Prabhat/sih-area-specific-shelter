# 🌡️ ThermoShelter AI

### Area-Specific Passive Shelter Design & Thermal Simulation Platform

> **Explore shelter designs for the climate they will face — before building them.**

ThermoShelter AI is a **Python + Streamlit prototype** for early-stage passive shelter design exploration. It combines a reduced-order thermal simulation, local climate/weather files, a material database, rule-based climate recommendations, parametric optimization, and interactive 2D/3D visualizations in one workflow.

The current implementation is designed to help a user compare shelter concepts and understand **how geometry, insulation, glazing, orientation, materials, solar gains, and heat-loss pathways affect modeled indoor temperature**.

> **Implementation note:** despite the product name, the inspected repository does **not** contain a trained AI/ML model. The current recommendation pipeline uses deterministic rules plus **Optuna TPE-based numerical optimization**. No live EnergyPlus, ANSYS, NASA, or IMD API integration is implemented.

---

## 🏆 Smart India Hackathon 2026

| Item | Details |
|---|---|
| **Competition** | Smart India Hackathon 2026 |
| **Project** | ThermoShelter AI |
| **Focus** | Area-specific passive shelter design and thermal simulation |
| **Team** | **Rocket** |
| **Current stage** | Working prototype / MVP |

This README describes the implementation currently present in the repository. Official SIH challenge identifiers or other competition metadata are intentionally not invented here.

---

## 1. 🎯 Problem Statement

Shelters used in disaster response, remote locations, field operations, and difficult climates are often selected or designed from generic configurations. A design that works reasonably well in one climate may perform very differently somewhere else.

For a shelter, small design decisions can change the thermal response:

- wall material and insulation thickness
- window area and glazing type
- shelter geometry and roof form
- orientation and passive solar exposure
- occupant heat gains
- ventilation/infiltration assumptions
- local outdoor temperature and solar conditions

The practical problem is not simply **“Can this shelter be simulated?”**. It is:

> **“Which shelter configuration is worth exploring for this climate and set of requirements?”**

High-fidelity building and CFD tools can answer detailed engineering questions, but they generally require more specialist setup. On the other end, a basic spreadsheet or calculator may not provide an integrated path from **climate → design → simulation → comparison → recommendation → visualization**.

ThermoShelter AI targets that early design-space exploration gap.

---

## 2. 💡 Our Solution

ThermoShelter AI brings the main early-stage steps into a single Streamlit application:

```text
User Requirements
       ↓
Climate / Weather Data
       ↓
Auto-Sizing + Climate Rules
       ↓
Material / Glazing / Geometry Choices
       ↓
Reduced-Order Thermal Simulation
       ↓
Comfort + Heat-Loss Metrics
       ↓
Parametric Optimization / Comparison
       ↓
Recommended or Compared Designs
       ↓
2D Floor Plan + Interactive 3D Model
```

The goal is **fast, explainable design exploration**, not final structural, mechanical, or building-code certification.

---

## 3. ⚙️ How ThermoShelter AI Works

The application currently has four main user workflows.

### A. Design a Shelter

The user selects a supported location, number of occupants, and temporary/permanent use. The app then:

1. classifies the climate
2. auto-sizes a starting shelter geometry
3. applies climate-specific rule-based envelope guidance
4. searches design parameters with Optuna TPE
5. verifies the selected design with the main thermal simulation
6. displays thermal, solar, comfort, heat-loss, and geometry results
7. renders a 2D floor plan and 3D climate-adaptive model

### B. Improve a Shelter

The app runs a **baseline vs optimized** comparison using the same auto-sized geometry and occupancy:

```text
Baseline
- brick wall
- no added insulation
- single-clear glazing
- 2.0 m² window area
- south orientation

              VS

Optimized
- optimizer-selected insulation
- optimizer-selected window area
- optimizer-selected wall material
- optimizer-selected glazing
- optimizer-selected orientation
```

The comparison shows scenario-specific differences in comfort and modeled heat loss.

### C. Choose Materials

The Material Comparison Studio runs the same 168-hour simulation setup across the loaded candidate materials and presents thermal curves, U-values, temperature statistics, comfort metrics, discomfort degree-hours, and modeled heat loss.

### D. Compare Shelter Types

The app includes five simulation archetypes:

- rectangular flat roof
- rectangular pitched roof
- compact shelter
- elongated shelter
- custom dimensions

The standard archetypes can also be benchmarked after scaling them to the same floor area, so form-related differences can be compared more fairly.

---

## 4. 🚀 Key Features

| Feature | Current implementation |
|---|---|
| Climate-specific scenarios | Five active UI locations with climate mappings |
| Auto-sizing | Geometry calculated from occupants and permanence |
| Thermal simulation | Reduced-order transient model, up to 168 hours in the UI flows |
| Thermal comfort | Static 18–24 °C comfort band and degree-hour discomfort metric |
| Heat-flow breakdown | Walls, roof, floor, glazing, ventilation and radiation |
| Solar analysis | Hourly irradiance, incident window power and useful glazing gain |
| Material comparison | Batch simulation over the loaded materials database |
| Optimization | Optuna TPE search over insulation, window area, material, glazing and orientation |
| Recommendations | Climate mapping + rule-based guidance + optimized parameter selection |
| Baseline comparison | Standardized baseline vs optimized scenario |
| Shelter archetypes | Flat, pitched, compact, elongated and custom forms |
| 2D visualization | Plotly floor-plan view |
| 3D visualization | Plotly Mesh3d climate-adaptive shelter model |
| Data validation | Dedicated validation script for bundled datasets |
| Automated tests | Formula, simulation and 3D visualization test suites |

---

## 5. 🧾 User Inputs

### Shelter Designer

The current UI asks for:

| Input | Current range / choices |
|---|---|
| Location | Leh, Chennai, Delhi, Jaisalmer, Bengaluru |
| Occupants | 1–10 |
| Permanence | Temporary / Permanent |

The recommendation workflow then derives the starting geometry and optimization variables internally.

### Shelter Archetype Workflow

| Input | Current range / choices |
|---|---|
| Climate zone | Five active locations |
| Shelter archetype | Four predefined models + custom dimensions |
| Occupants | 1–8 |
| Custom length | 2.5–10.0 m |
| Custom width | 2.5–10.0 m |
| Custom height | 2.2–4.0 m |
| Custom roof | Flat / pitched |

### Material Comparison Studio

| Input | Current range / choices |
|---|---|
| Climate zone | Five active locations |
| Added insulation | 0–200 mm |
| Window area | 1–10 m² |
| Occupants | 1–8 |

---

## 6. 📊 Simulation Outputs

The thermal engine returns and the UI exposes results including:

| Output | Meaning |
|---|---|
| Indoor temperature series | Modeled hourly indoor temperature |
| Outdoor temperature series | Weather temperature used by the simulation |
| Solar irradiance | Sum of direct and diffuse solar inputs used by the engine |
| Incident solar power | Solar power incident on the modeled window area |
| Useful solar thermal gain | Solar heat admitted through glazing in the model |
| Wall heat flow | Modeled conductive wall heat transfer |
| Roof heat flow | Modeled conductive roof heat transfer |
| Floor heat flow | Modeled floor heat transfer |
| Window heat flow | Modeled glazing heat transfer |
| Ventilation heat flow | Sensible heat exchange associated with ACH |
| Radiation heat flow | Simplified longwave radiation term |
| Net heat flow | Net thermal balance used for the temperature update |
| Average / minimum / maximum indoor temperature | Summary temperature statistics |
| Comfort hours / percentage | Time inside the 18–24 °C band |
| Discomfort degree-hours | Accumulated temperature exceedance outside the band |
| Integrated solar energy | Useful modeled solar gain in kWh |
| Component heat-loss totals | Positive modeled losses in kWh by component |
| Envelope U-values | Wall, roof, floor and glazing transmittance values |
| Geometry metrics | Floor area, volume, wall area, roof area and window area |

### Important distinction

The simulation reports **modeled thermal energy flows and losses**. These are not the same thing as measured field energy consumption. The current UI does not provide a verified whole-building energy-use model or a measured fuel-consumption prediction.

---

## 7. 🧮 Thermal / Physics Model — In Simple Terms

The current simulator is a **reduced-order, single-zone thermal model**. Think of the shelter as one thermal node whose temperature changes when heat enters or leaves.

The core energy balance is approximately:

$$
C_{thermal}\frac{dT_{in}}{dt}
=
Q_{solar}+Q_{internal}
-Q_{conduction}-Q_{ventilation}-Q_{radiation}
$$

### Geometry

For the rectangular base geometry:

$$A_{floor}=L\times W$$

$$V=L\times W\times H$$

$$A_{wall}=2(L+W)H$$

For pitched roofs, the code additionally calculates roof slope area, gable area, ridge height, total height, and added roof volume.

### Thermal resistance and U-value

For each material layer:

$$R_i=\frac{L_i}{k_i}$$

The assembly resistance is:

$$R_{total}=R_{inside}+\sum_i\frac{L_i}{k_i}+R_{outside}$$

and:

$$U=\frac{1}{R_{total}}$$

So, in simple terms, **more resistance means less conductive heat transfer**.

### Conductive heat flow

$$
Q_{conduction}=U\,A\,(T_{in}-T_{out})
$$

The code applies this idea to walls, roof, floor, and windows.

### Solar gain through glazing

The MVP uses a lumped glazing equation:

$$
Q_{solar,glazing}=I\,A_{window}\,SHGC\,F
$$

where the orientation factor is a simplified representation of solar exposure.

### Ventilation / infiltration

The model derives airflow from air changes per hour:

$$
\dot V=\frac{ACH\,V}{3600}
$$

and then calculates sensible heat exchange as:

$$
Q_{vent}=\rho\,\dot V\,c_p\,(T_{in}-T_{out})
$$

### Internal heat

The model uses an occupant heat-gain baseline of **80 W/person** and adds a fixed **40 W** base equipment/lighting allowance in the simulation service.

### Longwave radiation

The simulation includes a simplified Stefan–Boltzmann radiation term using the outdoor temperature as the surrounding boundary and a fixed emissivity value in the simulation loop.

### Thermal capacitance and time stepping

The current simulation uses a **lumped thermal capacitance** and an explicit **forward-Euler** update:

$$
T_{t+\Delta t}=T_t+\frac{Q_{net}\Delta t}{C_{thermal}}
$$

Normal simulation runs use sub-hour timesteps internally, while results are recorded hourly. The UI workflows model **168 hours (7 days)**.

### Comfort model

Comfort is currently a simple temperature band:

```text
Below 18 °C      → Too Cold
18–24 °C         → Comfortable
Above 24 °C      → Too Hot
```

This is **not** a full PMV/PPD, adaptive comfort, humidity-coupled, or CFD-based comfort calculation.

---

## 8. 🧱 Material Database & Comparison

The repository contains `data/materials/materials.json` with structured properties for each material, including:

- density
- thermal conductivity
- specific heat
- emissivity
- solar absorptivity
- indicative cost estimate
- source / notes
- typical, minimum and maximum values

The material loader also supports common aliases such as `brick`, `concrete`, `puf_insulation`, `eps_insulation`, `xps_insulation`, `stone`, `mud`, `adobe`, and `wood` when the corresponding database material exists.

### How comparison works

The Material Comparison Studio keeps the main scenario fixed and simulates candidate wall materials through the same thermal engine. It then compares:

```text
Material
   ↓
Thermal Conductivity / U-Value
   ↓
168-Hour Indoor Temperature
   ↓
Comfort + Discomfort
   ↓
Modeled Component Heat Loss
```

This is useful for **relative scenario comparison**, but it should not be interpreted as a field-certified material performance ranking.

### Glazing database

A separate `data/materials/glazing.json` file stores richer glazing metadata, including U-value, SHGC, thickness, visible transmittance, sources, and notes.

However, the **active simulation path currently uses four glazing presets defined directly in `services/simulation_service.py`**:

| Simulation preset | U-value used by engine | SHGC used by engine |
|---|---:|---:|
| Single clear | 5.80 W/m²·K | 0.82 |
| Double clear | 2.80 W/m²·K | 0.70 |
| Double low-E | 1.80 W/m²·K | 0.50 |
| Triple low-E | 1.00 W/m²·K | 0.35 |

The JSON glazing dataset and the active simulation presets therefore should not be treated as identical sources of truth for runtime glazing values.

---

## 9. ☀️ Climate Data

The active simulation service reads local EPW weather files from:

```text
data/weather/
├── leh.epw
├── chennai.epw
├── delhi.epw
├── jaisalmer.epw
└── bengaluru.epw
```

`services/climate_service.py` uses `pvlib.iotools.read_epw` to read the weather file and extract:

- air temperature
- direct normal irradiance
- diffuse horizontal irradiance
- wind speed
- relative humidity
- location metadata from the EPW file

### Current active locations

| Location | Climate mapping in the app |
|---|---|
| Leh | Cold |
| Jaisalmer | Hot-dry |
| Chennai | Hot-humid |
| Delhi | Composite |
| Bengaluru | Moderate |

The repository also contains `data/climate/locations.json` with broader location metadata, including locations such as Kargil, Srinagar, and Mumbai. Those records do **not** automatically mean that the current Streamlit simulation UI supports them; the active UI is tied to the five locations above and their local EPW files.

There is also a companion `data/climate/weather.csv` dataset and a `data_loader.py` interface for loading standardized climate records. These are part of the repository data layer and should not be confused with a live external weather API.

> **No live IMD/NASA/other weather API is used by the current application.** Source strings present inside the JSON datasets are metadata references, not runtime integrations.

---

## 10. 🧠 Optimization & Recommendation System

### Optimization

`services/optimize.py` uses **Optuna's TPE sampler** with a fixed seed of `42`.

The optimizer searches these variables:

| Variable | Search space in current code |
|---|---|
| Insulation thickness | 0–0.25 m, 0.005 m steps |
| Window area | 0.5 m² to a geometry-dependent upper bound, 0.1 m² steps |
| Wall material | `brick`, `concrete`, `puf_insulation` when set to auto |
| Glazing | single, double, double low-E, triple low-E |
| Orientation | south, north, east, west |

The optimization objective is to **minimize discomfort degree-hours** from the simulated 168-hour scenario.

The optimizer uses a faster 15-substep-per-hour simulation for candidate trials, then the selected design is run again through the normal simulation path for the displayed result.

### Recommendation layer

`services/recommender.py` adds deterministic climate logic before optimization:

```text
Location
   ↓
Climate Classification
   ↓
Auto-Size from Occupancy + Permanence
   ↓
Rule-Based Material / Roof / Orientation Guidance
   ↓
Optuna Parameter Search
   ↓
Best Candidate
   ↓
Climate-Specific Explanation
```

The climate recommendation rules are currently mapped for five city names. They are **rules encoded in Python**, not a trained machine-learning system.

---

## 11. 🏗️ 2D / 3D Visualization

### 2D

The Streamlit app generates an interactive Plotly floor-plan view showing the shelter footprint and fenestration/orientation context used by the UI.

### 3D

`services/visual3d.py` builds an interactive Plotly `Mesh3d` model. Depending on climate, the visualization may include features such as:

- pitched or flat roof form
- doors and windows
- climate-specific roof/exterior styling
- snow-cap and thermal vestibule visuals for the cold scenario
- reflective-roof and parapet visuals for the hot-dry scenario
- verandah, ridge-vent and trees in the hot-humid visualization
- landscaping in the moderate scenario
- a human scale reference
- sun indicator and north compass

Users can rotate, zoom, pan, and inspect the interactive model in the Streamlit page.

> The 3D view is an **architectural/communication visualization**, not a structural analysis, BIM model, CFD mesh, or construction-ready drawing.

---

## 12. 🔍 Existing Solutions & the Gap

ThermoShelter AI sits between two common categories of tools:

| Existing approach | Strength | Gap addressed by this project |
|---|---|---|
| High-fidelity building / CFD simulation tools | Detailed engineering analysis | Higher setup complexity for rapid early-stage exploration |
| Generic calculators / spreadsheets | Simple scenario calculations | Less integrated design comparison and visualization |
| Static shelter templates | Fast deployment decisions | Limited thermal scenario exploration across alternatives |
| ThermoShelter AI | Climate + design + reduced-order simulation + comparison + visualization | Intended as an early-stage decision-support layer, not a replacement for specialist tools |

The project is **not claiming that existing engineering software is inadequate**. The narrower opportunity is to make early design exploration easier for users who need to compare shelter concepts before moving to detailed engineering.

---

## 13. ⭐ USP — What Makes ThermoShelter AI Different?

### 1. From “simulate this” to “compare what to try”

The platform connects simulation with a search process rather than presenting a single isolated thermal result.

### 2. Climate-first workflow

The same interface can switch between cold, hot-dry, hot-humid, composite, and moderate scenarios currently represented in the application.

### 3. Explainable by construction

The equations, constants, optimization variables, data files, and recommendation rules are visible in the repository. Users do not have to trust a hidden prediction model.

### 4. One workflow for multiple design dimensions

Materials, insulation, window area, orientation, geometry, comfort and thermal losses can be explored without manually wiring together several separate analysis steps.

### 5. Visualization alongside numbers

The project combines metric dashboards and thermal plots with a 2D floor plan and interactive 3D representation.

### 6. Honest model boundary

The project deliberately positions the current model as **reduced-order early-stage decision support**, leaving high-fidelity verification and measured validation as later stages.

---

## 14. 🛠️ Technology Stack

| Layer | Technology actually present in the repository |
|---|---|
| Application UI | Streamlit |
| Visualization | Plotly |
| Programming language | Python |
| Numerical computing | NumPy |
| Data handling | Pandas |
| Weather file parsing | pvlib (`pvlib.iotools.read_epw`) |
| Optimization | Optuna (TPE sampler) |
| Testing | pytest |
| Data formats | JSON, CSV, EPW |

### What is **not** currently in the stack

- React / Vite frontend
- FastAPI backend
- Three.js / React Three Fiber
- EnergyPlus runtime integration
- ANSYS runtime integration
- live IMD/NASA weather API
- trained TensorFlow/PyTorch/scikit-learn model

---

## 15. 🏛️ System Architecture

```text
                         ┌──────────────────────┐
                         │      USER / JUDGE     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Streamlit app.py  │
                         │  UI + charts + views │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      ┌──────────────┐     ┌─────────────────┐    ┌────────────────┐
      │ Climate /    │     │ Recommendation  │    │ Optimization   │
      │ Data Loader  │     │ + Auto-Sizing   │    │ (Optuna TPE)   │
      └──────┬───────┘     └────────┬────────┘    └───────┬────────┘
             │                       │                     │
             └───────────────────────┼─────────────────────┘
                                     ▼
                         ┌──────────────────────┐
                         │ simulation_service.py│
                         └──────────┬───────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │ Geometry +   │    │ Thermal +    │    │ Solar +      │
        │ U-values     │    │ Ventilation  │    │ Radiation    │
        └──────────────┘    └──────────────┘    └──────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Comfort + Energy     │
                         │ Metrics / Results    │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
              ┌──────────────┐             ┌──────────────┐
              │ Plotly Charts│             │ 2D + 3D View  │
              └──────────────┘             └──────────────┘
```

The `services/` layer is the main computational core; `app.py` is the Streamlit presentation and orchestration layer.

---

## 16. 📁 Actual Project Structure

The structure below reflects the repository currently inspected:

```text
sih-area-specific-shelter/
│
├── .streamlit/
│   └── config.toml
│
├── app.py
├── data_loader.py
│
├── data/
│   ├── climate/
│   │   ├── locations.json
│   │   └── weather.csv
│   │
│   ├── materials/
│   │   ├── glazing.json
│   │   └── materials.json
│   │
│   ├── shelters/
│   │   └── templates.json
│   │
│   └── weather/
│       ├── bengaluru.epw
│       ├── chennai.epw
│       ├── delhi.epw
│       ├── jaisalmer.epw
│       └── leh.epw
│
├── services/
│   ├── __init__.py
│   ├── climate_service.py
│   ├── comfort.py
│   ├── formula_constants.py
│   ├── formulas.py
│   ├── geometry.py
│   ├── material_service.py
│   ├── optimize.py
│   ├── recommender.py
│   ├── simulation_service.py
│   ├── solar.py
│   ├── thermal.py
│   ├── ventilation.py
│   ├── visual3d.py
│   │
│   └── tests/
│       ├── test_formulas.py
│       ├── test_simulation_service.py
│       └── test_visual3d.py
│
├── docs/
│   ├── data_dictionary.md
│   └── equations.md
│
├── scripts/
│   └── validate_data.py
│
├── .gitignore
└── README.md
```

> The repository currently does **not** include a `requirements.txt`, `pyproject.toml`, Dockerfile, or Docker Compose file. Installation below therefore uses the libraries imported by the application and test code rather than referencing a non-existent dependency file.

---

## 17. 💻 Installation & Setup

### Prerequisites

Use a recent Python 3 installation and Git.

Create and activate a virtual environment from the repository root:

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install the Python packages required by the current code:

```bash
python -m pip install --upgrade pip
python -m pip install streamlit plotly numpy pandas pvlib optuna pytest
```

The repository does not currently provide a lock file or pinned dependency manifest, so versions may vary between environments.

---

## 18. ▶️ How to Run

From the repository root:

```bash
streamlit run app.py
```

Streamlit will print the local URL in the terminal. Open that address in a browser.

The `.streamlit/config.toml` file configures the current application theme and Streamlit server behavior.

---

## 19. 🧭 How to Use

### Design a Shelter

1. Open **Design a Shelter**.
2. Select one of the five active locations.
3. Choose the number of occupants.
4. Select **Temporary** or **Permanent**.
5. Click **Generate Climate-Optimized Design**.
6. Review the simulated temperature, comfort, solar and heat-loss results.
7. Inspect the recommended envelope specification.
8. Explore the 2D floor plan and interactive 3D model.

### Improve a Shelter

1. Open **Improve a Shelter**.
2. Select location, occupants and permanence.
3. Run the comparative benchmark.
4. Compare baseline and optimized temperature response, comfort and modeled heat loss.

### Choose Materials

1. Open **Choose Materials**.
2. Select a climate zone.
3. Set insulation thickness, window area and occupants.
4. Run the material evaluation.
5. Compare the thermal curves and summary table.

### Compare Shelter Types

1. Open **Compare Shelter Types**.
2. Select a climate and shelter archetype.
3. Use custom dimensions when needed.
4. Run the archetype simulation.
5. Review the 3D model, thermal results and cross-archetype matrix.

---

## 20. 🧪 Validation & Testing

The repository contains three main automated test areas.

### Formula tests — `services/tests/test_formulas.py`

These test deterministic calculations such as:

- temperature conversion
- floor area, wall area and volume
- thermal resistance and U-value
- conduction
- solar gain
- ventilation heat loss
- thermal capacity
- radiation
- internal heat gain
- net heat flow
- heating requirement helper
- comfort metrics
- design scoring
- unit conversions
- formula registry / metadata

### Simulation tests — `services/tests/test_simulation_service.py`

These cover checks such as:

- U-value calculations
- numerical stability over a 168-hour run
- insulation impact
- component heat-flow outputs
- compatibility of `simulate_shelter`
- glazing and orientation effects
- optimizer return structure
- SIH-required simulation fields
- pitched-roof geometry
- multiple shelter models

### 3D visualization tests — `services/tests/test_visual3d.py`

These check climate-specific rendering behavior for the five supported climate styles and verify that the 3D figure contains expected components.

### Dataset validator — `scripts/validate_data.py`

The validator checks the bundled locations, weather CSV, material database, glazing database, and shelter templates for required fields, duplicate IDs, basic ranges, and other physical/data consistency constraints.

Run it with:

```bash
python scripts/validate_data.py
```

Run the automated tests with:

```bash
python -m pytest services/tests
```

> The repository contains the tests and validation tooling described above. This README does **not** claim a particular pass rate or benchmark result because no fresh test-run report is being fabricated here.

---

## 21. ⚠️ Limitations

The current prototype has important boundaries.

### Thermal model limitations

- It is a reduced-order, single-node model rather than CFD.
- Thermal behavior is spatially lumped; individual wall/roof temperature fields are not solved.
- Radiation is simplified and uses a fixed emissivity and outdoor-air boundary representation.
- Solar gain through glazing uses a lumped SHGC and orientation factor rather than full solar geometry for every surface.
- Thermal capacitance is simplified rather than modeling a detailed multi-layer transient mass distribution.
- Ventilation modeling is sensible-only; latent moisture effects are not included.
- Wind speed and relative humidity are loaded from weather data, but they are not fully coupled into the current thermal balance.
- The current UI workflows use a 168-hour horizon rather than a full annual building simulation.

### Data limitations

- The active UI exposes five locations.
- Weather data is bundled locally; there is no live weather service.
- The repository has both a glazing JSON database and separate in-code simulation glazing presets, so those datasets are not completely unified in the runtime path.
- Material properties are database values/assumptions and are not automatically calibrated to a specific manufacturer's product or field installation.

### Visualization limitations

- The 3D model is an interactive presentation model, not a construction drawing.
- Visual climate features do not replace detailed structural, moisture, wind, fire, or snow-load analysis.

### Recommendation limitations

- The rule-based recommendation layer is encoded logic, not a trained ML predictor.
- The optimizer minimizes the selected discomfort metric for the configured simulation scenario; it is not a guarantee of globally optimal real-world construction.

---

## 22. 🛡️ Risks & Mitigation

| Risk | Why it matters | Current mitigation |
|---|---|---|
| Simplified physics is over-trusted | Users may treat estimates as certification | Explicit model limits and early-stage positioning |
| Incorrect or inconsistent source data | Can distort recommendations | Structured datasets + validation script + source fields |
| Optimizer finds a scenario-specific solution | A mathematically good result may not be practically best | Show design parameters and comparison outputs instead of hiding the search |
| Too little climate coverage | Some deployment locations may not be represented | Explicit supported-location list and local data files |
| Dependency drift | Missing/pending versions can make setup inconsistent | Documented manual install command; future dependency lock planned |
| Visual model mistaken for engineering model | Architectural appearance can imply precision | README explicitly labels 3D output as visualization only |

---

## 23. 🚧 Future Upgrades

The following are **planned/future capabilities, not current integrations**:

- annual and seasonal simulation modes
- more locations and climate datasets
- dynamic solar-position and surface-orientation modeling
- improved roof, wall and thermal-mass transient models
- humidity and latent heat coupling
- PMV/PPD and adaptive thermal comfort options
- better wind/airflow modelling
- high-fidelity CFD verification
- EnergyPlus / OpenFOAM / ANSYS comparison workflows
- sensor-based calibration against measured shelters
- live weather/API integrations after validation
- more formal cost and multi-objective optimization
- Pareto-front design exploration
- construction/material availability constraints for remote deployments
- versioned dependency manifests and automated CI
- exportable design reports and structured project files
- richer BIM/CAD interoperability

These items should only be described as implemented after corresponding code and data integrations are added to the repository.

---

## 24. 👥 Target Users & Use Cases

ThermoShelter AI is aimed at users who need to **screen shelter concepts early**, including:

- disaster-response and relief planning teams
- field and remote-site planners
- architects and building-design teams during concept development
- engineering students and researchers exploring passive thermal behavior
- organizations evaluating temporary vs permanent shelter concepts
- teams working in cold, hot-dry, hot-humid, composite, or moderate Indian climates represented by the current dataset

### Example use cases

**High-altitude shelter:** compare insulation, glazing and orientation choices for a Leh scenario.

**Rapid-response shelter:** explore a lightweight temporary geometry and compare its modeled thermal response.

**Material selection:** keep climate and geometry fixed and compare alternative envelope materials.

**Form selection:** compare flat-roof, pitched, compact and elongated archetypes under a common floor area.

---

## 25. 🌱 Sustainability Impact

The project is intended to support sustainability by making **passive-design alternatives easier to compare before construction**.

Potential contribution areas include:

- encouraging better use of passive solar gains where appropriate
- encouraging insulation and envelope optimization
- exposing heat-loss pathways before construction decisions are finalized
- reducing unnecessary physical design iterations
- supporting climate-resilient shelter concepts

These are **intended design benefits**, not measured environmental impact claims from field deployment. The current repository does not contain a validated carbon-savings or fuel-savings study.

---

## 26. 📚 References & Technical Basis

The repository itself is the primary reference for the implementation.

### Project documentation

- `docs/equations.md` — equations, variables, units and modelling assumptions
- `docs/data_dictionary.md` — dataset structures and standardized units
- `scripts/validate_data.py` — bundled-data validation rules

### Standards / technical references named in the repository

- ISO 6946 — thermal resistance and transmittance of building components
- IS 3792 — thermal performance / building-envelope reference used by the project
- ASHRAE Handbook — Fundamentals
- ASHRAE Standard 55 — thermal comfort reference
- EN 673 — glazing thermal performance reference
- NFRC 100 / 200 — fenestration performance references
- BIPM SI Brochure — SI unit basis
- CODATA 2018 — physical constant reference for the Stefan–Boltzmann constant used in code

### Software / library references

The implementation uses Streamlit, Plotly, NumPy, Pandas, pvlib, Optuna and pytest.

> Reference names stored in the data files or source comments describe the intended technical basis of the values/formulas; they do not imply that the application has performed external certification, formal standards compliance testing, or live API integration.

---

## 27. 👨‍💻 Team Rocket

| Member | Role |
|---|---|
| **M. Yagneshwar** | Team Leader |
| **Hari Prabhat Kumar** | Team Member |
| **Shaik Sohail** | Team Member |
| **K. M. Shanthan** | Team Member |
| **Syed Abid Ali** | Team Member |
| **K. Trishathi** | Team Member |

---

## 28. 📌 Current Project Status

### Implemented now

- Streamlit-based application in `app.py`
- five active climate/location scenarios in the UI
- local EPW climate loading through `pvlib`
- structured climate, material, glazing and shelter datasets
- centralized formula modules
- reduced-order 168-hour thermal simulation
- comfort and degree-hour metrics
- component heat-flow and energy summaries
- climate-based rule recommendations
- occupant-based auto-sizing
- Optuna TPE optimization
- baseline vs optimized workflow
- material comparison workflow
- shelter-archetype comparison workflow
- Plotly thermal/solar/heat-loss charts
- interactive 2D floor plan
- interactive 3D visualization
- automated formula, simulation and visualization tests
- bundled-data validation script

### Not yet implemented / not verified as production capability

- trained AI/ML prediction model
- live weather APIs
- EnergyPlus/ANSYS/CFD integration
- measured field calibration
- annual high-fidelity building simulation
- certified structural or building-performance analysis
- production dependency lock / CI pipeline
- construction-ready CAD/BIM output

---

## 29. ⚖️ Disclaimer

ThermoShelter AI is an **early-stage design exploration and decision-support prototype**.

Its thermal results are based on simplified assumptions, bundled datasets, and a reduced-order physics model. Results should **not** be used as the sole basis for:

- structural design
- snow/wind-load certification
- fire or life-safety approval
- building-code certification
- detailed HVAC sizing
- moisture / condensation certification
- final material specification
- construction drawings
- professional engineering sign-off

Real projects should be reviewed and validated by appropriately qualified architects and engineers using site-specific data, applicable codes, detailed modelling, and field evidence.

---

## 30. 🔭 Long-Term Vision

The long-term goal is to grow ThermoShelter AI into an evidence-backed design-support platform that can answer a practical question:

> **Given a location, climate, occupancy, shelter type and design constraints, which passive shelter concepts are worth taking forward to detailed engineering?**

The intended evolution is:

```text
Local / Reference Climate Data
            ↓
Rapid Reduced-Order Screening
            ↓
Multi-Objective Design Exploration
            ↓
High-Fidelity Verification
            ↓
Measured Field Calibration
            ↓
Evidence-Backed Climate-Specific Design Guidance
```

The current prototype is the **screening and exploration stage** of that vision.

---

## ❤️ ThermoShelter AI

**Climate-aware design. Physics-based exploration. Transparent optimization. Interactive visualization.**

> **Design for the climate — and understand the thermal consequences before you build.**
