"""
THERMOSHELTER AI - Optimization API Routes
==========================================
FastAPI route handlers for executing Bayesian multi-objective design optimization
via canonical contracts and OptimizationAdapter.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from services.contracts import (
    OptimizationInput,
    OptimizationResult,
    OptimizationCandidate,
    ShelterDesign,
    ClimateProfile,
    adapt_to_shelter_design,
)
from services.climate_service import get_climate_data
from services.simulation_adapter import OptimizationAdapter
from backend.simulation_routes import _resolve_climate, _resolve_design

logger = logging.getLogger("thermoshelter.api.optimization")

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


# =====================================================================
# REQUEST & RESPONSE SCHEMAS
# =====================================================================

class OptimizationRunRequest(BaseModel):
    """
    Standard request schema for executing Bayesian design optimization.
    Accepts canonical ShelterDesign or flat design parameters,
    along with target climate, city, search bounds, and multi-objective weights.
    """
    model_config = ConfigDict(extra="allow")

    design: Optional[Dict[str, Any]] = Field(
        None,
        description="Canonical ShelterDesign dictionary or baseline design specifications"
    )
    climate: Optional[Union[Dict[str, Any], str]] = Field(
        None,
        description="Canonical ClimateProfile dict, target city name, or backend climate profile"
    )
    city: Optional[str] = Field(
        None,
        description="Target city name (e.g. 'leh', 'jaisalmer', 'srinagar') when climate profile is omitted"
    )
    home_type: Optional[str] = Field(
        None,
        description="Shelter permanence: 'Permanent' (high thermal mass) or 'Temporary' (lightweight/portable)"
    )
    n_trials: int = Field(
        20,
        ge=1,
        le=200,
        description="Number of Optuna TPE optimization trials (default: 20)"
    )
    substeps: int = Field(
        15,
        ge=1,
        le=60,
        description="Integration substeps per hour during trial evaluations (default: 15)"
    )
    hours_to_simulate: int = Field(
        168,
        ge=24,
        le=8760,
        description="Simulation evaluation horizon in hours (default: 168 = 7 days)"
    )
    weights: Optional[Dict[str, float]] = Field(
        None,
        description="Multi-objective weights for 'comfort', 'efficiency', and 'solar' (must sum to ~1.0)"
    )
    min_insulation_m: Optional[float] = Field(
        None,
        ge=0.0,
        le=0.5,
        description="Minimum insulation thickness bound in meters"
    )
    max_insulation_m: Optional[float] = Field(
        None,
        ge=0.0,
        le=0.5,
        description="Maximum insulation thickness bound in meters"
    )
    min_window_area: Optional[float] = Field(
        None,
        ge=0.1,
        le=50.0,
        description="Minimum window fenestration area in m²"
    )
    max_window_area: Optional[float] = Field(
        None,
        ge=0.1,
        le=50.0,
        description="Maximum window fenestration area in m²"
    )
    allowed_wall_materials: Optional[List[str]] = Field(
        None,
        description="Restricted candidate list of structural wall materials"
    )
    allowed_glazings: Optional[List[str]] = Field(
        None,
        description="Restricted candidate list of glazing assemblies"
    )
    allowed_orientations: Optional[List[str]] = Field(
        None,
        description="Restricted candidate list of orientation angles/facades"
    )


# =====================================================================
# ENDPOINT: POST /api/optimization/run
# =====================================================================

@router.post(
    "/run",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Execute Bayesian Shelter Design Optimization",
    description=(
        "Executes multi-objective Bayesian optimization (Optuna TPE) over envelope insulation, "
        "fenestration aperture, glazing assembly, orientation, and wall materials. "
        "Returns ranked candidate designs (#1, #2, #3) with physical metrics, objective scores, "
        "and canonical digital twin designs."
    ),
)
def run_optimization_endpoint(request: OptimizationRunRequest) -> Dict[str, Any]:
    """
    Endpoint execution pipeline:
    1. Validate input payload and bounds
    2. Resolve target city and verify climate availability
    3. Resolve canonical baseline ShelterDesign
    4. Construct OptimizationInput contract via OptimizationAdapter
    5. Execute real Optuna TPE multi-objective optimization
    6. Attach canonical ShelterDesign representations to candidates
    7. Return standardized OptimizationResult JSON
    """
    try:
        raw_dict = request.model_dump()

        # 1. Validate & Resolve Target City / Climate
        city_name: Optional[str] = None
        if isinstance(request.climate, str):
            city_name = request.climate.strip().lower()
        elif isinstance(request.climate, dict):
            city_name = request.climate.get("city", request.climate.get("location"))
            if city_name:
                city_name = str(city_name).strip().lower()
            else:
                # If a full hourly profile is supplied, check its city field
                if "hourly_temperature" in request.climate and not request.climate.get("city"):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={"error": "Invalid Climate", "message": "Climate profile must specify target city"}
                    )
        elif request.city is not None:
            city_name = request.city.strip().lower()

        if city_name is not None and not city_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Invalid City", "message": "City name cannot be empty"}
            )

        target_city = city_name or "leh"

        # Verify climate availability for target city
        weather_check = get_climate_data(target_city)
        if "error" in weather_check:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Climate Not Found", "message": weather_check["error"]}
            )

        # 2. Resolve Baseline Shelter Design
        try:
            design = _resolve_design(request.design, raw_payload=raw_dict)
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Invalid Design Specification", "message": str(e)}
            )

        # 3. Construct OptimizationInput via Adapter
        try:
            extra_overrides = {
                k: v for k, v in raw_dict.items()
                if v is not None and k in {
                    "min_insulation_m", "max_insulation_m",
                    "min_window_area", "max_window_area",
                    "allowed_wall_materials", "allowed_glazings",
                    "allowed_orientations", "weights", "substeps",
                    "hours_to_simulate"
                }
            }

            opt_input = OptimizationAdapter.from_shelter_design(
                design=design,
                city_or_climate=target_city,
                home_type=request.home_type,
                n_trials=request.n_trials,
                **extra_overrides,
            )
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Invalid Optimization Parameters", "message": str(e)}
            )

        # 4. Execute Authoritative Python Bayesian Optimizer
        try:
            opt_result = OptimizationAdapter.run_optimization_from_input(opt_input)
        except ValueError as e:
            logger.error(f"Optimization calculation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Optimization failed", "message": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected optimization engine error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal optimization failure", "message": str(e)}
            )

        # 5. Attach Canonical Digital Twin to Each Candidate
        for candidate in opt_result.ranked_designs:
            if not candidate.canonical_design:
                cand_sd = OptimizationAdapter.candidate_to_shelter_design(
                    candidate=candidate,
                    base_design=design,
                )
                candidate.canonical_design = cand_sd.to_dict()

        # 6. Format Response
        response_data = opt_result.to_dict()
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error in optimization endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )
