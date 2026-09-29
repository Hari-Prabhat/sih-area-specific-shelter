# ThermoShelter AI — Member 1: Climate Intelligence & Climate Strategy Engine

## 1. System Overview

Member 1 implements the **Climate Intelligence Engine** and **Climate Strategy Engine** for ThermoShelter AI. It forms the primary foundational input layer of the entire architectural pipeline:

```
Location / Coordinates
         │
         ▼
Location Resolution (Offline-First / Geocoded)
         │
         ▼
Weather Provider Abstraction (External / Cache / Local Mock)
         │
         ▼
Unit Normalization & Validation (SI Standards)
         │
         ▼
ClimateProfile (Shared Pydantic Contract)
         │
         ▼
Climate Classification Engine (6 Canonical Zones)
         │
         ▼
Climate Strategy Engine
         │
         ▼
PassiveStrategy (Downstream Shared Contract)
```

### Strict Team Boundary Adherence
- **Owned by Member 1**: Location resolution, weather retrieval, data normalization, solar/wind/humidity/temperature synthesis, climate classification into 6 categories, and evidence-based qualitative passive design principles.
- **NOT Implemented by Member 1**:
  - *Geometry* (floor plans, dimensions, height, roof pitch, window areas) $\rightarrow$ Member 2
  - *Materials* (wall assemblies, insulation thicknesses in mm, R/U-values) $\rightarrow$ Member 2
  - *Simulation* (transient heat flow, indoor temperature, comfort hours) $\rightarrow$ Member 3
  - *Optimization* (Pareto optimization, genetic search) $\rightarrow$ Member 3
  - *Frontend / 3D / Reports* (Streamlit, Plotly) $\rightarrow$ Member 4

---

## 2. Directory & Module Architecture

```
sih-area-specific-shelter/
├── backend/
│   └── climate/
│       ├── __init__.py               # Package exports
│       ├── schemas.py                # Stable ClimateProfile & PassiveStrategy Pydantic models
│       ├── location_resolver.py      # Place-name resolution, geocoding & coordinate validation
│       ├── weather_provider.py       # Weather provider abstraction (Open-Meteo, Fallback, Composite)
│       ├── climate_cache.py          # Thread-safe in-memory TTL caching
│       ├── climate_resolver.py       # Unit normalization, extremes extraction & profile assembly
│       ├── climate_classifier.py     # Physics-based classifier for 6 climate zones
│       ├── climate_strategy.py       # Passive design strategy generator & explainability engine
│       ├── service.py                # Main orchestrator service
│       └── api.py                    # Framework-agnostic API dispatchers
├── data/
│   └── mock/
│       ├── leh_climate.json          # High-altitude cold desert benchmark (Golden Scenario)
│       ├── jaisalmer_climate.json    # Hot-arid desert benchmark
│       └── chennai_climate.json      # Warm-humid coastal benchmark
├── docs/
│   └── MEMBER1_CLIMATE_ENGINE.md     # Subsystem documentation (this document)
├── services/
│   └── climate_service.py            # Backwards-compatible adapter connecting legacy callers
└── tests/
    └── climate/
        ├── __init__.py
        ├── test_schemas.py           # Contract validation & serialization tests
        ├── test_location_resolver.py # Valid/invalid coords, geocoding & offline fallback
        ├── test_weather_provider.py  # Provider abstraction, fallback hierarchy & mock data
        ├── test_climate_resolver.py  # Unit normalization & climate data synthesis
        ├── test_climate_classifier.py# All 6 climate classification zones & threshold tests
        ├── test_climate_strategy.py  # Passive strategy generation & qualitative rules
        ├── test_climate_service.py   # End-to-end pipeline & API dispatching tests
        └── test_golden_scenario.py   # Golden scenario & multi-location differential tests
```

---

## 3. Shared Contracts

### 3.1 `ClimateProfile`
Versionable Pydantic v2 model consumed downstream by Members 2 and 3:

```python
class ClimateProfile(BaseModel):
    version: str = "1.0.0"
    location: Location
    climate: ClimateMetrics
    solar: SolarData
    wind: WindData
    humidity: HumidityData
    design_extremes: DesignExtremes
    data_quality: DataQuality
    current_weather: Optional[CurrentWeather] = None
```

Key Sub-models:
- **`Location`**: `place_name`, `latitude` (-90 to +90), `longitude` (-180 to +180), `elevation` (m), `timezone`.
- **`ClimateMetrics`**: `classification` (`ClimateZone`), `annual_mean_temperature` (°C), `minimum_temperature`, `maximum_temperature`, `diurnal_range_mean`.
- **`SolarData`**: `GHI` (W/m² mean flux), `DNI` (W/m²), `DHI` (W/m²), `annual_solar_ghi_kwh_m2` (kWh/m²/year), `unit`, `temporal_resolution`.
- **`WindData`**: `average_speed` (m/s $\ge 0$), `prevailing_direction`, `seasonal_profile`.
- **`HumidityData`**: `average_relative_humidity` (% $0 - 100$), `min_relative_humidity`, `max_relative_humidity`.
- **`DesignExtremes`**: `cold_extreme` (°C 99% heating design value), `hot_extreme` (°C 1% cooling design value), `heating_degree_days_18c`, `cooling_degree_days_18c`.
- **`DataQuality`**: `confidence` (`HIGH`, `MEDIUM`, `LOW`), `provenance` (`MEASURED`, `HISTORICAL`, `ESTIMATED`), `sources`, `notes`.
- **`CurrentWeather`**: `temperature` (°C), `relative_humidity` (%), `wind_speed` (m/s), `solar_irradiance` (W/m²), `is_observed` (bool), `source`.

