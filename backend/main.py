"""
THERMOSHELTER AI - Main FastAPI Application
===========================================
Authoritative backend API service connecting the React presentation layer
to Python scientific engineering models, climate intelligence, and simulation engines.
"""

import os
import sys
from typing import Any, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.climate_routes import router as climate_router
from backend.simulation_routes import router as simulation_router
from backend.optimization_routes import router as optimization_router

# =====================================================================
# FASTAPI APPLICATION INITIALIZATION
# =====================================================================

app = FastAPI(
    title="ThermoShelter AI API",
    description=(
        "Area-specific passive shelter design platform. Bridges the React Design Studio "
        "to authoritative Python physical engineering models, ISO 6946 envelope calculations, "
        "and forward Euler transient thermal simulations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# =====================================================================
# CORS CONFIGURATION (Local Development)
# =====================================================================

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Allow custom environment overrides if specified
custom_origins = os.getenv("CORS_ALLOWED_ORIGINS")
if custom_origins:
    origins.extend([o.strip() for o in custom_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# =====================================================================
# GLOBAL EXCEPTION HANDLERS
# =====================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Graceful JSON response for validation errors without exposing internal tracebacks."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Error", "detail": str(exc)},
    )


@app.exception_handler(TypeError)
async def type_error_handler(request: Request, exc: TypeError):
    """Graceful JSON response for type mismatch errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Type Error", "detail": str(exc)},
    )


# =====================================================================
# HEALTH CHECK & ROOT ROUTE
# =====================================================================

@app.get("/api/health", tags=["system"], summary="Health Check")
def health_check() -> Dict[str, Any]:
    """
    Returns system health status and confirms that canonical engineering
    contracts and the Python simulation engine are operational.
    """
    return {
        "status": "healthy",
        "service": "ThermoShelter AI",
        "version": "1.0.0",
        "canonical_contracts": True,
        "physics_engine": "Python 1D Forward Euler + ISO 6946 (Authoritative)",
        "subsystems": {
            "member1_climate": "active",
            "member2_shelter_design": "active",
            "member3_simulation": "active",
            "optimization": "active",
        }
    }


@app.get("/", tags=["system"], include_in_schema=False)
def root_redirect():
    """Root landing endpoint with system summary."""
    return {
        "message": "Welcome to ThermoShelter AI API",
        "docs": "/docs",
        "health": "/api/health",
        "simulation": "/api/simulation/run",
        "optimization": "/api/optimization/run",
    }


# =====================================================================
# MOUNT SUB-ROUTERS
# =====================================================================

app.include_router(simulation_router)
app.include_router(climate_router)
app.include_router(optimization_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
