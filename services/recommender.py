import os
import sys
import math
import json

# Ensure services directory is discoverable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.material_service import load_all_materials, get_material
    from services.optimize import run_optimization
except ImportError:
    from material_service import load_all_materials, get_material
    from optimize import run_optimization

# City to Climate Zone Mapping
CLIMATE_MAPPING = {
    "leh": "cold",
    "jaisalmer": "hot_dry",
    "chennai": "hot_humid",
    "delhi": "composite",
    "bengaluru": "moderate"
}

CLIMATE_DESCRIPTIONS = {
    "cold": "Severe Cold / Alpine (Ladakh Region)",
    "hot_dry": "Hot & Arid (Thar Desert Region)",
    "hot_humid": "Warm & Humid Coastal (Coromandel Coast)",
    "composite": "Composite / Extreme Seasonal Swings (Northern Plains)",
    "moderate": "Temperate / Moderate Plateau (Deccan Plateau)"
}


def auto_size_shelter(people: int, home_type: str) -> dict:
    """
    Computes shelter geometry based on occupancy and permanence.
    
    Logic:
      - floor_area = max(12.0, people * 4.5) m²
      - length = round(sqrt(floor_area * 1.3), 1)
      - width = round(floor_area / length, 1)
      - height = 2.6 for Temporary, 2.8 for Permanent
    """
    floor_area = max(12.0, float(people) * 4.5)
    length = round(math.sqrt(floor_area * 1.3), 1)
    width = round(floor_area / length, 1)
    height = 2.6 if home_type.lower().startswith("temp") else 2.8
    volume = round(length * width * height, 2)
    
    return {
        "floor_area_m2": round(floor_area, 1),
        "length_m": length,
        "width_m": width,
        "height_m": height,
        "volume_m3": volume
    }


def recommend_materials(climate_type: str, home_type: str) -> dict:
    """
    Recommends envelope materials, glazing, roof geometry, and orientation
    based on climate classification and shelter permanence.
    """
    is_temp = home_type.lower().startswith("temp")
    
    if climate_type == "cold":
        # Leh - Extreme cold, high solar radiation
        return {
            "wall_material_id": "puf_insulation" if is_temp else "brick",
            "wall_material_name": "PUF Insulated Sandwich Panel" if is_temp else "Cavity Brick Wall with Internal Mass",
            "roof_material": "Insulated Metal Sheet Roof (40° Pitch for snow runoff)" if is_temp else "Reinforced Insulated Concrete Pitched Roof",
            "roof_type": "pitched",
            "insulation_type": "Expanded Polyurethane Foam (PUF / EPS)",
            "glazing_type": "High-Performance Low-E Double/Triple Glazing with Argon Gas",
            "orientation_advice": "Orient primary glazing South (±15°) to capture maximum low-angle winter solar radiation.",
            "shading_advice": "Minimal overhangs on South facade to allow winter sun penetration; insulated night shutters."
        }
        
    elif climate_type == "hot_dry":
        # Jaisalmer - Intense heat, large diurnal swing
        return {
            "wall_material_id": "puf_insulation" if is_temp else "brick",
            "wall_material_name": "High-Reflectance Insulated Panel" if is_temp else "Dense Compressed Earth/Brick Wall with Outer Insulation",
            "roof_material": "High-Albedo Reflective Cool Roof with EPS Insulation",
            "roof_type": "flat",
            "insulation_type": "Extruded Polystyrene (XPS) / Mineral Wool",
            "glazing_type": "Solar-Control Tinted Low-E Glazing (Low SHGC < 0.35)",
            "orientation_advice": "East-West elongated building axis; primary openings facing North & South with deep reveals.",
            "shading_advice": "External movable louvers / Jaali screens to block direct summer solar radiation."
        }
        
    elif climate_type == "hot_humid":
        # Chennai - Constant heat, high humidity, low diurnal swing
        return {
            "wall_material_id": "puf_insulation" if is_temp else "concrete",
            "wall_material_name": "Lightweight Aerated Wall Panel" if is_temp else "Lightweight Concrete Block with Ventilated Cavity",
            "roof_material": "Sloped Ventilated Metal Deck with Radiant Barrier",
            "roof_type": "flat",
            "insulation_type": "Reflective Radiant Barrier + Light EPS",
            "glazing_type": "Clear Double Glazing with Louvered Shading",
            "orientation_advice": "Orient perpendicular to prevailing sea breezes (South-East / East) to maximize cross-ventilation.",
            "shading_advice": "Generous roof overhangs (min 0.8m) on all sides and large operable window openings."
        }
        
    elif climate_type == "composite":
        # Delhi - Extreme summer heat + chilly winter nights
        return {
            "wall_material_id": "puf_insulation" if is_temp else "brick",
            "wall_material_name": "Pre-insulated Modular Panel" if is_temp else "Standard Clay Brick with Exterior Insulation (EIFS)",
            "roof_material": "Insulated Concrete Deck with China Mosaic Cool Roof Coating",
            "roof_type": "flat",
            "insulation_type": "Rigid PUF / Rockwool Insulation",
            "glazing_type": "Double Glazed Unit (DGU) with Solar Low-E Coating",
            "orientation_advice": "North-South orientation with balanced window-to-wall ratios (WWR 15-20%).",
            "shading_advice": "Horizontal overhangs on South facade and vertical fins on East/West facades."
        }
        
    else:
        # Bengaluru - Moderate / Temperate
        return {
            "wall_material_id": "puf_insulation" if is_temp else "brick",
            "wall_material_name": "Standard Modular Panel" if is_temp else "Fly-Ash Brick / Standard Masonry",
            "roof_material": "Standard Concrete Slab with Waterproofing Membrane",
            "roof_type": "flat",
            "insulation_type": "Moderate EPS / Glass Wool Insulation",
            "glazing_type": "Standard Double Clear Glazing (4mm-12mm-4mm)",
            "orientation_advice": "North-South orientation to optimize natural daylighting and pleasant natural breezes.",
            "shading_advice": "Standard window overhangs (chajjas) for monsoon protection and glare reduction."
        }


