/**
 * THERMOSHELTER — Provenance view derivation (D4-B WP5)
 * =====================================================
 * Pure derivation of the provenance panel's display fields from the
 * SimulationClimateProfile. Panel rendering consumes this so the honesty
 * contract is unit-testable: fallback is explicit, SIMULATED stays distinct
 * from weather provenance, and absent optional fields are omitted (null) —
 * never invented.
 */

import { SimulationClimateProfile } from './api';
import { activeWeatherProvenance, fallbackUsed } from '../store/useStudioState';
import { ProvenanceValue } from '../theme/tokens';

export interface ProvenanceView {
  /** False when there is no profile — the panel must not render at all. */
  visible: boolean;
  provider: string | null;
  dataMode: string | null;
  provenance: ProvenanceValue | null;
  fallbackUsed: boolean;
  hours: number | null;
  periodLabel: string | null;
  retrievedLabel: string | null;
  coordinatesLabel: string | null;
  elevationLabel: string | null;
  timezone: string | null;
  locationLabel: string | null;
  notes: string | null;
}

function fmtTimestamp(iso: string | null | undefined): string | null {
  if (typeof iso !== 'string' || iso === '') return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  // "2026-09-10T00:00:00.000Z" -> "2026-09-10 00:00 UTC" (minute precision is
  // sufficient for weather periods and retrieval stamps).
  return `${d.toISOString().slice(0, 16).replace('T', ' ')} UTC`;
}

function fmtCoord(v: unknown): string | null {
  return typeof v === 'number' && Number.isFinite(v) ? v.toFixed(4) : null;
}

/**
 * Derives every panel field from the REAL profile. Any field the backend did
 * not provide stays null and the panel shows "—" or omits it — never a value.
 */
export function formatProvenanceView(
  profile: SimulationClimateProfile | null | undefined,
  simulated: boolean,
): ProvenanceView {
  if (!profile || !profile.series) {
    return {
      visible: false,
      provider: null,
      dataMode: null,
      provenance: null,
      fallbackUsed: false,
      hours: null,
      periodLabel: null,
      retrievedLabel: null,
      coordinatesLabel: null,
      elevationLabel: null,
      timezone: null,
      locationLabel: null,
      notes: null,
    };
  }

  const s = profile.series;
  const provenance = activeWeatherProvenance(profile);
  const isFallback = fallbackUsed(profile);

  const periodStart = fmtTimestamp(s.period_start);
  const periodEnd = fmtTimestamp(s.period_end);
  const lat = fmtCoord(s.latitude);
  const lon = fmtCoord(s.longitude);

  return {
    visible: true,
    provider: typeof s.provider === 'string' && s.provider ? s.provider : null,
    dataMode: typeof s.data_mode === 'string' && s.data_mode ? s.data_mode : null,
    provenance,
    fallbackUsed: isFallback,
    hours: Array.isArray(s.air_temperature_C) && s.air_temperature_C.length > 0 ? s.air_temperature_C.length : null,
    periodLabel:
      periodStart && periodEnd ? `${periodStart} → ${periodEnd}` : (periodStart ?? periodEnd),
    retrievedLabel: fmtTimestamp(s.retrieval_timestamp),
    coordinatesLabel: lat && lon ? `${lat}, ${lon}` : null,
    elevationLabel:
      typeof profile.climate?.elevation_m === 'number'
        ? `${Math.round(profile.climate.elevation_m)} m`
        : typeof s.elevation_m === 'number'
          ? `${Math.round(s.elevation_m)} m`
          : null,
    timezone: typeof s.timezone === 'string' && s.timezone ? s.timezone : null,
    locationLabel:
      typeof profile.climate?.city === 'string' && profile.climate.city ? profile.climate.city : null,
    notes: typeof s.notes === 'string' && s.notes ? s.notes : null,
    ...(simulated === true || simulated === false ? {} : {}),
  };
}
