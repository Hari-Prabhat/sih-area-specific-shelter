"""
THERMOSHELTER AI - Simulation API Routes
=========================================
FastAPI route handlers for running the authoritative Python thermal simulation engine
via canonical contracts and SimulationAdapter.
"""

from typing import Any, Dict, List, Optional, Union
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from services.contracts import (
    ClimateProfile,
    ShelterDesign,
    SimulationInput,
    SimulationResult,
    adapt_backend_climate_profile,
    adapt_to_climate_profile,
    adapt_to_shelter_design,
    create_mock_climate_profile,
)
from services.climate_service import get_climate_data
from services.simulation_adapter import SimulationAdapter
from services.shelter.models import DataProvenance

logger = logging.getLogger("thermoshelter.api.simulation")

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


# =====================================================================
# REQUEST & RESPONSE SCHEMAS
# =====================================================================

class SimulationRunRequest(BaseModel):
    """
    Standard request schema for executing a thermal simulation.
    Accepts canonical hierarchical ShelterDesign or flat parameter dictionary,
    along with canonical ClimateProfile, city name, or backend climate object.
    """
    model_config = ConfigDict(extra="allow")

    design: Optional[Dict[str, Any]] = Field(
        None,
        description="Canonical ShelterDesign dictionary or flat design parameters"
    )
    climate: Optional[Union[Dict[str, Any], str]] = Field(
        None,
        description="Canonical ClimateProfile dict, city name, or backend climate profile"
    )
    city: Optional[str] = Field(
        None,
        description="Target city name (e.g. 'leh', 'jaisalmer', 'chennai') when climate profile is omitted"
    )
    hours_to_simulate: int = Field(
        168,
        ge=1,
        le=8760,
        description="Duration of simulation in hours (default: 168)"
    )
    substeps: int = Field(
        60,
        ge=1,
        le=3600,
        description="Numerical integration steps per hour (default: 60)"
    )
    initial_indoor_temp: float = Field(
        20.0,
        ge=-60.0,
        le=60.0,
        description="Initial interior air temperature in °C"
    )


# =====================================================================
# RESOLVER HELPERS
# =====================================================================

def _resolve_climate(
    climate_input: Optional[Union[Dict[str, Any], str]],
    city_fallback: Optional[str] = None
) -> ClimateProfile:
    """
    Resolves canonical ClimateProfile from various input representations:
    1. Direct ClimateProfile instance or canonical dict with hourly curves
    2. Backend Member 1 ClimateProfile (Pydantic model)
    3. City name lookup in EnergyPlus weather datasets / CSV
    4. Deterministic synthetic fixture fallback
    """
    if isinstance(climate_input, str):
        city_name = climate_input.strip().lower()
    elif isinstance(climate_input, dict):
        # Case A: canonical flat climate profile with hourly time series
        if "hourly_temperature" in climate_input and len(climate_input.get("hourly_temperature", [])) > 0:
            return adapt_to_climate_profile(climate_input)

        # Case B: backend Member 1 structured Pydantic climate profile
        if "location" in climate_input and "climate" in climate_input and "solar" in climate_input:
            from backend.climate.schemas import ClimateProfile as BackendClimateProfile
            bp = BackendClimateProfile.model_validate(climate_input)
            return adapt_backend_climate_profile(bp)

        # Case C: dictionary specifying a city name
        city_name = climate_input.get("city", climate_input.get("location", "leh")).strip().lower()
    elif city_fallback:
        city_name = city_fallback.strip().lower()
    else:
        city_name = "leh"

    # Fetch weather dataset from data/weather/{city}.epw or data/climate/weather.csv
    weather_dict = get_climate_data(city_name)
    if "error" not in weather_dict and len(weather_dict.get("hourly_temperature", [])) > 0:
        return ClimateProfile(
            city=weather_dict["city"],
            latitude=weather_dict.get("latitude", 34.1526),
            longitude=weather_dict.get("longitude", 77.5771),
            hourly_temperature=weather_dict["hourly_temperature"],
            hourly_direct_solar=weather_dict["hourly_direct_solar"],
            hourly_diffuse_solar=weather_dict["hourly_diffuse_solar"],
            hourly_wind_speed=weather_dict.get("hourly_wind_speed"),
            hourly_humidity=weather_dict.get("hourly_humidity"),
            climate_zone="cold" if "leh" in city_name else ("hot_dry" if "jaisalmer" in city_name else "composite"),
            data_source=f"EPW_CSV_{city_name.upper()}",
            data_provenance=DataProvenance.HISTORICAL,
            data_confidence=0.90,
        )

    # Deterministic fallback fixture
    return create_mock_climate_profile(city_name)


