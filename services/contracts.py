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
    door_area_m2: float = 2.0
    door_u_value: float = 1.80

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
    door_heat_flow: Optional[List[float]] = None
    hourly_door_loss: Optional[List[float]] = None
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
        d["hourly_door_loss"] = self.door_heat_flow
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
        door_loss = data.get("door_heat_flow", data.get("hourly_door_loss", []))
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
            door_heat_flow=[float(x) for x in door_loss] if door_loss else None,
            hourly_door_loss=[float(x) for x in door_loss] if door_loss else None,
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
    # ------------------------------------------------------------------
    # D5-B door-area fidelity: the canonical ShelterDesign's door_area is
    # the SINGLE authoritative opening value. It is NOT an optimization
    # variable - it is carried here only so that feasibility checks and
    # every candidate/best simulation evaluate against the SAME door area
    # the resulting canonical design represents. Default 2.0 m2 is the
    # pre-existing canonical/engine default (shelter/models.py and
    # simulation_service.py), not a newly invented value.
    # ------------------------------------------------------------------
    door_area_m2: float = 2.0
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
    # Phase C climate scenario contract: canonical ClimateProfile dict that
    # defines the SINGLE climate scenario for all candidate evaluations.
    # When supplied, the optimizer evaluates against THESE hourly vectors and
    # never falls back to city-key statistics.
    climate_scenario: Optional[Dict[str, Any]] = None
    # ------------------------------------------------------------------
    # D5-A geometry-optimization FOUNDATION (contract only).
    #
    # When optimize_geometry is False (default), the optimizer behaves
    # exactly as in Phase C: geometry stays fixed at length/width/height
    # and these bounds are ignored.
    #
    # When optimize_geometry is True, ALL SIX bound fields are REQUIRED and
    # validated here. There are deliberately NO default engineering limits:
    # minimum areas, aspect ratios, clear heights, etc. require explicit
    # engineering/product decisions and are not invented by this contract.
    # The optimizer must fail loudly rather than silently assume bounds.
    #
    # NOTE (D5-A): only rectangular-footprint dimensions (length/width/height)
    # are contract-covered. Shape (cylindrical/dome/pyramid) is NOT safe to
    # optimize - the thermal engine simulates rectangular envelopes only.
    # ------------------------------------------------------------------
    optimize_geometry: bool = False
    min_length_m: Optional[float] = None
    max_length_m: Optional[float] = None
    min_width_m: Optional[float] = None
    max_width_m: Optional[float] = None
    min_height_m: Optional[float] = None
    max_height_m: Optional[float] = None
    # ------------------------------------------------------------------
    # D5-B: orientation-independent aspect-ratio bounds.
    #
    # aspect_ratio = max(length/width, width/length)
    #
    # This is deliberately orientation-independent: 6x4 and 4x6 both give
    # 1.5, so a geometry must never be rejected merely because the length
    # and width labels are swapped. Like every geometry limit here these
    # bounds are PROPOSED PROTOTYPE ENGINEERING ASSUMPTIONS - not DRDO,
    # regulatory, ISO, or field-validated requirements. Optional: validated
    # only when supplied. NO floor-area bounds are added - the L/W bounds
    # already imply the area envelope, and redundant fields invite drift.
    # ------------------------------------------------------------------
    min_aspect_ratio: Optional[float] = None
    max_aspect_ratio: Optional[float] = None
    # Product-hardening pass: authoritative shelter form carried with the
    # optimization configuration. Shape is EVALUATED (every trial/candidate
    # simulation uses the actual form) but NOT SEARCHED — changing shape
    # remains an explicit user decision, not an optimizer variable.
    shape: str = "rectangular"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validates optimization bounds and parameter consistency."""
        if not self.city or not isinstance(self.city, str):
            raise ValueError("City name must be a non-empty string.")

        if self.length <= 0.0 or self.width <= 0.0 or self.height <= 0.0:
            raise ValueError("Shelter dimensions must be strictly positive (> 0).")

        # D5-B: door area must be a finite, non-negative area (0 = door-less
        # design is legitimate; the engine clamps negatives to 0).
        if not math.isfinite(self.door_area_m2) or self.door_area_m2 < 0.0:
            raise ValueError(
                f"door_area_m2 must be a finite non-negative area (m2), got {self.door_area_m2}"
            )

        self.validate_geometry_bounds()
        self.validate_search_bounds()

    def validate_search_bounds(self) -> None:
        """Validates insulation, window-area, trial, and weight consistency."""
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

    def validate_geometry_bounds(self) -> None:
        """
        Validates the D5-A optional geometry-optimization bounds.

        Mathematical constraints only (positivity, finiteness, min <= max,
        base dimension within bounds). No arbitrary engineering minima or
        maxima are introduced here.

        Raises:
            ValueError: On any invalid or incomplete geometry configuration.
        """
        if not self.optimize_geometry:
            return

        bounds = (
            ("length", self.min_length_m, self.max_length_m),
            ("width", self.min_width_m, self.max_width_m),
            ("height", self.min_height_m, self.max_height_m),
        )
        base = {"length": self.length, "width": self.width, "height": self.height}

        for dim, lo, hi in bounds:
            if lo is None or hi is None:
                raise ValueError(
                    f"optimize_geometry=True requires explicit min_{dim}_m and "
                    f"max_{dim}_m bounds; none are invented by default."
                )
            for name, value in ((f"min_{dim}_m", lo), (f"max_{dim}_m", hi)):
                if not math.isfinite(value):
                    raise ValueError(f"{name} must be finite, got {value}")
                if value <= 0.0:
                    raise ValueError(f"{name} must be strictly positive (> 0), got {value}")
            if hi < lo:
                raise ValueError(
                    f"max_{dim}_m ({hi}) cannot be less than min_{dim}_m ({lo})"
                )
            # The optimizer evaluates candidates between the supplied bounds;
            # the baseline geometry must lie inside the search space it defines.
            if not (lo <= base[dim] <= hi):
                raise ValueError(
                    f"Base {dim} ({base[dim]} m) lies outside the geometry "
                    f"bounds [{lo}, {hi}] m."
                )

        for name, value in (
            ("min_aspect_ratio", self.min_aspect_ratio),
            ("max_aspect_ratio", self.max_aspect_ratio),
        ):
            if value is None:
                continue
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if value < 1.0:
                raise ValueError(
                    f"{name} must be >= 1.0 (aspect_ratio = max(L/W, W/L) is "
                    f"orientation-independent and cannot be below 1), got {value}"
                )
        if (
            self.min_aspect_ratio is not None
            and self.max_aspect_ratio is not None
            and self.max_aspect_ratio < self.min_aspect_ratio
        ):
            raise ValueError(
                f"max_aspect_ratio ({self.max_aspect_ratio}) cannot be less than "
                f"min_aspect_ratio ({self.min_aspect_ratio})"
            )
        if self.max_aspect_ratio is not None and self.optimize_geometry:
            base_ar = max(self.length / self.width, self.width / self.length)
            if base_ar > self.max_aspect_ratio:
                raise ValueError(
                    f"Base geometry aspect ratio ({base_ar:.3f}) exceeds "
                    f"max_aspect_ratio ({self.max_aspect_ratio})."
                )

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
            # D5-B: accept the canonical design's door area (flat legacy key
            # "door_area" tolerated for direct dict callers).
            door_area_m2=float(data.get("door_area_m2", data.get("door_area", 2.0))),
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
            climate_scenario=data.get("climate_scenario"),
            optimize_geometry=bool(data.get("optimize_geometry", False)),
            min_length_m=data.get("min_length_m"),
            max_length_m=data.get("max_length_m"),
            min_width_m=data.get("min_width_m"),
            max_width_m=data.get("max_width_m"),
            min_height_m=data.get("min_height_m"),
            max_height_m=data.get("max_height_m"),
            min_aspect_ratio=data.get("min_aspect_ratio"),
            max_aspect_ratio=data.get("max_aspect_ratio"),
            shape=str(data.get("shape", "rectangular")),
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
    canonical_design: Optional[Dict[str, Any]] = None
    # Phase C: provenance of the climate scenario each candidate was
    # evaluated against (traceability from results back to weather data).
    climate_provenance: Optional[str] = None
    climate_data_mode: Optional[str] = None
    climate_fallback_used: Optional[bool] = None
    thermal_mass_level: Optional[str] = None
    # ------------------------------------------------------------------
    # D5-A: candidate geometry contract (prepared, not yet optimized).
    #
    # These fields are populated by the optimizer ONLY from the canonical
    # geometry engine / the engine's own reported result - never recomputed
    # by a second geometry implementation. When geometry is not optimized
    # they report the candidate's BASE geometry so every consumer (Apply,
    # Blueprint, 3D, Report) sees the same truth.
    #
    # surface_to_volume_ratio is the thermal-relevant envelope-to-volume
    # ratio: gross envelope area / enclosed volume. It stays None when the
    # engine does not report both values (e.g. roof type not applicable).
    # ------------------------------------------------------------------
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    floor_area_m2: Optional[float] = None
    surface_to_volume_ratio: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_shelter_design(self, base_design: Optional[Any] = None) -> ShelterDesign:
        """Constructs a canonical ShelterDesign digital twin from this optimization candidate."""
        if self.canonical_design:
            return ShelterDesign.from_dict(self.canonical_design)
        # ------------------------------------------------------------------
        # D5-B geometry fidelity: when the candidate carries optimized trial
        # geometry, that geometry is AUTHORITATIVE and must reach the applied
        # ShelterDesign unchanged. The base design's dimensions are only the
        # fallback for legacy candidates (no geometry search).
        # ------------------------------------------------------------------
        b_len = self.length_m if self.length_m is not None else (
            base_design.length if base_design and hasattr(base_design, "length") else 4.0
        )
        b_wid = self.width_m if self.width_m is not None else (
            base_design.width if base_design and hasattr(base_design, "width") else 3.0
        )
        b_hgt = self.height_m if self.height_m is not None else (
            base_design.height if base_design and hasattr(base_design, "height") else 2.8
        )
        b_occ = base_design.occupants if base_design and hasattr(base_design, "occupants") else 2
        b_type = base_design.shelter_type if base_design and hasattr(base_design, "shelter_type") else "Permanent"
        b_roof = base_design.roof_type if base_design and hasattr(base_design, "roof_type") else "flat"
        b_pitch = base_design.pitch_angle_deg if base_design and hasattr(base_design, "pitch_angle_deg") else 0.0
        b_ach = base_design.ach if base_design and hasattr(base_design, "ach") else DEFAULT_ACH

        # D5-B door fidelity: the door is NOT an optimization variable, so the
        # base design's authoritative door_area must reach the applied design
        # instead of silently resetting to the ShelterDesign constructor
        # default. (The live route path sets candidate.canonical_design from
        # the base design, which already preserves the door; this guards the
        # constructed fallback path used by direct callers.)
        b_door: Optional[float] = None
        if base_design is not None and hasattr(base_design, "door_area"):
            try:
                base_door = float(base_design.door_area)
            except (TypeError, ValueError):
                base_door = -1.0
            if math.isfinite(base_door) and base_door >= 0.0:
                b_door = base_door
        door_kwargs: Dict[str, Any] = {"door_area": b_door} if b_door is not None else {}

        return ShelterDesign(
            design_id=f"optimized_candidate_{self.rank}",
            name=f"{self.label} ({self.wall_material_name}, {self.insulation_mm}mm)",
            length=b_len,
            width=b_wid,
            height=b_hgt,
            wall_material=self.wall_material,
            insulation_thickness_m=self.insulation_thickness_m,
            window_area=self.window_area_m2,
            glazing=self.glazing,
            orientation=self.orientation,
            occupants=b_occ,
            shelter_type=b_type,
            roof_type=b_roof,
            pitch_angle_deg=b_pitch,
            ach=b_ach,
            **door_kwargs,
            provenance=DataProvenance.OPTIMIZED,
        )

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
            canonical_design=data.get("canonical_design"),
            climate_provenance=data.get("climate_provenance"),
            climate_data_mode=data.get("climate_data_mode"),
            climate_fallback_used=data.get("climate_fallback_used"),
            thermal_mass_level=data.get("thermal_mass_level"),
            length_m=data.get("length_m"),
            width_m=data.get("width_m"),
            height_m=data.get("height_m"),
            floor_area_m2=data.get("floor_area_m2"),
            surface_to_volume_ratio=data.get("surface_to_volume_ratio"),
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
    # Phase C: the exact climate scenario every candidate was evaluated
    # against, with full provenance for traceability.
    climate_scenario: Optional[Dict[str, Any]] = None
    climate_provenance: Optional[str] = None
    climate_data_mode: Optional[str] = None
    climate_fallback_used: bool = False
    # D5-B: number of trials pruned by pre-simulation geometry feasibility
    # rejection. Reported for transparency - the search space actually
    # explored is trials minus pruned, and silent clamping is never used.
    n_pruned: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes OptimizationResult to dictionary."""
        ranked = [c.to_dict() if isinstance(c, OptimizationCandidate) else c for c in self.ranked_designs]
        d = {
            "city": self.city,
            "home_type": self.home_type,
            "n_pruned": self.n_pruned,
            "insulation_thickness_m": self.insulation_thickness_m,
            "insulation_mm": self.insulation_mm,
            "window_area_m2": self.window_area_m2,
            "wall_material": self.wall_material,
            "glazing": self.glazing,
            "glazing_name": self.glazing_name,
            "orientation": self.orientation,
            "discomfort_score": self.discomfort_score,
            "simulation_result": self.simulation_result,
            "ranked_designs": ranked,
            "recommended_design": ranked[0] if ranked else None,
            "n_trials": self.n_trials,
            "explanation": self.explanation,
            "climate_scenario": self.climate_scenario,
            "climate_provenance": self.climate_provenance,
            "climate_data_mode": self.climate_data_mode,
            "climate_fallback_used": self.climate_fallback_used,
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
            climate_scenario=data.get("climate_scenario"),
            climate_provenance=data.get("climate_provenance"),
            climate_data_mode=data.get("climate_data_mode"),
            climate_fallback_used=bool(data.get("climate_fallback_used", False)),
            n_pruned=int(data.get("n_pruned", 0)),
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
        # Phase C: explicit model-derived / design / fallback categories
        "MODEL_ANALYSIS": DataProvenance.MODEL_ANALYSIS,
        "FORECAST": DataProvenance.FORECAST,
        "HISTORICAL_REANALYSIS": DataProvenance.HISTORICAL_REANALYSIS,
        "DESIGN": DataProvenance.DESIGN,
        "FALLBACK": DataProvenance.FALLBACK,
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


