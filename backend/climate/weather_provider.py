"""
THERMOSHELTER AI - Weather & Climate Provider Abstraction
=========================================================
Vendor-agnostic abstraction layer supporting real-time observations,
historical climate norms, and local offline fallbacks with caching.
"""



from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from backend.climate.climate_cache import ClimateCache
from backend.climate.errors import ClimateErrorCategory, ClimateServiceError
from backend.climate.schemas import (
    CurrentWeather,
    DataConfidence,
    DataProvenance,
    DataQuality,
    DesignExtremes,
    HourlyWeatherSeries,
    HumidityData,
    SolarData,
    TemperatureProfile,
    WeatherDataMode,
    WindData,
)

logger = logging.getLogger("thermoshelter.climate.weather")


class BaseWeatherProvider(ABC):
    """Abstract base class for all meteorological and solar data providers."""

    @abstractmethod
    def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        """Retrieves instantaneous observed weather conditions."""
        pass

    @abstractmethod
    def get_historical_climate(
        self, latitude: float, longitude: float
    ) -> Tuple[TemperatureProfile, WindData, HumidityData, DesignExtremes, DataQuality]:
        """Retrieves multi-year climatological normals and design extremes."""
        pass

    @abstractmethod
    def get_solar_data(self, latitude: float, longitude: float) -> SolarData:
        """Retrieves solar irradiance (GHI, DNI, DHI) and insolation data."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the provider is currently reachable."""
        pass


