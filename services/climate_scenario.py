"""
THERMOSHELTER AI - Climate Scenario Selection for Optimization (Phase C)
========================================================================
Deterministic, explainable design-week selection over canonical
ClimateProfile hourly data. This module NEVER fabricates weather: it only
selects an index window from arrays that already exist in the profile and
slices every vector on the SAME indices, so temperature, direct solar,
diffuse solar (and any optional vectors) stay perfectly aligned.

Methodology (explicit, deterministic, NOT an official building standard):

  COLD design week
      The 168-hour window with the LOWEST mean outdoor air temperature.
      Rationale: envelope performance under sustained cold exposure is
      governed by the continuous mean, not a single extreme hour.

  HOT design week
      The 168-hour window with the HIGHEST mean outdoor air temperature.

  TYPICAL design week
      The 168-hour window whose mean temperature is closest to the mean
      of the whole series; ties are broken by the lowest mean absolute
      deviation from the series mean (most representative variability).

Window stepping: candidate windows advance in 24-hour steps from the
series start; the LAST candidate window ends exactly at the series end.
Ties resolve to the EARLIEST window. The selection is fully reproducible.

Insufficient data is an explicit error (ClimateScenarioError) - never a
silent fabrication. Callers preserve their existing valid behavior.
"""

from typing import Any, Dict, List, Optional

try:
    from services.contracts import ClimateProfile
except ImportError:  # pragma: no cover - direct script execution
    from contracts import ClimateProfile  # type: ignore


SCENARIO_KINDS = ("cold", "hot", "typical")
DEFAULT_WINDOW_HOURS = 168


class ClimateScenarioError(ValueError):
    """Raised when a climate scenario cannot be established from the data."""


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _mean_abs_deviation(values: List[float], ref: float) -> float:
    return sum(abs(v - ref) for v in values) / len(values)


def select_design_week(
    profile: ClimateProfile,
    kind: str = "typical",
    hours: int = DEFAULT_WINDOW_HOURS,
) -> ClimateProfile:
    """
    Selects a deterministic design-week window from a canonical ClimateProfile.

    Returns a NEW ClimateProfile whose hourly vectors are the selected window
    (solar arrays sliced on the identical indices - consistency by
    construction). Provenance, location, elevation, timezone, and timestamps
    (sliced) are preserved; a selection note is appended to data_source.

    Raises ClimateScenarioError when the series is shorter than the requested
    window or the kind is unknown. No substitution, no interpolation.
    """
    if kind not in SCENARIO_KINDS:
        raise ClimateScenarioError(
            f"Unknown design-week kind '{kind}'. Use one of: {', '.join(SCENARIO_KINDS)}"
        )
    window = int(hours)
    if window <= 0:
        raise ClimateScenarioError(f"Design-week window must be positive, got {hours}")

    temps = profile.hourly_temperature
    n = len(temps)
    if n < window:
        raise ClimateScenarioError(
            f"Climate series has only {n} hourly samples; a {window}-hour design "
            "week cannot be selected without fabricating data. Provide a longer "
            "historical/design dataset or use the full series as the scenario."
        )

    # Candidate window start indices: 24h steps, last window ends at series end.
    step = 24
    starts = list(range(0, n - window + 1, step))
    last_start = n - window
    if not starts or starts[-1] != last_start:
        starts.append(last_start)

    windows = [temps[s : s + window] for s in starts]
    means = [_mean(w) for w in windows]
    series_mean = _mean(temps)

    if kind == "cold":
        best = min(range(len(starts)), key=lambda i: (means[i], starts[i]))
    elif kind == "hot":
        best = max(range(len(starts)), key=lambda i: (means[i], -starts[i]))
    else:  # typical
        devs = [_mean_abs_deviation(w, series_mean) for w in windows]
        best = min(range(len(starts)), key=lambda i: (abs(means[i] - series_mean), devs[i], starts[i]))

    s = starts[best]
    selection_note = (
        f"{kind.capitalize()} design week selected deterministically "
        f"({kind} mean-temperature methodology over {window}h windows, "
        f"24h stepping; window {s}..{s + window - 1} of {n} samples)."
    )

    def _slice(arr: Optional[List[float]]) -> Optional[List[float]]:
        if arr is None or len(arr) < n:
            return None
        return list(arr[s : s + window])

    selected = ClimateProfile(
        city=profile.city,
        latitude=profile.latitude,
        longitude=profile.longitude,
        hourly_temperature=list(temps[s : s + window]),
        hourly_direct_solar=list(profile.hourly_direct_solar[s : s + window]),
        hourly_diffuse_solar=list(profile.hourly_diffuse_solar[s : s + window]),
        hourly_wind_speed=_slice(profile.hourly_wind_speed),
        hourly_humidity=_slice(profile.hourly_humidity),
        climate_zone=profile.climate_zone,
        elevation_m=profile.elevation_m,
        timezone_offset_hours=profile.timezone_offset_hours,
        hourly_cloud_cover=_slice(profile.hourly_cloud_cover),
        hourly_precipitation=_slice(profile.hourly_precipitation),
        timestamps=(list(profile.timestamps[s : s + window]) if profile.timestamps else None),
        data_source=f"{profile.data_source} | {selection_note}",
        data_provenance=profile.data_provenance,
        data_confidence=profile.data_confidence,
    )
    return selected


