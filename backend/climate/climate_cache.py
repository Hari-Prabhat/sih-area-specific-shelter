"""
THERMOSHELTER AI - Climate Cache
================================
Thread-safe in-memory cache with Time-To-Live (TTL) expiration
for meteorological and solar irradiance queries.
"""

import threading
import time
from typing import Any, Dict, Optional, Tuple


class ClimateCache:
    """
    In-memory key-value cache with per-item TTL expiration.
    """

    def __init__(self, default_ttl_seconds: float = 3600.0):
        self._default_ttl = default_ttl_seconds
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def generate_key(prefix: str, lat: float, lon: float, **kwargs) -> str:
        """Generates a standardized cache key with rounded coordinate precision (3 decimals)."""
        lat_r = round(lat, 3)
        lon_r = round(lon, 3)
        extra = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        if extra:
            return f"{prefix}:{lat_r}:{lon_r}:{extra}"
        return f"{prefix}:{lat_r}:{lon_r}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a cached value if present and unexpired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Stores a value with an expiration timestamp."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = time.time() + ttl
        with self._lock:
            self._store[key] = (value, expiry)

    def clear(self) -> None:
        """Clears all cached items."""
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        """Returns the number of active items in cache."""
        with self._lock:
            # Purge expired on query
            now = time.time()
            self._store = {k: v for k, v in self._store.items() if v[1] > now}
            return len(self._store)