def _resolve_design(
    design_input: Optional[Dict[str, Any]],
    raw_payload: Optional[Dict[str, Any]] = None
) -> ShelterDesign:
    """
    Resolves canonical ShelterDesign from:
    1. Nested canonical ShelterDesign dictionary
    2. Flat legacy design dictionary
    3. Top-level request parameters
    """
    if design_input and isinstance(design_input, dict):
        return adapt_to_shelter_design(design_input)

    # If design is omitted from 'design' key, check if top-level fields specify design parameters
    if raw_payload:
        non_design_keys = {"climate", "city", "hours_to_simulate", "substeps", "initial_indoor_temp"}
        candidate_design = {k: v for k, v in raw_payload.items() if k not in non_design_keys}
        if candidate_design:
            return adapt_to_shelter_design(candidate_design)

    # Default baseline design
    return adapt_to_shelter_design({})


# =====================================================================
# ENDPOINT: POST /api/simulation/run
# =====================================================================

@router.post(
    "/run",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Execute Thermal Simulation",
    description=(
        "Executes a physically rigorous transient thermal simulation using the authoritative "
        "Python simulation engine (forward Euler solver + ISO 6946 multi-layer U-values). "
        "Returns full timeseries, component heat flow breakdown, comfort metrics, and energy totals."
    )
)
def run_simulation_endpoint(request: SimulationRunRequest) -> Dict[str, Any]:
    """
    Endpoint execution pipeline:
    1. Validate input payload
    2. Construct canonical ClimateProfile
    3. Construct canonical ShelterDesign
    4. Adapt to SimulationInput
    5. Run simulation via SimulationAdapter -> simulation_service.run_simulation
    6. Return validated SimulationResult JSON
    """
    try:
        raw_dict = request.model_dump()

        # 1. Resolve Climate
        try:
            climate = _resolve_climate(request.climate, city_fallback=request.city)
        except Exception as e:
            logger.warning(f"Failed to resolve climate: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Invalid climate specification", "message": str(e)}
            )

        # 2. Resolve Shelter Design
        try:
            design = _resolve_design(request.design, raw_payload=raw_dict)
        except Exception as e:
            logger.warning(f"Failed to resolve shelter design: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Invalid shelter design specification", "message": str(e)}
            )

        # 3. Create SimulationInput via Adapter
        try:
            sim_input = SimulationAdapter.to_simulation_input(
                climate=climate,
                design=design,
                hours_to_simulate=request.hours_to_simulate,
                substeps=request.substeps,
                initial_indoor_temp=request.initial_indoor_temp,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Invalid simulation parameters", "message": str(e)}
            )
        except TypeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Type mismatch in simulation input", "message": str(e)}
            )

        # 4. Execute Real Python Thermal Simulation Engine
        try:
            result = SimulationAdapter.run_simulation_from_input(sim_input)
        except ValueError as e:
            logger.error(f"Simulation execution error: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Simulation calculation failed", "message": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected simulation error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal simulation failure", "message": str(e)}
            )

        # 5. Return standardized SimulationResult payload
        return result.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error in simulation endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )
