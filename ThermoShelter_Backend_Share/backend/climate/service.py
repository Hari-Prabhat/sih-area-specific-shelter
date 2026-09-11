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
from typing import Any, Dict, Optional, Tuple, Union
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
)
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
