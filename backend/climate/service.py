"""
THERMOSHELTER AI - Climate Intelligence & Strategy Service
==========================================================
Central orchestrator for Member 1 Subsystem. Provides unified methods for:
  1. Location resolution
  2. Weather retrieval & unit normalization
  3. Climate profile synthesis
  4. Physics-based climate classification
  5. Passive architectural strategy generation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from backend.climate.climate_classifier import ClassificationExplanation, ClimateClassifier
from backend.climate.climate_resolver import assemble_climate_profile
from backend.climate.climate_strategy import ClimateStrategyEngine
from backend.climate.location_resolver import LocationResolver
from backend.climate.schemas import (
    ClimateProfile,
    ClimateZone,
    CurrentWeather,
    Location,
    PassiveStrategy,

    HourlyWeatherSeries,)
from backend.climate.weather_provider import BaseWeatherProvider, CompositeWeatherProvider


class ClimateAnalysisResult(BaseModel):
    """Unified container bundling all Member 1 outputs for downstream members."""
    location: Location
    profile: ClimateProfile
    classification: ClassificationExplanation
    strategy: PassiveStrategy


class ClimateService:
    """
    Production-ready service coordinating the Climate Intelligence
    and Climate Strategy engines.
    """

    def __init__(
        self,
        weather_provider: Optional[BaseWeatherProvider] = None,
        location_resolver: Optional[LocationResolver] = None,
        data_dir: Optional[Union[str, Path]] = None,
        enable_online: bool = True
    ):
        self.data_dir = Path(data_dir) if data_dir else None
        self.location_resolver = location_resolver or LocationResolver(data_dir=self.data_dir)
        self.weather_provider = weather_provider or CompositeWeatherProvider(
            enable_online=enable_online,
            data_dir=self.data_dir
        )

    def search_locations(self, name: str, count: int = 5, allow_online: bool = True) -> List[Location]:
        """Returns candidate locations for disambiguation of ambiguous queries."""
        return self.location_resolver.search_locations(name, count=count, allow_online=allow_online)

    def resolve_from_pincode(self, pincode: str, allow_online: bool = True) -> Location:
        """Resolves an Indian PIN code to a validated Location via India Post + geocoding."""
        return self.location_resolver.resolve_from_pincode(pincode, allow_online=allow_online)

    def get_hourly_weather(
        self,
        location: Union[Location, str, Tuple[float, float], Dict[str, Any]],
        mode: str = "forecast",
        hours: int = 168,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> "HourlyWeatherSeries":
        """
        Retrieves a typed hourly weather timeseries for a location.

        Modes (never conflated):
          - 'live':       168-hour window ending at the current hour (observed + NWP).
          - 'forecast':   168-hour forward forecast from now.
          - 'historical': hourly reanalysis (ERA5) for the requested window.
          - 'design':     explicitly-requested bundled EPW design-year climate
                           from the nearest benchmark station (labelled DESIGN).

        The returned series carries explicit data_mode / provenance / fallback_used
        metadata; raw provider payloads never cross this boundary.
        """
        from backend.climate.errors import ClimateErrorCategory, ClimateServiceError
        from backend.climate.schemas import WeatherDataMode

        loc = self.resolve_location(location)

        if mode == "forecast":
            return self.weather_provider.get_hourly_forecast(loc.latitude, loc.longitude, hours=hours)
        if mode == "live":
            return self.weather_provider.get_hourly_forecast(
                loc.latitude, loc.longitude, hours=hours, include_past=True
            )
        if mode == "historical":
            return self.weather_provider.get_hourly_archive(
                loc.latitude, loc.longitude, start_date=start_date, end_date=end_date, hours=hours
            )
        if mode == "design":
            return self.weather_provider.get_design_climate(loc.latitude, loc.longitude, hours=hours)
        raise ClimateServiceError(
            ClimateErrorCategory.INVALID_CLIMATE_DATA,
            f"Unknown weather mode '{mode}'. Use 'live', 'forecast', or 'historical'.",
        )

    def get_simulation_climate_profile(
        self,
        location: Union[Location, str, Tuple[float, float], Dict[str, Any]],
        mode: str = "forecast",
        hours: int = 168,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_elevation: bool = True,
    ) -> Dict[str, Any]:
        """
        End-to-end climate pipeline for simulation input:

        location -> coordinates -> hourly weather (real provider arrays)
                 -> canonical ClimateProfile -> passive strategy inputs

        Returns {"climate": <canonical profile dict>, "series": <HourlyWeatherSeries dict>,
                 "strategy": <PassiveStrategy dict>}.

        The canonical profile carries the provider's REAL hourly arrays (no
        diurnal synthesis) plus full provenance. Raises ClimateServiceError
        with a machine-readable category on any failure.
        """
        from backend.climate.errors import ClimateErrorCategory, ClimateServiceError
        from backend.climate.timeseries_normalizer import hourly_series_to_climate_profile
        from backend.climate.climate_strategy import ClimateStrategyEngine

        loc = self.resolve_location(location)

        series = self.get_hourly_weather(
            loc, mode=mode, hours=hours, start_date=start_date, end_date=end_date
        )

        # Provider-backed elevation for the resolved coordinates when the
        # series does not already carry one.
        elevation_m = series.elevation_m
        if include_elevation and elevation_m is None:
            elevation_m = self.weather_provider.get_elevation(loc.latitude, loc.longitude)

        profile = hourly_series_to_climate_profile(
            series,
            display_name=loc.place_name,
        )
        if elevation_m is not None and profile.elevation_m is None:
            profile.elevation_m = float(elevation_m)

        # Passive strategy inputs derived from the profile statistics
        # (classification is the existing explainable NBC-aligned engine).
        try:
            stats_profile = self.get_climate_profile(loc, include_current_weather=False)
            strategy = self.generate_passive_strategy(stats_profile)
        except Exception:
            strategy = None

        return {
            "climate": profile.to_dict(),
            "series": series.model_dump(),
            "strategy": strategy.model_dump() if strategy is not None else None,
        }

    def resolve_location(self, query: Union[str, Tuple[float, float], Dict[str, Any], Location]) -> Location:
        """Resolves place name, coordinates, or dictionary into a validated Location."""
        return self.location_resolver.resolve(query)

    def get_current_weather(self, location: Union[Location, str, Tuple[float, float]]) -> CurrentWeather:
        """Retrieves observed real-time weather snapshot."""
        loc = self.resolve_location(location)
        return self.weather_provider.get_current_weather(loc.latitude, loc.longitude)

    def get_climate_profile(
        self,
        location: Union[Location, str, Tuple[float, float], Dict[str, Any]],
        include_current_weather: bool = True
    ) -> ClimateProfile:
        """
        Synthesizes the authoritative ClimateProfile for a given location or coordinate pair.
        """
        loc = self.resolve_location(location)

        # Retrieve climatological normals and solar insolation
        temp_prof, wind_data, hum_data, extremes, quality = self.weather_provider.get_historical_climate(
            loc.latitude, loc.longitude
        )
        solar_data = self.weather_provider.get_solar_data(loc.latitude, loc.longitude)

        # Retrieve live current weather if requested
        current_weather: Optional[CurrentWeather] = None
        if include_current_weather:
            try:
                current_weather = self.weather_provider.get_current_weather(loc.latitude, loc.longitude)
            except Exception:
                pass

        # Perform classification on physical metrics
        classification_result = ClimateClassifier.classify(
            temperature=temp_prof,
            humidity=hum_data,
            design_extremes=extremes,
            solar=solar_data,
            wind=wind_data
        )

        # Assemble normalized profile
        profile = assemble_climate_profile(
            location=loc,
            temperature=temp_prof,
            solar=solar_data,
            wind=wind_data,
            humidity=hum_data,
            design_extremes=extremes,
            data_quality=quality,
            classification=classification_result.zone,
            current_weather=current_weather
        )

        return profile

    def classify_climate(self, profile: ClimateProfile) -> ClassificationExplanation:
        """Derives the climate classification and diagnostic explanation for a profile."""
        return ClimateClassifier.classify(
            temperature=profile.climate,
            humidity=profile.humidity,
            design_extremes=profile.design_extremes,
            solar=profile.solar,
            wind=profile.wind
        )

    def generate_passive_strategy(self, profile: ClimateProfile) -> PassiveStrategy:
        """Generates evidence-based passive design principles for a profile."""
        return ClimateStrategyEngine.generate_strategy(profile)

    def analyze(
        self,
        query: Union[str, Tuple[float, float], Dict[str, Any], Location],
        include_current_weather: bool = True
    ) -> ClimateAnalysisResult:
        """
        Complete end-to-end pipeline execution:
        Query -> Location -> Weather/Climate -> Normalization -> Profile -> Classifier -> Strategy.
        """
        loc = self.resolve_location(query)
        profile = self.get_climate_profile(loc, include_current_weather=include_current_weather)
        classification = self.classify_climate(profile)
        strategy = self.generate_passive_strategy(profile)

        return ClimateAnalysisResult(
            location=loc,
            profile=profile,
            classification=classification,
            strategy=strategy
        )


# Global default instance for direct imports
default_climate_service = ClimateService()
