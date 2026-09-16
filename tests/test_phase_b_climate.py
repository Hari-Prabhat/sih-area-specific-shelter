"""
THERMOSHELTER - Phase B Climate & Location Intelligence Tests
=============================================================
Covers the Phase B additions WITHOUT any mandatory external network calls:

  1. LocationResolver: coordinates / strings / invalid rejection
  2. WeatherProvider: mocked Open-Meteo responses (valid, timeout,
     rate-limit, malformed), trailing-null trimming, live labelling
  3. Fallback hierarchy: provider failure -> clearly-labelled FALLBACK
  4. ClimateNormalizer: real arrays pass through 1:1, provenance mapping,
     missing solar rejected explicitly (never fabricated)
  5. 168-hour mapping: exact lengths, aligned arrays
  6. Climate -> simulation bridge over the real FastAPI routes
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from backend.climate.errors import ClimateErrorCategory, ClimateServiceError
from backend.climate.schemas import HourlyWeatherSeries, Location, WeatherDataMode
from backend.climate.climate_cache import ClimateCache
from backend.climate.service import ClimateService
from backend.climate.timeseries_normalizer import hourly_series_to_climate_profile
from backend.climate.weather_provider import CompositeWeatherProvider

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _openmeteo_payload(n_hours=24, start="2026-07-01T00:00", nulls_tail=0, interior_null=False):
    """Synthetic valid Open-Meteo forecast payload (SI-consistent)."""
    t0 = datetime.fromisoformat(start)
    times = [(t0 + timedelta(hours=i)).isoformat() for i in range(n_hours)]
    temp = [20.0 + (i % 24) * 0.5 for i in range(n_hours)]
    if nulls_tail:
        temp = temp[: n_hours - nulls_tail] + [None] * nulls_tail
    if interior_null:
        temp[5] = None

    def arr(base, amp=1.0):
        vals = [base + amp * (i % 12) / 12.0 for i in range(n_hours)]
        if nulls_tail:
            vals = vals[: n_hours - nulls_tail] + [None] * nulls_tail
        return vals

    return {
        "latitude": 28.6, "longitude": 77.2,
        "elevation": 216.0, "timezone": "Asia/Kolkata",
        "hourly": {
            "time": times,
            "temperature_2m": temp,
            "relative_humidity_2m": arr(55.0),
            "wind_speed_10m": arr(3.0),
            "wind_direction_10m": arr(270.0, 4.0),
            "precipitation": arr(0.1, 0.1),
            "cloud_cover": arr(40.0),
            "shortwave_radiation": arr(400.0),
            "direct_normal_irradiance": arr(500.0),
            "diffuse_radiation": arr(120.0),
        },
    }


def _http_ok(payload):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    return resp


def _http_status(status):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"error": True, "reason": "synthetic"}
    return resp


def _online_composite():
    """Composite with live provider enabled but a fresh, isolated cache."""
    return CompositeWeatherProvider(enable_online=True, cache=ClimateCache(default_ttl_seconds=60.0))


def _design_payload(hours=48):
    return {
        "length": 6.0, "width": 4.0, "height": 2.6, "roof_type": "pitched",
        "roof_angle": 15.0, "orientation": 180.0, "wall_thickness": 0.23,
        "window_area": 1.8, "window_glazing": "double", "door_area": 1.9,
        "insulation_type": "puf", "insulation_thickness": 0.05,
        "occupants": 4, "ach_ventilation": 1.0,
    }


# =====================================================================
# 1. LOCATION RESOLUTION
# =====================================================================

class TestLocationResolution(unittest.TestCase):
    def setUp(self):
        from backend.climate.location_resolver import LocationResolver
        self.resolver = LocationResolver()

    def test_coordinate_string_resolves(self):
        loc = self.resolver.resolve("34.1526, 77.5771")
        assert isinstance(loc, Location)
        assert loc.latitude == pytest.approx(34.1526, abs=1e-4)

    def test_tuple_coordinates_resolve(self):
        loc = self.resolver.resolve((26.9157, 70.9083))
        assert loc.latitude == pytest.approx(26.9157, abs=1e-4)

    def test_invalid_coordinates_rejected(self):
        with pytest.raises(Exception):
            self.resolver.resolve("999.0, 999.0")

    def test_out_of_range_latitude_rejected(self):
        with pytest.raises(Exception):
            self.resolver.resolve("95.0, 77.0")

    def test_unknown_place_clearly_invalid(self):
        with pytest.raises(Exception):
            self.resolver.resolve("zzz_not_a_real_place_xyz")

    def test_coordinate_string_search_returns_validated_candidate(self):
        res = self.resolver.search_locations("22.7196, 75.8577")
        assert len(res) == 1
        assert res[0].latitude == pytest.approx(22.7196, abs=1e-4)
        assert res[0].longitude == pytest.approx(75.8577, abs=1e-4)

    def test_name_search_still_works_after_coordinate_support(self):
        res = self.resolver.search_locations("jaisal")
        assert res and "Jaisalmer" in res[0].place_name


# =====================================================================
# 2. WEATHER PROVIDER (MOCKED OPEN-METEO)
# =====================================================================

class TestWeatherProviderMocked(unittest.TestCase):
    def _provider(self):
        p = _online_composite()
        return p, p.external

    def test_valid_forecast_payload(self):
        comp, _ = self._provider()
        with patch("backend.climate.weather_provider.requests.get", return_value=_http_ok(_openmeteo_payload())):
            series = comp.get_hourly_forecast(28.6, 77.2, hours=24)
        assert series.data_mode == WeatherDataMode.FORECAST
        assert len(series.air_temperature_C) == 24
        assert series.solar_direct_W_m2 is not None and len(series.solar_direct_W_m2) == 24
        assert series.provider.startswith("Open-Meteo")
        assert series.fallback_used is False
        assert series.elevation_m == pytest.approx(216.0)

    def test_timeout_raises_typed_error(self):
        import requests as _requests
        comp, _ = self._provider()
        with patch(
            "backend.climate.weather_provider.requests.get",
            side_effect=_requests.Timeout("boom"),
        ):
            with pytest.raises(ClimateServiceError) as exc:
                comp.external.get_hourly_forecast(28.6, 77.2, hours=24)
        assert exc.value.category == ClimateErrorCategory.PROVIDER_TIMEOUT

    def test_timeout_composite_falls_back_labelled(self):
        import requests as _requests
        comp, _ = self._provider()
        with patch(
            "backend.climate.weather_provider.requests.get",
            side_effect=_requests.Timeout("boom"),
        ):
            series = comp.get_hourly_forecast(28.6, 77.2, hours=24)
        assert series.data_mode == WeatherDataMode.FALLBACK
        assert series.fallback_used is True
        assert "not live" in (series.notes or "").lower() or "fallback" in (series.provider or "").lower()

    def test_rate_limit_mapped(self):
        comp, _ = self._provider()
        with patch(
            "backend.climate.weather_provider.requests.get",
            return_value=_http_status(429),
        ):
            with pytest.raises(ClimateServiceError) as exc:
                comp.external.get_hourly_forecast(28.6, 77.2, hours=24)
        assert exc.value.category == ClimateErrorCategory.PROVIDER_RATE_LIMIT

    def test_malformed_response_mapped(self):
        comp, _ = self._provider()
        with patch(
            "backend.climate.weather_provider.requests.get",
            return_value=_http_ok({"unexpected": "shape"}),
        ):
            with pytest.raises(ClimateServiceError) as exc:
                comp.external.get_hourly_forecast(28.6, 77.2, hours=24)
        assert exc.value.category == ClimateErrorCategory.MALFORMED_RESPONSE

    def test_trailing_nulls_trimmed_to_usable_window(self):
        comp, _ = self._provider()
        payload = _openmeteo_payload(n_hours=48, nulls_tail=20)
        with patch("backend.climate.weather_provider.requests.get", return_value=_http_ok(payload)):
            series = comp.get_hourly_forecast(28.6, 77.2, hours=24, include_past=True)
        # Trailing provider nulls are trimmed, never substituted
        assert all(v is not None for v in series.air_temperature_C)
        assert series.data_mode == WeatherDataMode.LIVE  # past window = live, never "forecast"
        assert "trim" in (series.notes or "").lower()

    def test_interior_nulls_rejected_not_substituted(self):
        comp, _ = self._provider()
        payload = _openmeteo_payload(n_hours=24, interior_null=True)
        with patch("backend.climate.weather_provider.requests.get", return_value=_http_ok(payload)):
            with pytest.raises(ClimateServiceError) as exc:
                comp.external.get_hourly_forecast(28.6, 77.2, hours=24)
        assert exc.value.category == ClimateErrorCategory.DATA_UNAVAILABLE


# =====================================================================
# 3. CLIMATE NORMALIZER -> CANONICAL PROFILE
# =====================================================================

class TestTimeseriesNormalizer(unittest.TestCase):
    def _series(self, mode=WeatherDataMode.FORECAST, solar=True):
        t0 = datetime(2026, 7, 1)
        n = 24
        return HourlyWeatherSeries(
            latitude=28.6, longitude=77.2, elevation_m=216.0, timezone="Asia/Kolkata",
            timestamps=[(t0 + timedelta(hours=i)).isoformat() for i in range(n)],
            air_temperature_C=[20.0 + 0.5 * i for i in range(n)],
            relative_humidity_percent=[55.0] * n,
            wind_speed_mps=[3.0] * n,
            solar_direct_W_m2=[500.0] * n if solar else None,
            solar_diffuse_W_m2=[120.0] * n if solar else None,
            data_mode=mode, provenance="MEASURED" if mode == WeatherDataMode.LIVE else "SIMULATED", provider="Test Provider",
            retrieval_timestamp="2026-09-16T00:00:00Z",
            period_start="2026-07-01T00:00:00", period_end="2026-07-01T23:00:00",
            fallback_used=False, notes="",
        )

    def test_real_arrays_pass_through_one_to_one(self):
        from services.contracts import ClimateProfile as Canonical
        series = self._series()
        profile = hourly_series_to_climate_profile(series, display_name="Test Site")
        assert isinstance(profile, Canonical)
        assert profile.hourly_temperature == series.air_temperature_C
        assert profile.hourly_direct_solar == series.solar_direct_W_m2
        assert profile.hourly_diffuse_solar == series.solar_diffuse_W_m2
        assert len(profile.timestamps) == 24
        assert profile.elevation_m == pytest.approx(216.0)

    def test_missing_solar_rejected_not_fabricated(self):
        series = self._series(solar=False)
        with pytest.raises(ClimateServiceError) as exc:
            hourly_series_to_climate_profile(series)
        assert exc.value.category == ClimateErrorCategory.DATA_UNAVAILABLE

    def test_fallback_mode_maps_to_estimated_provenance(self):
        from services.shelter.models import DataProvenance
        profile = hourly_series_to_climate_profile(self._series(mode=WeatherDataMode.FALLBACK))
        assert profile.data_provenance == DataProvenance.ESTIMATED

    def test_historical_mode_maps_to_historical_provenance(self):
        from services.shelter.models import DataProvenance
        profile = hourly_series_to_climate_profile(self._series(mode=WeatherDataMode.HISTORICAL))
        assert profile.data_provenance == DataProvenance.HISTORICAL


# =====================================================================
# 4. DESIGN MODE & 168-HOUR MAPPING
# =====================================================================

class TestDesignModeAndWindow(unittest.TestCase):
    def test_design_mode_explicitly_labelled(self):
        svc = ClimateService(enable_online=False)
        series = svc.get_hourly_weather("28.6, 77.2", mode="design", hours=168)
        assert series.data_mode == WeatherDataMode.DESIGN
        assert series.fallback_used is False
        assert "design" in (series.provider or "").lower() or "EPW" in (series.provider or "")
        # 168-hour mapping: exact length, aligned arrays
        assert len(series.timestamps) == 168
        assert len(series.air_temperature_C) == 168
        assert len(series.solar_direct_W_m2) == 168
        assert len(series.solar_diffuse_W_m2) == 168
        assert series.period_start == series.timestamps[0]
        assert series.period_end == series.timestamps[-1]

    def test_offline_live_request_falls_back_never_faked_live(self):
        svc = ClimateService(enable_online=False)
        series = svc.get_hourly_weather("28.6, 77.2", mode="live", hours=24)
        assert series.data_mode == WeatherDataMode.FALLBACK
        assert series.fallback_used is True
        assert "not" in (series.notes or "").lower() and "live" in (series.notes or "").lower()


# =====================================================================
# 5. CLIMATE API ROUTES
# =====================================================================

class TestClimateRoutes(unittest.TestCase):
    def test_geocode_route_returns_candidates(self):
        r = client.get("/api/climate/geocode", params={"query": "Delhi", "count": 2})
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 1
        assert all("latitude" in c and "longitude" in c for c in body["results"])

    def test_weather_route_design_mode(self):
        r = client.get("/api/climate/weather", params={"location": "28.6,77.2", "mode": "design", "hours": 24})
        assert r.status_code == 200
        body = r.json()
        assert body["data_mode"] == "design"
        assert len(body["air_temperature_C"]) == 24

    def test_weather_route_invalid_coordinates_structured(self):
        r = client.get("/api/climate/weather", params={"location": "999,999", "mode": "forecast"})
        assert r.status_code == 422
        assert r.json()["detail"]["error"] == "invalid_location"

    def test_weather_route_invalid_mode_structured(self):
        r = client.get("/api/climate/weather", params={"location": "Delhi", "mode": "weekly"})
        assert r.status_code == 422

    def test_simulation_profile_route_shape(self):
        r = client.get(
            "/api/climate/simulation-profile",
            params={"location": "jaisalmer", "mode": "design", "hours": 24},
        )
        assert r.status_code == 200
        body = r.json()
        cl = body["climate"]
        assert len(cl["hourly_temperature"]) == 24
        assert cl["data_provenance"] in ("historical", "estimated", "measured", "simulated")
        assert body["series"]["data_mode"] == "design"
        # Passive strategy inputs accompany the profile (explainable, not opaque)
        assert body["strategy"] is not None
        assert body["strategy"].get("primary_strategy")


# =====================================================================
# 6. CLIMATE -> SIMULATION BRIDGE (END TO END)
# =====================================================================

class TestClimateSimulationBridge(unittest.TestCase):
    def test_climate_derived_profile_drives_simulation(self):
        prof = client.get(
            "/api/climate/simulation-profile",
            params={"location": "jaisalmer", "mode": "design", "hours": 48},
        ).json()
        cl = prof["climate"]

        payload = {
            "city": cl.get("city", "jaisalmer"),
            "design": _design_payload(),
            "climate": cl,
            "hours_to_simulate": 24,
            "substeps": 15,
        }
        r = client.post("/api/simulation/run", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()

        # Simulation consumed the climate-derived arrays (same window)
        assert len(data["outdoor_temperatures"]) == 24
        assert data["outdoor_temperatures"][0] == pytest.approx(cl["hourly_temperature"][0], abs=0.15)
        assert data["total_heat_loss_kwh"] > 0.0
        assert data["integrated_solar_energy_kwh"] > 0.0


if __name__ == "__main__":
    unittest.main()
