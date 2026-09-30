# ThermoShelter AI — Engineering Methodology & Equations

**Purpose:** Technical description of the mathematical and thermal models implemented in the current repository.

---

## 1. Methodology Overview

ThermoShelter AI uses a **reduced-order, single-zone transient thermal model** for rapid early-stage shelter comparison.

The model treats the shelter as a lumped thermal system with one primary indoor air temperature state.

The simulation combines:

- shelter geometry;
- envelope thermal resistance;
- U-values;
- conductive heat transfer;
- glazing solar gain;
- sensible ventilation heat exchange;
- longwave radiation;
- internal heat gains;
- lumped thermal capacity; and
- explicit forward-Euler temperature integration.

The model is intended for **rapid comparative design screening**, not final engineering certification.

---

## 2. Geometry Model

The geometry subsystem is implemented in `services/geometry.py`.

### 2.1 Floor Area

For a rectangular shelter:

$A_{floor}=L\times W$

Where:

- $A_{floor}$ = floor area, m²
- $L$ = shelter length, m
- $W$ = shelter width, m

### 2.2 Enclosed Volume

For the simplified rectangular volume:

$V=L\times W\times H$

Where:

- $V$ = enclosed volume, m³
- $H$ = mean internal height, m

For pitched roofs, the repository includes a dedicated geometric calculation that accounts for roof slope, gable area, ridge height, and the corresponding additional volume.

### 2.3 Gross Wall Area

For four vertical walls:

$A_{wall,gross}=2(L+W)H$

### 2.4 Net Opaque Wall Area

Openings are subtracted from the gross wall area:

$A_{wall,net} = A_{wall,gross} - A_{window} - A_{door}$

The implementation validates that openings do not exceed the gross wall area.

---

## 3. Thermal Resistance

Thermal resistance is implemented in `services/thermal.py` and used by the simulation service.

### 3.1 Homogeneous Layer

For a material layer:

$R_i=\frac{L_i}{k_i}$

Where:

- $R_i$ = thermal resistance of layer, m²·K/W
- $L_i$ = layer thickness, m
- $k_i$ = thermal conductivity, W/(m·K)

### 3.2 Multi-Layer Assembly

The total resistance is:

$R_{total} = R_{inside} + \sum_{i=1}^{n}\frac{L_i}{k_i} + R_{outside}$

The implementation uses default interior/exterior surface-film resistances defined in `services/formula_constants.py`.

The repository documentation associates the vertical-wall defaults with ISO 6946 / IS 3792 reference practice.

### 3.3 U-Value

Overall thermal transmittance:

$U=\frac{1}{R_{total}}$

Units:

$W/(m^2K)$

Lower U-value represents lower modeled conductive transmission per unit area for a given temperature difference.

---

## 4. Conductive Heat Transfer

The component conductive heat-flow model is:

$\dot Q_{cond} = U A (T_{in}-T_{out})$

Where:

- $\dot Q_{cond}$ = conductive heat transfer rate, W
- $U$ = component U-value, W/(m²·K)
- $A$ = component area, m²
- $T_{in}$ = indoor temperature, °C
- $T_{out}$ = outdoor temperature, °C

The simulation applies this relationship separately to major envelope components:

- walls;
- roof;
- floor; and
- windows.

The sign convention is that a positive value represents heat transfer from the warmer indoor condition toward the outdoor condition.

---

## 5. Envelope Assembly U-Values

The simulation service calculates separate U-values for:

- walls;
- roof;
- floor; and
- glazing.

For a wall, the base material and optional insulation layer are assembled into a total thermal resistance.

Conceptually:

```text
Inside film
    +
Wall substrate
    +
Insulation
    +
Outside film
    ↓
R_total
    ↓
U = 1 / R_total
```

The roof uses horizontal surface resistance defaults.

The floor is represented by a simplified fixed assembly using the current simulation defaults.

---

## 6. Solar Irradiance

The climate service loads hourly direct and diffuse solar irradiance from the EPW weather data.

The simulation combines:

$I_{solar}=I_{direct}+I_{diffuse}$

The resulting hourly solar flux is used for the glazing solar-gain calculation.

The implementation also reports incident solar power associated with the modeled window area.

---

## 7. Opaque Surface Solar Gain

The solar module defines an absorbed opaque-surface model:

$\dot Q_{solar,opaque} = I_{solar} A \alpha F$

Where:

- $I_{solar}$ = incident solar irradiance, W/m²
- $A$ = exposed area, m²
- $\alpha$ = solar absorptivity
- $F$ = effective solar/orientation factor

