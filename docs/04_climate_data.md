# ThermoShelter AI — Climate & Weather Data

**Purpose:** Document the climate metadata and weather datasets used by the current prototype.

---

## 1. Climate Data Architecture

ThermoShelter uses two complementary climate-data layers:

1. **Location metadata** — `data/climate/locations.json`
2. **Hourly weather data** — `data/climate/weather.csv` and bundled EPW files in `data/weather/`

The active simulation reads the local EPW files through `services/climate_service.py`, using `pvlib` for EPW parsing.

### Current active simulation locations

| Location | Climate type | Role |
|---|---|---|
| Leh | Cold / High-Altitude Desert | Severe-cold scenario |
| Jaisalmer | Hot-Dry / Arid Desert | Extreme heat scenario |
| Delhi | Composite | Seasonal-extreme scenario |
| Chennai | Warm-Humid / Coastal | Humid-heat scenario |
| Bengaluru | Moderate / Plateau | Moderate-climate scenario |

The repository's metadata database contains **7 locations** in total, while the current recommendation and EPW simulation workflow actively uses the five locations above.

---

## 2. Location Metadata

`locations.json` contains:

- unique location ID;
- name and region;
- latitude/longitude;
- altitude;
- climate type;
- Köppen classification;
- design winter temperature;
- design summer temperature;
- annual solar GHI;
- heating degree days;
- cooling degree days;
- source; and
- engineering notes.

Examples:

| Location | Elevation | Design winter | Design summer | Annual solar GHI |
|---|---:|---:|---:|---:|
| Leh | 3524 m | -18.5 °C | 26.0 °C | 2100 kWh/m² |
| Jaisalmer | 225 m | 7.0 °C | 46.0 °C | 2250 kWh/m² |
| Delhi | 216 m | 5.0 °C | 43.5 °C | 1900 kWh/m² |
| Chennai | 6 m | 20.0 °C | 39.0 °C | 1950 kWh/m² |
| Bengaluru | — | — | — | — |

The exact values used by the application should always be taken from the repository data files rather than from presentation slides.

---

## 3. EPW Weather Dataset

The active simulation contains five bundled EPW files:

```text
data/weather/
├── leh.epw
├── jaisalmer.epw
├── delhi.epw
├── chennai.epw
└── bengaluru.epw
```

The local/bundled approach makes the prototype reproducible without requiring a live weather service.

The climate service extracts hourly variables including:

- dry-bulb/ambient temperature;
- direct normal irradiance;
- diffuse horizontal irradiance;
- wind speed; and
- relative humidity.

The simulation combines direct and diffuse solar components for its solar-gain calculations.

---

## 4. Weather CSV

`data/climate/weather.csv` contains **1,176 rows** and the validation suite checks:

- timestamp;
- location ID;
- ambient temperature;
- solar irradiance;
- wind speed;
- relative humidity; and
- cloud cover.

The validation rules reject invalid timestamps, negative solar irradiance/wind speed, relative humidity outside 0–100%, and cloud-cover values outside 0–1.

---

## 5. Climate Classification

The recommendation engine maps the five active locations to design categories:

```text
Leh        → cold
Jaisalmer  → hot_dry
Chennai    → hot_humid
Delhi      → composite
Bengaluru  → moderate
```

This classification drives climate-specific design recommendations.

Examples:

### Leh
- high insulation;
- solar capture;
- pitched/snow-shedding roof;
- reduced thermal losses.

### Jaisalmer
- solar rejection;
- shading;
- reflective roof;
- thermal mass.

### Chennai
- cross ventilation;
- generous shading;
- lightweight/moisture-aware envelope strategy.

### Delhi
- balanced summer/winter envelope response.

### Bengaluru
- moderate envelope and passive daylight/ventilation strategies.

---

## 6. Data Sources

The location metadata records sources such as:

- IMD;
- NREL NSRDB;
- ASHRAE Fundamentals;
- BEE/ECBC;
- ISHRAE;
- MNRE; and
- NBC references.

The metadata source field should be treated as **provenance information for the stored engineering dataset**, not as proof that every value has been independently field-validated by the ThermoShelter team.

---

## 7. Data Validation

The repository includes:

```text
scripts/validate_data.py
```

The validation suite checks:

| Dataset | Current count |
|---|---:|
| Locations | 7 |
| Weather CSV rows | 1,176 |
| Materials | 19 |
| Glazing records | 7 |
| Shelter templates | 4 |

The current validation command reports:

> **ALL CHECKS PASSED SUCCESSFULLY. DATASETS ARE 100% COMPLIANT.**

This verifies dataset structure and value constraints; it does not constitute real-world climate-data certification.

---

## 8. Current Limitations

- The active simulation is based on bundled/local climate profiles.
- There is no live weather API integration in the current repository.
- The application does not currently generate a location-specific EPW profile dynamically.
- Humidity is available in the weather data, but the current thermal model primarily uses sensible heat effects rather than a complete latent-moisture model.
- The weather dataset should be treated as a modelling input, not a substitute for site-specific engineering measurements.

---

## 9. Future Extension

A production version can extend the climate subsystem with:

```text
User Location
     ↓
Live / Verified Climate Source
     ↓
Climate Classification
     ↓
Design Weather Profile
     ↓
Seasonal / Annual Simulation
     ↓
Climate-Specific Optimization
```

This would allow the current five-location prototype to evolve into a broader area-specific shelter design platform.
