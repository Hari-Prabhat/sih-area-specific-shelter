"""
THERMOSHELTER AI - Climate API Routes
======================================
FastAPI route handlers for Member 1 Climate Intelligence Subsystem.
Mounts Location, Profile, Classification, Strategy, and Analysis handlers.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.climate.api import (
    AnalyzeRequest,
    ClassifyRequest,
    ClimateAPI,
    LocationRequest,
    ProfileRequest,
    StrategyRequest,
    default_climate_api,
)

router = APIRouter(prefix="/api/climate", tags=["climate"])


@router.post("/location", summary="Resolve Geographic Location")
def resolve_location(request: LocationRequest) -> Dict[str, Any]:
    """Resolves place name or coordinate pair into validated Location."""
    try:
        return default_climate_api.handle_location(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Location resolution error", "message": str(e)}
        )


@router.post("/profile", summary="Synthesize Climate Profile")
def synthesize_profile(request: ProfileRequest) -> Dict[str, Any]:
    """Synthesizes structured Pydantic ClimateProfile for a given location."""
    try:
        return default_climate_api.handle_profile(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Climate profile synthesis error", "message": str(e)}
        )


@router.post("/classify", summary="Classify Climate Zone")
def classify_climate(request: ClassifyRequest) -> Dict[str, Any]:
    """Classifies a ClimateProfile into one of the 6 canonical climate zones."""
    try:
        return default_climate_api.handle_classify(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Climate classification error", "message": str(e)}
        )


@router.post("/strategy", summary="Generate Passive Strategies")
def generate_strategy(request: StrategyRequest) -> Dict[str, Any]:
    """Recommends evidence-based passive architectural strategies for a ClimateProfile."""
    try:
        return default_climate_api.handle_strategy(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Passive strategy generation error", "message": str(e)}
        )


@router.post("/analyze", summary="Full Climate Analysis Pipeline")
def full_analysis(request: AnalyzeRequest) -> Dict[str, Any]:
    """Runs complete end-to-end Member 1 pipeline: Location -> Profile -> Classification -> Strategy."""
    try:
        return default_climate_api.handle_analyze(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Climate analysis error", "message": str(e)}
        )
