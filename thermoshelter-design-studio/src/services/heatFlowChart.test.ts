/**
 * Heat-flow chart data tests (D4-B WP4/WP7) — Vitest
 * ==================================================
 * The chart consumes ONLY real backend arrays. Tests prove: real arrays
 * produce correct points, alignment is defensive (shortest common length),
 * absent arrays produce honest empty states, units remain W, and nothing is
 * ever synthesized or interpolated.
 */

import { describe, expect, it } from 'vitest';

import {
  HEAT_FLOW_SERIES,
  buildHeatFlowChartData,
  buildSolarChartData,
  buildThermalStorageChartData,
} from './heatFlowChart';
import type { CanonicalSimulationResult } from './api';

/** Minimal canonical result skeleton with controllable hourly arrays. */
function makeResult(overrides: Record<string, unknown> = {}): CanonicalSimulationResult {
  return {
    city: 'test',
    indoor_temperatures: Array.from({ length: 24 }, () => 20),
    outdoor_temperatures: Array.from({ length: 24 }, () => 10),
    solar_irradiance: [],
    solar_power: [],
    solar_thermal_gain: [],
    hourly_internal_gain: [],
    wall_heat_flow: Array.from({ length: 24 }, (_, i) => 100 + i),
    roof_heat_flow: Array.from({ length: 24 }, () => 80),
    floor_heat_flow: Array.from({ length: 24 }, () => 30),
    window_heat_flow: Array.from({ length: 24 }, () => 25),
    door_heat_flow: Array.from({ length: 24 }, () => 10),
    ventilation_heat_flow: Array.from({ length: 24 }, () => 40),
    radiation_heat_flow: Array.from({ length: 24 }, () => 15),
    net_heat_flow: Array.from({ length: 24 }, (_, i) => -(200 + i)),
    thermal_storage_flow: Array.from({ length: 24 }, () => -50),
    ...overrides,
  } as unknown as CanonicalSimulationResult;
}

describe('buildHeatFlowChartData — real arrays (WP7)', () => {
  it('produces one point per hour from real arrays with W values preserved verbatim', () => {
    const r = makeResult();
    const data = buildHeatFlowChartData(r);
    expect(data.hasData).toBe(true);
    expect(data.hourCount).toBe(24);
    expect(data.points).toHaveLength(24);
    expect(data.availableSeries.map((s) => s.key)).toEqual(HEAT_FLOW_SERIES.map((s) => s.key));
    // Real values pass through unmodified (units remain W).
    expect(data.points[0].wall_heat_flow).toBe(100);
    expect(data.points[5].wall_heat_flow).toBe(105);
    expect(data.points[0].net_heat_flow).toBe(-200);
    expect(data.points[0].time).toBe('D1 00:00');
    expect(data.points[25 - 1]?.time ?? data.points[23].time).toBe('D1 23:00');
  });

  it('aligns defensively to the shortest common length without padding', () => {
    const r = makeResult({ radiation_heat_flow: Array.from({ length: 10 }, () => 15) });
    const data = buildHeatFlowChartData(r);
    expect(data.hasData).toBe(true);
    expect(data.hourCount).toBe(10);
    expect(data.points).toHaveLength(10);
  });

  it('excludes absent/invalid arrays instead of zero-filling them', () => {
    const r = makeResult({ door_heat_flow: undefined, roof_heat_flow: [1, NaN, 3] });
    const data = buildHeatFlowChartData(r);
    const keys = data.availableSeries.map((s) => s.key);
    expect(keys).not.toContain('door_heat_flow');
    expect(keys).not.toContain('roof_heat_flow');
    expect(data.points[0].door_heat_flow).toBeUndefined();
    expect(data.points[0].roof_heat_flow).toBeUndefined();
    expect(data.points[0].wall_heat_flow).toBe(100);
  });

  it('reports honest absence when no component arrays exist (empty state driver)', () => {
    const r = makeResult({
      wall_heat_flow: [],
      roof_heat_flow: [],
      floor_heat_flow: [],
      window_heat_flow: [],
      door_heat_flow: [],
      ventilation_heat_flow: [],
      radiation_heat_flow: [],
      net_heat_flow: [],
    });
    const data = buildHeatFlowChartData(r);
    expect(data.hasData).toBe(false);
    expect(data.points).toEqual([]);
    expect(data.availableSeries).toEqual([]);
  });
});

describe('buildSolarChartData — real solar binding (WP7)', () => {
  it('binds incident and thermal-gain arrays verbatim (W)', () => {
    const r = makeResult({
      solar_power: Array.from({ length: 24 }, (_, i) => 500 + i),
      solar_thermal_gain: Array.from({ length: 24 }, (_, i) => 150 + i),
    });
    const solar = buildSolarChartData(r);
    expect(solar.hasData).toBe(true);
    expect(solar.hasIncident).toBe(true);
    expect(solar.hasThermalGain).toBe(true);
    expect(solar.points).toHaveLength(24);
    expect(solar.points[0].incident).toBe(500);
    expect(solar.points[3].thermalGain).toBe(153);
  });

  it('handles only-one-array-present honestly (no substitution)', () => {
    const r = makeResult({
      solar_power: Array.from({ length: 12 }, (_, i) => 400 + i),
      solar_thermal_gain: undefined,
    });
    const solar = buildSolarChartData(r);
    expect(solar.hasIncident).toBe(true);
    expect(solar.hasThermalGain).toBe(false);
    expect(solar.points).toHaveLength(12);
    expect(solar.points[0].thermalGain).toBe(0);
  });

  it('reports absence when both solar arrays are missing', () => {
    const solar = buildSolarChartData(makeResult());
    expect(solar.hasData).toBe(false);
    expect(solar.points).toEqual([]);
  });
});

describe('buildThermalStorageChartData — storage is labelled separately (WP4/WP7)', () => {
  it('returns the real storage flow capped at the shared hour count', () => {
    const r = makeResult({ radiation_heat_flow: Array.from({ length: 10 }, () => 15) });
    const storage = buildThermalStorageChartData(r, 10);
    expect(storage.hasData).toBe(true);
    expect(storage.points).toHaveLength(10);
    expect(storage.points[0].storage).toBe(-50);
  });

  it('reports absence when the optional array is missing', () => {
    const storage = buildThermalStorageChartData(makeResult({ thermal_storage_flow: undefined }), 24);
    expect(storage.hasData).toBe(false);
    expect(storage.points).toEqual([]);
  });
});

describe('no synthetic data (WP7)', () => {
  it('never fabricates points beyond the real hour count', () => {
    const r = makeResult({ wall_heat_flow: Array.from({ length: 5 }, () => 100) });
    const data = buildHeatFlowChartData(r);
    expect(data.points).toHaveLength(5);
    // The 6th hour simply does not exist — no interpolation.
    expect(data.points[5]).toBeUndefined();
  });
});