This is a simplified quasi-steady surface absorption relationship.

The main transient simulation focuses on useful solar gain through glazing rather than using a full exterior surface heat-balance model.

---

## 8. Glazing Solar Heat Gain

The active glazing model is:

$\dot Q_{solar,glazing} = I_{solar} A_{window} SHGC F_{shading}$

Where:

- $I_{solar}$ = incident solar irradiance, W/m²
- $A_{window}$ = modeled window area, m²
- $SHGC$ = Solar Heat Gain Coefficient
- $F_{shading}$ = effective shading/orientation factor

The current glazing presets include:

| Preset | Modeled U-value (W/m²·K) | SHGC |
|---|---:|---:|
| Single clear | 5.80 | 0.82 |
| Double clear | 2.80 | 0.70 |
| Double low-E | 1.80 | 0.50 |
| Triple low-E | 1.00 | 0.35 |

These are the runtime preset values defined in `services/simulation_service.py`.

---

## 9. Orientation Factors

The current simulation uses simplified orientation factors:

| Orientation | Factor |
|---|---:|
| South | 1.00 |
| North | 0.45 |
| East | 0.70 |
| West | 0.75 |

The implementation applies this factor to the glazing solar-gain calculation.

The model therefore represents orientation as a simplified solar-exposure parameter rather than performing a complete hourly solar-position and surface-incidence calculation for every facade.

---

## 10. Ventilation / Air-Exchange Model

Airflow from Air Changes per Hour (ACH) is calculated as:

$\dot V = \frac{ACH\times V}{3600}$

Where:

- $\dot V$ = volumetric airflow, m³/s
- $ACH$ = air changes per hour
- $V$ = shelter volume, m³
- 3600 = seconds per hour

The sensible ventilation heat-transfer rate is:

$\dot Q_{vent} = \rho \dot V c_p (T_{in}-T_{out})$

Where:

- $\rho$ = air density, kg/m³
- $c_p$ = air specific heat, J/(kg·K)
- $\dot V$ = airflow, m³/s

The current implementation treats ventilation as a **sensible heat exchange mechanism**. Moisture/latent enthalpy effects are not modelled.

---

## 11. Longwave Radiation

The simulation includes a simplified longwave radiation term:

$\dot Q_{rad} = \epsilon\sigma A \left( T_{in,K}^{4}-T_{out,K}^{4} \right)$

Where:

- $\epsilon$ = effective emissivity;
- $\sigma$ = Stefan-Boltzmann constant;
- $A$ = modeled radiating area;
- $T_{in,K}$ = indoor absolute temperature, K;
- $T_{out,K}$ = outdoor absolute temperature, K.

The implementation converts Celsius to Kelvin before applying the fourth-power radiation relationship.

The current simulation uses the roof area as the effective area for its radiation coefficient.

This is a reduced-order approximation and should not be interpreted as a complete enclosure surface-to-surface radiative exchange model.

---

## 12. Internal Heat Gains

Occupant heat is calculated using the number of occupants and the configured heat-per-person value.

The simulation additionally applies an approximate **40 W base equipment/lighting gain**.

Conceptually:

$Q_{internal} = N_{occupants}q_{person} + Q_{base}$

Where:

- $N_{occupants}$ = number of occupants;
- $q_{person}$ = heat gain per occupant;
- $Q_{base}$ = fixed equipment/lighting allowance.

---

## 13. Thermal Capacity

The simulation represents thermal inertia through a lumped thermal capacity.

The basic thermal-capacity relationship is:

$C=mc_p$

Where:

- $C$ = thermal capacity, J/K
- $m$ = effective thermal mass, kg
- $c_p$ = specific heat, J/(kg·K)

The current simulation derives air mass from shelter volume and air density, then applies an internal multiplier to represent additional effective thermal mass:

```text
air mass = volume × air density

effective thermal capacity
    =
air mass × air specific heat × 3
```

This is an intentionally simplified lumped representation rather than a detailed multilayer transient conduction model.

---

## 14. Net Heat Balance

The core simulation concept is:

$Q_{net} = Q_{solar} + Q_{internal} - (Q_{conductive+vent} + Q_{rad})$

The conductive/ventilation term combines the precomputed heat-loss coefficients with the current indoor/outdoor temperature difference.

Expanded conceptually:

$$Q_{\text{net}} = Q_{\text{solar}} + Q_{\text{internal}} - \left[ (UA)_{\text{walls}} + (UA)_{\text{roof}} + (UA)_{\text{floor}} + (UA)_{\text{windows}} + (UA)_{\text{vent}} \right] (T_{\text{in}} - T_{\text{out}}) - Q_{\text{rad}}$$

