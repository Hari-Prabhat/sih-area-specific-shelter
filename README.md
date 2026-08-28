# 🌡️ ThermoShelter AI

### Area-Specific Passive Shelter Design & Thermal Simulation Platform

> **Design the shelter for the climate — instead of designing the climate control for the shelter.**

ThermoShelter AI is a software-based platform for designing **climate-specific, energy-efficient passive shelters**.

The platform takes local atmospheric conditions, shelter geometry, material properties, openings, occupancy, and thermal characteristics as inputs. It then performs a physics-based thermal simulation and compares multiple possible designs to recommend a configuration that provides better thermal comfort while reducing external heating/cooling requirements.

The initial focus is on **high-altitude cold regions such as Ladakh**, with an architecture designed to support other climatic regions in the future.

---

## 🎯 Problem Statement

Conventional shelters are often designed using generic configurations rather than being optimized for the climatic conditions of their deployment region.

In extreme climates such as Ladakh, this can result in:

* High heat losses through walls and roofs
* Significant heat loss through doors and windows
* Poor thermal comfort during night-time
* Greater dependence on external heating
* Increased fuel consumption
* Higher operating costs
* Increased environmental impact

Ladakh presents an interesting passive-design opportunity because of its cold climate combined with strong solar availability.

The challenge is therefore:

> **How can we computationally determine the most suitable shelter shape, orientation, materials, insulation, openings, and thermal mass for a particular climate?**

---

# 💡 Our Solution

ThermoShelter AI provides a simple workflow:

```text
Location
    ↓
Climate Data
    ↓
Shelter Parameters
    ↓
Material Selection
    ↓
Thermal Simulation
    ↓
Design Optimization
    ↓
Thermal Comfort Analysis
    ↓
Recommended Shelter
    ↓
3D Visualization
```

Instead of requiring users to manually run complex engineering simulations for every configuration, the platform provides a simplified interface for rapidly exploring multiple designs.

---

# 🚀 Key Features

## 1. 📍 Area-Specific Design

The user can define a location and corresponding climatic conditions.

Example:

```text
Location: Leh, Ladakh
Altitude: High
Climate: Cold
Solar availability: High
```

The same framework can later be applied to different climatic regions.

---

## 2. 🏠 Custom Shelter Configuration

Users can define:

* Shelter type
* Number of occupants
* Length
* Width
* Height
* Shape
* Orientation
* Wall material
* Roof material
* Floor material
* Insulation
* Window area
* Door area
* Glazing type
* Thermal mass

---

## 3. ☀️ Solar Energy Estimation

The platform estimates useful solar thermal gain based on:

* Solar irradiance
* Surface area
* Orientation
* Material properties
* Window area
* Glazing characteristics

---

## 4. 🔥 Thermal Simulation

The system uses a reduced-order transient thermal model to estimate:

* Indoor temperature
* Heat gain
* Heat loss
* Conductive losses
* Ventilation/infiltration losses
* Thermal storage
* Net heat flow

The model is designed for **rapid design-space exploration**, rather than replacing high-fidelity CFD software.

---

## 5. 🌡️ Thermal Comfort Analysis

The system evaluates indoor temperature against a configurable comfort range.

Example:

```text
Too Cold
   ↓
Comfortable
   ↓
Too Hot
```

The dashboard reports:

* Minimum temperature
* Maximum temperature
* Comfort hours
* Temperature variation

---

## 6. 🧱 Material Comparison

Different materials can be evaluated under the same climatic conditions.

Example:

```text
Mud Brick
Stone
Concrete
Wood
EPS Insulation
Mineral Wool
Composite Materials
```

The system compares their thermal performance based on material properties such as:

* Thermal conductivity
* Density
* Specific heat
* Emissivity
* Absorptivity
* Thickness

---

## 7. 🔬 Design Optimization

The platform can evaluate multiple combinations of:

* Materials
* Insulation
* Orientation
* Window area
* Glazing
* Thermal mass
* Shelter geometry

The designs are ranked according to configurable performance criteria.

Example:

```text
                Design A   Design B   Design C

Comfort Hours      10         17         21
Heat Loss         High       Medium      Low
Solar Gain        Medium      High       High
Energy Demand     High       Medium      Low

                         ↓

                 🏆 DESIGN C
```

---

## 8. 🧠 Explainable Recommendation

Instead of simply saying:

> "Design C is best."

ThermoShelter AI explains why.

Example:

```text
Recommended Design

✓ Lower conductive heat loss
✓ Better thermal retention
✓ Higher useful solar gain
✓ More comfort hours
✓ Lower external heating requirement
```

This makes the optimization transparent and understandable.

---

## 9. 🌐 3D Shelter Visualization

The selected design can be represented as a lightweight interactive 3D model.

The model reflects parameters such as:

* Length
* Width
* Height
* Shape
* Orientation
* Windows
* Doors
* Roof
* Materials

Users can:

* Rotate
* Zoom
* Pan
* Inspect the shelter

---

# 🧮 Thermal Model

The MVP uses a simplified transient energy-balance approach.

