"""
THERMOSHELTER AI - Shared Subsystem Contracts & Data Models
============================================================
Defines standardized, typed, validated, and serializable data models
for cross-member integration:

  - Member 1 -> Member 3: ClimateProfile
  - Member 2 -> Member 3: ShelterDesign
  - Member 3 Internal:    SimulationInput, OptimizationInput
  - Member 3 -> Member 4: SimulationResult, OptimizationResult

Architecture:
  Clean boundary dataclasses ensuring independent testability and safe integration.
"""

from dataclasses import asdict, dataclass, field
import json
import math
from typing import Any, Dict, List, Optional, Union
import numpy as np

from services.formula_constants import (
    DEFAULT_ACH,
    DEFAULT_COMFORT_MAX,
    DEFAULT_COMFORT_MIN,
    DEFAULT_OCCUPANT_HEAT_GAIN,
)
from services.shelter.models import (
    DataProvenance,
    GlazingDefinition,
    MaterialAssembly,
    MaterialLayer,
    OpeningDefinition,
    PassiveStrategy,
    ShelterDesign,
    ShelterGeometry,
    ShelterRequirements,
    ThermalMassDefinition,
    ZoneDefinition,
)


# =====================================================================
# 1. UPSTREAM CONTRACT: CLIMATE PROFILE (Member 1 Contract)
# =====================================================================