### 3.2 `PassiveStrategy`
Versionable Pydantic v2 model providing qualitative architectural directives:

```python
class PassiveStrategy(BaseModel):
    version: str = "1.0.0"
    climate_mode: ClimateZone
    primary_strategy: str
    secondary_strategies: List[str]
    solar_capture: PriorityLevel       # HIGH | MODERATE | LOW | MINIMIZED
    thermal_mass: PriorityLevel        # HIGH | MODERATE | LOW
    insulation_priority: PriorityLevel # HIGH | MODERATE | LOW
    ventilation_strategy: str          # Qualitative mode
    shading_strategy: str              # Qualitative approach
    opening_strategy: str              # Qualitative fenestration approach
    airlock: bool                      # Mandatory entrance vestibule
    thermal_buffer: bool               # Unconditioned perimeter buffer spaces
    explanation: str                   # Grounded, evidence-based narrative
    rules_triggered: List[str]         # Diagnostic rule identifiers
```

---

## 4. Normalization Standards

The engine strictly enforces physical engineering units:
- **Temperature**: Always normalized to Celsius (°C). Valid range: -80°C to +70°C. Explicit conversion methods for Fahrenheit and Kelvin.
- **Wind Speed**: Always normalized to meters per second (m/s). Negative values rejected. Explicit converters for km/h, mph, and knots.
- **Relative Humidity**: Always normalized to percentage (0.0% to 100.0%). Fractions ($0.0 \le RH \le 1.0$) automatically converted to %.
- **Solar Irradiance Flux**: Expressed as continuous area flux in Watts per square meter (W/m²).
- **Solar Energy Insolation**: Expressed as cumulative energy in kilowatt-hours per square meter per year (kWh/m²/year). Explicitly distinguished from instantaneous flux to prevent unit confusion.
- **Current vs Design Distinction**: Current observed weather is never substituted for annual climatological design baselines.

---

## 5. Climate Classification Logic

Centralized in `backend/climate/climate_classifier.py` with transparent, physics-based thresholds:

| Climate Zone | Defining Physical Criteria | Canonical Benchmark |
| :--- | :--- | :--- |
| **`EXTREME COLD`** | $T_{\text{cold\_extreme}} \le -10^\circ\text{C}$ or $T_{\text{min}} \le -15^\circ\text{C}$ or ($HDD_{18} \ge 4000$ and $T_{\text{annual\_mean}} \le 8^\circ\text{C}$) | Leh, Ladakh (-18.5°C winter, 4850 HDD) |
| **`HOT DRY`** | $T_{\text{hot\_extreme}} \ge 38^\circ\text{C}$ and $RH_{\text{avg}} \le 45\%$ and Diurnal $\ge 12^\circ\text{C}$ | Jaisalmer, Rajasthan (46.0°C summer, 28% RH) |
| **`HOT HUMID`** | $T_{\text{cold\_extreme}} \ge 15^\circ\text{C}$, $T_{\text{hot\_extreme}} \ge 32^\circ\text{C}$, and $RH_{\text{avg}} \ge 65\%$ | Chennai, Tamil Nadu (20.0°C winter, 74% RH) |
| **`VARIABLE`** | Seasonal swing ($T_{\text{hot}} - T_{\text{cold}}$) $\ge 30^\circ\text{C}$, $T_{\text{hot}} \ge 38^\circ\text{C}$, and $T_{\text{cold}} \le 10^\circ\text{C}$ | Delhi NCR (5.0°C winter to 43.5°C summer) |
| **`COLD`** | $T_{\text{cold\_extreme}} \le 2^\circ\text{C}$ or $T_{\text{annual\_mean}} \le 16^\circ\text{C}$ or $HDD_{18} \ge 2200$ | Srinagar, J&K (-4.0°C winter, 2650 HDD) |
| **`TEMPERATE`** | Mild baseline: $17^\circ\text{C} \le T_{\text{annual\_mean}} \le 26^\circ\text{C}$, $T_{\text{cold}} \ge 7^\circ\text{C}$, $T_{\text{hot}} \le 35^\circ\text{C}$ | Bengaluru, Karnataka (14°C winter, 33.5°C summer) |

---

## 6. Weather Provider & Fallback Hierarchy

The system employs a 3-tier resilient provider pattern:
1. **Cache Layer**: In-memory thread-safe cache with TTL (30 min for current weather, 24 hr for historical climate).
2. **External Live Provider**: Open-Meteo REST API (zero-configuration, free global coverage, ECMWF/GFS weather and solar radiation models).
3. **Local Offline Fallback**: Instantaneous resolution from local mock benchmarks (`data/mock/`) and `data/climate/locations.json`. Works with zero network access.