class LocalFallbackWeatherProvider(BaseWeatherProvider):
    """
    Offline-first provider loading verified mock datasets and local climatology.
    Guarantees operation in field and offline scenarios without external network access.
    """

    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        if data_dir is None:
            current_dir = Path(__file__).resolve().parent
            self.base_dir = current_dir.parent.parent
            self.data_dir = self.base_dir / "data"
        else:
            self.data_dir = Path(data_dir)
            self.base_dir = self.data_dir.parent

        self._mock_profiles: Dict[str, Dict[str, Any]] = {}
        self._locations: List[Dict[str, Any]] = []
        self._load_datasets()

    def _load_datasets(self) -> None:
        """Loads mock benchmarks and locations.json."""
        mock_dir = self.data_dir / "mock"
        if mock_dir.exists():
            for mock_path in mock_dir.glob("*_climate.json"):
                key = mock_path.stem.replace("_climate", "").lower()
                try:
                    with open(mock_path, "r", encoding="utf-8") as f:
                        self._mock_profiles[key] = json.load(f)
                except Exception:
                    pass

        locations_path = self.data_dir / "climate" / "locations.json"
        if locations_path.exists():
            try:
                with open(locations_path, "r", encoding="utf-8") as f:
                    self._locations = json.load(f)
            except Exception:
                pass

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    def _find_closest_dataset(self, latitude: float, longitude: float) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
        """Finds closest mock profile or location record."""
        # Check mock profiles first
        best_mock_key = None
        best_mock_dist = float("inf")
        for key, data in self._mock_profiles.items():
            loc = data.get("location", {})
            m_lat = loc.get("latitude")
            m_lon = loc.get("longitude")
            if m_lat is not None and m_lon is not None:
                dist = self._haversine(latitude, longitude, m_lat, m_lon)
                if dist < best_mock_dist:
                    best_mock_dist = dist
                    best_mock_key = key

        # If mock is within 150 km, use it
        if best_mock_key and best_mock_dist <= 150.0:
            return best_mock_key, self._mock_profiles[best_mock_key], best_mock_dist

        # Check locations.json
        best_loc = None
        best_loc_dist = float("inf")
        for loc in self._locations:
            l_lat = loc.get("latitude")
            l_lon = loc.get("longitude")
            if l_lat is not None and l_lon is not None:
                dist = self._haversine(latitude, longitude, l_lat, l_lon)
                if dist < best_loc_dist:
                    best_loc_dist = dist
                    best_loc = loc

        if best_loc:
            # Check if this location has an exact mock counterpart
            loc_id = best_loc.get("id", "").lower()
            if loc_id in self._mock_profiles:
                return loc_id, self._mock_profiles[loc_id], best_loc_dist
            return loc_id, {"_location_only": best_loc}, best_loc_dist

        # Ultimate fallback to Leh benchmark if absolutely nothing is found
        if "leh" in self._mock_profiles:
            return "leh", self._mock_profiles["leh"], 9999.0
        return None, None, float("inf")

    def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        key, data, dist = self._find_closest_dataset(latitude, longitude)
        if data and "current_weather" in data:
            cw = data["current_weather"]
            return CurrentWeather(
                temperature=cw.get("temperature", 15.0),
                relative_humidity=cw.get("relative_humidity", 50.0),
                wind_speed=cw.get("wind_speed", 3.0),
                wind_direction=cw.get("wind_direction", 180.0),
                solar_irradiance=cw.get("solar_irradiance", 450.0),
                timestamp=cw.get("timestamp"),
                is_observed=False,
                source=f"Local Fallback ({key.title() if key else 'Default'} Benchmark, {dist:.1f}km)"
            )

        # Baseline fallback
        return CurrentWeather(
            temperature=18.0,
            relative_humidity=50.0,
            wind_speed=3.0,
            wind_direction=180.0,
            solar_irradiance=500.0,
            is_observed=False,
            source="Local Fallback Generic Climatological Estimate"
        )

    def get_historical_climate(
        self, latitude: float, longitude: float
    ) -> Tuple[TemperatureProfile, WindData, HumidityData, DesignExtremes, DataQuality]:
        key, data, dist = self._find_closest_dataset(latitude, longitude)

        # If we have a full mock profile (Leh, Jaisalmer, Chennai)
        if data and "climate" in data:
            c = data["climate"]
            w = data.get("wind", {})
            h = data.get("humidity", {})
            d = data.get("design_extremes", {})
            q = data.get("data_quality", {})

            temp_profile = TemperatureProfile(
                annual_mean_temperature=c["annual_mean_temperature"],
                minimum_temperature=c["minimum_temperature"],
                maximum_temperature=c["maximum_temperature"],
                diurnal_range_mean=c.get("diurnal_range_mean", 12.0),
                monthly_temperatures=c.get("monthly_temperatures"),
                temperature_profile=c.get("temperature_profile", {}),
                source=data.get("location", {}).get("source", "Local Climatological Table"),
                provenance=DataProvenance.HISTORICAL
            )

            wind_data = WindData(
                average_speed=w.get("average_speed", 3.5),
                prevailing_direction=w.get("prevailing_direction", "NW"),
                seasonal_profile=w.get("seasonal_profile", {}),
                source=w.get("source", "IMD Local Records"),
                provenance=DataProvenance.HISTORICAL
            )

            humidity_data = HumidityData(
                average_relative_humidity=h.get("average_relative_humidity", 50.0),
                min_relative_humidity=h.get("min_relative_humidity", 30.0),
                max_relative_humidity=h.get("max_relative_humidity", 70.0),
                seasonal_profile=h.get("seasonal_profile", {}),
                source=h.get("source", "IMD Local Records"),
                provenance=DataProvenance.HISTORICAL
            )

            design_extremes = DesignExtremes(
                cold_extreme=d.get("cold_extreme", -10.0),
                hot_extreme=d.get("hot_extreme", 35.0),
                heating_degree_days_18c=d.get("heating_degree_days_18c", 2000.0),
                cooling_degree_days_18c=d.get("cooling_degree_days_18c", 1000.0),
                relevant_design_values=d.get("relevant_design_values", {})
            )

            data_quality = DataQuality(
                confidence=DataConfidence.HIGH if dist <= 50.0 else DataConfidence.MEDIUM,
                provenance=DataProvenance.HISTORICAL,
                sources=q.get("sources", ["Local Climatological Normals"]),
                notes=f"Loaded from offline benchmark dataset ({key.title() if key else 'Generic'}, distance {dist:.1f} km)."
            )

            return temp_profile, wind_data, humidity_data, design_extremes, data_quality

        # If we matched a record in locations.json that isn't one of the 3 primary mock files
        if data and "_location_only" in data:
            loc = data["_location_only"]
            w_min = loc.get("design_winter_temp_c", 5.0)
            s_max = loc.get("design_summer_temp_c", 35.0)
            mean_temp = (w_min + s_max) / 2.0

            temp_profile = TemperatureProfile(
                annual_mean_temperature=round(mean_temp, 1),
                minimum_temperature=w_min - 5.0,
                maximum_temperature=s_max + 3.0,
                diurnal_range_mean=12.0,
                source=loc.get("source", "locations.json"),
                provenance=DataProvenance.ESTIMATED
            )

            wind_data = WindData(
                average_speed=3.5,
                prevailing_direction="NW",
                source="Regional Estimation",
                provenance=DataProvenance.ESTIMATED
            )

            humidity_data = HumidityData(
                average_relative_humidity=50.0,
                min_relative_humidity=30.0,
                max_relative_humidity=70.0,
                source="Regional Estimation",
                provenance=DataProvenance.ESTIMATED
            )

            design_extremes = DesignExtremes(
                cold_extreme=w_min,
                hot_extreme=s_max,
                heating_degree_days_18c=loc.get("heating_degree_days_18c", 1500.0),
                cooling_degree_days_18c=loc.get("cooling_degree_days_18c", 1500.0),
                relevant_design_values={"notes": loc.get("notes", "")}
            )

            data_quality = DataQuality(
                confidence=DataConfidence.MEDIUM,
                provenance=DataProvenance.ESTIMATED,
                sources=[loc.get("source", "locations.json")],
                notes=f"Synthesized from regional location entry '{loc.get('name')}' (distance {dist:.1f} km)."
            )

            return temp_profile, wind_data, humidity_data, design_extremes, data_quality

        raise RuntimeError(f"Unable to resolve offline climate for coordinates ({latitude}, {longitude})")

    def get_solar_data(self, latitude: float, longitude: float) -> SolarData:
        key, data, dist = self._find_closest_dataset(latitude, longitude)
        if data and "solar" in data:
            s = data["solar"]
            return SolarData(
                GHI=s.get("GHI", 220.0),
                DNI=s.get("DNI", 260.0),
                DHI=s.get("DHI", 75.0),
                annual_solar_ghi_kwh_m2=s.get("annual_solar_ghi_kwh_m2", 2000.0),
                peak_sun_hours_day=s.get("peak_sun_hours_day", 5.5),
                unit=s.get("unit", "W/m²"),
                temporal_resolution=s.get("temporal_resolution", "annual_mean_flux"),
                source=s.get("source", "Local Climatological Table"),
                provenance=DataProvenance.HISTORICAL
            )

        if data and "_location_only" in data:
            loc = data["_location_only"]
            annual_kwh = loc.get("annual_solar_ghi_kwh_m2", 1950.0)
            ghi_flux = round((annual_kwh * 1000.0) / 8760.0, 1)
            return SolarData(
                GHI=ghi_flux,
                DNI=round(ghi_flux * 1.25, 1),
                DHI=round(ghi_flux * 0.30, 1),
                annual_solar_ghi_kwh_m2=annual_kwh,
                peak_sun_hours_day=round(annual_kwh / 365.0, 2),
                unit="W/m²",
                temporal_resolution="annual_mean_flux",
                source=loc.get("source", "locations.json"),
                provenance=DataProvenance.ESTIMATED
            )

        # Baseline fallback
        return SolarData(
            GHI=220.0,
            DNI=260.0,
            DHI=70.0,
            annual_solar_ghi_kwh_m2=1927.0,
            peak_sun_hours_day=5.28,
            unit="W/m²",
            temporal_resolution="annual_mean_flux",
            source="Offline Default Solar Model",
            provenance=DataProvenance.ESTIMATED
        )

    def is_available(self) -> bool:
        return True