@dataclass
class ClimateProfile:
    """
    Contract representing climate and weather time series data provided by Member 1.

    SI Units:
      - hourly_temperature: °C
      - hourly_direct_solar: W/m² (Direct Normal Irradiance, DNI)
      - hourly_diffuse_solar: W/m² (Diffuse Horizontal Irradiance, DHI)
      - hourly_wind_speed: m/s (optional)
      - hourly_humidity: % relative humidity [0, 100] (optional)
      - hourly_cloud_cover: fraction [0.0, 1.0] (optional)
      - hourly_precipitation: mm (optional)
      - elevation_m: meters above sea level (optional)
      - timezone_offset_hours: UTC offset in hours [-14.0, +14.0] (optional)
      - latitude, longitude: decimal degrees
      - timestamps: ISO 8601 strings (optional)
      - data_source: data origin description (e.g. "EPW_Leh_ISD", "Synthetic_diurnal")
      - data_provenance: DataProvenance constant (e.g. "measured", "historical", "simulated")
      - data_confidence: fraction [0.0, 1.0] (optional)
    """
    city: str
    latitude: float
    longitude: float
    hourly_temperature: List[float]
    hourly_direct_solar: List[float]
    hourly_diffuse_solar: List[float]
    hourly_wind_speed: Optional[List[float]] = None
    hourly_humidity: Optional[List[float]] = None
    climate_zone: Optional[str] = None
    elevation_m: Optional[float] = None
    timezone_offset_hours: Optional[float] = None
    hourly_cloud_cover: Optional[List[float]] = None
    hourly_precipitation: Optional[List[float]] = None
    timestamps: Optional[List[str]] = None
    data_source: str = "synthetic"
    data_provenance: str = DataProvenance.SIMULATED
    data_confidence: Optional[float] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validates physical sanity and array consistency of climate data."""
        if not self.city or not isinstance(self.city, str):
            raise ValueError("City name must be a non-empty string.")

        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude must be between -90 and 90 degrees, got {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude must be between -180 and 180 degrees, got {self.longitude}")

        n_hours = len(self.hourly_temperature)
        if n_hours == 0:
            raise ValueError("hourly_temperature time series cannot be empty.")

        if len(self.hourly_direct_solar) != n_hours:
            raise ValueError(
                f"hourly_direct_solar length ({len(self.hourly_direct_solar)}) "
                f"must match hourly_temperature length ({n_hours})"
            )
        if len(self.hourly_diffuse_solar) != n_hours:
            raise ValueError(
                f"hourly_diffuse_solar length ({len(self.hourly_diffuse_solar)}) "
                f"must match hourly_temperature length ({n_hours})"
            )

        # Check for non-finite values or extreme physics
        for i, t in enumerate(self.hourly_temperature):
            if not math.isfinite(t) or t < -80.0 or t > 70.0:
                raise ValueError(f"Invalid hourly temperature at index {i}: {t}°C")

        for i, dni in enumerate(self.hourly_direct_solar):
            if not math.isfinite(dni) or dni < 0.0 or dni > 1500.0:
                raise ValueError(f"Invalid hourly direct solar at index {i}: {dni} W/m²")

        for i, dhi in enumerate(self.hourly_diffuse_solar):
            if not math.isfinite(dhi) or dhi < 0.0 or dhi > 1000.0:
                raise ValueError(f"Invalid hourly diffuse solar at index {i}: {dhi} W/m²")

        if self.hourly_wind_speed is not None:
            if len(self.hourly_wind_speed) != n_hours:
                raise ValueError("hourly_wind_speed length must match hourly_temperature length.")
            for i, ws in enumerate(self.hourly_wind_speed):
                if not math.isfinite(ws) or ws < 0.0:
                    raise ValueError(f"Invalid hourly wind speed at index {i}: {ws} m/s")

        if self.hourly_humidity is not None:
            if len(self.hourly_humidity) != n_hours:
                raise ValueError("hourly_humidity length must match hourly_temperature length.")
            for i, rh in enumerate(self.hourly_humidity):
                if not math.isfinite(rh) or rh < 0.0 or rh > 100.0:
                    raise ValueError(f"Invalid hourly relative humidity at index {i}: {rh}%")

        if self.elevation_m is not None:
            if not (-500.0 <= self.elevation_m <= 9000.0):
                raise ValueError(f"Elevation must be between -500 and 9000 meters, got {self.elevation_m}")

        if self.timezone_offset_hours is not None:
            if not (-14.0 <= self.timezone_offset_hours <= 14.0):
                raise ValueError(f"Timezone offset must be between -14 and +14 hours, got {self.timezone_offset_hours}")

        if self.hourly_cloud_cover is not None:
            if len(self.hourly_cloud_cover) != n_hours:
                raise ValueError("hourly_cloud_cover length must match hourly_temperature length.")
            for i, cc in enumerate(self.hourly_cloud_cover):
                if not math.isfinite(cc) or not (0.0 <= cc <= 1.0):
                    raise ValueError(f"Invalid hourly cloud cover at index {i}: {cc}")

        if self.hourly_precipitation is not None:
            if len(self.hourly_precipitation) != n_hours:
                raise ValueError("hourly_precipitation length must match hourly_temperature length.")
            for i, pr in enumerate(self.hourly_precipitation):
                if not math.isfinite(pr) or pr < 0.0:
                    raise ValueError(f"Invalid hourly precipitation at index {i}: {pr} mm")

        if self.timestamps is not None:
            if len(self.timestamps) != n_hours:
                raise ValueError("timestamps length must match hourly_temperature length.")

        if self.data_confidence is not None:
            if not (0.0 <= self.data_confidence <= 1.0):
                raise ValueError(f"data_confidence must be between 0.0 and 1.0, got {self.data_confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ClimateProfile to standard dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClimateProfile":
        """Constructs ClimateProfile from dictionary with graceful key resolution."""
        city = data.get("city", "unknown")
        lat = float(data.get("latitude", 0.0))
        lon = float(data.get("longitude", 0.0))
        t_arr = [float(x) for x in data.get("hourly_temperature", [])]
        dni_arr = [float(x) for x in data.get("hourly_direct_solar", [])]
        dhi_arr = [float(x) for x in data.get("hourly_diffuse_solar", [])]
        ws_raw = data.get("hourly_wind_speed")
        ws_arr = [float(x) for x in ws_raw] if ws_raw is not None else None
        rh_raw = data.get("hourly_humidity")
        rh_arr = [float(x) for x in rh_raw] if rh_raw is not None else None
        cc_raw = data.get("hourly_cloud_cover")
        cc_arr = [float(x) for x in cc_raw] if cc_raw is not None else None
        pr_raw = data.get("hourly_precipitation")
        pr_arr = [float(x) for x in pr_raw] if pr_raw is not None else None
        ts_raw = data.get("timestamps")
        ts_arr = [str(x) for x in ts_raw] if ts_raw is not None else None
        cz = data.get("climate_zone")
        elev = float(data["elevation_m"]) if data.get("elevation_m") is not None else None
        tz = float(data["timezone_offset_hours"]) if data.get("timezone_offset_hours") is not None else None
        src = str(data.get("data_source", "synthetic"))
        prov = str(data.get("data_provenance", DataProvenance.SIMULATED))
        conf = float(data["data_confidence"]) if data.get("data_confidence") is not None else None

        return cls(
            city=city,
            latitude=lat,
            longitude=lon,
            hourly_temperature=t_arr,
            hourly_direct_solar=dni_arr,
            hourly_diffuse_solar=dhi_arr,
            hourly_wind_speed=ws_arr,
            hourly_humidity=rh_arr,
            climate_zone=cz,
            elevation_m=elev,
            timezone_offset_hours=tz,
            hourly_cloud_cover=cc_arr,
            hourly_precipitation=pr_arr,
            timestamps=ts_arr,
            data_source=src,
            data_provenance=prov,
            data_confidence=conf,
        )


# =====================================================================
# 2. NUMERICAL ENVELOPE PARAMETERS (Member 3 Internal Model)
# =====================================================================

@dataclass
class SimulationEnvelopeParameters:
    """
    Physical simulation envelope parameters consumed by Member 3's numerical solver.
    Extracts and maps multi-layer U-values, total thermal capacitance, and aperture areas
    from the canonical ShelterDesign model via SimulationAdapter.

    SI Units:
      - wall_u_value: W/(m²·K)
      - roof_u_value: W/(m²·K)
      - floor_u_value: W/(m²·K)
      - window_u_value: W/(m²·K)
      - window_shgc: dimensionless fraction [0, 1]
      - window_area_m2: square meters (m²)
      - gross_wall_area_m2: square meters (m²)
      - roof_area_m2: square meters (m²)
      - floor_area_m2: square meters (m²)
      - volume_m3: cubic meters (m³)
      - effective_thermal_capacity_j_k: Joules per Kelvin (J/K)
      - orientation_deg: degrees [0, 360]
      - ach: air changes per hour (1/h)
      - occupants: integer count (persons)
      - heat_per_person: Watts per occupant (W/person)
    """
    wall_u_value: float = 1.5
    roof_u_value: float = 0.8
    floor_u_value: float = 0.5
    window_u_value: float = 2.8
    window_shgc: float = 0.70
    window_area_m2: float = 2.0
    gross_wall_area_m2: float = 39.2
    roof_area_m2: float = 12.0
    floor_area_m2: float = 12.0
    volume_m3: float = 33.6
    effective_thermal_capacity_j_k: float = 1.0e7
    orientation_deg: float = 180.0
    ach: float = DEFAULT_ACH
    occupants: int = 2
    heat_per_person: float = DEFAULT_OCCUPANT_HEAT_GAIN
    roof_type: str = "flat"
    pitch_angle_deg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationEnvelopeParameters":
        return cls(**data)


# =====================================================================
# 3. MEMBER 3 CONTRACT: SIMULATION INPUT
# =====================================================================

@dataclass
class SimulationInput:
    """
    Standard input contract consumed by Member 3's simulation engine.
    Encapsulates ClimateProfile + canonical ShelterDesign with numerical solver settings
    and derived simulation envelope parameters.
    """
    climate: ClimateProfile
    design: ShelterDesign
    hours_to_simulate: int = 168
    substeps: int = 60
    initial_indoor_temp: float = 20.0
    envelope_parameters: Optional[SimulationEnvelopeParameters] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validates simulation run configuration."""
        if not isinstance(self.climate, ClimateProfile):
            raise TypeError("climate must be an instance of ClimateProfile.")
        if not isinstance(self.design, ShelterDesign):
            raise TypeError("design must be an instance of ShelterDesign.")

        if self.hours_to_simulate <= 0:
            raise ValueError(f"hours_to_simulate must be positive, got {self.hours_to_simulate}")

        available_hours = len(self.climate.hourly_temperature)
        if self.hours_to_simulate > available_hours:
            raise ValueError(
                f"Requested hours ({self.hours_to_simulate}) exceeds available weather hours ({available_hours})"
            )

        if not (1 <= self.substeps <= 3600):
            raise ValueError(f"substeps must be between 1 and 3600 per hour, got {self.substeps}")

        if not (-60.0 <= self.initial_indoor_temp <= 60.0):
            raise ValueError(f"Unrealistic initial indoor temperature: {self.initial_indoor_temp}°C")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes SimulationInput to standard dictionary."""
        d = {
            "climate": self.climate.to_dict(),
            "design": self.design.to_dict(),
            "hours_to_simulate": self.hours_to_simulate,
            "substeps": self.substeps,
            "initial_indoor_temp": self.initial_indoor_temp,
        }
        if self.envelope_parameters is not None:
            d["envelope_parameters"] = self.envelope_parameters.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationInput":
        """Constructs SimulationInput from dictionary."""
        climate_dict = data.get("climate", {})
        design_dict = data.get("design", {})
        climate = ClimateProfile.from_dict(climate_dict)
        design = ShelterDesign.from_dict(design_dict)
        env_dict = data.get("envelope_parameters")
        env_params = SimulationEnvelopeParameters.from_dict(env_dict) if env_dict else None
        return cls(
            climate=climate,
            design=design,
            hours_to_simulate=int(data.get("hours_to_simulate", 168)),
            substeps=int(data.get("substeps", 60)),
            initial_indoor_temp=float(data.get("initial_indoor_temp", 20.0)),
            envelope_parameters=env_params,
        )


# =====================================================================
# 4. DOWNSTREAM CONTRACT: SIMULATION RESULT (Member 3 -> Member 4 / 5)
# =====================================================================

@dataclass
class SimulationResult:
    """
    Standard output contract produced by Member 3's simulation engine.
    Exposes full timeseries, component breakdown, energy totals, comfort metrics,
    and assembly properties for visualization in 2D charts and 3D digital twins.
    """
    city: str
    indoor_temperatures: List[float]
    outdoor_temperatures: List[float]
    solar_irradiance: List[float]
    solar_power: List[float]
    solar_thermal_gain: List[float]
    hourly_internal_gain: List[float]
    wall_heat_flow: List[float]
    roof_heat_flow: List[float]
    floor_heat_flow: List[float]
    window_heat_flow: List[float]
    ventilation_heat_flow: List[float]
    radiation_heat_flow: List[float]
    net_heat_flow: List[float]
    comfort_status: str
    comfort_status_series: List[str]
    comfort_hours: float
    comfort_percentage: float
    discomfort_degree_hours: float
    integrated_solar_energy_kwh: float
    integrated_incident_solar_kwh: float
    component_heat_loss_kwh: Dict[str, float]
    total_heat_loss_kwh: float
    comfort_metrics: Dict[str, Any]
    energy_totals_kwh: Dict[str, Any]
    u_values: Dict[str, float]
    geometry: Dict[str, Any]
    specs: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    # Phase D Enhanced Physical Metrics (with defaults for compatibility)
    thermal_storage_flow: Optional[List[float]] = None
    hourly_thermal_storage: Optional[List[float]] = None
    hourly_heating_demand: Optional[List[float]] = None
    hourly_cooling_demand: Optional[List[float]] = None
    hourly_net_load: Optional[List[float]] = None
    heating_demand_kwh: float = 0.0
    cooling_demand_kwh: float = 0.0
    total_conditioning_demand_kwh: float = 0.0
    effective_thermal_capacity_j_k: float = 0.0
    thermal_mass_breakdown: Optional[Dict[str, float]] = None

    @property
    def indoor_temperature(self) -> List[float]:
        """Legacy alias for backward compatibility."""
        return self.indoor_temperatures

    @property
    def outdoor_temperature(self) -> List[float]:
        """Legacy alias for backward compatibility."""
        return self.outdoor_temperatures

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes SimulationResult to dictionary compatible with existing
        frontend and test expectations.
        """
        d = asdict(self)
        # Add legacy aliases for backward compatibility
        d["indoor_temperature"] = self.indoor_temperatures
        d["outdoor_temperature"] = self.outdoor_temperatures
        d["hourly_solar_gain"] = self.solar_thermal_gain
        d["hourly_wall_loss"] = self.wall_heat_flow
        d["hourly_roof_loss"] = self.roof_heat_flow
        d["hourly_window_loss"] = self.window_heat_flow
        d["hourly_vent_loss"] = self.ventilation_heat_flow
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        """Constructs SimulationResult from dictionary with fallback alias mapping."""
        in_temps = data.get("indoor_temperatures", data.get("indoor_temperature", []))
        out_temps = data.get("outdoor_temperatures", data.get("outdoor_temperature", []))
        sol_gain = data.get("solar_thermal_gain", data.get("hourly_solar_gain", []))
        wall_loss = data.get("wall_heat_flow", data.get("hourly_wall_loss", []))
        roof_loss = data.get("roof_heat_flow", data.get("hourly_roof_loss", []))
        win_loss = data.get("window_heat_flow", data.get("hourly_window_loss", []))
        vent_loss = data.get("ventilation_heat_flow", data.get("hourly_vent_loss", []))
        th_storage = data.get("thermal_storage_flow", data.get("hourly_thermal_storage"))
        q_heat = data.get("hourly_heating_demand")
        q_cool = data.get("hourly_cooling_demand")
        q_net_load = data.get("hourly_net_load")

        return cls(
            city=str(data.get("city", "unknown")),
            indoor_temperatures=[float(x) for x in in_temps],
            outdoor_temperatures=[float(x) for x in out_temps],
            solar_irradiance=[float(x) for x in data.get("solar_irradiance", [])],
            solar_power=[float(x) for x in data.get("solar_power", [])],
            solar_thermal_gain=[float(x) for x in sol_gain],
            hourly_internal_gain=[float(x) for x in data.get("hourly_internal_gain", [])],
            wall_heat_flow=[float(x) for x in wall_loss],
            roof_heat_flow=[float(x) for x in roof_loss],
            floor_heat_flow=[float(x) for x in data.get("floor_heat_flow", [])],
            window_heat_flow=[float(x) for x in win_loss],
            ventilation_heat_flow=[float(x) for x in vent_loss],
            radiation_heat_flow=[float(x) for x in data.get("radiation_heat_flow", [])],
            net_heat_flow=[float(x) for x in data.get("net_heat_flow", [])],
            comfort_status=str(data.get("comfort_status", "Unknown")),
            comfort_status_series=list(data.get("comfort_status_series", [])),
            comfort_hours=float(data.get("comfort_hours", 0.0)),
            comfort_percentage=float(data.get("comfort_percentage", 0.0)),
            discomfort_degree_hours=float(data.get("discomfort_degree_hours", 0.0)),
            integrated_solar_energy_kwh=float(data.get("integrated_solar_energy_kwh", 0.0)),
            integrated_incident_solar_kwh=float(data.get("integrated_incident_solar_kwh", 0.0)),
            component_heat_loss_kwh=dict(data.get("component_heat_loss_kwh", {})),
            total_heat_loss_kwh=float(data.get("total_heat_loss_kwh", 0.0)),
            comfort_metrics=dict(data.get("comfort_metrics", {})),
            energy_totals_kwh=dict(data.get("energy_totals_kwh", {})),
            u_values=dict(data.get("u_values", {})),
            geometry=dict(data.get("geometry", {})),
            specs=dict(data.get("specs", {})),
            warnings=list(data.get("warnings", [])),
            thermal_storage_flow=[float(x) for x in th_storage] if th_storage is not None else None,
            hourly_thermal_storage=[float(x) for x in th_storage] if th_storage is not None else None,
            hourly_heating_demand=[float(x) for x in q_heat] if q_heat is not None else None,
            hourly_cooling_demand=[float(x) for x in q_cool] if q_cool is not None else None,
            hourly_net_load=[float(x) for x in q_net_load] if q_net_load is not None else None,
            heating_demand_kwh=float(data.get("heating_demand_kwh", data.get("energy_totals_kwh", {}).get("heating_demand_kwh", 0.0))),
            cooling_demand_kwh=float(data.get("cooling_demand_kwh", data.get("energy_totals_kwh", {}).get("cooling_demand_kwh", 0.0))),
            total_conditioning_demand_kwh=float(data.get("total_conditioning_demand_kwh", data.get("energy_totals_kwh", {}).get("total_conditioning_demand_kwh", 0.0))),
            effective_thermal_capacity_j_k=float(data.get("effective_thermal_capacity_j_k", 0.0)),
            thermal_mass_breakdown=dict(data["thermal_mass_breakdown"]) if data.get("thermal_mass_breakdown") is not None else None,
        )


