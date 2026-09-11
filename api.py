"""
ThermoShelter AI — FastAPI Backend
===================================
Thin JSON API layer over the existing Python engineering services.
No physics here — just serialization and routing.
"""

import os
import sys
import json
import math
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Path setup ──────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(ROOT_DIR, "services")
COMPONENTS_DIR = os.path.join(ROOT_DIR, "components")

for p in [ROOT_DIR, SERVICES_DIR, COMPONENTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Service imports ─────────────────────────────────────────────────────────────
from services.climate_service import get_climate_data
from services.simulation_service import run_simulation, SHELTER_MODELS, GLAZING_PROPERTIES, ORIENTATION_FACTORS
from services.recommender import (
    get_recommendation,
    auto_size_shelter,
    recommend_materials,
    CLIMATE_MAPPING,
    CLIMATE_DESCRIPTIONS,
)
from services.material_service import load_all_materials, get_material
from components.validation import run_analytical_validation_benchmark
from components.export import generate_markdown_report
from components.inputs import CITIES_METADATA

# ── FastAPI app ─────────────────────────────────────────────────────────────────
app = FastAPI(title="ThermoShelter AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AutoSizeRequest(BaseModel):
    people: int = 4
    home_type: str = "Permanent"

class RecommendMaterialsRequest(BaseModel):
    climate_type: str = "cold"
    home_type: str = "Permanent"

class SimulationRequest(BaseModel):
    city: str = "leh"
    length: float = 4.0
    width: float = 3.0
    height: float = 2.8
    wall_material: str = "brick"
    insulation_thickness_m: float = 0.05
    window_area: float = 2.0
    glazing: str = "double_clear"
    orientation: str = "south"
    roof_type: str = "flat"
    occupants: int = 4
    hours_to_simulate: int = 168
    shelter_model: Optional[str] = None

class OptimizationRequest(BaseModel):
    city: str = "leh"
    people: int = 4
    home_type: str = "Permanent"
    n_trials: int = 35
    max_insulation_mm: float = 200.0
    max_window_area: Optional[float] = None

class ComparisonRequest(BaseModel):
    city: str = "leh"
    people: int = 4
    home_type: str = "Permanent"

class MaterialComparisonRequest(BaseModel):
    city: str = "leh"
    insulation_mm: float = 50.0
    window_area: float = 2.5
    occupants: int = 4

class ArchetypeComparisonRequest(BaseModel):
    city: str = "leh"
    occupants: int = 4
    height: float = 2.8

class SensitivityRequest(BaseModel):
    city: str = "leh"
    parameter: str = "insulation"  # insulation | window_area
    occupants: int = 4

class ExportRequest(BaseModel):
    city: str = "leh"
    people: int = 4
    home_type: str = "Permanent"
    n_trials: int = 35
    max_insulation_mm: float = 200.0
    max_window_area: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — strip numpy from results for JSON serialization
# ═══════════════════════════════════════════════════════════════════════════════

def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy types to Python natives for JSON."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonify(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ThermoShelter AI"}


# ── Climate ──────────────────────────────────────────────────────────────────
@app.get("/api/climate/cities")
def get_cities():
    cities = []
    for city_id, meta in CITIES_METADATA.items():
        climate_type = CLIMATE_MAPPING.get(city_id, "composite")
        cities.append({
            "id": city_id,
            "display": meta["display"],
            "badge": meta["badge"],
            "elevation": meta["elevation"],
            "winter_temp": meta["winter_temp"],
            "summer_temp": meta["summer_temp"],
            "solar_ghi": meta["solar_ghi"],
            "hdd": meta["hdd"],
            "source": meta["source"],
            "type": meta["type"],
            "climate_type": climate_type,
            "climate_description": CLIMATE_DESCRIPTIONS.get(climate_type, climate_type),
        })
    return {"cities": cities}


@app.get("/api/climate/{city}")
def get_climate(city: str):
    data = get_climate_data(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    meta = CITIES_METADATA.get(city.lower(), {})
    climate_type = CLIMATE_MAPPING.get(city.lower(), "composite")
    return _jsonify({
        **data,
        "metadata": meta,
        "climate_type": climate_type,
        "climate_description": CLIMATE_DESCRIPTIONS.get(climate_type, climate_type),
    })


# ── Materials ────────────────────────────────────────────────────────────────
@app.get("/api/materials")
def get_materials():
    mats = load_all_materials()
    return _jsonify({"materials": mats})


@app.get("/api/materials/{material_id}")
def get_single_material(material_id: str):
    mat = get_material(material_id)
    if "error" in mat:
        raise HTTPException(status_code=404, detail=mat["error"])
    return _jsonify(mat)


# ── Shelter Models / Glazing / Orientation ───────────────────────────────────
@app.get("/api/shelter-models")
def get_shelter_models():
    return _jsonify({"models": SHELTER_MODELS})


@app.get("/api/glazing")
def get_glazing():
    return _jsonify({"glazing": GLAZING_PROPERTIES})


@app.get("/api/orientations")
def get_orientations():
    return _jsonify({"orientations": ORIENTATION_FACTORS})


# ── Auto-size ────────────────────────────────────────────────────────────────
@app.post("/api/auto-size")
def post_auto_size(req: AutoSizeRequest):
    geo = auto_size_shelter(req.people, req.home_type)
    return _jsonify(geo)


# ── Recommend Materials ──────────────────────────────────────────────────────
@app.post("/api/recommend-materials")
def post_recommend_materials(req: RecommendMaterialsRequest):
    mats = recommend_materials(req.climate_type, req.home_type)
    return _jsonify(mats)


# ── Simulation ───────────────────────────────────────────────────────────────
@app.post("/api/simulation")
def post_simulation(req: SimulationRequest):
    result = run_simulation(
        city=req.city,
        length=req.length,
        width=req.width,
        height=req.height,
        wall_material=req.wall_material,
        insulation_thickness_m=req.insulation_thickness_m,
        window_area=req.window_area,
        glazing=req.glazing,
        orientation=req.orientation,
        roof_type=req.roof_type,
        occupants=req.occupants,
        hours_to_simulate=req.hours_to_simulate,
        shelter_model=req.shelter_model,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return _jsonify(result)


# ── Optimization ─────────────────────────────────────────────────────────────
@app.post("/api/optimization")
def post_optimization(req: OptimizationRequest):
    rec = get_recommendation(
        city=req.city,
        people=req.people,
        home_type=req.home_type,
        n_trials=req.n_trials,
        max_insulation_mm=req.max_insulation_mm,
        max_window_area=req.max_window_area,
    )
    if not rec or not rec.get("simulation_result"):
        raise HTTPException(status_code=500, detail="Optimization failed")
    return _jsonify(rec)


# ── Comparison (Baseline vs Optimized) ───────────────────────────────────────
@app.post("/api/comparison")
def post_comparison(req: ComparisonRequest):
    # Optimized
    rec = get_recommendation(
        city=req.city,
        people=req.people,
        home_type=req.home_type,
        n_trials=35,
    )
    if not rec or not rec.get("simulation_result"):
        raise HTTPException(status_code=500, detail="Optimization failed")

    geo = rec["geometry"]
    base_mat = "brick" if req.home_type == "Permanent" else "wood"

    # Baseline (uninsulated)
    baseline = run_simulation(
        city=req.city,
        length=geo["length_m"],
        width=geo["width_m"],
        height=geo["height_m"],
        wall_material=base_mat,
        insulation_thickness_m=0.0,
        window_area=2.0,
        glazing="single_clear",
        orientation="south",
        occupants=req.people,
        hours_to_simulate=168,
    )

    optimized = rec["simulation_result"]
    return _jsonify({
        "baseline": baseline,
        "optimized": optimized,
        "recommendation": rec,
    })


# ── Material Comparison ──────────────────────────────────────────────────────
@app.post("/api/material-comparison")
def post_material_comparison(req: MaterialComparisonRequest):
    all_mat = load_all_materials()
    candidates = [
        k for k in all_mat
        if isinstance(all_mat[k], dict) and all_mat[k].get("category") == "wall"
    ]
    if not candidates:
        candidates = ["brick", "concrete", "puf_insulation", "stone", "mud"]

    results = []
    for m_key in candidates[:8]:
        m_info = all_mat.get(m_key, {})
        sim = run_simulation(
            city=req.city,
            length=4.5,
            width=3.2,
            height=2.8,
            wall_material=m_key,
            insulation_thickness_m=req.insulation_mm / 1000.0,
            window_area=req.window_area,
            occupants=req.occupants,
            hours_to_simulate=168,
        )
        if "error" not in sim:
            results.append({
                "key": m_key,
                "name": m_info.get("name", m_key.title()),
                "conductivity": m_info.get("thermal_conductivity", 0),
                "density": m_info.get("density", 0),
                "wall_u": sim["u_values"]["wall_u"],
                "wall_r": sim["u_values"]["wall_r_total"],
                "avg_t": sim["comfort_metrics"]["avg"],
                "min_t": sim["comfort_metrics"]["min_t"],
                "max_t": sim["comfort_metrics"]["max_t"],
                "comfort_hrs": sim["comfort_hours"],
                "comfort_pct": sim["comfort_percentage"],
                "discomfort_dh": sim["discomfort_degree_hours"],
                "total_loss_kwh": sim["total_heat_loss_kwh"],
                "indoor_temps": sim["indoor_temperature"],
                "outdoor_temps": sim["outdoor_temperature"],
            })
    return _jsonify({"materials": results})


# ── Archetype Comparison ─────────────────────────────────────────────────────
@app.post("/api/archetype-comparison")
def post_archetype_comparison(req: ArchetypeComparisonRequest):
    results = []
    for m_key in ["rectangular_flat", "rectangular_pitched", "compact_shelter", "elongated_shelter"]:
        spec = SHELTER_MODELS[m_key]
        d = spec["default_dimensions"]
        sim = run_simulation(
            city=req.city,
            length=d["length"],
            width=d["width"],
            height=req.height,
            roof_type=spec["roof_type"],
            shelter_model=m_key,
            wall_material="brick",
            insulation_thickness_m=0.06,
            window_area=2.2,
            occupants=req.occupants,
            hours_to_simulate=168,
        )
        if "error" not in sim:
            results.append({
                "key": m_key,
                "name": spec["name"],
                "description": spec["description"],
                "roof_type": spec["roof_type"],
                "dimensions": d,
                "comfort_pct": sim["comfort_percentage"],
                "discomfort_dh": sim["discomfort_degree_hours"],
                "heat_loss_kwh": sim["total_heat_loss_kwh"],
                "indoor_temps": sim["indoor_temperature"],
                "outdoor_temps": sim["outdoor_temperature"],
                "geometry": sim["geometry"],
            })
    return _jsonify({"archetypes": results})


# ── Sensitivity ──────────────────────────────────────────────────────────────
@app.post("/api/sensitivity")
def post_sensitivity(req: SensitivityRequest):
    if req.parameter == "insulation":
        values = [0, 20, 40, 60, 80, 100, 120, 150, 180, 200]
        unit = "mm"
        label = "Insulation Thickness"
    else:
        values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
        unit = "m²"
        label = "Window Aperture Area"

    comfort_list = []
    loss_list = []
    for v in values:
        sim = run_simulation(
            city=req.city,
            length=4.5,
            width=3.2,
            height=2.8,
            insulation_thickness_m=(v / 1000.0) if req.parameter == "insulation" else 0.06,
            window_area=2.5 if req.parameter == "insulation" else v,
            occupants=req.occupants,
            hours_to_simulate=168,
        )
        comfort_list.append(sim.get("comfort_percentage", 0))
        loss_list.append(sim.get("total_heat_loss_kwh", 0))

    return _jsonify({
        "parameter": label,
        "unit": unit,
        "values": values,
        "comfort": comfort_list,
        "loss": loss_list,
    })


# ── Validation ───────────────────────────────────────────────────────────────
@app.get("/api/validation")
def get_validation():
    benchmark = run_analytical_validation_benchmark()
    return _jsonify(benchmark)


# ── Export ────────────────────────────────────────────────────────────────────
@app.post("/api/export/markdown")
def post_export_markdown(req: ExportRequest):
    rec = get_recommendation(
        city=req.city,
        people=req.people,
        home_type=req.home_type,
        n_trials=req.n_trials,
        max_insulation_mm=req.max_insulation_mm,
        max_window_area=req.max_window_area,
    )
    if not rec or not rec.get("simulation_result"):
        raise HTTPException(status_code=500, detail="Failed to generate report")
    md = generate_markdown_report(rec, rec["simulation_result"], req.city)
    return {"markdown": md}


@app.post("/api/export/json")
def post_export_json(req: ExportRequest):
    rec = get_recommendation(
        city=req.city,
        people=req.people,
        home_type=req.home_type,
        n_trials=req.n_trials,
        max_insulation_mm=req.max_insulation_mm,
        max_window_area=req.max_window_area,
    )
    if not rec or not rec.get("simulation_result"):
        raise HTTPException(status_code=500, detail="Failed to generate export")
    sim = rec["simulation_result"]
    export_data = {
        "city": req.city,
        "climate_type": rec["climate_type"],
        "home_type": rec["home_type"],
        "people": rec["people"],
        "geometry": rec["geometry"],
        "materials": rec["materials"],
        "optimal_insulation_mm": rec["optimal_insulation_mm"],
        "optimal_window_area_m2": rec["optimal_window_area_m2"],
        "u_values": sim.get("u_values", {}),
        "comfort_metrics": sim.get("comfort_metrics", {}),
        "total_heat_loss_kwh": sim.get("total_heat_loss_kwh", 0),
        "integrated_solar_energy_kwh": sim.get("integrated_solar_energy_kwh", 0),
        "ranked_designs": rec.get("ranked_designs", []),
    }
    return _jsonify(export_data)


# ═══════════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
