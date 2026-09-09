"""
THERMOSHELTER AI - Climate Normalization & Profile Assembly Engine
==================================================================
Validates, normalizes physical engineering units, guards against unit confusion
(e.g., kWh/m²/day vs W/m²), distinguishes current observations from design baselines,
and synthesizes the complete, authoritative ClimateProfile.
"""

from typing import Any, Dict, Optional, Tuple, Union

from backend.climate.schemas import (
    ClimateMetrics,
    ClimateProfile,
    ClimateZone,
    CurrentWeather,
    DataConfidence,
    DataProvenance,
    DataQuality,
    DesignExtremes,
    HumidityData,
    Location,
    SolarData,
    TemperatureProfile,
    WindData,
)


class ClimateNormalizer:
    """
    Standardizes physical climate variables into canonical SI units:
    - Temperature: Celsius (°C)
    - Wind speed: meters per second (m/s)
    - Humidity: percentage (0 - 100%)
    - Solar Irradiance: Watts per square meter (W/m²)
    - Solar Energy: kilowatt-hours per square meter per year (kWh/m²/year)
    - Coordinates: decimal degrees (-90 to +90, -180 to +180)
    """

    @staticmethod
    def normalize_temperature(val: float, from_unit: str = "C") -> float:
        """Converts temperature to °C and checks terrestrial bounds."""
        unit = from_unit.strip().upper()
        if unit in ("F", "FAHRENHEIT"):
            temp_c = (val - 32.0) * (5.0 / 9.0)
        elif unit in ("K", "KELVIN"):
            temp_c = val - 273.15
        elif unit in ("C", "CELSIUS"):
            temp_c = float(val)
        else:
            raise ValueError(f"Unknown temperature unit '{from_unit}'. Use 'C', 'F', or 'K'.")

        if not (-80.0 <= temp_c <= 70.0):
            raise ValueError(f"Normalized temperature {temp_c:.1f}°C outside terrestrial physical limits (-80°C to 70°C)")
        return round(temp_c, 2)

    @staticmethod
    def normalize_wind_speed(val: float, from_unit: str = "m/s") -> float:
        """Converts wind speed to m/s and ensures non-negative bounds."""
        unit = from_unit.strip().lower()
        if unit in ("m/s", "ms", "meters_per_second"):
            speed = float(val)
        elif unit in ("km/h", "kmh", "kph"):
            speed = val / 3.6
        elif unit in ("mph", "miles_per_hour"):
            speed = val * 0.44704
        elif unit in ("knots", "kt"):
            speed = val * 0.514444
        else:
            raise ValueError(f"Unknown wind unit '{from_unit}'. Use 'm/s', 'km/h', 'mph', or 'knots'.")

        if speed < 0.0:
            raise ValueError(f"Wind speed cannot be negative: {speed} m/s")
        if speed > 120.0:
            raise ValueError(f"Wind speed {speed:.1f} m/s exceeds extreme hurricane bounds (>120 m/s)")
        return round(speed, 2)

    @staticmethod
    def normalize_relative_humidity(val: float) -> float:
        """Ensures relative humidity is between 0.0% and 100.0%."""
        rh = float(val)
        # If passed as a fraction 0.0 - 1.0 (e.g. 0.45), convert to %
        if 0.0 <= rh <= 1.0 and rh != 0.0 and rh != 1.0:
            rh = rh * 100.0

        if not (0.0 <= rh <= 100.0):
            raise ValueError(f"Relative humidity must be within [0, 100]%, got {rh}")
        return round(rh, 1)

    @staticmethod
    def normalize_solar_flux(val: float, from_unit: str = "W/m²") -> float:
        """Validates instantaneous solar irradiance flux (W/m²)."""
        flux = float(val)
        if flux < 0.0:
            raise ValueError(f"Solar irradiance flux cannot be negative: {flux}")
        if flux > 1400.0:
            raise ValueError(f"Solar irradiance {flux} W/m² exceeds extraterrestrial solar constant (1361 W/m²)")
        return round(flux, 1)

    @staticmethod
    def convert_daily_insolation_to_annual_and_flux(kwh_m2_day: float) -> Tuple[float, float]:
        """
        Converts daily insolation (kWh/m²/day) to:
        1. Cumulative annual insolation (kWh/m²/year)
        2. Time-averaged annual continuous flux (W/m²)
        """
        if kwh_m2_day < 0.0:
            raise ValueError("Daily insolation cannot be negative")
        annual_kwh = round(kwh_m2_day * 365.0, 1)
        # annual_kwh * 1000 Wh / 8760 hours = W/m² mean continuous flux
        mean_flux = round((annual_kwh * 1000.0) / 8760.0, 1)
        return annual_kwh, mean_flux

    @staticmethod
    def convert_annual_insolation_to_flux(annual_kwh_m2: float) -> float:
        """Converts annual cumulative insolation (kWh/m²/year) to 24h mean flux (W/m²)."""
        if annual_kwh_m2 < 0.0:
            raise ValueError("Annual insolation cannot be negative")
        return round((annual_kwh_m2 * 1000.0) / 8760.0, 1)


def assemble_climate_profile(
    location: Location,
    temperature: TemperatureProfile,
    solar: SolarData,
    wind: WindData,
    humidity: HumidityData,
    design_extremes: DesignExtremes,
    data_quality: DataQuality,
    classification: ClimateZone,
    current_weather: Optional[CurrentWeather] = None,
    version: str = "1.0.0"
) -> ClimateProfile:
    """
    Constructs and validates the unified ClimateProfile shared contract.
    Ensures strict separation between current weather observations and historical design baselines.
    """
    # Defensive unit sanity checks
    temp_annual = ClimateNormalizer.normalize_temperature(temperature.annual_mean_temperature)
    temp_min = ClimateNormalizer.normalize_temperature(temperature.minimum_temperature)
    temp_max = ClimateNormalizer.normalize_temperature(temperature.maximum_temperature)

    if temp_min > temp_max:
        raise ValueError(f"Minimum temperature ({temp_min}°C) cannot exceed maximum temperature ({temp_max}°C)")

    wind_speed = ClimateNormalizer.normalize_wind_speed(wind.average_speed)
    avg_rh = ClimateNormalizer.normalize_relative_humidity(humidity.average_relative_humidity)
    solar_ghi = ClimateNormalizer.normalize_solar_flux(solar.GHI)

    climate_metrics = ClimateMetrics(
        classification=classification,
        annual_mean_temperature=temp_annual,
        minimum_temperature=temp_min,
        maximum_temperature=temp_max,
        diurnal_range_mean=temperature.diurnal_range_mean or round(temp_max - temp_min, 1),
        temperature_profile=temperature.temperature_profile
    )

    return ClimateProfile(
        version=version,
        location=location,
        climate=climate_metrics,
        solar=solar,
        wind=wind,
        humidity=humidity,
        design_extremes=design_extremes,
        data_quality=data_quality,
        current_weather=current_weather
    )
