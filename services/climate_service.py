import csv
import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional

# This magic line finds the project root folder no matter where you run the script from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEATHER_DIR = os.path.join(BASE_DIR, "data", "weather")
CLIMATE_DATA_DIR = os.path.join(BASE_DIR, "data", "climate")

@lru_cache(maxsize=32)
def get_climate_data(city_name: str) -> Dict[str, Any]:
    """
    Load hourly weather data for a city (cached in-memory for high performance).
    Attempts to read EPW via pvlib if available; gracefully falls back to
    standard weather.csv dataset if pvlib is not installed.
    """
    city_clean = str(city_name).lower().strip()
    file_path = os.path.join(WEATHER_DIR, f"{city_clean}.epw")

    # 1. Attempt EPW read via pvlib if installed
    try:
        from pvlib.iotools import read_epw
        if os.path.exists(file_path):
            df, metadata = read_epw(file_path)
            return {
                "city": city_clean,
                "latitude": metadata["latitude"],
                "longitude": metadata["longitude"],
                "hourly_temperature": df["temp_air"].tolist(),
                "hourly_direct_solar": df["dni"].tolist(),
                "hourly_diffuse_solar": df["dhi"].tolist(),
                "hourly_wind_speed": df["wind_speed"].tolist(),
                "hourly_humidity": df["relative_humidity"].tolist(),
            }
    except ImportError:
        pass

    # 2. Pure-Python Fallback using data/climate/weather.csv and locations.json
    weather_csv = os.path.join(CLIMATE_DATA_DIR, "weather.csv")
    locations_json = os.path.join(CLIMATE_DATA_DIR, "locations.json")

    lat, lon = 34.1526, 77.5771  # Default to Leh coordinates
    if os.path.exists(locations_json):
        try:
            with open(locations_json, "r", encoding="utf-8") as f:
                locs = json.load(f)
                for loc in locs:
                    if loc.get("id", "").lower() == city_clean or loc.get("name", "").lower() == city_clean:
                        lat = loc.get("latitude", lat)
                        lon = loc.get("longitude", lon)
                        break
        except Exception:
            pass

    if os.path.exists(weather_csv):
        temps, solar, winds, humidities = [], [], [], []
        try:
            with open(weather_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("location_id", "").lower() == city_clean:
                        temps.append(float(row.get("ambient_temperature", 0.0)))
                        solar.append(float(row.get("solar_irradiance", 0.0)))
                        winds.append(float(row.get("wind_speed", 0.0)))
                        humidities.append(float(row.get("relative_humidity", 0.0)))
            if temps:
                return {
                    "city": city_clean,
                    "latitude": lat,
                    "longitude": lon,
                    "hourly_temperature": temps,
                    "hourly_direct_solar": [round(s * 0.75, 1) for s in solar],
                    "hourly_diffuse_solar": [round(s * 0.25, 1) for s in solar],
                    "hourly_wind_speed": winds,
                    "hourly_humidity": humidities,
                }
        except Exception:
            pass

    return {"error": f"Weather data for '{city_name}' not found."}


# ------------------------------------------------------------------------------
# MEMBER 1 ENGINE BRIDGES (Convenience functions for existing services)
# ------------------------------------------------------------------------------
def get_climate_profile(location_query: str):
    """Bridge to Member 1 ClimateProfile synthesis."""
    from backend.climate.service import default_climate_service
    return default_climate_service.get_climate_profile(location_query)


def get_passive_strategy(location_query: str):
    """Bridge to Member 1 PassiveStrategy generation."""
    from backend.climate.service import default_climate_service
    profile = default_climate_service.get_climate_profile(location_query)
    return default_climate_service.generate_passive_strategy(profile)


def analyze_climate(location_query: str):
    """Bridge to Member 1 complete ClimateAnalysisResult."""
    from backend.climate.service import default_climate_service
    return default_climate_service.analyze(location_query)


if __name__ == "__main__":
    data = get_climate_data("leh")
    print(f"Loaded: {data['city']}")
    print(f"Hours of data: {len(data['hourly_temperature'])}")
    print(f"Coldest temp: {min(data['hourly_temperature'])} C")
    print(f"Warmest temp: {max(data['hourly_temperature'])} C")