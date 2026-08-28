# 📚 ThermoShelter AI — Data Dictionary & Climate/Materials Reference Guide

## 1. Overview & Architecture

The **ThermoShelter AI Data Layer** provides structured, standardized, and validated datasets required by the thermal simulation engine to model passive heating, heat retention, thermal mass buffering, and fenestration gains across extreme climates.

---

## 2. Standardized Physical Units & Climate Normalization

All datasets follow strict SI metric standards:

| Physical Quantity | Standard Unit | Symbol / Dimension | Description / Application |
| :--- | :--- | :--- | :--- |
| **Temperature** | Degrees Celsius | `°C` | Ambient air, indoor operative, and surface boundary temperatures |
| **Solar Irradiance** | Watts per square meter | `W/m²` | Global Horizontal Irradiance (GHI) and direct incident beam flux |
| **Wind Speed** | Meters per second | `m/s` | Convective surface boundary velocity at 10m height |
| **Relative Humidity** | Percent | `%` | Atmospheric moisture content ($0\% - 100\%$) |
| **Cloud Cover** | Fraction | Dimensionless | Sky clearness metric ($0.0 = \text{clear sky}, 1.0 = \text{overcast}$) |
| **Dimensions** | Meters | `m` | Length, width, height, and envelope layer thicknesses |
| **Thermal Conductivity ($k$)** | Watts per meter-Kelvin | `W/m·K` | Steady-state conductive heat transfer rate |
| **Density ($\rho$)** | Kilograms per cubic meter | `kg/m³` | Volumetric mass density of construction material |
| **Specific Heat Capacity ($c_p$)** | Joules per kilogram-Kelvin | `J/kg·K` | Thermal capacitance / thermal mass heat storage capacity |
| **Emissivity ($\epsilon$)** | Fraction | Dimensionless | Long-wave infrared radiation exchange ($0.0 - 1.0$) |
| **Solar Absorptivity ($\alpha$)** | Fraction | Dimensionless | Short-wave solar radiation absorption fraction ($0.0 - 1.0$) |
| **Overall Heat Transfer ($U$)** | Watts per square meter-Kelvin | `W/m²·K` | Fenestration and assembly thermal conductance |
| **Solar Heat Gain Coefficient ($\text{SHGC}$)** | Fraction | Dimensionless | Fraction of incident solar radiation admitted through glazing ($0.0 - 1.0$) |

---

## 3. Dataset Schemas & Dictionaries

### 3.1 Location Metadata (`data/climate/locations.json`)

Geographical coordinates, elevation, and design weather benchmarks.

| Field Name | Type | Unit | Description & Engineering Purpose |
| :--- | :--- | :--- | :--- |
| `id` | `string` | — | Unique lowercase machine identifier (e.g. `"leh"`, `"kargil"`, `"delhi"`) |
| `name` | `string` | — | Official city/region display name |
| `country` | `string` | — | Country of deployment |
| `region` | `string` | — | State or Union Territory |
| `latitude` | `float` | `°N` | Geodetic latitude ($-90.0$ to $+90.0$) |
| `longitude` | `float` | `°E` | Geodetic longitude ($-180.0$ to $+180.0$) |
| `altitude` | `float` | `m` | Altitude above mean sea level. Essential for atmospheric pressure and radiation adjustments |
| `climate_type` | `string` | — | Human-readable climate zone (e.g. `"Cold (High-Altitude Desert)"`, `"Hot-Dry"`, `"Composite"`) |
| `koppen_classification` | `string` | — | Standard Köppen-Geiger climate code (e.g. `BWk`, `Dsb`, `BSh`, `Aw`) |
| `design_winter_temp_c` | `float` | `°C` | 99.6% ASHRAE winter design dry-bulb temperature (extreme heating benchmark) |
| `design_summer_temp_c` | `float` | `°C` | 0.4% ASHRAE summer design dry-bulb temperature (cooling benchmark) |
| `annual_solar_ghi_kwh_m2` | `float` | `kWh/m²` | Annual cumulative Global Horizontal Solar Irradiance |
| `heating_degree_days_18c` | `integer` | `HDD (18°C)` | Annual heating degree days based on 18°C comfort threshold |
| `cooling_degree_days_18c` | `integer` | `CDD (18°C)` | Annual cooling degree days based on 18°C comfort threshold |
| `source` | `string` | — | Meteorological agency citation (IMD, ASHRAE, ISHRAE, NREL NSRDB) |
| `notes` | `string` | — | Passive design context, diurnal characteristics, and shelter engineering advice |

---

### 3.2 Weather Timeseries (`data/climate/weather.csv` & `weather_{location_id}.csv`)

Hourly atmospheric observations for transient energy balance simulation.

> **Dataset Identification**: Clearly identified as a **high-fidelity reference/demo dataset** derived from IMD climatological normals, ASHRAE Climatic Design Conditions, and NREL solar radiation models.

| Field Name | Type | Unit | Range / Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | `string` | ISO 8601 / `YYYY-MM-DD HH:MM:SS` | Sequential hourly | Simulation timestep timestamp |
| `location_id` | `string` | — | Foreign key to `locations.json` | Associated location identifier |
| `ambient_temperature` | `float` | `°C` | $-40.0$ to $+55.0$ | Ambient dry-bulb air temperature ($T_{out}$) |
| `solar_irradiance` | `float` | `W/m²` | $0.0$ to $1200.0$ | Global Horizontal Irradiance ($I_{solar}$) |
| `wind_speed` | `float` | `m/s` | $\ge 0.0$ | Outdoor wind speed ($v_{wind}$) for convective $h_c$ calculations |
| `relative_humidity` | `float` | `%` | $0.0$ to $100.0$ | Ambient relative humidity |
| `cloud_cover` | `float` | Fraction | $0.0$ to $1.0$ | Fractional cloud obscuration for night-sky longwave radiation ($Q_{rad,sky}$) |