class OpenMeteoWeatherProvider(BaseWeatherProvider):
    """
    Live external provider using Open-Meteo's open-access meteorological API.
    Zero-configuration, requires no vendor API keys.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, timeout_seconds: float = 3.5):
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        try:
            # Fast ping with 1s timeout
            r = requests.get(
                self.FORECAST_URL,
                params={"latitude": 34.15, "longitude": 77.58, "current": "temperature_2m"},
                timeout=1.2
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "direct_normal_irradiance",
                "diffuse_radiation",
                "shortwave_radiation"
            ],
            "wind_speed_unit": "ms"
        }
        resp = requests.get(self.FORECAST_URL, params=params, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})

        # Compute total solar irradiance if shortwave radiation is provided
        solar = current.get("shortwave_radiation")
        if solar is None:
            dni = current.get("direct_normal_irradiance") or 0.0
            dhi = current.get("diffuse_radiation") or 0.0
            solar = dni + dhi

        return CurrentWeather(
            temperature=float(current.get("temperature_2m", 20.0)),
            relative_humidity=float(current.get("relative_humidity_2m", 50.0)),
            wind_speed=max(0.0, float(current.get("wind_speed_10m", 3.0))),
            wind_direction=current.get("wind_direction_10m"),
            solar_irradiance=max(0.0, float(solar)) if solar is not None else None,
            timestamp=current.get("time"),
            is_observed=True,
            source="Open-Meteo Live Forecast API"
        )

    # ------------------------------------------------------------------
    # HOURLY TIMESERIES (Phase B)
    # ------------------------------------------------------------------

    _HOURLY_VARIABLES = [
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "wind_direction_10m",
        "precipitation",
        "cloud_cover",
        "shortwave_radiation",
        "direct_normal_irradiance",
        "diffuse_radiation",
    ]

    def get_hourly_forecast(
        self, latitude: float, longitude: float, hours: int = 168, include_past: bool = False
    ) -> HourlyWeatherSeries:
        """
        Retrieves an hourly forecast timeseries (numerical weather prediction).
        Default horizon is 168 hours from the current hour (Open-Meteo
        forecast_hours), matching the simulation's 7-day horizon. With
        include_past=True the window ends at the current hour (past_hours)
        for a live/nowcast scenario, and the series is labelled LIVE (never
        presented as a future forecast).
        """
        params: Dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": self._HOURLY_VARIABLES,
            "wind_speed_unit": "ms",
            "timezone": "auto",
            "forecast_hours": max(1, min(int(hours), 384)),
        }
        if include_past:
            params.pop("forecast_hours", None)
            params["past_hours"] = max(1, min(int(hours), 168))

        try:
            resp = requests.get(self.FORECAST_URL, params=params, timeout=self.timeout_seconds)
        except requests.Timeout as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_TIMEOUT,
                f"Open-Meteo forecast request timed out after {self.timeout_seconds}s",
            ) from exc
        except requests.RequestException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code == 429:
                raise ClimateServiceError(
                    ClimateErrorCategory.PROVIDER_RATE_LIMIT,
                    "Open-Meteo rate limit reached (HTTP 429)",
                ) from exc
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_ERROR,
                f"Open-Meteo forecast request failed: {exc}",
            ) from exc

        if resp.status_code == 429:
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_RATE_LIMIT,
                "Open-Meteo rate limit reached (HTTP 429)",
            )
        if resp.status_code != 200:
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_ERROR,
                f"Open-Meteo forecast returned HTTP {resp.status_code}",
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.MALFORMED_RESPONSE,
                "Open-Meteo forecast returned a non-JSON payload",
            ) from exc

        if data.get("error"):
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_ERROR,
                f"Open-Meteo forecast error: {data.get('reason', 'unknown')}",
            )

        return self._parse_hourly_payload(
            data,
            latitude=latitude,
            longitude=longitude,
            mode=(WeatherDataMode.LIVE if include_past else WeatherDataMode.FORECAST),
            provenance=(
                DataProvenance.MODEL_ANALYSIS if include_past else DataProvenance.FORECAST
            ),
            provider_label=(
                "Open-Meteo Recent Conditions (NWP analysis, ending now)"
                if include_past
                else "Open-Meteo Forecast (NWP model ensemble)"
            ),
            requested_hours=(int(hours) if include_past else None),
        )

    def get_hourly_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        hours: int = 168,
    ) -> HourlyWeatherSeries:
        """
        Retrieves an hourly HISTORICAL reanalysis timeseries (ERA5, ~25 km grid).
        Reanalysis data is model-derived - it is neither an on-site measurement
        nor a design climate, and is labelled accordingly.
        """
        if end_date is None:
            end_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        if start_date is None:
            start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=max(1, (int(hours) + 23) // 24) - 1)
            start_date = start_dt.strftime("%Y-%m-%d")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": self._HOURLY_VARIABLES,
            "wind_speed_unit": "ms",
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date,
        }
        try:
            resp = requests.get(self.ARCHIVE_URL, params=params, timeout=self.timeout_seconds)
        except requests.Timeout as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_TIMEOUT,
                f"Open-Meteo archive request timed out after {self.timeout_seconds}s",
            ) from exc
        except requests.RequestException as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_ERROR,
                f"Open-Meteo archive request failed: {exc}",
            ) from exc

        if resp.status_code != 200:
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_ERROR,
                f"Open-Meteo archive returned HTTP {resp.status_code}",
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.MALFORMED_RESPONSE,
                "Open-Meteo archive returned a non-JSON payload",
            ) from exc

        if data.get("error"):
            raise ClimateServiceError(
                ClimateErrorCategory.PROVIDER_ERROR,
                f"Open-Meteo archive error: {data.get('reason', 'unknown')}",
            )

        return self._parse_hourly_payload(
            data,
            latitude=latitude,
            longitude=longitude,
            mode=WeatherDataMode.HISTORICAL,
            provenance=DataProvenance.HISTORICAL_REANALYSIS,
            provider_label="Open-Meteo Historical Reanalysis (ERA5)",
            requested_hours=None,
        )

    def get_elevation(self, latitude: float, longitude: float) -> float:
        """
        Provider-backed elevation from the Open-Meteo Elevation API
        (Copernicus DEM GLO-90, ~90 m resolution). This is a gridded DEM
        estimate, not survey-grade accuracy.
        """
        try:
            resp = requests.get(
                "https://api.open-meteo.com/v1/elevation",
                params={"latitude": latitude, "longitude": longitude},
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.ELEVATION_FAILURE,
                f"Open-Meteo elevation request timed out after {self.timeout_seconds}s",
            ) from exc
        except requests.RequestException as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.ELEVATION_FAILURE,
                f"Open-Meteo elevation request failed: {exc}",
            ) from exc

        if resp.status_code != 200:
            raise ClimateServiceError(
                ClimateErrorCategory.ELEVATION_FAILURE,
                f"Open-Meteo elevation returned HTTP {resp.status_code}",
            )
        try:
            data = resp.json()
            elevation_values = data.get("elevation")
            if not isinstance(elevation_values, list) or not elevation_values:
                raise ValueError("missing 'elevation' array")
            return float(elevation_values[0])
        except (ValueError, TypeError, KeyError) as exc:
            raise ClimateServiceError(
                ClimateErrorCategory.MALFORMED_RESPONSE,
                f"Open-Meteo elevation payload malformed: {exc}",
            ) from exc

    def _parse_hourly_payload(
        self,
        data: Dict[str, Any],
        latitude: float,
        longitude: float,
        mode: WeatherDataMode,
        provenance: DataProvenance,
        provider_label: str,
        requested_hours: Optional[int] = None,
    ) -> HourlyWeatherSeries:
        """
        Validates an Open-Meteo hourly payload and maps it into the canonical
        HourlyWeatherSeries contract. Required fields are enforced; optional
        fields are carried only when actually present. No substitution, no
        synthetic interpolation.
        """
        hourly = data.get("hourly")
        if not isinstance(hourly, dict):
            raise ClimateServiceError(
                ClimateErrorCategory.MALFORMED_RESPONSE,
                "Open-Meteo payload missing 'hourly' object",
            )

        timestamps = hourly.get("time")
        temps = hourly.get("temperature_2m")
        if not isinstance(timestamps, list) or not timestamps:
            raise ClimateServiceError(
                ClimateErrorCategory.MALFORMED_RESPONSE,
                "Open-Meteo payload missing hourly 'time' array",
            )
        if not isinstance(temps, list) or len(temps) != len(timestamps):
            raise ClimateServiceError(
                ClimateErrorCategory.MALFORMED_RESPONSE,
                "Open-Meteo payload temperature array missing or misaligned",
            )
        # Open-Meteo pads the response tail with nulls beyond the usable model
        # horizon (notably solar variables when past_hours is requested). A pure
        # trailing-null suffix is trimmed to the usable window; interior nulls
        # are a genuine data gap and are rejected, never substituted.
        null_idx = [i for i, t in enumerate(temps) if t is None]
        if null_idx:
            first, last = null_idx[0], null_idx[-1]
            if last != len(temps) - 1 or (last - first + 1) != len(null_idx):
                raise ClimateServiceError(
                    ClimateErrorCategory.DATA_UNAVAILABLE,
                    "Open-Meteo hourly temperature series contains interior null values",
                )
            temps = temps[: first]
        timestamps = timestamps[: len(temps)]
        trimmed = len(null_idx) > 0
        for _k, _v in hourly.items():
            if isinstance(_v, list) and len(_v) > len(timestamps):
                hourly[_k] = _v[: len(timestamps)]
        # Honour the requested window length: with past_hours the provider
        # returns the full remaining horizon, so slice to the requested count
        # (taking the most recent hours). Forward forecasts already match.
        if requested_hours is not None and len(timestamps) > requested_hours:
            take = int(requested_hours)
            for _k, _v in hourly.items():
                if isinstance(_v, list) and len(_v) > take:
                    hourly[_k] = _v[-take:]
            timestamps = timestamps[-take:]
            temps = temps[-take:]
            trimmed = True

        def _opt(key: str) -> Optional[List[float]]:
            arr = hourly.get(key)
            if not isinstance(arr, list) or any(v is None for v in arr):
                return None  # omit rather than substitute
            return [float(v) for v in arr]

        series = HourlyWeatherSeries(
            latitude=float(latitude),
            longitude=float(longitude),
            elevation_m=(float(data["elevation"]) if data.get("elevation") is not None else None),
            timezone=data.get("timezone"),
            timestamps=[str(t) for t in timestamps],
            air_temperature_C=[float(t) for t in temps],
            relative_humidity_percent=_opt("relative_humidity_2m"),
            wind_speed_mps=_opt("wind_speed_10m"),
            wind_direction_deg=_opt("wind_direction_10m"),
            precipitation_mm=_opt("precipitation"),
            cloud_cover_percent=_opt("cloud_cover"),
            solar_global_W_m2=_opt("shortwave_radiation"),
            solar_direct_W_m2=_opt("direct_normal_irradiance"),
            solar_diffuse_W_m2=_opt("diffuse_radiation"),
            data_mode=mode,
            provenance=provenance,
            provider=provider_label,
            retrieval_timestamp=datetime.utcnow().isoformat() + "Z",
            period_start=str(timestamps[0]),
            period_end=str(timestamps[-1]),
            fallback_used=False,
            notes=(
                "Window trimmed to %d usable hours; provider response extended "
                "beyond the available model horizon with nulls." % len(timestamps)
            )
            if trimmed
            else "",
        )
        logger.info(
            "Open-Meteo hourly series resolved: mode=%s hours=%d lat=%.4f lon=%.4f tz=%s",
            mode.value, len(series.timestamps), latitude, longitude, series.timezone,
        )
        return series

    def get_historical_climate(
        self, latitude: float, longitude: float
    ) -> Tuple[TemperatureProfile, WindData, HumidityData, DesignExtremes, DataQuality]:
        """
        Queries statistical climate variables or historical archive.
        Falls back to daily aggregations from Open-Meteo.
        """
        # Query 14-day daily forecast statistics as a proxy for live seasonal assessment
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "wind_speed_10m_max",
                "relative_humidity_2m_mean"
            ],
            "forecast_days": 14,
            "wind_speed_unit": "ms"
        }
        resp = requests.get(self.FORECAST_URL, params=params, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})

        t_means = daily.get("temperature_2m_mean", [20.0])
        t_mins = daily.get("temperature_2m_min", [10.0])
        t_maxs = daily.get("temperature_2m_max", [30.0])
        w_speeds = daily.get("wind_speed_10m_max", [4.0])
        rh_means = daily.get("relative_humidity_2m_mean", [50.0])

        annual_mean = float(sum(t_means) / len(t_means))
        observed_min = float(min(t_mins))
        observed_max = float(max(t_maxs))
        avg_wind = float(sum(w_speeds) / len(w_speeds))
        avg_rh = float(sum(rh_means) / len(rh_means))

        # Extrapolate engineering design extremes with safety margins
        cold_extreme = round(observed_min - 3.0, 1)
        hot_extreme = round(observed_max + 3.0, 1)

        # Approximate degree days
        hdd = max(0.0, (18.0 - annual_mean) * 365.0) if annual_mean < 18.0 else 0.0
        cdd = max(0.0, (annual_mean - 18.0) * 365.0) if annual_mean > 18.0 else 0.0

        temp_profile = TemperatureProfile(
            annual_mean_temperature=round(annual_mean, 1),
            minimum_temperature=round(observed_min, 1),
            maximum_temperature=round(observed_max, 1),
            diurnal_range_mean=round(observed_max - observed_min, 1),
            source="Open-Meteo Aggregated Meteorological Service",
            provenance=DataProvenance.MEASURED
        )

        wind_data = WindData(
            average_speed=round(avg_wind, 2),
            prevailing_direction="Variable",
            source="Open-Meteo Global Numerical Weather Model",
            provenance=DataProvenance.MEASURED
        )

        humidity_data = HumidityData(
            average_relative_humidity=round(avg_rh, 1),
            min_relative_humidity=max(0.0, round(avg_rh - 20.0, 1)),
            max_relative_humidity=min(100.0, round(avg_rh + 20.0, 1)),
            source="Open-Meteo Global Numerical Weather Model",
            provenance=DataProvenance.MEASURED
        )

        design_extremes = DesignExtremes(
            cold_extreme=cold_extreme,
            hot_extreme=hot_extreme,
            heating_degree_days_18c=round(hdd, 1),
            cooling_degree_days_18c=round(cdd, 1)
        )

        data_quality = DataQuality(
            confidence=DataConfidence.HIGH,
            provenance=DataProvenance.MEASURED,
            sources=["Open-Meteo Global Numerical Weather Prediction (ECMWF/GFS)"],
            notes="Derived from live external numerical forecast model."
        )

        return temp_profile, wind_data, humidity_data, design_extremes, data_quality

    def get_solar_data(self, latitude: float, longitude: float) -> SolarData:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["shortwave_radiation_sum"],
            "forecast_days": 7
        }
        resp = requests.get(self.FORECAST_URL, params=params, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        # shortwave_radiation_sum is in MJ/m²
        radiation_mj = daily.get("shortwave_radiation_sum", [18.0])
        avg_mj_day = sum(radiation_mj) / len(radiation_mj)

        # 1 MJ/m² = 1,000,000 J/m² / 3600 = 277.78 Wh/m² = 0.2778 kWh/m²
        avg_kwh_m2_day = avg_mj_day * 0.27778
        annual_kwh_m2 = avg_kwh_m2_day * 365.0
        # Instantaneous mean flux across 24h:
        mean_flux_w_m2 = (annual_kwh_m2 * 1000.0) / 8760.0

        return SolarData(
            GHI=round(mean_flux_w_m2, 1),
            DNI=round(mean_flux_w_m2 * 1.3, 1),
            DHI=round(mean_flux_w_m2 * 0.35, 1),
            annual_solar_ghi_kwh_m2=round(annual_kwh_m2, 1),
            peak_sun_hours_day=round(avg_kwh_m2_day, 2),
            unit="W/m²",
            temporal_resolution="annual_mean_flux",
            source="Open-Meteo Solar Radiation Model",
            provenance=DataProvenance.MEASURED
        )


class CompositeWeatherProvider(BaseWeatherProvider):
    """
    Hierarchical provider combining external API, cache, and local fallback.
    Gracefully handles network drops, timeouts, and rate limits.
    """

    def __init__(
        self,
        enable_online: bool = True,
        cache: Optional[ClimateCache] = None,
        data_dir: Optional[Union[str, Path]] = None,
        timeout_seconds: float = 3.0
    ):
        self.enable_online = enable_online
        self.cache = cache or ClimateCache()
        self.fallback = LocalFallbackWeatherProvider(data_dir=data_dir)
        self.external = OpenMeteoWeatherProvider(timeout_seconds=timeout_seconds)

    def is_available(self) -> bool:
        return True

    def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        cache_key = self.cache.generate_key("curr_weather", latitude, longitude)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.enable_online:
            try:
                result = self.external.get_current_weather(latitude, longitude)
                self.cache.set(cache_key, result, ttl_seconds=1800.0)  # 30 min cache
                return result
            except Exception:
                # External API failed or offline; fall through to local fallback
                pass

        # Offline / Fallback
        result = self.fallback.get_current_weather(latitude, longitude)
        self.cache.set(cache_key, result, ttl_seconds=3600.0)
        return result

    def get_historical_climate(
        self, latitude: float, longitude: float
    ) -> Tuple[TemperatureProfile, WindData, HumidityData, DesignExtremes, DataQuality]:
        cache_key = self.cache.generate_key("hist_climate", latitude, longitude)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # For historical climate, prefer local station records (locations.json / mock benchmarks)
        # if the site is a known benchmark station (e.g. Leh, Jaisalmer, Chennai).
        # Otherwise, query external or local fallback.
        try:
            # Check if coordinates match a known high-fidelity local station closely
            key, data, dist = self.fallback._find_closest_dataset(latitude, longitude)
            if dist <= 35.0 and data and "climate" in data:
                result = self.fallback.get_historical_climate(latitude, longitude)
                self.cache.set(cache_key, result, ttl_seconds=86400.0)
                return result
        except Exception:
            pass

        if self.enable_online:
            try:
                result = self.external.get_historical_climate(latitude, longitude)
                self.cache.set(cache_key, result, ttl_seconds=86400.0)
                return result
            except Exception:
                pass

        result = self.fallback.get_historical_climate(latitude, longitude)
        self.cache.set(cache_key, result, ttl_seconds=86400.0)
        return result

    def get_solar_data(self, latitude: float, longitude: float) -> SolarData:
        cache_key = self.cache.generate_key("solar_data", latitude, longitude)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            key, data, dist = self.fallback._find_closest_dataset(latitude, longitude)
            if dist <= 35.0 and data and "solar" in data:
                result = self.fallback.get_solar_data(latitude, longitude)
                self.cache.set(cache_key, result, ttl_seconds=86400.0)
                return result
        except Exception:
            pass

        if self.enable_online:
            try:
                result = self.external.get_solar_data(latitude, longitude)
                self.cache.set(cache_key, result, ttl_seconds=86400.0)
                return result
            except Exception:
                pass

        result = self.fallback.get_solar_data(latitude, longitude)
        self.cache.set(cache_key, result, ttl_seconds=86400.0)
        return result


    # ------------------------------------------------------------------
    # HOURLY TIMESERIES + ELEVATION HIERARCHY (Phase B)
    # live provider -> cached valid data -> bundled design fallback -> error
    # ------------------------------------------------------------------

    def get_hourly_forecast(
        self, latitude: float, longitude: float, hours: int = 168, include_past: bool = False
    ) -> HourlyWeatherSeries:
        mode_key = "past" if include_past else "fwd"
        cache_key = self.cache.generate_key("hourly_forecast", latitude, longitude, hours=hours, window=mode_key)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.enable_online:
            try:
                result = self.external.get_hourly_forecast(latitude, longitude, hours=hours, include_past=include_past)
                # Forecast models refresh continuously; keep a short TTL.
                self.cache.set(cache_key, result, ttl_seconds=1800.0)
                return result
            except ClimateServiceError as exc:
                logger.warning("Hourly forecast provider failed (%s); falling back", exc.category.value)
            except Exception as exc:  # defensive: never let provider bugs crash the route
                logger.warning("Unexpected hourly forecast failure: %s", exc)

        result = self._fallback_hourly_series(latitude, longitude, hours, requested_mode="forecast")
        self.cache.set(cache_key, result, ttl_seconds=600.0)
        return result

    def get_hourly_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        hours: int = 168,
    ) -> HourlyWeatherSeries:
        cache_key = self.cache.generate_key(
            "hourly_archive", latitude, longitude, start=start_date or "auto", end=end_date or "auto"
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.enable_online:
            try:
                result = self.external.get_hourly_archive(
                    latitude, longitude, start_date=start_date, end_date=end_date, hours=hours
                )
                # Reanalysis archives are immutable; cache for a full day.
                self.cache.set(cache_key, result, ttl_seconds=86400.0)
                return result
            except ClimateServiceError as exc:
                logger.warning("Hourly archive provider failed (%s); falling back", exc.category.value)
            except Exception as exc:
                logger.warning("Unexpected hourly archive failure: %s", exc)

        result = self._fallback_hourly_series(latitude, longitude, hours, requested_mode="historical")
        self.cache.set(cache_key, result, ttl_seconds=600.0)
        return result

    def get_elevation(self, latitude: float, longitude: float) -> Optional[float]:
        """
        Provider-backed elevation (Copernicus DEM GLO-90 via Open-Meteo).
        Falls back to the nearest bundled benchmark station's elevation when
        the DEM service is unreachable; the estimate is then labelled as such.
        Returns None only when neither source can supply a value.
        """
        cache_key = self.cache.generate_key("elevation", latitude, longitude)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.enable_online:
            try:
                elevation = self.external.get_elevation(latitude, longitude)
                self.cache.set(cache_key, elevation, ttl_seconds=86400.0)
                return elevation
            except ClimateServiceError as exc:
                logger.warning("Elevation provider failed (%s); using station fallback", exc.category.value)
            except Exception as exc:
                logger.warning("Unexpected elevation failure: %s", exc)

        # Nearest bundled benchmark station elevation (documented estimate).
        try:
            key, _data, dist = self.fallback._find_closest_dataset(latitude, longitude)
            if key and dist < 150.0:
                for loc in getattr(self.fallback, "_locations", []):
                    if loc.get("id", "").lower() == key:
                        altitude = loc.get("altitude")
                        if altitude is not None:
                            self.cache.set(cache_key, float(altitude), ttl_seconds=86400.0)
                            return float(altitude)
        except Exception:
            pass
        return None

    def get_design_climate(
        self, latitude: float, longitude: float, hours: int = 168
    ) -> HourlyWeatherSeries:
        """
        Returns the DESIGN-mode hourly series from the nearest bundled EPW
        benchmark station. This is explicitly-requested design-year data
        (not a fallback for failed live calls, hence mode=DESIGN), labelled
        with the source station and its distance from the requested site.
        """
        return self._bundled_epw_series(latitude, longitude, hours, mode=WeatherDataMode.DESIGN)

    def _fallback_hourly_series(
        self, latitude: float, longitude: float, hours: int, requested_mode: str
    ) -> HourlyWeatherSeries:
        """FALLBACK variant of the bundled EPW series (provider failure path)."""
        return self._bundled_epw_series(latitude, longitude, hours, mode=WeatherDataMode.FALLBACK)

    def _bundled_epw_series(
        self, latitude: float, longitude: float, hours: int, mode: WeatherDataMode
    ) -> HourlyWeatherSeries:
        """
        Builds a clearly-labelled hourly series from the bundled EPW
        design-climate dataset of the nearest benchmark station. This is real
        design-year data - never presented as live weather.
        """
        from services.climate_service import get_climate_data  # lazy import, no cycle

        try:
            key, _data, dist = self.fallback._find_closest_dataset(latitude, longitude)
        except Exception:
            key, dist = "leh", 9999.0
        station = key or "leh"

        weather = get_climate_data(station)
        if "error" in weather or not weather.get("hourly_temperature"):
            raise ClimateServiceError(
                ClimateErrorCategory.DATA_UNAVAILABLE,
                f"No weather data available for coordinates ({latitude}, {longitude}) "
                "and no bundled fallback dataset could be loaded",
            )

        n = max(1, min(int(hours), len(weather["hourly_temperature"])))
        # Nominal design-year timestamps (Jan 1..7); documented as nominal.
        timestamps = [
            (datetime(2001, 1, 1) + timedelta(hours=i)).isoformat() for i in range(n)
        ]

        def _slice(arr: Optional[List[Any]]) -> Optional[List[float]]:
            if not arr or len(arr) < n:
                return None
            return [float(v) for v in arr[:n]]

        is_fallback = mode == WeatherDataMode.FALLBACK
        provider = (
            f"Bundled EPW design climate ({station.upper()})"
            if not is_fallback
            else f"Bundled EPW design climate ({station.upper()}) [provider fallback]"
        )
        series = HourlyWeatherSeries(
            latitude=float(latitude),
            longitude=float(longitude),
            elevation_m=None,
            timezone="Asia/Kolkata",
            timestamps=timestamps,
            air_temperature_C=[float(t) for t in weather["hourly_temperature"][:n]],
            relative_humidity_percent=_slice(weather.get("hourly_humidity")),
            wind_speed_mps=_slice(weather.get("hourly_wind_speed")),
            solar_direct_W_m2=_slice(weather.get("hourly_direct_solar")),
            solar_diffuse_W_m2=_slice(weather.get("hourly_diffuse_solar")),
            data_mode=mode,
            provenance=DataProvenance.ESTIMATED if is_fallback else DataProvenance.HISTORICAL,
            provider=provider,
            retrieval_timestamp=datetime.utcnow().isoformat() + "Z",
            period_start=timestamps[0],
            period_end=timestamps[-1],
            fallback_used=is_fallback,
            notes=(
                (
                    f"Live provider unavailable for requested series; serving the bundled "
                    f"{station.upper()} EPW design-climate year (nearest benchmark, "
                    f"{dist:.0f} km). Timestamps are nominal design-year values, NOT the "
                    f"requested period. Treat as DESIGN/FALLBACK, not live weather."
                )
                if is_fallback
                else (
                    f"Bundled {station.upper()} EPW design-climate year (nearest benchmark, "
                    f"{dist:.0f} km from requested site). Timestamps are nominal design-year "
                    f"values. Suitable for design studies, not live conditions."
                )
            ),
        )
        logger.info(
            "Bundled EPW series served: mode=%s station=%s dist=%.0fkm hours=%d",
            mode.value, station, dist, n,
        )
        return series