This balance is evaluated repeatedly within each hour.

---

## 15. Forward-Euler Temperature Update

The indoor temperature is updated using:

$T_{t+\Delta t} = T_t + \frac{Q_{net}\Delta t}{C}$

Where:

- $T_t$ = current indoor temperature;
- $\Delta t$ = numerical timestep, seconds;
- $Q_{net}$ = net thermal power, W;
- $C$ = effective thermal capacity, J/K.

Since:

$1W=1J/s$

the quantity $Q_{net}\Delta t$ represents thermal energy transferred during the timestep.

---

## 16. Time Discretization

The simulation uses explicit sub-hour integration:

$\Delta t = \frac{3600}{N_{substeps}}$

For the main simulation default:

$N_{substeps}=60$

Therefore:

$\Delta t=60\ seconds$

The weather boundary conditions remain hourly, while the indoor thermal state is advanced at the smaller numerical timestep.

The main user workflow uses a **168-hour** simulation horizon.

During optimization, the repository deliberately uses fewer substeps per hour to reduce computational cost across many candidate simulations.

After optimization, the best candidate is re-simulated using the authoritative 168-hour simulation configuration.

---

## 17. Comfort Model

The current comfort model uses a simple temperature band:

$18^\circ C \leq T_{in} \leq 24^\circ C$

The implementation classifies each timestep as:

- `too_cold`;
- `comfortable`; or
- `too_hot`.

### Comfort Hours

If the simulation timestep represented by each recorded temperature is $\Delta t_h$ hours:

$ComfortHours = N_{comfortable} \Delta t_h$

### Comfort Percentage

The application calculates:

$Comfort\% = \frac{ComfortHours}{SimulationHours} \times100$

### Discomfort Degree-Hours

For temperatures below the comfort band:

$DH_{cold} = \sum (18-T_i)$

For temperatures above the band:

$DH_{hot} = \sum (T_i-24)$

Therefore:

$DH_{discomfort} = \sum \begin{cases} 18-T_i, & T_i<18\\ 0, & 18\leq T_i\leq24\\ T_i-24, & T_i>24 \end{cases}$

The optimization objective uses this modeled discomfort degree-hour measure.

### Important limitation

This is **not** a full PMV/PPD model, adaptive comfort model, or humidity-coupled comfort model.

---

## 18. Energy Integration

Hourly power quantities are converted to energy using time integration.

Conceptually:

$E=\int P(t)\,dt$

For hourly discrete results, the implementation aggregates the hourly values and converts the resulting energy into kWh.

The platform reports:

- integrated useful solar energy;
- incident solar energy;
- internal gains;
- wall losses;
- roof losses;
- floor losses;
- window losses;
- ventilation losses;
- radiation losses; and
- total modeled heat-loss components.

These are **model outputs**, not measured building energy consumption.

---

## 19. Component Heat Balance

The simulation tracks the following components independently:

```text
                     Solar Gain
                         │
                         ▼
                 ┌───────────────┐
                 │ Indoor Thermal│
                 │     Node      │
                 └───────────────┘
                  ▲  ▲  ▲  ▲  ▲
                  │  │  │  │  │
             Internal │  │  │  │
                      │  │  │  │
              Walls ──┘  │  │  │
              Roof ──────┘  │  │
              Floor ───────┘  │
              Windows ───────┘
              Ventilation ────┘
              Radiation ──────┘
```

This decomposition allows the application to show where modeled thermal gains/losses originate.

---

## 20. Optimization Methodology

The optimization module uses:

- Optuna;
- TPE sampler;
- fixed random seed of 42 in the current optimization setup; and
- a minimization objective.

The search variables can include:

```text
Insulation thickness
Window area
Wall material
Glazing
Orientation
```

The optimization pipeline is:

```text
Candidate Parameters
        ↓
Candidate Shelter
        ↓
Reduced-resolution Simulation
        ↓
Discomfort Degree-Hours
        ↓
Optuna Objective
        ↓
Next Trial
        ↓
Best Candidate
        ↓
Final 168-hour Simulation
```

This is optimization-driven intelligence, not supervised machine learning.

---

## 21. Material Modelling

Material records can contain:

- thermal conductivity;
- density;
- specific heat;
- emissivity;
- solar absorptivity;
- indicative cost;
- source; and
- notes.

For envelope U-value calculations, thermal conductivity is the primary material property used in the layer-resistance calculation.