---

### 3.3 Building Materials Database (`data/materials/materials.json`)

Categorized thermo-physical properties with structured uncertainty ranges:

```json
{
  "typical_value": 0.60,
  "min_value": 0.45,
  "max_value": 0.85,
  "unit": "W/m·K"
}
```

| Field Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `id` | `string` | — | Unique identifier (e.g. `"mud_brick"`, `"eps_insulation"`, `"trombe_wall_mass"`) |
| `name` | `string` | — | Engineering name and vernacular description |
| `category` | `string` | — | Assembly role: `"wall"`, `"roof"`, `"floor"`, `"insulation"`, `"thermal_mass"` |
| `density` | `object` | `kg/m³` | Mass per unit volume ($\rho$). Critical for calculating thermal mass $C = \rho \cdot V \cdot c_p$ |
| `thermal_conductivity` | `object` | `W/m·K` | Conductive heat transfer capability ($k$). Determines R-value: $R = L / k$ |
| `specific_heat` | `object` | `J/kg·K` | Specific heat capacity ($c_p$). Quantifies heat retention |
| `emissivity` | `object` | Dimensionless ($0-1$) | Surface longwave thermal radiation emission factor ($\epsilon$) |
| `solar_absorptivity` | `object` | Dimensionless ($0-1$) | Surface shortwave absorption coefficient ($\alpha$) |
| `cost_estimate` | `object` | `USD/m³` or `USD/m²` | Indicative material cost for economic trade-off analysis |
| `source` | `string` | — | Standards citation (IS 3792, ASHRAE Fundamentals, EN ISO 10456, NIST, SECMOL) |
| `notes` | `string` | — | Thermal inertia, moisture vulnerability, and construction recommendations |

---

### 3.4 Glazing Systems Database (`data/materials/glazing.json`)

Fenestration optical and conductive properties.

| Field Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `id` | `string` | — | Glazing system ID (e.g. `"double_low_e_argon_16mm"`, `"polycarbonate_twinwall_10mm"`) |
| `name` | `string` | — | Glazing description (glass panes, gas fill, coatings) |
| `U_value` | `object` | `W/m²·K` | Overall thermal transmittance (conductive + convective + radiative) |
| `SHGC` | `object` | Dimensionless ($0-1$) | Solar Heat Gain Coefficient (direct transmission + absorbed and re-radiated heat) |
| `thickness` | `object` | `m` | Total pane/unit assembly thickness |
| `visible_transmittance` | `float` | Dimensionless ($0-1$) | Visual light transmission (daylighting factor) |
| `source` | `string` | — | Standards reference (NFRC 100/200, EN 673, ASHRAE) |
| `notes` | `string` | — | Performance trade-off (solar heat gain vs night-time conductive heat loss) |

---

### 3.5 Shelter Archetype Templates (`data/shelters/templates.json`)

Standard geometrical configurations and recommended envelope presets.

| Field Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `id` | `string` | — | Archetype ID (e.g. `"temporary_emergency_shelter"`, `"small_permanent_shelter"`, `"family_shelter"`, `"field_shelter"`) |
| `name` | `string` | — | Full archetype display title |
| `capacity` | `integer` | Persons | Designed occupant capacity (used for internal heat gain $Q_{internal} = n \cdot 80\text{W}$) |
| `default_length` | `float` | `m` | Exterior length dimension |
| `default_width` | `float` | `m` | Exterior width dimension |
| `default_height` | `float` | `m` | Eave/ceiling height dimension |
| `shape` | `string` | — | Geometrical form factor (`"rectangular"`, `"rectangular_trombe"`, `"rectangular_shed_roof"`, `"modular_rectangular"`) |
| `floor_area_m2` | `float` | `m²` | Net usable floor area |
| `internal_volume_m3`| `float` | `m³` | Air volume for ventilation infiltration losses: $\dot{V}_{inf} = \text{ACH} \cdot V / 3600$ |
| `recommended_envelope` | `object` | — | Baseline material pairing for walls, roof, floor, glazing, and thermal mass |
| `description` | `string` | — | Deployment scenario and structural notes |

---

## 4. Python Data Access API (`data_loader.py`)

The simulation engine accesses all datasets via pure Python functions without hardcoded constants:

```python
import data_loader

# 1. Load Locations
locations = data_loader.load_locations(as_dataframe=False)
leh_meta = data_loader.get_location("leh")

# 2. Load Weather Timeseries
weather_df = data_loader.load_weather(location_id="leh", as_dataframe=True)

# 3. Load Materials with Category Filtering
insulations = data_loader.load_materials(category="insulation", as_dataframe=False)
mud_brick = data_loader.get_material("mud_brick")

# 4. Load Glazing Specs
glazings = data_loader.load_glazing(as_dataframe=False)
low_e_argon = data_loader.get_glazing("double_low_e_argon_16mm")

# 5. Load Shelter Templates
shelter_template = data_loader.load_shelter_templates(template_id="small_permanent_shelter")
```

---

## 5. Automated Data Validation

Execute the validation suite directly:

```bash
python scripts/validate_data.py
```

Or execute automated tests via `pytest`:

```bash
python -m pytest tests/
```
