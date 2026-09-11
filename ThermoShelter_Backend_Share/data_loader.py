"""
THERMOSHELTER AI - Data Access & Loader Utility
==================================================
Reusable data access functions for climate, weather, materials, glazing,
and shelter templates. Designed for seamless integration into the
thermal simulation engine without hardcoding assumptions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

# Directory path discovery relative to data_loader.py location
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def _load_json(file_path: Path) -> List[Dict[str, Any]]:
    """Helper to load and parse JSON files safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found at expected path: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_locations(as_dataframe: bool = False) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """
    Loads metadata for all supported geographic locations.

    Parameters:
        as_dataframe (bool): If True, returns a pandas DataFrame. Default is False.

    Returns:
        List[Dict[str, Any]] or pd.DataFrame: Location records containing coordinates,
        altitude, Köppen classification, design temperatures, and reference sources.
    """
    path = DATA_DIR / "climate" / "locations.json"
    data = _load_json(path)
    if as_dataframe:
        return pd.DataFrame(data)
    return data

def get_location(location_id: str) -> Dict[str, Any]:
    """
    Retrieves metadata for a specific location by ID (e.g., 'leh', 'kargil', 'delhi').

    Parameters:
        location_id (str): Unique identifier of the location (case-insensitive).

    Returns:
        Dict[str, Any]: Location metadata record.

    Raises:
        ValueError: If location_id is not found in the dataset.
    """
    loc_id_clean = location_id.strip().lower()
    locations = load_locations(as_dataframe=False)
    for loc in locations:
        if loc["id"].lower() == loc_id_clean:
            return loc
    available = [loc["id"] for loc in locations]
    raise ValueError(f"Location '{location_id}' not found. Available locations: {available}")