Thermal mass is represented in the current simulation through a simplified effective thermal-capacity treatment rather than a full time-dependent multilayer wall conduction model.

---

## 22. Engineering Assumptions

The current model assumes or simplifies:

1. A primary single-zone indoor thermal state.
2. Rectangular base geometry for core area/volume calculations.
3. Simplified pitched-roof geometry when selected.
4. Hourly weather boundary conditions.
5. Sub-hour numerical integration between weather points.
6. Simplified glazing solar gain.
7. Simplified orientation/shading factors.
8. Sensible-only ventilation heat exchange.
9. Simplified longwave radiation.
10. Lumped effective thermal capacity.
11. Fixed/default comfort temperature limits.
12. No explicit moisture balance.
13. No CFD.
14. No structural analysis.
15. No field calibration in the current repository.

---

## 23. Model Verification vs Real-World Validation

It is important to distinguish two concepts.

### Software verification

This asks:

> Does the implementation behave according to its programmed equations and expected input/output relationships?

The repository includes unit and integration tests for formulas, simulation, optimization/recommendation behavior, data validation, and visualization.

### Engineering validation

This asks:

> Does the model accurately reproduce measured real-world shelter behaviour?

The current repository does **not** provide field-calibration results or physical-test validation.

Therefore, the correct technical claim is:

> ThermoShelter provides rapid, physics-based comparative screening under defined assumptions.

It should not be presented as a fully validated replacement for professional building simulation or physical testing.

---

## 24. Numerical and Physical Limitations

### Reduced-order representation

The shelter is represented using a simplified thermal node rather than detailed wall-node thermal diffusion.

### Solar simplification

The current orientation factors are simplified constants rather than a complete hourly facade solar-position model.

### Radiation simplification

Radiation is represented using a reduced effective-area model.

### Ventilation simplification

Only sensible heat exchange is represented; latent humidity effects are omitted.

### Comfort simplification

The 18–24 °C band is a screening indicator, not a complete human thermal-comfort model.

### Weather scope

The active simulation uses bundled EPW profiles for the currently supported locations.

---

## 25. Why a Reduced-Order Model is Appropriate for the Prototype

The goal of the current platform is **rapid design-space exploration**.

Optimization requires repeated simulation of many candidate configurations. A high-fidelity model for every candidate could substantially increase computational cost.

The current architecture therefore uses:

```text
Fast reduced-order simulation
        ↓
Large design-space exploration
        ↓
Candidate ranking
        ↓
Final authoritative simulation
        ↓
Future high-fidelity verification
```

This is a deliberate prototype architecture rather than an accidental omission of CFD.

---

## 26. Engineering Evidence to Collect for SIH

For each important performance claim, the team should retain:

```text
Claim
  ↓
Input scenario
  ↓
Model configuration
  ↓
Equation / method
  ↓
Simulation output
  ↓
Comparison
  ↓
Evidence / screenshot / data
```

Examples:

- baseline versus optimized discomfort degree-hours;
- insulation-thickness sensitivity;
- window-area sensitivity;
- orientation comparison;
- material comparison;
- climate-specific recommendation comparison;
- indoor-temperature response;
- component heat-flow breakdown.

Any numerical performance percentage presented to judges should state the scenario and baseline against which it was calculated.

---

## 27. Engineering Traceability

| Engineering concept | Repository implementation |
|---|---|
| Geometry | `services/geometry.py` |
| Thermal resistance | `services/thermal.py` |
| U-value | `services/thermal.py`, `simulation_service.py` |
| Solar gain | `services/solar.py`, `simulation_service.py` |
| Ventilation | `services/ventilation.py` |
| Comfort | `services/comfort.py` |
| Central formula interface | `services/formulas.py` |
| Climate data | `services/climate_service.py` |
| Material data | `services/material_service.py` + JSON database |
| Simulation orchestration | `services/simulation_service.py` |
| Optimization | `services/optimize.py` |
| Recommendations | `services/recommender.py` |
| Validation | `tests/` + `services/tests/` + `scripts/validate_data.py` |

---

## 28. Conclusion

ThermoShelter AI's engineering methodology is based on a transparent chain of calculations:

> **Climate data → Geometry → Envelope resistance → Heat-transfer components → Net heat balance → Transient temperature → Comfort/energy metrics → Optimization**

The methodology is intentionally lightweight enough for rapid exploration while retaining explicit physical relationships.

The current model should therefore be positioned as an **early-stage engineering screening and optimization framework**. Future development can add higher-fidelity thermal modelling, humidity effects, more complete solar geometry, field calibration, and professional simulation verification.

