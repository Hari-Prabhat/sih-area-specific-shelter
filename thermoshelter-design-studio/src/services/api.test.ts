/**
 * Frontend API client unit tests (Vitest)
 * ========================================
 * Verifies canonical design -> payload propagation (including thermal mass)
 * and the ApiError classification contract. No thermal math is performed
 * here — Python remains the sole physics authority.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  ApiError,
  buildCanonicalSimulationPayload,
  checkApiHealth,
  describeApiError,
  describeClimateError,
  fetchSimulationClimateProfile,
  geocodeLocations,
  runSimulationViaApi,
  SimulationClimateProfile,
} from './api';
import type { ClimateData, ShelterDesign, MaterialProperties } from '../types';

const climate: ClimateData = {
  location: 'Leh, Ladakh',
  altitude: 3500,
  ambientTempMin: -25,
  ambientTempMax: 30,
  avgAmbientTemp: 5,
  solarIrradiance: 2000,
  avgSunshineHours: 7.9,
  windSpeed: 6.5,
  humidity: 25,
  cloudFreeDays: 320,
};

const design: ShelterDesign = {
  length: 6,
  width: 4,
  height: 3,
  shape: 'rectangular',
  orientation: 180,
  roofAngle: 30,
  wallThickness: 0.3,
  windowArea: 3,
  windowGlazing: 'double',
  doorArea: 2,
  insulationType: 'EPS',
  insulationThickness: 5,
  ach: 0.5,
  thermalMassEnabled: true,
  thermalMassThickness: 20,
};

const wallMaterial: MaterialProperties = {
  name: 'Rammed Earth (Stabilized)',
  thermalConductivity: 0.7,
  density: 2000,
  specificHeat: 900,
  emissivity: 0.9,
  solarAbsorptance: 0.6,
  cost: 10,
  category: 'wall',
};

const insulation: MaterialProperties = {
  ...wallMaterial,
  name: 'EPS',
  thermalConductivity: 0.025,
};

describe('buildCanonicalSimulationPayload', () => {
  it('propagates the canonical design parameters', () => {
    const payload = buildCanonicalSimulationPayload(climate, design, wallMaterial, insulation, 168);
    expect(payload.city).toBe('leh');
    expect(payload.design.length).toBe(6);
    expect(payload.design.width).toBe(4);
    expect(payload.design.height).toBe(3);
    expect(payload.design.wall_thickness_m).toBe(0.3);
    expect(payload.design.window_area).toBe(3);
    expect(payload.design.door_area).toBe(2);
    expect(payload.design.orientation).toBe(180);
    expect(payload.design.roof_type).toBe('pitched');
    expect(payload.design.pitch_angle_deg).toBe(30);
    expect(payload.design.glazing).toBe('double_clear');
    expect(payload.design.insulation_thickness_m).toBeGreaterThan(0);
    expect(payload.hours_to_simulate).toBe(168);
  });

  it('propagates enabled thermal mass as SI meters (cm / 100)', () => {
    const payload = buildCanonicalSimulationPayload(climate, design, wallMaterial, insulation);
    expect(payload.design.thermal_mass_enabled).toBe(true);
    expect(payload.design.thermal_mass_thickness_m).toBeCloseTo(0.2, 10);
  });

  it('sends zero thermal mass when disabled', () => {
    const payload = buildCanonicalSimulationPayload(
      climate,
      { ...design, thermalMassEnabled: false },
      wallMaterial,
      insulation,
    );
    expect(payload.design.thermal_mass_enabled).toBe(false);
    expect(payload.design.thermal_mass_thickness_m).toBe(0);
  });

  it('derives a flat roof when roofAngle is zero', () => {
    const payload = buildCanonicalSimulationPayload(
      climate,
      { ...design, roofAngle: 0 },
      wallMaterial,
      insulation,
    );
    expect(payload.design.roof_type).toBe('flat');
    expect(payload.design.pitch_angle_deg).toBe(0);
  });
});

describe('D4-A WP1/WP2: mission & envelope input propagation', () => {
  it('sends the mission occupancy into the direct-simulation payload (no hardcoded 2)', () => {
    const payload = buildCanonicalSimulationPayload(
      climate,
      design,
      wallMaterial,
      insulation,
      168,
      undefined,
      6,
    );
    expect(payload.design.occupants).toBe(6);
  });

  it('sends the design ACH state (no hardcoded 0.5)', () => {
    const payload = buildCanonicalSimulationPayload(
      climate,
      { ...design, ach: 1.2 },
      wallMaterial,
      insulation,
    );
    expect(payload.design.ach).toBe(1.2);
  });

  it('sends the explicit insulation-thickness design state as SI metres (cm / 100)', () => {
    const payload = buildCanonicalSimulationPayload(
      climate,
      { ...design, insulationType: 'XPS', insulationThickness: 12 },
      wallMaterial,
      insulation,
    );
    expect(payload.design.insulation_thickness_m).toBeCloseTo(0.12, 10);
  });

  it('sends zero insulation thickness for uninsulated designs or zero cm', () => {
    const noneType = buildCanonicalSimulationPayload(
      climate,
      { ...design, insulationType: 'None', insulationThickness: 10 },
      wallMaterial,
      insulation,
    );
    expect(noneType.design.insulation_thickness_m).toBe(0);

    const zeroCm = buildCanonicalSimulationPayload(
      climate,
      { ...design, insulationThickness: 0 },
      wallMaterial,
      insulation,
    );
    expect(zeroCm.design.insulation_thickness_m).toBe(0);
  });

  it('produces a deterministic payload: identical inputs yield identical JSON', () => {
    const a = JSON.stringify(buildCanonicalSimulationPayload(climate, design, wallMaterial, insulation, 168, undefined, 4));
    const b = JSON.stringify(buildCanonicalSimulationPayload(climate, design, wallMaterial, insulation, 168, undefined, 4));
    expect(a).toBe(b);
  });

  it('keeps canonical solver configuration (backend SimulationInput defaults)', () => {
    // services/contracts.py SimulationInput defaults: substeps=60, initial_indoor_temp=20.0
    const payload = buildCanonicalSimulationPayload(climate, design, wallMaterial, insulation);
    expect(payload.substeps).toBe(60);
    expect(payload.initial_indoor_temp).toBe(20.0);
  });
});

describe('describeApiError', () => {
  it('reports unavailable only for unreachable-backend errors', () => {
    const err = new ApiError('unavailable', 'Backend unreachable:Failed to fetch');
    expect(describeApiError(err)).toBe(
      'Simulation service unavailable. Start the FastAPI backend and try again.'
    );
  });

  it('keeps invalid-input and simulation-failure messages distinct', () => {
    const invalid = new ApiError('invalid_input', 'Invalid design input: length must be positive', 422);
    const failed = new ApiError('simulation_failed', 'Simulation failed: diverged', 500);
    expect(describeApiError(invalid)).toContain('Invalid design input');
    expect(describeApiError(invalid)).not.toContain('service unavailable');
    expect(describeApiError(failed)).toContain('Simulation failed');
    expect(describeApiError(failed)).not.toContain('service unavailable');
  });

  it('falls back to the raw message for unknown errors', () => {
    expect(describeApiError(new Error('boom'))).toBe('boom');
  });
});

describe('API error classification from responses', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('classifies network rejection as unavailable', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(checkApiHealth()).rejects.toMatchObject({ kind: 'unavailable' });
  });

  it('classifies 422 as invalid_input with parsed FastAPI detail', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: { error: 'Invalid shelter design specification', message: 'length must be positive' },
        }),
        { status: 422, headers: { 'Content-Type': 'application/json' } }
      )
    );
    await expect(runSimulationViaApi(climate, design, wallMaterial, insulation)).rejects.toMatchObject({
      kind: 'invalid_input',
      status: 422,
    });
  });

  it('classifies 500 as simulation_failed and preserves the reason', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ detail: { error: 'Internal simulation failure', message: 'numerical divergence' } }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    );
    await expect(runSimulationViaApi(climate, design, wallMaterial, insulation)).rejects.toMatchObject({
      kind: 'simulation_failed',
      status: 500,
    });
  });

  it('classifies proxy-down (5xx, non-JSON body) as unavailable, not simulation failure', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response('Empty reply / proxy error', { status: 500 })
    );
    await expect(runSimulationViaApi(climate, design, wallMaterial, insulation)).rejects.toMatchObject({
      kind: 'unavailable',
      status: 500,
    });
  });

  it('parses native FastAPI validation arrays into readable text', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ detail: [{ loc: ['body', 'design', 'length'], msg: 'value greater than 0 required' }] }),
        { status: 422, headers: { 'Content-Type': 'application/json' } }
      )
    );
    const err = await runSimulationViaApi(climate, design, wallMaterial, insulation).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.kind).toBe('invalid_input');
    expect(err.message).toContain('body.design.length');
  });
});

// ==========================================================================
// Phase B: Climate & Location Intelligence client
// ==========================================================================

const climateProfileFixture: SimulationClimateProfile = {
  climate: {
    city: 'Test Site',
    climate_zone: 'hot_dry',
    data_provenance: 'simulated',
    data_source: 'Open-Meteo Forecast (NWP model ensemble) [forecast]',
    elevation_m: 216.0,
    timestamps: ['2026-07-01T00:00', '2026-07-01T01:00'],
    hourly_temperature: [31.2, 30.8],
    hourly_direct_solar: [0, 0],
    hourly_diffuse_solar: [0, 0],
  },
  series: {
    latitude: 28.6,
    longitude: 77.2,
    elevation_m: 216.0,
    timezone: 'Asia/Kolkata',
    timestamps: ['2026-07-01T00:00', '2026-07-01T01:00'],
    air_temperature_C: [31.2, 30.8],
    solar_direct_W_m2: [0, 0],
    solar_diffuse_W_m2: [0, 0],
    data_mode: 'forecast',
    provenance: 'SIMULATED',
    provider: 'Open-Meteo Forecast (NWP model ensemble)',
    retrieval_timestamp: '2026-09-16T00:00:00Z',
    period_start: '2026-07-01T00:00',
    period_end: '2026-07-01T01:00',
    fallback_used: false,
  },
  strategy: { primary_strategy: 'Thermal mass damping + nocturnal flush cooling' },
};

describe('climate payload construction (Phase B)', () => {
  it('omits the climate override on the classic preset path', () => {
    const payload = buildCanonicalSimulationPayload(climate, design, wallMaterial, insulation);
    expect(payload.climate).toBeUndefined();
    expect(payload.city).toBe('leh');
  });

  it('attaches the backend climate profile and its city when provided', () => {
    const payload = buildCanonicalSimulationPayload(
      climate,
      design,
      wallMaterial,
      insulation,
      168,
      climateProfileFixture,
    );
    expect(payload.city).toBe('Test Site');
    expect(payload.climate).toBe(climateProfileFixture.climate);
    expect(payload.climate?.hourly_temperature).toEqual([31.2, 30.8]);
    // The canonical design payload itself is unchanged
    expect(payload.design.length).toBe(6);
    expect(payload.design.thermal_mass_enabled).toBe(true);
  });
});

describe('climate API client (Phase B)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('geocodeLocations parses backend candidates', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({
          query: 'jaisalmer',
          count: 1,
          results: [{ place_name: 'Jaisalmer, Rajasthan', latitude: 26.9157, longitude: 70.9083 }],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );
    const results = await geocodeLocations('jaisalmer', 4);
    expect(results).toHaveLength(1);
    expect(results[0].latitude).toBeCloseTo(26.9157, 3);
    const calledUrl = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(calledUrl).toContain('/api/climate/geocode?query=jaisalmer');
  });

  it('fetchSimulationClimateProfile requests the given location/mode/hours', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify(climateProfileFixture), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    const profile = await fetchSimulationClimateProfile('28.6,77.2', 'live', 168);
    expect(profile.series.data_mode).toBe('forecast'); // fixture mode preserved
    const calledUrl = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(calledUrl).toContain('/api/climate/simulation-profile');
    expect(calledUrl).toContain('mode=live');
    expect(calledUrl).toContain('hours=168');
  });

  it('classifies climate 422 (invalid location) as invalid_input, not unavailable', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ detail: { error: 'invalid_location', message: 'Could not resolve location' } }),
        { status: 422, headers: { 'Content-Type': 'application/json' } }
      )
    );
    const err = await fetchSimulationClimateProfile('zzz', 'live', 24).catch((e: unknown) => e);
    expect(err).toMatchObject({ kind: 'invalid_input', status: 422 });
    expect(describeClimateError(err)).toContain('Could not resolve location');
  });

  it('classifies climate network failure as unavailable', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new TypeError('Failed to fetch'));
    const err = await geocodeLocations('delhi').catch((e: unknown) => e);
    expect(err).toMatchObject({ kind: 'unavailable' });
    expect(describeClimateError(err)).toContain('Climate service unavailable');
  });

  it('runSimulationViaApi posts the climate-derived profile to /api/simulation/run', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({}), { status: 500 })
    );
    // We only need to inspect the request body; the 500 keeps the call short.
    await runSimulationViaApi(climate, design, wallMaterial, insulation, 168, climateProfileFixture).catch(() => null);
    const [, init] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(String(init.body));
    expect(body.city).toBe('Test Site');
    expect(body.climate.hourly_temperature).toEqual([31.2, 30.8]);
  });
});
