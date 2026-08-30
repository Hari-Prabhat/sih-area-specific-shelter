# 🌡️ ThermoShelter AI
### Area-Specific Passive Shelter Design & Thermal Simulation Platform

> **Explore climate-specific shelter designs before building them.**

ThermoShelter AI is a **Python + Streamlit prototype** for early-stage passive shelter design exploration. It combines local climate data, a reduced-order thermal model, material comparison, rule-based recommendations, Optuna optimization, and interactive 2D/3D visualization.

> **Important:** The current repository does **not** contain a trained AI/ML model or live EnergyPlus, ANSYS, NASA, or IMD API integration. The name “AI” refers to the intended intelligent design workflow; the current recommendation system is rule-based and optimization-driven.

---

## 🎯 Problem Statement

Shelters can behave very differently under different climates. Choosing the right geometry, insulation, materials, glazing, orientation and ventilation assumptions is difficult when design decisions are made using generic shelter templates or disconnected calculations.

ThermoShelter AI addresses this early-stage design problem by connecting:

**Climate → Shelter Design → Thermal Simulation → Optimization → Comparison → Visualization**

---

## 💡 Our Solution

The platform lets users explore climate-specific shelter concepts and understand their modeled thermal performance before moving to detailed engineering.

```text
User Inputs
    ↓
Climate + Weather Data
    ↓
Auto-Sizing + Climate Rules
    ↓
Material / Geometry / Glazing
    ↓
Reduced-Order Thermal Simulation
    ↓
Comfort + Heat-Loss Metrics
    ↓
Optuna Optimization / Comparison
    ↓
2D Floor Plan + 3D Visualization
```

---

## 🚀 Key Features

- 🌍 **5 active climate locations:** Leh, Jaisalmer, Delhi, Chennai, Bengaluru
- 🏠 **Shelter auto-sizing** based on occupants and temporary/permanent use
- 🌡️ **168-hour transient thermal simulation**
- 🧱 **Material database and comparison**
- 🪟 **Glazing and window-area exploration**
- ☀️ **Solar-gain and heat-flow analysis**
- 🧭 **Orientation comparison**
- 🤖 **Optuna TPE optimization** for reduced discomfort degree-hours
- 📊 **Baseline vs optimized design comparison**
- 🏗️ **Flat, pitched, compact, elongated and custom shelter models**
- 📐 **Interactive 2D floor plan**
- 🧊 **Interactive Plotly 3D shelter visualization**
- 🧪 **Automated tests and dataset validation**

---

## 🧾 User Inputs

| Workflow | Inputs |
|---|---|
| Design a Shelter | Location, occupants, temporary/permanent |
| Improve a Shelter | Location, occupants, temporary/permanent |
| Choose Materials | Climate, insulation thickness, window area, occupants |
| Compare Shelter Types | Climate, shelter type, occupants, dimensions/roof for custom model |

---

## 📊 Simulation Outputs

The application provides:

- Indoor/outdoor temperature profiles
- Average, minimum and maximum indoor temperature
- Comfort hours and comfort percentage
- Discomfort degree-hours
- Wall, roof, floor and window heat flow
- Ventilation and radiation heat flow
- Solar irradiance and useful solar gain
- Integrated modeled thermal energy
- Envelope U-values
- Floor area, volume and other geometry metrics

These are **modeled results**, not measured field energy consumption.

---

## 🧮 Thermal Model

The current engine is a **reduced-order, single-zone thermal model**. The shelter is represented as one thermal node with heat entering and leaving through simplified pathways.

Conceptually:

```text
Net Heat = Solar Gain + Internal Heat
           - Conduction - Ventilation - Radiation

Indoor Temperature
        ↓
   updated over time
```

The implementation uses thermal resistance/U-values, conduction, simplified solar glazing gain, ventilation heat exchange, internal gains, longwave radiation and lumped thermal capacitance with forward-Euler time stepping.

The comfort model is a simple **18–24 °C temperature band**. It is not PMV/PPD, CFD, or a full humidity-coupled comfort model.

---

## 🧱 Materials & Climate Data

### Materials

`data/materials/materials.json` stores properties such as:

