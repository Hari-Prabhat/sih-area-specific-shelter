"""
THERMOSHELTER AI - Climate Timeseries Normalizer (Phase B)
==========================================================
Converts a typed HourlyWeatherSeries (provider-weather contract) into the
canonical services.contracts.ClimateProfile consumed by the simulation
adapter and thermal engine - using the REAL provider hourly arrays.

Unlike adapt_backend_climate_profile() (which synthesizes a deterministic
diurnal profile from statistical climate data when no hourly series is
available), this module never fabricates: it requires genuine hourly
temperature/solar arrays and passes them through 1:1, preserving
timestamps, elevation, timezone, and provenance.

Data-mode terminology (must never be conflated):
  live       -> MODEL_ANALYSIS (recent NWP model analysis ending now; NOT an
                on-site measured observation)
  forecast   -> FORECAST (forward-looking numerical weather prediction)
  historical -> HISTORICAL_REANALYSIS (model reanalysis, e.g. ERA5)
  design     -> DESIGN (representative EPW/TMY design-year climate)
  fallback   -> FALLBACK (bundled dataset served when providers fail)
"""

import logging
from typing import Optional

from backend.climate.errors import ClimateErrorCategory, ClimateServiceError
from backend.climate.schemas import HourlyWeatherSeries, WeatherDataMode
from services.contracts import ClimateProfile as CanonicalClimateProfile
from services.shelter.models import DataProvenance as CanonicalProvenance

logger = logging.getLogger("thermoshelter.climate.normalize")

# WeatherDataMode -> canonical provenance (Phase C terminology:
# model-derived products are never labelled MEASURED)
_MODE_PROVENANCE = {
    WeatherDataMode.LIVE: CanonicalProvenance.MODEL_ANALYSIS,
    WeatherDataMode.FORECAST: CanonicalProvenance.FORECAST,
    WeatherDataMode.HISTORICAL: CanonicalProvenance.HISTORICAL_REANALYSIS,
    WeatherDataMode.DESIGN: CanonicalProvenance.DESIGN,
    WeatherDataMode.FALLBACK: CanonicalProvenance.FALLBACK,
}

# WeatherDataMode -> data confidence fraction
_MODE_CONFIDENCE = {
    WeatherDataMode.LIVE: 0.90,
    WeatherDataMode.FORECAST: 0.90,
    WeatherDataMode.HISTORICAL: 0.85,
    WeatherDataMode.DESIGN: 0.80,
    WeatherDataMode.FALLBACK: 0.50,
}


def _window_climate_zone(series: HourlyWeatherSeries) -> str:
    """
    Deterministic, explainable zone approximation from the window itself.
    This is a coarse window-based classification for provenance only - the
    authoritative site classification remains the ClimateClassifier's
    statistical analysis (NBC/ASHRAE-aligned thresholds).
    """
    temps = series.air_temperature_C
    mean_t = sum(temps) / max(1, len(temps))
    rh = series.relative_humidity_percent
    mean_rh = (sum(rh) / len(rh)) if rh else None

    if mean_t < 5.0:
        return "cold"
    if mean_t >= 28.0:
        if mean_rh is not None and mean_rh >= 65.0:
            return "hot_humid"
        return "hot_dry"
    if mean_rh is not None and mean_rh >= 75.0:
        return "hot_humid"
    return "composite"


def hourly_series_to_climate_profile(
    series: HourlyWeatherSeries,
    climate_zone: Optional[str] = None,
    display_name: Optional[str] = None,
) -> CanonicalClimateProfile:
    """
    Maps a validated HourlyWeatherSeries into the canonical ClimateProfile
    with the provider's real hourly arrays. Required simulation inputs
    (temperature, direct solar, diffuse solar) must exist in the series -
    missing solar data raises an explicit error instead of being invented.
    """
    if series.solar_direct_W_m2 is None or series.solar_diffuse_W_m2 is None:
        raise ClimateServiceError(
            ClimateErrorCategory.DATA_UNAVAILABLE,
            "Provider did not supply hourly solar radiation (DNI/DHI), which the "
            "thermal simulation requires. Choose a provider window that includes "
            "radiation variables or use design-climate data.",
        )

    if not (series.solar_direct_W_m2 and series.solar_diffuse_W_m2):
        raise ClimateServiceError(
            ClimateErrorCategory.INVALID_CLIMATE_DATA,
            "Hourly solar arrays are empty",
        )

    provenance = _MODE_PROVENANCE[series.data_mode]
    confidence = _MODE_CONFIDENCE[series.data_mode]
    zone = climate_zone or _window_climate_zone(series)

    profile = CanonicalClimateProfile(
        city=display_name or series.timezone or f"{series.latitude:.4f},{series.longitude:.4f}",
        latitude=series.latitude,
        longitude=series.longitude,
        hourly_temperature=list(series.air_temperature_C),
        hourly_direct_solar=list(series.solar_direct_W_m2),
        hourly_diffuse_solar=list(series.solar_diffuse_W_m2),
        hourly_wind_speed=list(series.wind_speed_mps) if series.wind_speed_mps else None,
        hourly_humidity=list(series.relative_humidity_percent)
        if series.relative_humidity_percent
        else None,
        climate_zone=zone,
        elevation_m=series.elevation_m,
        timestamps=list(series.timestamps),
        data_source=f"{series.provider} [{series.data_mode.value}]",
        data_provenance=provenance,
        data_confidence=confidence,
    )

    logger.info(
        "Normalized %d-hour %s series for (%.4f, %.4f): provenance=%s zone=%s fallback=%s",
        len(profile.hourly_temperature),
        series.data_mode.value,
        series.latitude,
        series.longitude,
        provenance,
        zone,
        series.fallback_used,
    )
    return profile