The basic model is:

$$
C_{eff}\frac{dT_{in}}{dt}
=
Q_{solar}
+
Q_{internal}
-
Q_{conduction}
-
Q_{ventilation}
-
Q_{radiation}
$$

### Conductive heat transfer

$$
Q_{conduction}=UA(T_{in}-T_{out})
$$

where:

$$
U=\frac{1}{R_{total}}
$$

For multilayer construction:

$$
R_{total}=R_{inside}+\sum\frac{L_i}{k_i}+R_{outside}
$$

### Thermal mass

$$
C=mC_p
$$

### Solar gain

A simplified solar-gain model is used for the MVP.

### Ventilation

Ventilation/infiltration losses are estimated using air-exchange rate and shelter volume.

All assumptions and equations are documented in:

```text
docs/equations.md
```

---

# 🏗️ System Architecture

```text
                    ┌──────────────────┐
                    │      USER        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ React Frontend   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   FastAPI API    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼───────────────┐
              ▼              ▼               ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │ Climate     │ │ Thermal     │ │ Optimization│
      │ Engine      │ │ Engine      │ │ Engine      │
      └─────────────┘ └─────────────┘ └─────────────┘
              │              │               │
              └──────────────┼───────────────┘
                             ▼
                    ┌──────────────────┐
                    │ Results Engine   │
                    └────────┬─────────┘
                             │
              ┌──────────────┴─────────────┐
              ▼                            ▼
       ┌──────────────┐             ┌──────────────┐
       │ Data Charts  │             │ 3D Shelter   │
       │ & Analytics  │             │ Visualization│
       └──────────────┘             └──────────────┘
```

---

# 🛠️ Technology Stack

## Frontend

* React
* Vite
* Tailwind CSS
* Recharts
* Three.js / React Three Fiber

## Backend

* Python
* FastAPI
* Pydantic

## Scientific Computing

* NumPy
* Pandas
* SciPy

## Data

* CSV
* JSON
* SQLite/PostgreSQL-ready architecture

## Deployment

* Docker
* Docker Compose

---

# 📁 Project Structure

```text
thermoshelter-ai/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── README.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── tests/
│
├── simulation/
│   ├── thermal/
│   ├── solar/
│   ├── ventilation/
│   ├── thermal_mass/
│   └── tests/
│
├── optimization/
│   ├── optimizer.py
│   ├── scoring.py
│   └── tests/
│
├── data/
│   ├── climate/
│   ├── materials/
│   ├── glazing/
│   └── shelters/
│
├── visualization/
│   ├── models/
│   └── components/
│
├── docs/
│   ├── architecture.md
│   ├── equations.md
│   ├── api.md
│   ├── data_dictionary.md
│   └── validation.md
│
├── tests/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

# 🔌 API

The backend exposes APIs such as:

```text
GET  /health
GET  /locations
GET  /locations/{location_id}
GET  /materials
GET  /materials/{material_id}
POST /simulate
POST /optimize
```

### Example simulation request

```json
{
  "location_id": "leh",
  "occupants": 6,
  "shelter_type": "permanent",

  "geometry": {
    "length": 5,
    "width": 4,
    "height": 3,
    "shape": "rectangular",
    "orientation": 180
  },

  "materials": {
    "wall": "mud_brick",
    "roof": "composite",
    "floor": "concrete",
    "insulation": "eps"
  },

  "openings": {
    "window_area": 4,
    "door_area": 2,
    "glazing": "double_glazed"
  },

  "thermal_mass": {
    "type": "high"
  }
}
```

### Example output

```json
{
  "summary": {
    "min_indoor_temperature": 0,
    "max_indoor_temperature": 0,
    "comfort_hours": 0,
    "total_solar_energy_kwh": 0,
    "total_heat_loss_kwh": 0,
    "external_energy_requirement_kwh": 0
  },

  "time_series": []
}
```

Actual values are generated by the simulation engine.

---

# 🎯 MVP

The Minimum Viable Product focuses on the complete end-to-end workflow:

```text
User Input
     ↓
Climate Data
     ↓
Material Selection
     ↓
Thermal Simulation
     ↓
Temperature Prediction
     ↓
Heat Loss Calculation
     ↓
Solar Energy Calculation
     ↓
Design Comparison
     ↓
Optimization
     ↓
Recommended Design
     ↓