- thermal conductivity
- density
- specific heat
- emissivity
- solar absorptivity
- indicative cost
- source/notes

`data/materials/glazing.json` contains glazing metadata. The active simulation also defines its runtime glazing presets in `services/simulation_service.py`.

### Climate

The active simulation reads local EPW files:

```text
data/weather/
├── leh.epw
├── chennai.epw
├── delhi.epw
├── jaisalmer.epw
└── bengaluru.epw
```

Weather is therefore **bundled/local**, not fetched from a live API.

---

## 🧠 Optimization & Recommendations

The current optimization system uses **Optuna's TPE sampler**.

It searches combinations of:

- insulation thickness
- window area
- wall material
- glazing
- orientation

The objective is to minimize simulated **discomfort degree-hours** for the selected scenario.

The recommendation layer in `services/recommender.py` uses **deterministic climate rules** and then integrates optimization results. It is not a trained machine-learning model.

---

## ⭐ USP

ThermoShelter AI combines several early-stage design tasks in one workflow:

> **Climate-aware recommendation + physics-based screening + optimization + material comparison + 2D/3D visualization**

The emphasis is on **fast and explainable design exploration**, rather than replacing professional engineering tools.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| Language | Python |
| Visualization | Plotly |
| Numerical computing | NumPy |
| Data handling | Pandas |
| Weather parsing | pvlib |
| Optimization | Optuna |
| Testing | pytest |
| Data | JSON, CSV, EPW |

---

## 🏛️ Architecture

```text
                    Streamlit UI
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Climate/Data     Recommender      Optimizer
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                Thermal Simulation
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Thermal         Solar        Ventilation
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                 Results & Metrics
                         │
                 ┌───────┴───────┐
                 ↓               ↓
             Plotly 2D        Plotly 3D
```

---

## 📁 Project Structure

```text
sih-area-specific-shelter/
├── app.py
├── data_loader.py
├── data/
│   ├── climate/
│   ├── materials/
│   ├── shelters/
│   └── weather/
├── services/
│   ├── climate_service.py
│   ├── comfort.py
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
│   └── tests/
├── docs/
├── scripts/
└── README.md
```

---

## 💻 Installation & Run

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it, then install the current dependencies:

```bash
python -m pip install streamlit plotly numpy pandas pvlib optuna pytest
```

Run the application:

```bash
streamlit run app.py
```

---

## 🧪 Validation & Testing

The repository includes:

- formula unit tests
- thermal simulation tests
- 3D visualization tests
- dataset validation through `scripts/validate_data.py`

Run tests:

```bash
python -m pytest services/tests
```

Validate datasets:

```bash
python scripts/validate_data.py
```

No unsupported accuracy or performance percentage is claimed here.

---

## ⚠️ Limitations

The current prototype is intentionally simplified:

- single-zone reduced-order thermal model
- 168-hour simulation horizon in the main UI workflows
- simplified radiation and solar modelling
- simplified ventilation/infiltration treatment
- simple 18–24 °C comfort band
- bundled weather data only
- limited active location coverage
- no field calibration
- no high-fidelity CFD/building simulation

Therefore, ThermoShelter AI is for **early-stage design exploration and decision support**, not final engineering certification or construction approval.

---

## 🚧 Future Scope

Planned upgrades include:

- annual/seasonal simulation
- more climate locations
- improved solar and thermal-mass modelling
- humidity and adaptive comfort modelling
- multi-objective optimization
- measured-field calibration
- high-fidelity simulation verification
- live climate-data integrations
- CAD/BIM and report export

These are **future capabilities**, not current features.

---

## 🌱 Sustainability Impact

The project aims to support more climate-responsive shelter design by making passive alternatives easier to compare before construction.

Potential benefits include better envelope decisions, greater use of passive strategies, fewer early design iterations, and improved climate resilience.

No measured carbon or energy-savings percentage is claimed by the current prototype.

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

## 🔭 Long-Term Vision

Build an evidence-backed platform that moves from:

**Climate Data → Rapid Screening → Optimization → High-Fidelity Verification → Field Validation → Climate-Specific Shelter Design Guidance**

---

### ThermoShelter AI
**Climate-aware design. Physics-based exploration. Transparent optimization.**
