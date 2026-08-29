import os
from pvlib.iotools import read_epw

# This magic line finds the project root folder no matter where you run the script from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEATHER_DIR = os.path.join(BASE_DIR, "data", "weather")

def get_climate_data(city_name):
    """
    Load hourly weather data for a city.
    """
    file_path = os.path.join(WEATHER_DIR, f"{city_name.lower()}.epw")

    if not os.path.exists(file_path):
        return {"error": f"Weather file for '{city_name}' not found."}

    # Read the complex .epw file into a clean table
    df, metadata = read_epw(file_path)

    return {
        "city": city_name,
        "latitude": metadata["latitude"],
        "longitude": metadata["longitude"],
        "hourly_temperature": df["temp_air"].tolist(),
        "hourly_direct_solar": df["dni"].tolist(),
        "hourly_diffuse_solar": df["dhi"].tolist(),
        "hourly_wind_speed": df["wind_speed"].tolist(),
        "hourly_humidity": df["relative_humidity"].tolist(),
    }

if __name__ == "__main__":
    data = get_climate_data("leh")
    print(f"Loaded: {data['city']}")
    print(f"Hours of data: {len(data['hourly_temperature'])}")
    print(f"Coldest temp: {min(data['hourly_temperature'])} C")
    print(f"Warmest temp: {max(data['hourly_temperature'])} C")