def resolve_optimization_scenario(
    profile: ClimateProfile,
    hours: int = DEFAULT_WINDOW_HOURS,
    scenario_kind: Optional[str] = None,
) -> ClimateProfile:
    """
    Establishes THE climate scenario for optimization from a canonical profile.

    Behaviour (documented, deterministic):
      - scenario_kind given ("cold" | "hot" | "typical"):
            deterministic design-week selection (requires sufficient data).
      - scenario_kind None and the series is longer than the window:
            the FIRST `hours` samples are used - i.e. the dataset's defined
            window (a live/forecast week fetched by the user, or the start of
            a design-year dataset). This is an explicit, documented choice,
            never an arbitrary silent one.
      - series shorter than or equal to the window:
            the full series is the scenario (nothing is dropped).

    Humidity and wind are carried as metadata vectors sliced on the same
    indices; the current thermal engine does not consume them (documented
    limitation, not invented physics).
    """
    n = len(profile.hourly_temperature)
    window = int(hours)

    if scenario_kind is not None:
        return select_design_week(profile, kind=scenario_kind, hours=window)

    if n <= window:
        return profile
    return _head_window(profile, window)


def _head_window(profile: ClimateProfile, window: int) -> ClimateProfile:
    """First `window` samples of the profile (its defined scenario window)."""
    def _slice(arr: Optional[List[float]]) -> Optional[List[float]]:
        if arr is None or len(arr) < len(profile.hourly_temperature):
            return None
        return list(arr[:window])

    return ClimateProfile(
        city=profile.city,
        latitude=profile.latitude,
        longitude=profile.longitude,
        hourly_temperature=list(profile.hourly_temperature[:window]),
        hourly_direct_solar=list(profile.hourly_direct_solar[:window]),
        hourly_diffuse_solar=list(profile.hourly_diffuse_solar[:window]),
        hourly_wind_speed=_slice(profile.hourly_wind_speed),
        hourly_humidity=_slice(profile.hourly_humidity),
        climate_zone=profile.climate_zone,
        elevation_m=profile.elevation_m,
        timezone_offset_hours=profile.timezone_offset_hours,
        hourly_cloud_cover=_slice(profile.hourly_cloud_cover),
        hourly_precipitation=_slice(profile.hourly_precipitation),
        timestamps=(list(profile.timestamps[:window]) if profile.timestamps else None),
        data_source=profile.data_source,
        data_provenance=profile.data_provenance,
        data_confidence=profile.data_confidence,
    )