3D Visualization
```

### MVP outputs

The system must provide:

* Predicted indoor temperature
* Ambient temperature comparison
* Solar energy gain
* Heat loss
* Heat flow
* Comfort hours
* External energy requirement
* Design ranking
* Recommended configuration
* 3D shelter visualization

---

# 🏆 USP

### From Simulation to Recommendation

Existing engineering tools can perform sophisticated thermal simulations.

ThermoShelter AI focuses on making the process:

**Climate-specific + Parametric + Explainable + User-friendly**

Instead of asking:

> "What happens if I build this shelter?"

ThermoShelter asks:

> **"What shelter should I build for this climate?"**

---

# 🌍 Scalability

The initial implementation focuses on Ladakh, but the architecture is designed for multiple climate zones.

### Phase 1

Ladakh / high-altitude cold regions

### Phase 2

Other Himalayan regions

### Phase 3

Indian climate zones

* Cold
* Hot-dry
* Warm-humid
* Composite
* Temperate

### Phase 4

Global climate locations

---

# 🔮 Future Roadmap

## Phase 1 — Hackathon MVP

* Climate dataset
* Material database
* Thermal model
* Solar calculation
* Heat-loss calculation
* Optimization
* Dashboard
* 3D model

## Phase 2 — Engineering Validation

Integrate/validate against:

* ANSYS
* EnergyPlus
* OpenFOAM

High-fidelity simulations can be used to validate the reduced-order model.

## Phase 3 — Real-Time Climate

Integrate live weather data to allow simulations based on current atmospheric conditions.

## Phase 4 — IoT Integration

Deploy sensors inside real shelters:

```text
Indoor Temperature
Outdoor Temperature
Humidity
Solar Radiation
Surface Temperature
Wind
```

## Phase 5 — Digital Twin

```text
Real Shelter
      ↕
IoT Sensors
      ↕
ThermoShelter Model
      ↕
Simulation
      ↕
Prediction
```

The system could continuously calibrate the model using real measurements.

---

# 👥 Team

The project is divided into six technical workstreams.

| Member         | Responsibility                                   |
| -------------- | ------------------------------------------------ |
| 👨‍💻 Member 1 | Project Lead, Architecture, Integration & DevOps |
| 🔬 Member 2    | Thermal Simulation & Physics Engine              |
| 📊 Member 3    | Climate & Material Data Engineering              |
| ⚙️ Member 4    | Backend & API Development                        |
| 🎨 Member 5    | Frontend & Dashboard                             |
| 🏠 Member 6    | 3D Visualization & Data Visualization            |

---

# 🔄 Development Workflow

We use Git feature branches.

```text
main
 │
 └── develop
       │
       ├── feature/thermal-engine
       ├── feature/data-engine
       ├── feature/backend
       ├── feature/frontend
       ├── feature/visualization
       └── feature/devops
```

### Commit convention

```text
feat: add thermal simulation
feat: add material database
feat: implement optimization
fix: correct solar gain calculation
fix: handle invalid dimensions
docs: update thermal equations
test: add simulation validation
```

---

# 🧪 Validation Strategy

The MVP uses a reduced-order physics model.

Validation will be performed progressively using:

1. Analytical calculations
2. Synthetic test cases
3. Reference measurements where available
4. ANSYS/EnergyPlus comparison
5. Real shelter sensor data in future versions

Potential validation metrics include:

```text
MAE
RMSE
MAPE
```

The system will clearly distinguish between:

**simulated data**

and

**measured/reference data**.

---

# ⚠️ Model Limitations

The initial version is not intended to replace high-fidelity CFD.

The reduced-order model uses simplified assumptions for:

* solar gain
* radiation
* airflow
* thermal mass
* indoor comfort

Future versions can improve these using:

* detailed solar-position calculations
* CFD
* EnergyPlus
* ANSYS
* real sensor data
* advanced thermal comfort models

---

# 🚀 Getting Started

## Prerequisites

Install:

* Git
* Python 3.11+
* Node.js 20+
* npm
* Docker (optional)

---

## Clone Repository

```bash
git clone https://github.com/YOUR-USERNAME/thermoshelter-ai.git

cd thermoshelter-ai
```

---

## Backend

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## Frontend

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🐳 Docker

The project is designed to support Docker-based deployment.

Run:

```bash
docker compose up --build
```

This will start the frontend and backend services.

---

# 📊 Example Use Case

### Scenario

A relief organization wants to deploy a shelter for six people in Leh.

The user enters:

```text
Location:
Leh

Occupants:
6

Shelter:
Permanent

Dimensions:
5m × 4m × 3m

Orientation:
South

Wall:
Mud brick

Insulation:
EPS

Glazing:
Double glazing

Thermal Mass:
High
```

The system simulates the shelter and compares alternative configurations.

The final result provides:

```text
Indoor Temperature
Solar Gain
Heat Loss
Comfort Hours
Energy Requirement
Recommended Design
```

The user can then inspect the recommended design through the 3D model.

---

# 🌱 Impact

ThermoShelter AI aims to contribute toward:

* Reduced heating/cooling energy demand
* Reduced fossil-fuel dependence
* Improved thermal comfort
* Climate-resilient shelter design
* Faster engineering decision-making
* Better utilization of passive solar energy
* Sustainable infrastructure in remote regions

---

# 🧭 Vision

The long-term vision is to create a platform where anyone can answer:

> **"Given this location, climate, budget and population, what is the most thermally efficient shelter I can build?"**

without requiring every design iteration to be manually modeled from scratch in a high-fidelity engineering package.

---

## ⭐ ThermoShelter AI

**Climate-aware design.
Physics-based simulation.
Intelligent optimization.
Passive comfort.**

> **Design better shelters. Use less energy. Adapt to the climate.**