def load_weather(
    location_id: Optional[str] = None,
    as_dataframe: bool = True
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Loads hourly weather records.

    Parameters:
        location_id (Optional[str]): If provided, loads weather only for the specified
            location ID (e.g., 'leh'). If None, loads weather for all locations.
        as_dataframe (bool): If True, returns a pandas DataFrame. Default is True.

    Returns:
        pd.DataFrame or List[Dict[str, Any]]: Standardized hourly weather data with columns:
        [timestamp, location_id, ambient_temperature, solar_irradiance, wind_speed,
         relative_humidity, cloud_cover].

    Units:
        - ambient_temperature: °C
        - solar_irradiance: W/m² (Global Horizontal Irradiance)
        - wind_speed: m/s
        - relative_humidity: % (0 - 100)
        - cloud_cover: fraction (0.0 - 1.0)
    """
    if location_id:
        loc_id_clean = location_id.strip().lower()
        loc_file = DATA_DIR / "climate" / f'weather_{loc_id_clean}.csv'
        if loc_file.exists():
            df = pd.read_csv(loc_file)
        else:
            # Fallback to filtering master file
            master_file = DATA_DIR / "climate" / "weather.csv"
            if not master_file.exists():
                raise FileNotFoundError(f"Weather master dataset not found at {master_file}")
            df = pd.read_csv(master_file)
            df = df[df["location_id"].str.lower() == loc_id_clean].copy()
            if df.empty:
                raise ValueError(f"No weather records found for location_id '{location_id}'.")
    else:
        master_file = DATA_DIR / "climate" / "weather.csv"
        if not master_file.exists():
            raise FileNotFoundError(f"Weather master dataset not found at {master_file}")
        df = pd.read_csv(master_file)

    if as_dataframe:
        return df
    return df.to_dict(orient="records")

def load_materials(
    category: Optional[str] = None,
    as_dataframe: bool = False
) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """
    Loads building and insulation materials database.

    Parameters:
        category (Optional[str]): Filter by category ('wall', 'roof', 'floor', 'insulation', 'thermal_mass').
        as_dataframe (bool): If True, returns a pandas DataFrame. Default is False.

    Returns:
        List[Dict[str, Any]] or pd.DataFrame: Material property specifications including
        density (kg/m¯s), thermal_conductivity (W/m·K), specific_heat (J/kg·K),
        emissivity (dimensionless), solar_absorptivity (dimensionless), cost_estimate, and uncertainty ranges.
    """
    path = DATA_DIR / "materials" / "materials.json"
    data = _load_json(path)
    if category:
        cat_clean = category.strip().lower()
        data = [m for m in data if m["category"].lower() == cat_clean]
        if not data:
            valid_cats = sorted(list({m["category"] for m in _load_json(path)}))
            raise ValueError(f"No materials found for category '{category}'. Valid categories: {valid_cats}")

    if as_dataframe:
        flattened = []
        for m in data:
            flat = {
                "id": m["id"],
                "name": m["name"],
                "category": m["mcategory"] if "mcategory" in m else m["category"],
                "density_typical": m["density"]["typical_value"],
                "density_min": m["density"]["min_value"],
                "density_max": m["density"]["max_value"],
                "thermal_conductivity_typical": m["thermal_conductivity"]["typical_value"],
                "thermal_conductivity_min": m["thermal_conductivity"]["min_value"],
                "thermal_conductivity_max": m["thermal_conductivity"]["max_value"],
                "specific_heat_typical": m["specific_heat"]["typical_value"],
                "specific_heat_min": m["specific_heat"]["min_value"],
                "specific_heat_max": m["specific_heat"]["max_value"],
                "emissivity_typical": m["emissivity"]["typical_value"],
                "solar_absorptivity_typical": m["solar_absorptivity"]["typical_value"],
                "cost_estimate_typical": m["cost_estimate"]["typical_value"],
                "source": m.get("source", ""),
                "notes": m.get("notes", "")
            }
            flattened.append(flat)
        return pd.DataFrame(flattened)
    return data

def get_material(material_id: str) -> Dict[str, Any]:
    """
    Retrieves a single material by its unique identifier.

    Parameters:
        material_id (str): Unique material ID (e.g. 'mud_brick', 'eps_insulation').

    Returns:
        Dict[str, Any]: Material record with full uncertainty bounds and source citations.
    """
    mat_id_clean = material_id.strip().lower()
    materials = load_materials(as_dataframe=False)
    for m in materials:
        if m["id"].lower() == mat_id_clean:
            return m
    available = [m["id"] for m in materials]
    raise ValueError(f"Material '{material_id}' not found. Available IDs: {available}")

def load_glazing(as_dataframe: bool = False) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """
    Loads glazing systems and fenestration options.

    Parameters:
        as_dataframe (bool): If True, returns a pandas DataFrame. Default is False.

    Returns:
        List[Dict[str, Any]] or pd.DataFrame: Glazing records containing U_value (W/m²·K),
        SHGC (dimensionless), thickness (m), visible_transmittance, and citations.
    """
    path = DATA_DIR / "materials" / "glazing.json"
    data = _load_json(path)
    if as_dataframe:
        flattened = []
        for g in data:
            flat = {
                "id": g["id"],
                "name": g["name"],
                "U_value_typical": g["U_value"]["typical_value"],
                "U_value_min": g["U_value"]["min_value"],
                "U_value_max": g["U_value"]["max_value"],
                "SHGC_typical": g["SHGC"]["typical_value"],
                "SHGC_min": g["SHGC"]["min_value"],
                "SHGC_max": g["SHGC"]["max_value"],
                "thickness_typical": g["thickness"]["typical_value"],
                "visible_transmittance": g.get("visible_transmittance"),
                "source": g.get("source", ""),
                "notes": g.get("notes", "")
            }
            flattened.append(flat)
        return pd.DataFrame(flattened)
    return data

def get_glazing(glazing_id: str) -> Dict[str, Any]:
    """
    Retrieves a single glazing specification by its unique identifier.

    Parameters:
        glazing_id (str): Unique glazing ID (e.g. 'single_clear_4mm', 'double_low_e_argon_16mm').

    Returns:
        Dict[str, Any]: Glazing record with thermal and optical properties.
    """
    g_id_clean = glazing_id.strip().lower()
    glazings = load_glazing(as_dataframe=False)
    for g in glazings:
        if g["id"].lower() == g_id_clean:
            return g
    available = [g["id"] for g in glazings]
    raise ValueError(f"Glazing '{glazing_id}' not found. Available IDs: {available}")

def load_shelter_templates(
    template_id: Optional[str] = None,
    as_dataframe: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, Any], pd.DataFrame]:
    """
    Loads shelter archetype templates (dimensions, geometry shape, envelope recommendations).

    Parameters:
        template_id (Optional[str]): If specified, returns a single matching template dict.
        as_dataframe (bool): If True, returns a pandas DataFrame. Default is False.

    Returns:
        List[Dict[str, Any]] or Dict[str, Any] or pd.DataFrame: Shelter template records.
    """
    path = DATA_DIR / "shelters" / "templates.json"
    data = _load_json(path)
    if template_id:
        t_clean = template_id.strip().lower()
        for t in data:
            if t["id"].lower() == t_clean:
                return t
        available = [t["id"] for t in data]
        raise ValueError(f"Shelter template '{template_id}' not found. Available templates: {available}")

    if as_dataframe:
        return pd.DataFrame(data)
    return data