def generate_design_explanation(city: str, climate_type: str, home_type: str, 
                                insulation_mm: float, window_area_m2: float) -> str:
    """
    Generates a concise, climate-tailored rationale explaining the recommended design.
    """
    if climate_type == "cold":
        return (
            f"**Why this design works for {city.upper()}:** In high-altitude cold climates like Ladakh, sub-zero "
            f"temperatures and severe freeze-thaw cycles dominate. The recommendation couples a thick **{insulation_mm:.0f} mm "
            f"insulation layer** with a dedicated **{window_area_m2:.1f} m² South-facing solar aperture**. During daylight hours, "
            f"direct solar radiation freely enters to charge the indoor thermal envelope. At night, heavy thermal insulation and "
            f"a 40° snow-shedding roof retain trapped heat, drastically cutting supplementary heating fuel consumption."
        )
    elif climate_type == "hot_dry":
        return (
            f"**Why this design works for {city.upper()}:** Arid desert zones experience high daytime solar loads and rapid "
            f"nocturnal radiation loss. The recommendation employs thermal mass walls with **{insulation_mm:.0f} mm exterior insulation** "
            f"to delay heat penetration (thermal lag). A controlled window area of **{window_area_m2:.1f} m²** paired with low-SHGC glazing "
            f"minimizes direct solar gain, while a high-albedo cool roof reflects over 80% of solar irradiance."
        )
    elif climate_type == "hot_humid":
        return (
            f"**Why this design works for {city.upper()}:** Coastal tropical climates suffer from high humidity and sticky nights. "
            f"Thermal mass is ineffective here; instead, the design prioritizes large cross-ventilation apertures of **{window_area_m2:.1f} m²** "
            f"aligned with prevailing coastal winds. A moderate **{insulation_mm:.0f} mm radiant barrier** and deep roof overhangs shield "
            f"the structure from intense tropical sun while maintaining maximum continuous airflow."
        )
    elif climate_type == "composite":
        return (
            f"**Why this design works for {city.upper()}:** Composite climates endure blistering 45°C summers and 5°C winter nights. "
            f"An optimized **{insulation_mm:.0f} mm insulation envelope** combined with a balanced **{window_area_m2:.1f} m² window area** "
            f"provides year-round resilience. Summer overheating is blocked via horizontal shading fins, while winter sun is harvested "
            f"through the South aperture."
        )
    else:
        return (
            f"**Why this design works for {city.upper()}:** Temperate plateau climates have mild seasonal variations. The optimized "
            f"**{insulation_mm:.0f} mm insulation** and **{window_area_m2:.1f} m² daylighting windows** maintain indoor conditions within "
            f"the 18°C–24°C thermal comfort band nearly 100% of the year with virtually zero active energy expenditure."
        )


def get_recommendation(city: str, people: int, home_type: str, n_trials: int = 40) -> dict:
    """
    End-to-end recommendation workflow combining auto-sizing, AI parametric
    optimization, material selection, and architectural rationale.
    """
    climate_type = CLIMATE_MAPPING.get(city.lower(), "composite")
    geo = auto_size_shelter(people, home_type)
    mat_rec = recommend_materials(climate_type, home_type)
    
    # Run AI Optimization using auto-sized geometry and selected wall material
    opt_result = run_optimization(
        city=city,
        length=geo["length_m"],
        width=geo["width_m"],
        height=geo["height_m"],
        wall_material=mat_rec["wall_material_id"],
        occupants=people,
        n_trials=n_trials,
    )
    insulation_mm = round(opt_result["insulation_thickness_m"] * 1000, 0)
    window_area_m2 = opt_result["window_area_m2"]
    
    explanation = generate_design_explanation(
        city=city,
        climate_type=climate_type,
        home_type=home_type,
        insulation_mm=insulation_mm,
        window_area_m2=window_area_m2
    )
    
    return {
        "city": city,
        "climate_type": climate_type,
        "climate_name": CLIMATE_DESCRIPTIONS.get(climate_type, climate_type.title()),
        "home_type": home_type,
        "people": people,
        "geometry": geo,
        "materials": mat_rec,
        "optimal_insulation_m": opt_result["insulation_thickness_m"],
        "optimal_insulation_mm": insulation_mm,
        "optimal_window_area_m2": window_area_m2,
        "optimal_wall_material": opt_result["wall_material"],
        "optimal_glazing": opt_result["glazing"],
        "optimal_glazing_name": opt_result.get("glazing_name", opt_result["glazing"]),
        "optimal_orientation": opt_result["orientation"],
        "discomfort_score": opt_result["discomfort_score"],
        "simulation_result": opt_result.get("simulation_result"),
        "explanation": explanation
    }

