"""
THERMOSHELTER AI - Climate API Routes
======================================
FastAPI route handlers for Member 1 Climate Intelligence Subsystem.
Mounts Location, Profile, Classification, Strategy, and Analysis handlers.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
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
from backend.climate.errors import ClimateErrorCategory, ClimateServiceError
from backend.climate.service import default_climate_service

router = APIRouter(prefix="/api/climate", tags=["climate"])


def _climate_http_error(exc: Exception) -> HTTPException:
    """
    Maps climate pipeline failures to machine-readable HTTP errors:
        ClimateServiceError -> {"error": <category>, "message": ...} at its mapped status
        ValueError          -> 422 {"error": "invalid_location", "message": ...}
        other               -> 500 {"error": "internal_error", ...}
    Never masks the underlying failure category as a generic outage.
    """
    if isinstance(exc, ClimateServiceError):
        return HTTPException(
            status_code=ClimateServiceError.http_status_for(exc.category),
            detail=exc.to_http_detail(),
        )
    if isinstance(exc, ValueError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": ClimateErrorCategory.INVALID_LOCATION.value,
                "message": str(exc),
            },
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": ClimateErrorCategory.INTERNAL_ERROR.value,
            "message": str(exc),
        },
    )


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


# =====================================================================
# PHASE B: LOCATION INTELLIGENCE & LIVE WEATHER ENDPOINTS
# =====================================================================


@router.get("/geocode", summary="Geocode a Place Name (with candidates)")
def geocode_location(
    query: str = Query(..., min_length=1, description="Place name, district, state, or 'lat, lon' pair"),
    count: int = Query(5, ge=1, le=10, description="Maximum candidates to return"),
) -> Dict[str, Any]:
    """Resolves a place query into candidate Location models for disambiguation."""
    try:
        candidates: List[Any] = default_climate_service.search_locations(query, count=count)
        return {
            "query": query,
            "count": len(candidates),
            "results": [c.model_dump() for c in candidates],
        }
    except Exception as e:
        raise _climate_http_error(e)


@router.get("/pincode", summary="Resolve an Indian PIN Code")
def resolve_pincode(
    pin: str = Query(..., min_length=6, max_length=6, description="6-digit Indian PIN code"),
) -> Dict[str, Any]:
    """Resolves a PIN code via the India Post directory + geocoding into a validated Location."""
    try:
        loc = default_climate_service.resolve_from_pincode(pin)
        return loc.model_dump()
    except Exception as e:
        raise _climate_http_error(e)


@router.get("/weather", summary="Hourly Weather Timeseries (live / forecast / historical / design)")
def get_weather(
    location: str = Query(..., min_length=1, description="Place name or 'lat, lon' pair"),
    mode: str = Query("forecast", pattern="^(live|forecast|historical|design)$", description="Dataset mode"),
    hours: int = Query(168, ge=1, le=384, description="Number of hourly samples"),
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Historical start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Historical end (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """
    Typed hourly weather timeseries with explicit provenance.

    Modes are never conflated: 'live' ends at the current hour, 'forecast'
    starts now, 'historical' is ERA5 reanalysis for the requested window.
    When providers are unreachable, bundled design climate is served and
    clearly labelled data_mode='fallback' (never presented as live).
    """
    try:
        series = default_climate_service.get_hourly_weather(
            location, mode=mode, hours=hours, start_date=start_date, end_date=end_date
        )
        return series.model_dump(mode="json")
    except Exception as e:
        raise _climate_http_error(e)


@router.get("/simulation-profile", summary="Simulation-Ready Climate Profile")
def get_simulation_profile(
    location: str = Query(..., min_length=1, description="Place name or 'lat, lon' pair"),
    mode: str = Query("forecast", pattern="^(live|forecast|historical|design)$", description="Dataset mode"),
    hours: int = Query(168, ge=1, le=384, description="Number of hourly samples"),
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Historical start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Historical end (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """
    Full climate pipeline for simulation input:
    location -> coordinates -> hourly weather -> canonical ClimateProfile
    (real provider arrays, full provenance) -> passive strategy inputs.
    """
    try:
        return default_climate_service.get_simulation_climate_profile(
            location, mode=mode, hours=hours, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise _climate_http_error(e)
