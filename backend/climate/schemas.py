"""
THERMOSHELTER AI - Climate Intelligence Schemas & Shared Contracts
==================================================================
Versionable Pydantic v2 schemas defining ClimateProfile, PassiveStrategy,
and constituent physical metrics for downstream consumption.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DataProvenance(str, Enum):
    """Data origin and generation method."""
    MEASURED = "MEASURED"
    HISTORICAL = "HISTORICAL"
    ESTIMATED = "ESTIMATED"
    SIMULATED = "SIMULATED"
    OPTIMIZED = "OPTIMIZED"


class DataConfidence(str, Enum):
    """Reliability level of the climate dataset."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClimateZone(str, Enum):
    """
    Standard project climate zones for shelter engineering.
    Matches exactly the required 6 project categories.
    """
    EXTREME_COLD = "EXTREME COLD"
    COLD = "COLD"
    HOT_DRY = "HOT DRY"
    HOT_HUMID = "HOT HUMID"
    TEMPERATE = "TEMPERATE"
    VARIABLE = "VARIABLE"


class PriorityLevel(str, Enum):
    """Design priority level for passive strategies."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    MINIMIZED = "MINIMIZED"


class Location(BaseModel):
    """Geographic and site identification model."""
    model_config = ConfigDict(extra="ignore")

    place_name: str = Field(..., description="Human-readable location identifier (e.g., 'Leh, Ladakh')")
    latitude: float = Field(..., description="Latitude in decimal degrees (-90.0 to +90.0)")
    longitude: float = Field(..., description="Longitude in decimal degrees (-180.0 to +180.0)")
    elevation: Optional[float] = Field(None, description="Elevation above mean sea level in meters (m)")
    timezone: Optional[str] = Field("Asia/Kolkata", description="IANA Timezone or offset identifier")
    country: Optional[str] = Field("India", description="Country name")
    region: Optional[str] = Field(None, description="State, province, or geographic territory")
    source: Optional[str] = Field("Default", description="Data source or geocoding service")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude must be between -90.0 and +90.0 degrees, got {v}")
        return round(v, 6)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude must be between -180.0 and +180.0 degrees, got {v}")
        return round(v, 6)


class TemperatureProfile(BaseModel):
    """Thermal baseline metrics in degrees Celsius."""
    model_config = ConfigDict(extra="ignore")

    annual_mean_temperature: float = Field(..., description="Annual average dry bulb temperature (°C)")
    minimum_temperature: float = Field(..., description="Historical observed minimum temperature (°C)")
    maximum_temperature: float = Field(..., description="Historical observed maximum temperature (°C)")
    diurnal_range_mean: Optional[float] = Field(None, description="Average diurnal temperature variation (°C)")
    monthly_temperatures: Optional[List[float]] = Field(None, description="12-month mean dry bulb temperatures (°C)")
    temperature_profile: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed hourly/seasonal temperature distributions")
    source: str = Field("IMD / NREL Climatology", description="Source citation")
    provenance: DataProvenance = Field(DataProvenance.HISTORICAL, description="Data lineage")


class SolarData(BaseModel):
    """Solar irradiance and insolation data in SI units."""
    model_config = ConfigDict(extra="ignore")

    GHI: float = Field(..., ge=0.0, description="Global Horizontal Irradiance annual average flux (W/m²)")
    DNI: Optional[float] = Field(None, ge=0.0, description="Direct Normal Irradiance annual average flux (W/m²)")
    DHI: Optional[float] = Field(None, ge=0.0, description="Diffuse Horizontal Irradiance annual average flux (W/m²)")
    annual_solar_ghi_kwh_m2: Optional[float] = Field(None, ge=0.0, description="Annual cumulative GHI insolation (kWh/m²/year)")
    peak_sun_hours_day: Optional[float] = Field(None, ge=0.0, description="Average daily peak sun hours (hours/day)")
    unit: str = Field("W/m²", description="Physical unit of instantaneous irradiance")
    temporal_resolution: str = Field("annual_mean", description="Temporal meaning of irradiance values")
    source: str = Field("NREL NSRDB / NASA POWER", description="Source citation")
    provenance: DataProvenance = Field(DataProvenance.HISTORICAL, description="Data lineage")


class WindData(BaseModel):
    """Atmospheric wind metrics."""
    model_config = ConfigDict(extra="ignore")

    average_speed: float = Field(..., ge=0.0, description="Annual mean wind speed at 10m height (m/s)")
    prevailing_direction: Optional[str] = Field("NW", description="Prevailing wind compass direction or degrees")
    seasonal_profile: Optional[Dict[str, float]] = Field(default_factory=dict, description="Seasonal average wind speeds (m/s)")
    source: str = Field("IMD Climatological Tables", description="Source citation")
    provenance: DataProvenance = Field(DataProvenance.HISTORICAL, description="Data lineage")

    @field_validator("average_speed")
    @classmethod
    def validate_wind_speed(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError(f"Wind speed cannot be negative, got {v}")
        return round(v, 2)


class HumidityData(BaseModel):
    """Moisture and atmospheric humidity metrics."""
    model_config = ConfigDict(extra="ignore")

    average_relative_humidity: float = Field(..., ge=0.0, le=100.0, description="Annual mean relative humidity (%)")
    min_relative_humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Typical dry-period minimum RH (%)")
    max_relative_humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Monsoon/wet-period maximum RH (%)")
    seasonal_profile: Optional[Dict[str, float]] = Field(default_factory=dict, description="Seasonal relative humidity averages (%)")
    source: str = Field("IMD Climatological Normals", description="Source citation")
    provenance: DataProvenance = Field(DataProvenance.HISTORICAL, description="Data lineage")


class DesignExtremes(BaseModel):
    """Engineering design-basis extreme conditions (e.g., 99% heating, 1% cooling)."""
    model_config = ConfigDict(extra="ignore")

    cold_extreme: float = Field(..., description="Winter design dry-bulb temperature (99% or 99.6% design condition) (°C)")
    hot_extreme: float = Field(..., description="Summer design dry-bulb temperature (1% or 0.4% design condition) (°C)")
    heating_degree_days_18c: Optional[float] = Field(None, ge=0.0, description="Annual heating degree days base 18°C (HDD18)")
    cooling_degree_days_18c: Optional[float] = Field(None, ge=0.0, description="Annual cooling degree days base 18°C (CDD18)")
    relevant_design_values: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Supplementary ASHRAE/NBC design criteria")


class DataQuality(BaseModel):
    """Data integrity, confidence level, and provenance metadata."""
    model_config = ConfigDict(extra="ignore")

    confidence: DataConfidence = Field(DataConfidence.HIGH, description="Overall dataset confidence level")
    provenance: DataProvenance = Field(DataProvenance.HISTORICAL, description="Primary data provenance")
    sources: List[str] = Field(default_factory=list, description="List of source datasets or observational networks")
    notes: Optional[str] = Field(None, description="Contextual remarks regarding assumptions or sensor coverage")


class CurrentWeather(BaseModel):
    """Real-time observed meteorological conditions (distinct from design climate)."""
    model_config = ConfigDict(extra="ignore")

    temperature: float = Field(..., description="Current ambient dry-bulb temperature (°C)")
    relative_humidity: float = Field(..., ge=0.0, le=100.0, description="Current relative humidity (%)")
    wind_speed: float = Field(..., ge=0.0, description="Current wind speed (m/s)")
    wind_direction: Optional[float] = Field(None, ge=0.0, le=360.0, description="Current wind direction in degrees")
    solar_irradiance: Optional[float] = Field(None, ge=0.0, description="Current solar irradiance (W/m²)")
    timestamp: Optional[str] = Field(None, description="Observation timestamp in ISO 8601 format")
    is_observed: bool = Field(True, description="Flag indicating live observed data, not design climate")
    source: str = Field("Open-Meteo / Local Station", description="Weather station or API source")


class ClimateMetrics(BaseModel):
    """Synthesized climate metrics and classification."""
    model_config = ConfigDict(extra="ignore")

    classification: ClimateZone = Field(..., description="Project climate zone classification")
    annual_mean_temperature: float = Field(..., description="Annual average temperature (°C)")
    minimum_temperature: float = Field(..., description="Historical minimum temperature (°C)")
    maximum_temperature: float = Field(..., description="Historical maximum temperature (°C)")
    diurnal_range_mean: Optional[float] = Field(None, description="Average diurnal range (°C)")
    temperature_profile: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed profile structure")


class ClimateProfile(BaseModel):
    """
    Authoritative Shared Contract for Climate & Site Intelligence.
    Consumed by downstream Member 2 (Architecture/Envelope) and Member 3 (Simulation).
    """
    model_config = ConfigDict(extra="ignore")

    version: str = Field("1.0.0", description="Contract schema version")
    location: Location = Field(..., description="Geographic location and metadata")
    climate: ClimateMetrics = Field(..., description="Synthesized climate classification and baseline thermal metrics")
    solar: SolarData = Field(..., description="Solar resource and irradiance data")
    wind: WindData = Field(..., description="Wind speed and directional characteristics")
    humidity: HumidityData = Field(..., description="Moisture and relative humidity data")
    design_extremes: DesignExtremes = Field(..., description="Design-basis thermal extremes")
    data_quality: DataQuality = Field(..., description="Data provenance, confidence, and sources")
    current_weather: Optional[CurrentWeather] = Field(None, description="Optional live weather snapshot")


class PassiveStrategy(BaseModel):
    """
    Authoritative Shared Contract for Passive Design Strategies.
    Provides evidence-based architectural principles without prescribing physical dimensions or materials.
    """
    model_config = ConfigDict(extra="ignore")

    version: str = Field("1.0.0", description="Strategy contract schema version")
    climate_mode: ClimateZone = Field(..., description="Target climate zone")
    primary_strategy: str = Field(..., description="Core passive thermodynamic design principle")
    secondary_strategies: List[str] = Field(default_factory=list, description="Complementary architectural strategies")
    solar_capture: PriorityLevel = Field(..., description="Solar heat gain priority level")
    thermal_mass: PriorityLevel = Field(..., description="Thermal mass storage priority level")
    insulation_priority: PriorityLevel = Field(..., description="Building envelope insulation priority level")
    ventilation_strategy: str = Field(..., description="Natural / mechanical ventilation operation mode")
    shading_strategy: str = Field(..., description="Solar shading and overhang approach")
    opening_strategy: str = Field(..., description="Fenestration / glazing opening strategy")
    airlock: bool = Field(False, description="Whether an entrance airlock/vestibule is mandatory")
    thermal_buffer: bool = Field(False, description="Whether unconditioned perimeter thermal buffer zones are required")
    explanation: str = Field(..., description="Detailed, physics-grounded explanation tied to site climate metrics")
    rules_triggered: List[str] = Field(default_factory=list, description="Diagnostic list of triggered rule identifiers")
