"""
THERMOSHELTER AI - Climate Service Error Taxonomy
=================================================
Machine-readable error categories for the climate/location pipeline.
Each category maps deterministically to an HTTP status at the route layer
and to a distinct user-facing message class on the frontend (Phase A
ApiError kinds) — climate failures must never be masked as a generic
"service unavailable".
"""

from enum import Enum
from typing import Any, Dict, Optional


class ClimateErrorCategory(str, Enum):
    """Explicit, machine-readable failure categories."""

    INVALID_LOCATION = "invalid_location"          # Coordinates out of range / empty query
    GEOCODING_FAILURE = "geocoding_failure"        # Place name could not be resolved
    ELEVATION_FAILURE = "elevation_failure"        # Elevation lookup unavailable
    PROVIDER_TIMEOUT = "provider_timeout"          # Upstream weather service timed out
    PROVIDER_RATE_LIMIT = "provider_rate_limit"    # Upstream quota/rate limit hit
    PROVIDER_ERROR = "provider_error"              # Upstream returned an error response
    MALFORMED_RESPONSE = "malformed_response"      # Upstream payload failed validation
    DATA_UNAVAILABLE = "data_unavailable"          # No weather data for the request
    STALE_CACHE = "stale_cache"                    # Only expired cache data existed
    INVALID_CLIMATE_DATA = "invalid_climate_data"  # Data failed physical sanity checks
    INTERNAL_ERROR = "internal_error"              # Unexpected server-side failure


# Deterministic HTTP status mapping per category.
CATEGORY_HTTP_STATUS: Dict[ClimateErrorCategory, int] = {
    ClimateErrorCategory.INVALID_LOCATION: 422,
    ClimateErrorCategory.GEOCODING_FAILURE: 404,
    ClimateErrorCategory.ELEVATION_FAILURE: 502,
    ClimateErrorCategory.PROVIDER_TIMEOUT: 504,
    ClimateErrorCategory.PROVIDER_RATE_LIMIT: 429,
    ClimateErrorCategory.PROVIDER_ERROR: 502,
    ClimateErrorCategory.MALFORMED_RESPONSE: 502,
    ClimateErrorCategory.DATA_UNAVAILABLE: 404,
    ClimateErrorCategory.STALE_CACHE: 503,
    ClimateErrorCategory.INVALID_CLIMATE_DATA: 422,
    ClimateErrorCategory.INTERNAL_ERROR: 500,
}


class ClimateServiceError(Exception):
    """
    Raised by the climate/location pipeline with a machine-readable category.

    Route handlers convert this into
        HTTP <mapped status> {"detail": {"error": "<category>", "message": "..."}}
    so clients can classify failures without parsing prose.
    """

    def __init__(self, category: ClimateErrorCategory, message: str, detail: Optional[Any] = None):
        self.category = category
        self.message = message
        self.detail = detail
        super().__init__(message)

    def to_http_detail(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"error": self.category.value, "message": self.message}
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload

    @staticmethod
    def http_status_for(category: ClimateErrorCategory) -> int:
        return CATEGORY_HTTP_STATUS.get(category, 500)