# =====================================================================
# 5. MEMBER 3 CONTRACT: OPTIMIZATION INPUT
# =====================================================================

@dataclass
class OptimizationInput:
    """
    Standard configuration contract consumed by Member 3's optimization engine.
    Defines search boundaries, fixed parameters, target objectives, and constraints.
    """
    city: str
    home_type: str = "Permanent"
    length: float = 4.0
    width: float = 3.0
    height: float = 2.8
    wall_material: Optional[str] = None
    glazing: Optional[str] = None
    orientation: Optional[str] = None
    occupants: int = 2
    min_insulation_m: float = 0.0
    max_insulation_m: float = 0.20
    min_window_area: float = 0.5
    max_window_area: Optional[float] = None
    allowed_wall_materials: Optional[List[str]] = None
    allowed_glazings: Optional[List[str]] = None
    allowed_orientations: Optional[List[str]] = None
    n_trials: int = 40
    substeps: int = 15
    hours_to_simulate: int = 168
    weights: Optional[Dict[str, float]] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validates optimization bounds and parameter consistency."""
        if not self.city or not isinstance(self.city, str):
            raise ValueError("City name must be a non-empty string.")

        if self.length <= 0.0 or self.width <= 0.0 or self.height <= 0.0:
            raise ValueError("Shelter dimensions must be strictly positive (> 0).")

        if self.min_insulation_m < 0.0:
            raise ValueError(f"min_insulation_m cannot be negative, got {self.min_insulation_m}")
        if self.max_insulation_m < self.min_insulation_m:
            raise ValueError(
                f"max_insulation_m ({self.max_insulation_m}) cannot be less than "
                f"min_insulation_m ({self.min_insulation_m})"
            )

        if self.min_window_area < 0.0:
            raise ValueError(f"min_window_area cannot be negative, got {self.min_window_area}")
        if self.max_window_area is not None:
            if self.max_window_area < self.min_window_area:
                raise ValueError(
                    f"max_window_area ({self.max_window_area}) cannot be less than "
                    f"min_window_area ({self.min_window_area})"
                )

        if self.n_trials <= 0:
            raise ValueError(f"n_trials must be at least 1, got {self.n_trials}")
        if self.substeps <= 0:
            raise ValueError(f"substeps must be at least 1, got {self.substeps}")
        if self.hours_to_simulate <= 0:
            raise ValueError(f"hours_to_simulate must be at least 1, got {self.hours_to_simulate}")

        if self.weights is not None:
            w_sum = sum(self.weights.values())
            if not (0.95 <= w_sum <= 1.05):
                raise ValueError(f"Optimization weights must sum to 1.0, got {w_sum}")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes OptimizationInput to standard dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationInput":
        """Constructs OptimizationInput from dictionary."""
        return cls(
            city=str(data.get("city", "leh")),
            home_type=str(data.get("home_type", data.get("shelter_type", "Permanent"))),
            length=float(data.get("length", 4.0)),
            width=float(data.get("width", 3.0)),
            height=float(data.get("height", 2.8)),
            wall_material=data.get("wall_material"),
            glazing=data.get("glazing"),
            orientation=data.get("orientation"),
            occupants=int(data.get("occupants", 2)),
            min_insulation_m=float(data.get("min_insulation_m", 0.0)),
            max_insulation_m=float(data.get("max_insulation_m", 0.20)),
            min_window_area=float(data.get("min_window_area", 0.5)),
            max_window_area=float(data["max_window_area"]) if data.get("max_window_area") is not None else None,
            allowed_wall_materials=data.get("allowed_wall_materials"),
            allowed_glazings=data.get("allowed_glazings"),
            allowed_orientations=data.get("allowed_orientations"),
            n_trials=int(data.get("n_trials", 40)),
            substeps=int(data.get("substeps", 15)),
            hours_to_simulate=int(data.get("hours_to_simulate", 168)),
            weights=data.get("weights"),
        )


# =====================================================================
# 6. DOWNSTREAM CONTRACT: OPTIMIZATION RESULT (Member 3 -> Member 4 / 5)
# =====================================================================

@dataclass
class OptimizationCandidate:
    """
    Contract representing one ranked candidate shelter design produced by the optimizer.
    """
    rank: int
    label: str
    rationale: str
    overall_score: float
    sub_scores: Dict[str, float]
    insulation_mm: float
    insulation_thickness_m: float
    window_area_m2: float
    wall_material: str
    wall_material_name: str
    glazing: str
    glazing_name: str
    orientation: str
    comfort_hours: float
    comfort_percentage: float
    discomfort_dh: float
    total_heat_loss_kwh: float
    solar_gain_kwh: float
    u_values: Dict[str, float]
    heating_demand_kwh: float = 0.0
    cooling_demand_kwh: float = 0.0
    total_conditioning_demand_kwh: float = 0.0
    effective_thermal_capacity_j_k: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationCandidate":
        return cls(
            rank=int(data.get("rank", 1)),
            label=str(data.get("label", "Design #1")),
            rationale=str(data.get("rationale", "")),
            overall_score=float(data.get("overall_score", 0.0)),
            sub_scores=dict(data.get("sub_scores", {})),
            insulation_mm=float(data.get("insulation_mm", 0.0)),
            insulation_thickness_m=float(data.get("insulation_thickness_m", data.get("insulation_mm", 0.0) / 1000.0)),
            window_area_m2=float(data.get("window_area_m2", 2.0)),
            wall_material=str(data.get("wall_material", "brick")),
            wall_material_name=str(data.get("wall_material_name", data.get("wall_material", "Brick"))),
            glazing=str(data.get("glazing", "double_clear")),
            glazing_name=str(data.get("glazing_name", data.get("glazing", "Double Glazed"))),
            orientation=str(data.get("orientation", "south")),
            comfort_hours=float(data.get("comfort_hours", 0.0)),
            comfort_percentage=float(data.get("comfort_percentage", 0.0)),
            discomfort_dh=float(data.get("discomfort_dh", 0.0)),
            total_heat_loss_kwh=float(data.get("total_heat_loss_kwh", 0.0)),
            solar_gain_kwh=float(data.get("solar_gain_kwh", 0.0)),
            u_values=dict(data.get("u_values", {})),
            heating_demand_kwh=float(data.get("heating_demand_kwh", 0.0)),
            cooling_demand_kwh=float(data.get("cooling_demand_kwh", 0.0)),
            total_conditioning_demand_kwh=float(data.get("total_conditioning_demand_kwh", 0.0)),
            effective_thermal_capacity_j_k=float(data.get("effective_thermal_capacity_j_k", 0.0)),
        )



@dataclass
class OptimizationResult:
    """
    Standard output contract produced by Member 3's optimization engine.
    Exposes best design parameters, score, ranked candidates, and simulation metrics.
    """
    city: str
    home_type: str
    insulation_thickness_m: float
    insulation_mm: float
    window_area_m2: float
    wall_material: str
    glazing: str
    glazing_name: str
    orientation: str
    discomfort_score: float
    simulation_result: Dict[str, Any]
    ranked_designs: List[OptimizationCandidate]
    n_trials: int = 40
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes OptimizationResult to dictionary."""
        d = {
            "city": self.city,
            "home_type": self.home_type,
            "insulation_thickness_m": self.insulation_thickness_m,
            "insulation_mm": self.insulation_mm,
            "window_area_m2": self.window_area_m2,
            "wall_material": self.wall_material,
            "glazing": self.glazing,
            "glazing_name": self.glazing_name,
            "orientation": self.orientation,
            "discomfort_score": self.discomfort_score,
            "simulation_result": self.simulation_result,
            "ranked_designs": [c.to_dict() if isinstance(c, OptimizationCandidate) else c for c in self.ranked_designs],
            "n_trials": self.n_trials,
            "explanation": self.explanation,
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationResult":
        """Constructs OptimizationResult from dictionary."""
        raw_ranked = data.get("ranked_designs", [])
        candidates = [
            OptimizationCandidate.from_dict(c) if isinstance(c, dict) else c
            for c in raw_ranked
        ]
        return cls(
            city=str(data.get("city", "leh")),
            home_type=str(data.get("home_type", "Permanent")),
            insulation_thickness_m=float(data.get("insulation_thickness_m", 0.0)),
            insulation_mm=float(data.get("insulation_mm", data.get("insulation_thickness_m", 0.0) * 1000.0)),
            window_area_m2=float(data.get("window_area_m2", 2.0)),
            wall_material=str(data.get("wall_material", "brick")),
            glazing=str(data.get("glazing", "double_clear")),
            glazing_name=str(data.get("glazing_name", "Double Glazed")),
            orientation=str(data.get("orientation", "south")),
            discomfort_score=float(data.get("discomfort_score", 0.0)),
            simulation_result=dict(data.get("simulation_result", {})),
            ranked_designs=candidates,
            n_trials=int(data.get("n_trials", 40)),
            explanation=data.get("explanation"),
        )


# =====================================================================
# 7. DETERMINISTIC FALLBACK FIXTURES & ADAPTER UTILITIES
# =====================================================================

def create_mock_climate_profile(
    city: str = "leh",
    hours: int = 168,
    base_temp: float = -5.0,
    temp_swing: float = 8.0,
    peak_solar: float = 650.0
) -> ClimateProfile:
    """
    Creates a physically realistic, deterministic ClimateProfile test fixture for Member 3.

    Default generates Leh Ladakh winter conditions (-5°C mean, diurnal swing of 8°C, high solar).
    """
    t_series: List[float] = []
    dni_series: List[float] = []
    dhi_series: List[float] = []
    ws_series: List[float] = []
    rh_series: List[float] = []

    for h in range(hours):
        hour_of_day = h % 24
        # Temperature sinusoidal diurnal wave with peak at 14:00
        t = base_temp + (temp_swing / 2.0) * math.sin((hour_of_day - 8) * math.pi / 12.0)
        t_series.append(round(t, 2))

        # Solar irradiance curve between 07:00 and 17:00
        if 7 <= hour_of_day <= 17:
            solar_frac = math.sin((hour_of_day - 7) * math.pi / 10.0)
            dni = max(0.0, peak_solar * solar_frac)
            dhi = max(0.0, (peak_solar * 0.25) * solar_frac)
        else:
            dni = 0.0
            dhi = 0.0

        dni_series.append(round(dni, 1))
        dhi_series.append(round(dhi, 1))
        ws_series.append(2.5)  # Moderate breeze 2.5 m/s
        rh_series.append(40.0)  # Dry mountain air

    city_coords = {
        "leh": (34.1526, 77.5771, "cold", 3500.0, 5.5, "EPW_Leh_ISD", DataProvenance.HISTORICAL),
        "jaisalmer": (26.9157, 70.9083, "hot_dry", 225.0, 5.5, "EPW_Jaisalmer", DataProvenance.HISTORICAL),
        "chennai": (13.0827, 80.2707, "hot_humid", 6.0, 5.5, "EPW_Chennai", DataProvenance.HISTORICAL),
        "delhi": (28.6139, 77.2090, "composite", 216.0, 5.5, "EPW_Delhi", DataProvenance.HISTORICAL),
        "bengaluru": (12.9716, 77.5946, "temperate", 920.0, 5.5, "EPW_Bengaluru", DataProvenance.HISTORICAL),
    }
    lat, lon, zone, elev, tz, src, prov = city_coords.get(
        city.lower(), (34.1526, 77.5771, "cold", 1000.0, 5.5, "synthetic", DataProvenance.SIMULATED)
    )

    return ClimateProfile(
        city=city.lower(),
        latitude=lat,
        longitude=lon,
        hourly_temperature=t_series,
        hourly_direct_solar=dni_series,
        hourly_diffuse_solar=dhi_series,
        hourly_wind_speed=ws_series,
        hourly_humidity=rh_series,
        climate_zone=zone,
        elevation_m=elev,
        timezone_offset_hours=tz,
        data_source=src,
        data_provenance=prov,
        data_confidence=0.95,
    )


def create_mock_shelter_design(
    shelter_type: str = "Permanent",
    wall_material: str = "brick",
    insulation_thickness_m: float = 0.05,
    window_area: float = 2.0,
    glazing: str = "double_clear",
    occupants: int = 4
) -> ShelterDesign:
    """
    Creates a standard deterministic ShelterDesign test fixture.
    """
    is_temp = shelter_type.lower().startswith("temp")
    height = 2.6 if is_temp else 2.8
    mat = "puf_insulation" if (is_temp and wall_material == "brick") else wall_material

    return ShelterDesign(
        length=4.5,
        width=3.2,
        height=height,
        wall_material=mat,
        wall_thickness_m=0.10 if is_temp else 0.23,
        insulation_thickness_m=insulation_thickness_m,
        insulation_conductivity=0.025,
        roof_type="pitched" if not is_temp else "flat",
        pitch_angle_deg=30.0 if not is_temp else 0.0,
        roof_thickness_m=0.15,
        roof_conductivity=0.50,
        roof_insulation_m=insulation_thickness_m,
        window_area=window_area,
        glazing=glazing,
        orientation="south",
        ach=DEFAULT_ACH,
        occupants=occupants,
        shelter_type="Temporary" if is_temp else "Permanent",
        shelter_model="rectangular_pitched" if not is_temp else "rectangular_flat",
        heat_per_person=DEFAULT_OCCUPANT_HEAT_GAIN,
    )


def adapt_to_climate_profile(raw_data: Union[ClimateProfile, Dict[str, Any]]) -> ClimateProfile:
    """
    Adapter converting raw dictionary, Pydantic model, or weather service output into validated ClimateProfile.
    """
    if isinstance(raw_data, ClimateProfile):
        return raw_data
    elif type(raw_data).__name__ == "ClimateProfile" and hasattr(raw_data, "to_dict"):
        return ClimateProfile.from_dict(raw_data.to_dict())
    elif hasattr(raw_data, "model_dump"):
        return ClimateProfile.from_dict(raw_data.model_dump())
    elif isinstance(raw_data, dict):
        return ClimateProfile.from_dict(raw_data)
    else:
        raise TypeError(f"Cannot adapt object of type {type(raw_data)} to ClimateProfile")


def adapt_backend_climate_profile(backend_profile: Any) -> ClimateProfile:
    """
    Maps the backend.climate.schemas.ClimateProfile (Pydantic v2 structured model
    with Location, ClimateMetrics, SolarData, WindData, HumidityData, DesignExtremes,
    DataQuality) into the canonical services.contracts.ClimateProfile.

    This adapter bridges Member 1's rich structured climate data to the flat
    hourly-timeseries format consumed by Member 3's thermal simulation engine.

    IMPORTANT: The backend ClimateProfile contains annual/statistical climate data
    (mean temperatures, design extremes), NOT hourly timeseries. When hourly data
    is unavailable, this adapter synthesizes a deterministic diurnal profile from
    the statistical metrics. The resulting data_provenance is set to ESTIMATED
    to clearly distinguish it from measured or historical hourly data.

    Data preservation:
      - location: place_name, latitude, longitude, elevation
      - climate: classification, temperature extremes
      - solar: GHI, DNI, DHI (annual means used as peak for synthesis)
      - wind: average_speed
      - humidity: average_relative_humidity
      - data_quality: confidence, provenance, sources
    """
    if hasattr(backend_profile, "model_dump"):
        bp = backend_profile
    else:
        raise TypeError(
            f"Expected a Pydantic backend ClimateProfile, got {type(backend_profile)}"
        )

    loc = bp.location
    clim = bp.climate
    solar = bp.solar
    wind = bp.wind
    hum = bp.humidity
    extremes = bp.design_extremes
    quality = bp.data_quality

    # Determine provenance mapping
    prov_map = {
        "MEASURED": DataProvenance.MEASURED,
        "HISTORICAL": DataProvenance.HISTORICAL,
        "ESTIMATED": DataProvenance.ESTIMATED,
        "SIMULATED": DataProvenance.SIMULATED,
        "OPTIMIZED": DataProvenance.OPTIMIZED,
    }
    raw_prov = str(quality.provenance.value) if hasattr(quality.provenance, "value") else str(quality.provenance)
    canonical_prov = prov_map.get(raw_prov.upper(), DataProvenance.ESTIMATED)

    # Confidence mapping
    conf_map = {"HIGH": 0.95, "MEDIUM": 0.70, "LOW": 0.40}
    raw_conf = str(quality.confidence.value) if hasattr(quality.confidence, "value") else str(quality.confidence)
    canonical_conf = conf_map.get(raw_conf.upper(), 0.70)

    # Climate zone mapping
    zone_map = {
        "EXTREME COLD": "cold",
        "COLD": "cold",
        "HOT DRY": "hot_dry",
        "HOT HUMID": "hot_humid",
        "TEMPERATE": "temperate",
        "VARIABLE": "composite",
    }
    raw_zone = str(clim.classification.value) if hasattr(clim.classification, "value") else str(clim.classification)
    canonical_zone = zone_map.get(raw_zone.upper(), "composite")

    # Synthesize 168-hour deterministic diurnal profile from statistical data
    # This is clearly labeled as ESTIMATED — not measured hourly data
    hours = 168
    mean_temp = float(clim.annual_mean_temperature)
    t_min = float(clim.minimum_temperature)
    t_max = float(clim.maximum_temperature)
    diurnal_range = float(clim.diurnal_range_mean) if clim.diurnal_range_mean else (t_max - t_min) * 0.5
    half_swing = diurnal_range / 2.0

    # Peak solar from GHI or DNI annual mean (scale to peak instantaneous)
    peak_dni = float(solar.DNI) if solar.DNI else float(solar.GHI) * 0.75
    peak_dhi = float(solar.DHI) if solar.DHI else float(solar.GHI) * 0.25

    t_series: List[float] = []
    dni_series: List[float] = []
    dhi_series: List[float] = []
    ws_series: List[float] = []
    rh_series: List[float] = []

    avg_wind = float(wind.average_speed)
    avg_rh = float(hum.average_relative_humidity)

    for h in range(hours):
        hour_of_day = h % 24
        t = mean_temp + half_swing * math.sin((hour_of_day - 8) * math.pi / 12.0)
        t_series.append(round(t, 2))

        if 7 <= hour_of_day <= 17:
            solar_frac = math.sin((hour_of_day - 7) * math.pi / 10.0)
            dni_series.append(round(max(0.0, peak_dni * solar_frac), 1))
            dhi_series.append(round(max(0.0, peak_dhi * solar_frac), 1))
        else:
            dni_series.append(0.0)
            dhi_series.append(0.0)

        ws_series.append(round(avg_wind, 1))
        rh_series.append(round(avg_rh, 1))

    # Determine data source string
    sources = quality.sources if quality.sources else []
    data_source = ", ".join(sources) if sources else "backend_climate_service"

    # When synthesizing from annual stats, provenance is ESTIMATED
    # regardless of the backend's original provenance
    synthesis_prov = DataProvenance.ESTIMATED

    return ClimateProfile(
        city=loc.place_name.split(",")[0].strip().lower(),
        latitude=float(loc.latitude),
        longitude=float(loc.longitude),
        hourly_temperature=t_series,
        hourly_direct_solar=dni_series,
        hourly_diffuse_solar=dhi_series,
        hourly_wind_speed=ws_series,
        hourly_humidity=rh_series,
        climate_zone=canonical_zone,
        elevation_m=float(loc.elevation) if loc.elevation is not None else None,
        timezone_offset_hours=5.5,  # Default IST; backend uses IANA timezone string
        data_source=data_source,
        data_provenance=synthesis_prov,
        data_confidence=canonical_conf,
    )


def adapt_to_shelter_design(raw_data: Union[ShelterDesign, Dict[str, Any]]) -> ShelterDesign:
    """
    Adapter converting raw dictionary or design config into validated canonical ShelterDesign.
    """
    if isinstance(raw_data, ShelterDesign):
        return raw_data
    elif type(raw_data).__name__ == "ShelterDesign" and hasattr(raw_data, "to_dict"):
        return ShelterDesign.from_dict(raw_data.to_dict())
    elif isinstance(raw_data, dict):
        return ShelterDesign.from_dict(raw_data)
    else:
        raise TypeError(f"Cannot adapt object of type {type(raw_data)} to ShelterDesign")


def adapt_simulation_result(raw_result: Union[SimulationResult, Dict[str, Any]]) -> SimulationResult:
    """
    Adapter converting raw dictionary from run_simulation into validated SimulationResult contract.
    """
    if isinstance(raw_result, SimulationResult):
        return raw_result
    elif type(raw_result).__name__ == "SimulationResult" and hasattr(raw_result, "to_dict"):
        return SimulationResult.from_dict(raw_result.to_dict())
    elif isinstance(raw_result, dict):
        return SimulationResult.from_dict(raw_result)
    else:
        raise TypeError(f"Cannot adapt object of type {type(raw_result)} to SimulationResult")


def adapt_to_optimization_input(raw_data: Union[OptimizationInput, Dict[str, Any]]) -> OptimizationInput:
    """
    Adapter converting raw dictionary or config into validated OptimizationInput contract.
    """
    if isinstance(raw_data, OptimizationInput):
        return raw_data
    elif type(raw_data).__name__ == "OptimizationInput" and hasattr(raw_data, "to_dict"):
        return OptimizationInput.from_dict(raw_data.to_dict())
    elif isinstance(raw_data, dict):
        return OptimizationInput.from_dict(raw_data)
    else:
        raise TypeError(f"Cannot adapt object of type {type(raw_data)} to OptimizationInput")


def adapt_optimization_result(raw_result: Union[OptimizationResult, Dict[str, Any]]) -> OptimizationResult:
    """
    Adapter converting raw dictionary or optimization output into validated OptimizationResult contract.
    """
    if isinstance(raw_result, OptimizationResult):
        return raw_result
    elif type(raw_result).__name__ == "OptimizationResult" and hasattr(raw_result, "to_dict"):
        return OptimizationResult.from_dict(raw_result.to_dict())
    elif isinstance(raw_result, dict):
        return OptimizationResult.from_dict(raw_result)
    else:
        raise TypeError(f"Cannot adapt object of type {type(raw_result)} to OptimizationResult")