---

## 7. Golden Scenario Validation: Leh, Ladakh

### Input
- **Place Name**: `"Leh, Ladakh"`
- **Coordinates**: `34.1526°N, 77.5771°E`, Elevation: `3524 m`

### Execution
```python
from backend.climate.service import default_climate_service

result = default_climate_service.analyze("Leh, Ladakh")
```

### Result
- **Classification**: `EXTREME COLD` (Confidence: `HIGH`, Provenance: `HISTORICAL`)
- **Key Metrics**:
  - Winter Design Extreme: `-18.5°C`
  - Summer Design Extreme: `26.0°C`
  - Annual Mean Temperature: `5.3°C`
  - Solar GHI: `239.7 W/m²` (Cumulative: `2100 kWh/m²/year`)
  - Relative Humidity: `32.0%`
  - Heating Degree Days: `4850 HDD18`
- **Passive Strategy Generated**:
  - Primary: `Solar heat capture + envelope thermal protection`
  - Solar Capture: `HIGH`
  - Thermal Mass: `HIGH`
  - Insulation Priority: `HIGH`
  - Entrance Airlock: `True`
  - Thermal Buffer Zones: `True`
  - Ventilation Mode: `CONTROLLED_MINIMAL_PREHEATED`
  - Fenestration Strategy: `MINIMIZED_HIGH_PERFORMANCE_SOLAR_BIAS`
  - Explanation: Detailed, physics-grounded narrative referencing -18.5°C cold extreme and 4850 HDD.

---

## 8. Multi-Location Benchmark Contrast

| Metric / Directive | Leh, Ladakh | Jaisalmer, Rajasthan | Chennai, Tamil Nadu |
| :--- | :--- | :--- | :--- |
| **Climate Classification** | `EXTREME COLD` | `HOT DRY` | `HOT HUMID` |
| **Winter Design Extreme** | -18.5°C | 7.0°C | 20.0°C |
| **Summer Design Extreme** | 26.0°C | 46.0°C | 39.0°C |
| **Average Relative Humidity** | 32.0% | 28.5% | 74.0% |
| **Solar Capture Priority** | `HIGH` | `LOW` | `MINIMIZED` |
| **Thermal Mass Priority** | `HIGH` | `HIGH` | `LOW` |
| **Insulation Priority** | `HIGH` | `MODERATE` | `LOW` |
| **Entrance Airlock** | `True` | `False` | `False` |
| **Thermal Buffer Zones** | `True` | `False` | `False` |
| **Ventilation Strategy** | Controlled minimal | Nocturnal flush cooling | Continuous cross-ventilation |

---

## 9. API Usage

### Direct Python Invocation
```python
from backend.climate.service import default_climate_service

# Full pipeline
result = default_climate_service.analyze("Leh, Ladakh")
profile = result.profile
strategy = result.strategy
```

### Framework-Agnostic API Endpoints (`backend.climate.api`)
```python
from backend.climate.api import default_climate_api

# 1. Resolve location
loc = default_climate_api.handle_location({"query": "Leh, Ladakh"})

# 2. Get normalized profile
profile = default_climate_api.handle_profile({"location": "Leh, Ladakh"})

# 3. Classify profile
classification = default_climate_api.handle_classify({"profile": profile})

# 4. Generate passive strategy
strategy = default_climate_api.handle_strategy({"profile": profile})

# 5. Full end-to-end analysis
analysis = default_climate_api.handle_analyze({"location": "Leh, Ladakh"})
```

---

## 10. Downstream Integration Instructions

### For Member 2 (Architecture, Geometry & Envelopes)
- Read `strategy.solar_capture` to determine window-to-wall ratio bias (e.g. `HIGH` $\rightarrow$ prioritize south-facing glazing).
- Read `strategy.insulation_priority` to select wall assembly tiers (e.g. `HIGH` $\rightarrow$ maximize R-value specifications).
- Read `strategy.airlock` (`bool`) $\rightarrow$ if `True`, add an entrance vestibule airlock to the floor plan.
- Read `strategy.thermal_buffer` (`bool`) $\rightarrow$ if `True`, position unheated utility spaces/corridors on prevailing wind facades.

### For Member 3 (Thermal Simulation & Optimization)
- Read `profile.climate.annual_mean_temperature`, `profile.design_extremes.cold_extreme`, and `profile.design_extremes.hot_extreme` as boundary conditions for transient Forward Euler simulation.
- Read `profile.solar.GHI` and `profile.wind.average_speed` for convection and radiation boundary coefficients.
- Use `strategy.ventilation_strategy` to configure simulated Air Changes per Hour (ACH) schedule (e.g. day vs night).

### For Member 4 (Frontend UI & Visualization)
- Display `profile.location.place_name`, `profile.climate.classification`, and `strategy.primary_strategy` on the top summary dashboard.
- Render `strategy.explanation` in the evidence-based recommendation studio.
- Render `profile.data_quality.provenance` and `profile.data_quality.confidence` as reliability badges.
