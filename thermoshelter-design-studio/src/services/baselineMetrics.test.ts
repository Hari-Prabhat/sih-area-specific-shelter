/**
 * Baseline-metrics derivation tests (D4-A WP4) — Vitest
 * =====================================================
 * Comparison trust: baselines come ONLY from real simulation results.
 * The removed fabricated fallbacks (60 / 350 / 600 / 250) must never
 * reappear, and absence of a baseline must be explicit.
 */

import { describe, expect, it } from 'vitest';

import { deriveBaselineMetrics } from './baselineMetrics';
import type { CanonicalSimulationResult } from './api';
import type { SimulationResult } from '../types';

const canonicalResult = {
  city: 'leh',
  hours_simulated: 168,
  timestamps: [],
  indoor_temperatures: [],
  comfort_metrics: { avg: 18, min_t: 10, max_t: 24 },
  comfort_percentage: 72.4,
  discomfort_dh: 30,
  component_heat_loss_kwh: {
    wall_loss_kwh: 40,
    roof_loss_kwh: 20,
    floor_loss_kwh: 10,
    window_loss_kwh: 5,
    door_loss_kwh: 2,
  },
  total_heat_loss_kwh: 77,
  integrated_solar_energy_kwh: 123,
  solar_utilization_fraction: 0.5,
  energy_totals_kwh: { solar_gain_kwh: 123, heating_demand_kwh: 55, cooling_demand_kwh: 3 },
  effective_thermal_capacity_j_k: 2.5e7,
} as unknown as CanonicalSimulationResult;

const uiResult: SimulationResult = {
  avgInsideTemp: 18,
  minInsideTemp: 10,
  maxInsideTemp: 24,
  dailyTempVariation: 14,
  solarEnergyGain: 123,
  heatLossThroughWalls: 40,
  heatLossThroughRoof: 20,
  heatLossThroughFloor: 10,
  heatLossThroughWindows: 5,
  heatLossThroughDoors: 2,
  totalHeatLoss: 77,
  netHeatBalance: 46,
  thermalComfortIndex: 72,
  heatingDemandKwh: 55,
  hourlyTemperatures: [],
  monthlyTemperatures: [],
  recommendedImprovements: [],
};

describe('deriveBaselineMetrics (D4-A WP4: comparison trust)', () => {
  it('derives canonical metrics from a real simulation result', () => {
    const m = deriveBaselineMetrics({ ...uiResult, canonical: canonicalResult } as SimulationResult);
    expect(m.hasBaseline).toBe(true);
    expect(m.comfortPct).toBe(72);
    expect(m.heatingDemandKwh).toBe(55);
    expect(m.totalHeatLossKwh).toBe(77);
    expect(m.solarGainKwh).toBe(123);
  });

  it('derives genuine legacy-UI metrics when no canonical payload is attached', () => {
    const m = deriveBaselineMetrics(uiResult);
    expect(m.hasBaseline).toBe(true);
    expect(m.comfortPct).toBe(72);
    expect(m.heatingDemandKwh).toBe(55);
    expect(m.totalHeatLossKwh).toBe(77);
    expect(m.solarGainKwh).toBe(123);
  });

  it('reports honest absence when no baseline simulation exists', () => {
    const m = deriveBaselineMetrics(null);
    expect(m.hasBaseline).toBe(false);
    expect(m.comfortPct).toBeNull();
    expect(m.heatingDemandKwh).toBeNull();
    expect(m.totalHeatLossKwh).toBeNull();
    expect(m.solarGainKwh).toBeNull();
  });

  it('never fabricates values for undefined input', () => {
    const m = deriveBaselineMetrics(undefined);
    expect(m.hasBaseline).toBe(false);
    // The removed fabricated fallbacks must stay gone.
    expect(m.comfortPct).not.toBe(60);
    expect(m.heatingDemandKwh).not.toBe(350);
    expect(m.totalHeatLossKwh).not.toBe(600);
    expect(m.solarGainKwh).not.toBe(250);
  });
});
