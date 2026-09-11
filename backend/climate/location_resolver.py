"""
THERMOSHELTER AI - Location Resolver
====================================
Resolves geographic queries (place names, coordinate strings, or coordinate pairs)
to validated Location models with elevation, timezone, and provenance.
Includes offline-first matching and optional online geocoding.
"""

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from backend.climate.schemas import Location


class LocationResolver:
    """
    Location resolver supporting place names, coordinates, and offline fallbacks.
    """

    def __init__(self, data_dir: Optional[Union[str, Path]] = None, timeout_seconds: float = 3.0):
        if data_dir is None:
            # Default to repository data directory
            current_dir = Path(__file__).resolve().parent
            self.base_dir = current_dir.parent.parent
            self.data_dir = self.base_dir / "data"
        else:
            self.data_dir = Path(data_dir)
            self.base_dir = self.data_dir.parent

        self.timeout_seconds = timeout_seconds
        self._local_locations: List[Dict[str, Any]] = []
        self._load_local_locations()

    def _load_local_locations(self) -> None:
        """Loads known locations from data/climate/locations.json and data/mock."""
        locations_file = self.data_dir / "climate" / "locations.json"
        if locations_file.exists():
            try:
                with open(locations_file, "r", encoding="utf-8") as f:
                    self._local_locations.extend(json.load(f))
            except Exception:
                pass

        # Also load from mock datasets if present
        mock_dir = self.data_dir / "mock"
        if mock_dir.exists():
            for mock_file in mock_dir.glob("*_climate.json"):
                try:
                    with open(mock_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        loc = data.get("location", {})
                        if loc and not any(l.get("place_name") == loc.get("place_name") for l in self._local_locations):
                            self._local_locations.append({
                                "id": loc.get("place_name", "").split(",")[0].strip().lower(),
                                "name": loc.get("place_name", "").split(",")[0].strip(),
                                "country": loc.get("country", "India"),
                                "region": loc.get("region", ""),
                                "latitude": loc.get("latitude"),
                                "longitude": loc.get("longitude"),
                                "altitude": loc.get("elevation", 0.0),
                                "timezone": loc.get("timezone", "Asia/Kolkata"),
                                "source": loc.get("source", "Mock Dataset")
                            })
                except Exception:
                    pass

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates great-circle distance between two coordinate pairs in kilometers."""
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def _parse_coordinates_string(self, text: str) -> Optional[Tuple[float, float]]:
        """Extracts latitude and longitude if text is formatted as 'lat, lon'."""
        # Matches patterns like '34.1526, 77.5771' or '34.1526 N, 77.5771 E'
        coord_pattern = r"^\s*([-+]?\d{1,3}(?:\.\d+)?)\s*,\s*([-+]?\d{1,3}(?:\.\d+)?)\s*$"
        match = re.match(coord_pattern, text.strip())
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                return lat, lon
            except ValueError:
                return None
        return None

    def validate_coordinates(self, latitude: float, longitude: float) -> Tuple[float, float]:
        """Validates coordinate ranges."""
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Latitude must be between -90.0 and +90.0 degrees, got {latitude}")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Longitude must be between -180.0 and +180.0 degrees, got {longitude}")
        return float(latitude), float(longitude)

    def resolve_from_coordinates(
        self,
        latitude: float,
        longitude: float,
        elevation: Optional[float] = None,
        place_name: Optional[str] = None
    ) -> Location:
        """
        Creates Location model from coordinates, finding nearest known local station if available.
        """
        lat, lon = self.validate_coordinates(latitude, longitude)

        # Find nearest local station for reference
        nearest_loc = None
        min_dist = float("inf")
        for loc in self._local_locations:
            loc_lat = loc.get("latitude")
            loc_lon = loc.get("longitude")
            if loc_lat is not None and loc_lon is not None:
                dist = self.haversine_distance_km(lat, lon, loc_lat, loc_lon)
                if dist < min_dist:
                    min_dist = dist
                    nearest_loc = loc

        resolved_name = place_name
        resolved_elevation = elevation
        resolved_tz = "Asia/Kolkata"
        region = None
        country = "India"

        # If very close to a known station (within 35 km), borrow its metadata
        if nearest_loc and min_dist <= 35.0:
            if not resolved_name:
                resolved_name = f"{nearest_loc.get('name', 'Known Site')}, {nearest_loc.get('region', 'Ladakh')}"
            if resolved_elevation is None:
                resolved_elevation = nearest_loc.get("altitude")
            resolved_tz = nearest_loc.get("timezone", resolved_tz)
            region = nearest_loc.get("region")
            country = nearest_loc.get("country", country)
        elif not resolved_name:
            resolved_name = f"Coordinates ({lat:.4f}°N, {lon:.4f}°E)"

        return Location(
            place_name=resolved_name,
            latitude=lat,
            longitude=lon,
            elevation=resolved_elevation,
            timezone=resolved_tz,
            country=country,
            region=region,
            source=f"Coordinate Resolution (Nearest known station: {nearest_loc['name'] if nearest_loc else 'None'}, {min_dist:.1f} km)"
        )

    def resolve_from_name(self, name: str, allow_online: bool = True) -> Location:
        """
        Resolves a place name against the local database, falling back to online geocoding if enabled.
        """
        query_clean = name.strip()
        if not query_clean:
            raise ValueError("Place name cannot be empty")

        query_lower = query_clean.lower()

        # 1. Exact or substring match in local database
        for loc in self._local_locations:
            loc_id = loc.get("id", "").lower()
            loc_name = loc.get("name", "").lower()
            loc_region = loc.get("region", "").lower()

            if (
                query_lower == loc_id
                or query_lower == loc_name
                or query_lower in f"{loc_name}, {loc_region}".lower()
                or loc_name in query_lower
            ):
                return Location(
                    place_name=f"{loc['name']}, {loc.get('region', loc.get('country', 'India'))}",
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    elevation=loc.get("altitude"),
                    timezone=loc.get("timezone", "Asia/Kolkata"),
                    country=loc.get("country", "India"),
                    region=loc.get("region"),
                    source=loc.get("source", "Local Climatological Database")
                )

        # 2. Try online geocoding if permitted
        if allow_online:
            try:
                url = "https://geocoding-api.open-meteo.com/v1/search"
                params = {"name": query_clean, "count": 1, "format": "json"}
                response = requests.get(url, params=params, timeout=self.timeout_seconds)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results")
                    if results and len(results) > 0:
                        first = results[0]
                        return Location(
                            place_name=f"{first.get('name')}, {first.get('admin1', first.get('country', ''))}",
                            latitude=first["latitude"],
                            longitude=first["longitude"],
                            elevation=first.get("elevation"),
                            timezone=first.get("timezone", "Asia/Kolkata"),
                            country=first.get("country", "India"),
                            region=first.get("admin1"),
                            source="Open-Meteo Geocoding API"
                        )
            except Exception:
                # Network error, timeout, or rate limiting; fall through
                pass

        # 3. Not found
        available_names = [loc.get("name") for loc in self._local_locations if loc.get("name")]
        raise ValueError(
            f"Location '{query_clean}' could not be resolved. "
            f"Known local locations: {', '.join(sorted(set(available_names)))}. "
            f"Or supply coordinates directly in format 'latitude, longitude'."
        )

    def resolve(self, query: Union[str, Tuple[float, float], Dict[str, Any], Location]) -> Location:
        """
        Universal entry point to resolve any supported location input into a validated Location model.
        """
        if isinstance(query, Location):
            return query

        if isinstance(query, tuple) and len(query) == 2:
            return self.resolve_from_coordinates(query[0], query[1])

        if isinstance(query, dict):
            lat = query.get("latitude") or query.get("lat")
            lon = query.get("longitude") or query.get("lon")
            if lat is not None and lon is not None:
                return self.resolve_from_coordinates(
                    float(lat),
                    float(lon),
                    elevation=query.get("elevation") or query.get("altitude"),
                    place_name=query.get("place_name") or query.get("name")
                )
            if "name" in query or "place_name" in query:
                return self.resolve_from_name(query.get("name") or query.get("place_name"))

        if isinstance(query, str):
            # Check if it's a coordinate string
            coords = self._parse_coordinates_string(query)
            if coords:
                return self.resolve_from_coordinates(coords[0], coords[1])
            return self.resolve_from_name(query)

        raise TypeError(f"Unsupported location query type: {type(query)}")
