/**
 * Provenance view derivation tests (D4-B WP5/WP7) — Vitest
 * ========================================================
 * The provenance panel must render only real metadata: fallback must be
 * explicitly disclosed, SIMULATED must stay distinct from weather
 * provenance, and optional missing fields must be honestly omitted.
 */

import { describe, expect, it } from 'vitest';

import { formatProvenanceView } from './provenanceView';
import type { SimulationClimateProfile } from './api';

function makeProfile(overrides: Record<string, unknown> = {}): SimulationClimateProfile {
  return {
    climate: {
      city: 'Leh',
      climate_zone: 'cold',
      elevation_m: 3514,
      hourly_temperature: [],
    },
    series: {
      latitude: 34.1521,
      longitude: 77.5771,
      elevation_m: 3514,
      timezone: 'Asia/Kolkata',
      timestamps: Array.from({ length: 168 }, () => '2026-09-10T00:00:00Z'),
      air_temperature_C: Array.from({ length: 168 }, () => 5),
      data_mode: 'live',
      provenance: 'MODEL_ANALYSIS',
      provider: 'open-meteo',
      retrieval_timestamp: '2026-09-17T10:00:00Z',
      period_start: '2026-09-10T00:00:00Z',
      period_end: '2026-09-16T23:00:00Z',
      fallback_used: false,
      notes: 'Grid cell centre 0.1° resolution',
    },
    strategy: null,
    ...overrides,
  } as unknown as SimulationClimateProfile;
}

describe('formatProvenanceView — full provenance (WP7)', () => {
  it('exposes every real field when present', () => {
    const v = formatProvenanceView(makeProfile(), true);
    expect(v.visible).toBe(true);
    expect(v.provider).toBe('open-meteo');
    expect(v.dataMode).toBe('live');
    expect(v.provenance).toBe('MODEL_ANALYSIS');
    expect(v.fallbackUsed).toBe(false);
    expect(v.hours).toBe(168);
    expect(v.periodLabel).toBe(
      '2026-09-10 00:00 UTC → 2026-09-16 23:00 UTC',
    );
    expect(v.retrievedLabel).toBe('2026-09-17 10:00 UTC');
    expect(v.coordinatesLabel).toBe('34.1521, 77.5771');
    expect(v.elevationLabel).toBe('3514 m');
    expect(v.timezone).toBe('Asia/Kolkata');
    expect(v.locationLabel).toBe('Leh');
    expect(v.notes).toBe('Grid cell centre 0.1° resolution');
  });

  it('keeps SIMULATED result provenance a distinct flag from weather provenance', () => {
    const v = formatProvenanceView(makeProfile(), true);
    // Weather provenance is MODEL_ANALYSIS; the simulated flag is separate.
    expect(v.provenance).toBe('MODEL_ANALYSIS');
    // The `simulated` argument drives the separate SIMULATED chip/row.
    const v2 = formatProvenanceView(makeProfile(), false);
    expect(v2.provenance).toBe('MODEL_ANALYSIS');
  });
});

describe('formatProvenanceView — fallback disclosure (WP7)', () => {
  it('explicitly discloses fallback_used=true', () => {
    const v = formatProvenanceView(
      makeProfile({ series: { fallback_used: true, data_mode: 'fallback' } }),
      true,
    );
    expect(v.visible).toBe(true);
    expect(v.fallbackUsed).toBe(true);
    expect(v.dataMode).toBe('fallback');
  });

  it('maps a fallback data_mode to the canonical FALLBACK provenance', () => {
    const v = formatProvenanceView(
      makeProfile({
        series: { fallback_used: true, data_mode: 'fallback', provenance: 'FALLBACK' },
      }),
      true,
    );
    expect(v.provenance).toBe('FALLBACK');
  });
});

describe('formatProvenanceView — honest omission (WP7)', () => {
  it('returns visible=false for a null profile (no misleading panel)', () => {
    const v = formatProvenanceView(null, true);
    expect(v.visible).toBe(false);
    expect(v.provider).toBeNull();
    expect(v.provenance).toBeNull();
  });

  it('returns null (not invented values) for absent optional fields', () => {
    const v = formatProvenanceView(
      makeProfile({
        series: {
          latitude: 34.15,
          longitude: 77.57,
          timezone: null,
          notes: null,
          provider: 'open-meteo',
          data_mode: 'design',
          period_start: null,
          period_end: null,
          retrieval_timestamp: undefined,
          air_temperature_C: [],
          fallback_used: false,
        },
        climate: { city: null, elevation_m: null, hourly_temperature: [] },
      }),
      true,
    );
    expect(v.timezone).toBeNull();
    expect(v.notes).toBeNull();
    expect(v.periodLabel).toBeNull();
    expect(v.retrievedLabel).toBeNull();
    expect(v.hours).toBeNull();
    expect(v.elevationLabel).toBeNull();
    expect(v.locationLabel).toBeNull();
    // Coordinates still render — they are present.
    expect(v.coordinatesLabel).toBe('34.1500, 77.5700');
  });
});
