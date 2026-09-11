"""
THERMOSHELTER AI - Climate API Handlers & Endpoints
===================================================
Standardized, framework-agnostic API dispatchers and request/response models.
Can be invoked directly in Python or mounted onto FastAPI / Flask / Starlette.
"""

from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field

from backend.climate.schemas import (
    ClimateProfile,
    Location,
    PassiveStrategy,
)
from backend.climate.service import ClimateAnalysisResult, ClimateService, default_climate_service


# ------------------------------------------------------------------------------
# REQUEST SCHEMAS
# ------------------------------------------------------------------------------
class LocationRequest(BaseModel):
    query: Optional[str] = Field(None, description="Place name or coordinate string (e.g. 'Leh, Ladakh' or '34.15, 77.58')")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class ProfileRequest(BaseModel):
    location: Union[str, LocationRequest, Dict[str, Any]] = Field(..., description="Target location query, coords, or LocationRequest")
    include_current_weather: bool = Field(True, description="Whether to fetch instantaneous weather snapshot")


class ClassifyRequest(BaseModel):
    profile: ClimateProfile = Field(..., description="Target ClimateProfile to classify")


class StrategyRequest(BaseModel):
    profile: ClimateProfile = Field(..., description="Target ClimateProfile for passive strategy recommendation")


class AnalyzeRequest(BaseModel):
    location: Union[str, LocationRequest, Dict[str, Any]] = Field(..., description="Target location query or coordinate object")
    include_current_weather: bool = Field(True, description="Whether to include live observed weather")


# ------------------------------------------------------------------------------
# API HANDLERS (Framework-Agnostic Dispatchers)
# ------------------------------------------------------------------------------
class ClimateAPI:
    """
    Standard HTTP/RPC API controller for Climate Subsystem.
    """

    def __init__(self, service: Optional[ClimateService] = None):
        self.service = service or default_climate_service

    def handle_location(self, request: Union[LocationRequest, Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST /climate/location
        Resolves a place name or coordinate pair into a validated Location.
        """
        req = LocationRequest.model_validate(request) if isinstance(request, dict) else request
        if req.latitude is not None and req.longitude is not None:
            loc = self.service.resolve_location((req.latitude, req.longitude))
        elif req.query:
            loc = self.service.resolve_location(req.query)
        else:
            raise ValueError("Either 'query' or both 'latitude' and 'longitude' must be provided.")
        return loc.model_dump()

    def handle_profile(self, request: Union[ProfileRequest, Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST /climate/profile
        Synthesizes the complete, normalized ClimateProfile for a location.
        """
        req = ProfileRequest.model_validate(request) if isinstance(request, dict) else request
        target = req.location
        if isinstance(target, LocationRequest):
            if target.latitude is not None and target.longitude is not None:
                target = (target.latitude, target.longitude)
            else:
                target = target.query or ""

        profile = self.service.get_climate_profile(
            target,
            include_current_weather=req.include_current_weather
        )
        return profile.model_dump()

    def handle_classify(self, request: Union[ClassifyRequest, Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST /climate/classify
        Classifies a ClimateProfile into one of the 6 canonical climate categories.
        """
        req = ClassifyRequest.model_validate(request) if isinstance(request, dict) else request
        res = self.service.classify_climate(req.profile)
        return res.model_dump()

    def handle_strategy(self, request: Union[StrategyRequest, Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST /climate/strategy
        Generates evidence-based passive design requirements for a ClimateProfile.
        """
        req = StrategyRequest.model_validate(request) if isinstance(request, dict) else request
        strategy = self.service.generate_passive_strategy(req.profile)
        return strategy.model_dump()

    def handle_analyze(self, request: Union[AnalyzeRequest, Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST /climate/analyze
        Full end-to-end pipeline: Location -> Profile -> Classification -> Strategy.
        """
        req = AnalyzeRequest.model_validate(request) if isinstance(request, dict) else request
        target = req.location
        if isinstance(target, LocationRequest):
            if target.latitude is not None and target.longitude is not None:
                target = (target.latitude, target.longitude)
            else:
                target = target.query or ""

        res = self.service.analyze(target, include_current_weather=req.include_current_weather)
        return res.model_dump()


# Default singleton API instance
default_climate_api = ClimateAPI()
