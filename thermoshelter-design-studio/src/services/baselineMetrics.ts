/**
 * THERMOSHELTER — Comparative-analysis baseline derivation (D4-A WP4)
 * ===================================================================
 * Comparison trust: baseline metrics may ONLY come from a real simulation
 * result. If none exists, every metric is null and the caller must render a
 * truthful "run a baseline simulation" state. The former fabricated fallback
 * values (60 / 500×0.7 / 600 / 250) were removed and must never return.
 */

import type { CanonicalSimulationResult } from './api';
import type { SimulationResult } from '../types';

export interface BaselineMetrics {
  hasBaseline: boolean;
  comfortPct: number | null;
  heatingDemandKwh: number | null;
  totalHeatLossKwh: number | null;
  solarGainKwh: number | null;
}

/**
 * Derives comparison baseline metrics from a REAL simulation result only.
 *
 * - Canonical results (direct simulation via FastAPI) expose the authoritative
 *   physics totals on the attached `canonical` payload.
 * - Legacy UI-adapted results (e.g. material sweeps) contribute only their
 *   genuine backend-derived fields — no derived fakes.
 * - No result → `hasBaseline: false` with every metric null.
 */
export function deriveBaselineMetrics(baselineResult?: SimulationResult | null): BaselineMetrics {
  const canonical = (baselineResult as { canonical?: CanonicalSimulationResult } | null | undefined)
    ?.canonical;
  if (canonical) {
    return {
      hasBaseline: true,
      comfortPct: Math.round(canonical.comfort_percentage),
      heatingDemandKwh: Math.round(canonical.energy_totals_kwh.heating_demand_kwh),
      totalHeatLossKwh: Math.round(canonical.total_heat_loss_kwh),
      solarGainKwh: Math.round(canonical.integrated_solar_energy_kwh),
    };
  }
  if (baselineResult) {
    return {
      hasBaseline: true,
      comfortPct: Math.round(baselineResult.thermalComfortIndex),
      heatingDemandKwh: Math.round(baselineResult.heatingDemandKwh),
      totalHeatLossKwh: Math.round(baselineResult.totalHeatLoss),
      solarGainKwh: Math.round(baselineResult.solarEnergyGain),
    };
  }
  return {
    hasBaseline: false,
    comfortPct: null,
    heatingDemandKwh: null,
    totalHeatLossKwh: null,
    solarGainKwh: null,
  };
}
