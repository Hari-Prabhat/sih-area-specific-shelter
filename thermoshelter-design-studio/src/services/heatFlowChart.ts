/**
 * THERMOSHELTER — Heat-flow chart data preparation (D4-B WP4)
 * ==========================================================
 * Pure, testable transforms from the canonical SimulationResult's REAL
 * hourly arrays into chart points. No synthesis, no interpolation, no
 * substitution: when arrays are absent the result honestly reports
 * hasData=false, and the chart renders an empty state.
 *
 * Units: component heat-flow arrays are hourly average power in W
 * (services/simulation_service.py: each substep-integrated component is
 * divided by substeps per hour). Series are defensively aligned to the
 * shortest available length; never padded or extrapolated.
 */

import { CanonicalSimulationResult } from './api';

/** Component heat-flow series (W) — label, key, and render color. */
export interface HeatFlowSeriesDef {
  key: string;
  label: string;
  color: string;
}

/**
 * The seven envelope/ventilation component flows. All real backend arrays —
 * no derived or synthetic series. Colors are presentation-only.
 */
export const HEAT_FLOW_SERIES: HeatFlowSeriesDef[] = [
  { key: 'wall_heat_flow', label: 'Wall', color: '#f59e0b' },
  { key: 'roof_heat_flow', label: 'Roof', color: '#ef4444' },
  { key: 'floor_heat_flow', label: 'Floor', color: '#3b82f6' },
  { key: 'window_heat_flow', label: 'Window', color: '#06b6d4' },
  { key: 'door_heat_flow', label: 'Door', color: '#10b981' },
  { key: 'ventilation_heat_flow', label: 'Ventilation', color: '#8b5cf6' },
  { key: 'radiation_heat_flow', label: 'Radiation', color: '#ec4899' },
];

/**
 * One chart point per simulation hour. Every field is the actual backend
 * value at that hour — absent arrays are simply omitted from the point.
 */
export interface HeatFlowPoint extends Record<string, number | string | undefined> {
  hour: number;
  /** Hour label "D1 00:00" for the x-axis. */
  time: string;
  /** Net heat flow (W) — balance of all gains/losses; rendered as its own line. */
  net_heat_flow?: number;
}

/** Result of aligning the real arrays for the component chart. */
export interface HeatFlowChartData {
  points: HeatFlowPoint[];
  /** Series definitions actually present in the data (excludes absent arrays). */
  availableSeries: HeatFlowSeriesDef[];
  hasData: boolean;
  /** Hours covered after defensive alignment to the shortest common length. */
  hourCount: number;
}

function hourLabel(hour: number): string {
  const day = Math.floor(hour / 24) + 1;
  const hr = hour % 24;
  return `D${day} ${hr.toString().padStart(2, '0')}:00`;
}

/**
 * Aligns the component heat-flow arrays to the shortest common length and
 * produces chart points. Missing/invalid arrays are excluded (never zero-
 * filled); with no valid arrays at all, hasData=false drives an honest
 * empty state.
 */
export function buildHeatFlowChartData(canon: CanonicalSimulationResult): HeatFlowChartData {
  const series: Record<string, number[] | undefined> = {
    wall_heat_flow: canon.wall_heat_flow,
    roof_heat_flow: canon.roof_heat_flow,
    floor_heat_flow: canon.floor_heat_flow,
    window_heat_flow: canon.window_heat_flow,
    door_heat_flow: canon.door_heat_flow,
    ventilation_heat_flow: canon.ventilation_heat_flow,
    radiation_heat_flow: canon.radiation_heat_flow,
  };

  // Keep only genuinely usable arrays (non-empty, all-finite numbers).
  const validSeries = HEAT_FLOW_SERIES.filter((def) => {
    const arr = series[def.key];
    return (
      Array.isArray(arr) &&
      arr.length > 0 &&
      arr.every((v) => typeof v === 'number' && Number.isFinite(v))
    );
  });
  const availableSeries = validSeries.map((def) => ({
    key: def.key,
    label: def.label,
    color: def.color,
  }));

  // Net heat flow is rendered separately (not a stacked component) but is
  // validated and length-aligned with the components.
  const net = canon.net_heat_flow;
  const hasNet =
    Array.isArray(net) && net.length > 0 && net.every((v) => typeof v === 'number' && Number.isFinite(v));

  const usable = validSeries.map((def) => series[def.key] as number[]);
  if (hasNet) usable.push(net);
  if (usable.length === 0) {
    return { points: [], availableSeries: [], hasData: false, hourCount: 0 };
  }

  // Defensive alignment: shortest common length across present arrays. No
  // padding — the chart never shows values the backend did not compute.
  const hourCount = Math.min(...usable.map((arr) => arr.length), canon.indoor_temperatures?.length ?? Infinity);

  const points: HeatFlowPoint[] = [];
  for (let i = 0; i < hourCount; i++) {
    const point: HeatFlowPoint = { hour: i, time: hourLabel(i) };
    for (const def of validSeries) {
      point[def.key] = (series[def.key] as number[])[i];
    }
    if (hasNet) point.net_heat_flow = net[i];
    points.push(point);
  }
  return { points, availableSeries, hasData: true, hourCount };
}

/**
 * Solar chart data from the REAL solar arrays. `solar_power` is the incident
 * solar power on the glazing (W); `solar_thermal_gain` is the useful SHGC-
 * filtered thermal gain (W). Absent arrays yield hasData=false.
 */
export interface SolarChartData {
  points: { hour: number; time: string; incident: number; thermalGain: number }[];
  hasIncident: boolean;
  hasThermalGain: boolean;
  hasData: boolean;
}

export function buildSolarChartData(canon: CanonicalSimulationResult): SolarChartData {
  const incident = canon.solar_power;
  const gain = canon.solar_thermal_gain;

  const hasIncident = Array.isArray(incident) && incident.length > 0;
  const hasThermalGain = Array.isArray(gain) && gain.length > 0;
  if (!hasIncident && !hasThermalGain) {
    return { points: [], hasIncident: false, hasThermalGain: false, hasData: false };
  }

  // Align to the shortest present array (defensive, no padding).
  const lengths: number[] = [];
  if (hasIncident) lengths.push(incident.length);
  if (hasThermalGain) lengths.push(gain.length);
  const hourCount = Math.min(...lengths, canon.indoor_temperatures?.length ?? Infinity);

  const points: SolarChartData['points'] = [];
  for (let i = 0; i < hourCount; i++) {
    points.push({
      hour: i,
      time: hourLabel(i),
      incident: hasIncident ? Math.round(incident[i] * 10) / 10 : 0,
      thermalGain: hasThermalGain ? Math.round(gain[i] * 10) / 10 : 0,
    });
  }
  return { points, hasIncident, hasThermalGain, hasData: true };
}

/** Optional thermal-storage series (W) — labelled as storage flow, NOT heat loss. */
export function buildThermalStorageChartData(
  canon: CanonicalSimulationResult,
  hourCount: number,
): { points: { hour: number; time: string; storage: number }[]; hasData: boolean } {
  const storage = canon.thermal_storage_flow;
  if (!Array.isArray(storage) || storage.length === 0 || hourCount <= 0) {
    return { points: [], hasData: false };
  }
  const n = Math.min(hourCount, storage.length);
  const points: { hour: number; time: string; storage: number }[] = [];
  for (let i = 0; i < n; i++) {
    points.push({ hour: i, time: hourLabel(i), storage: storage[i] });
  }
  return { points, hasData: true };
}

/* ─────────────────────────────────────────────────────────────────────────
 * D4-C3: Internal Gains & Auxiliary Energy — REAL backend arrays only.
 * hourly_internal_gain: sensible internal gain (W, occupants × per-person W).
 * hourly_heating_demand / hourly_cooling_demand: auxiliary conditioning
 * power (W) required per hour. hourly_net_load = heating − cooling (W).
 * Same honesty rules as above: validate, align to the shortest present
 * array, never pad, zero-fill, or synthesize.
 * ────────────────────────────────────────────────────────────────────── */

/** One point per hour of the gains/auxiliary-energy chart. */
export interface GainsChartPoint extends Record<string, number | string | undefined> {
  hour: number;
  time: string;
  internalGain?: number;
  heatingDemand?: number;
  coolingDemand?: number;
  netLoad?: number;
}

export interface GainsChartData {
  points: GainsChartPoint[];
  hasInternalGain: boolean;
  hasHeatingDemand: boolean;
  hasCoolingDemand: boolean;
  hasNetLoad: boolean;
  hasData: boolean;
  hourCount: number;
}

export function buildGainsChartData(canon: CanonicalSimulationResult): GainsChartData {
  const internal = canon.hourly_internal_gain;
  const heating = canon.hourly_heating_demand;
  const cooling = canon.hourly_cooling_demand;
  const netLoad = canon.hourly_net_load;

  const ok = (a: unknown): a is number[] =>
    Array.isArray(a) && a.length > 0 && a.every((v) => typeof v === 'number' && Number.isFinite(v));

  const hasInternalGain = ok(internal);
  const hasHeatingDemand = ok(heating);
  const hasCoolingDemand = ok(cooling);
  const hasNetLoad = ok(netLoad);

  if (!hasInternalGain && !hasHeatingDemand && !hasCoolingDemand && !hasNetLoad) {
    return {
      points: [],
      hasInternalGain: false,
      hasHeatingDemand: false,
      hasCoolingDemand: false,
      hasNetLoad: false,
      hasData: false,
      hourCount: 0,
    };
  }

  const lengths: number[] = [];
  if (hasInternalGain) lengths.push((internal as number[]).length);
  if (hasHeatingDemand) lengths.push((heating as number[]).length);
  if (hasCoolingDemand) lengths.push((cooling as number[]).length);
  if (hasNetLoad) lengths.push((netLoad as number[]).length);
  const hourCount = Math.min(...lengths, canon.indoor_temperatures?.length ?? Infinity);

  const points: GainsChartPoint[] = [];
  for (let i = 0; i < hourCount; i++) {
    const p: GainsChartPoint = { hour: i, time: hourLabel(i) };
    if (hasInternalGain) p.internalGain = (internal as number[])[i];
    if (hasHeatingDemand) p.heatingDemand = (heating as number[])[i];
    if (hasCoolingDemand) p.coolingDemand = (cooling as number[])[i];
    if (hasNetLoad) p.netLoad = (netLoad as number[])[i];
    points.push(p);
  }
  return {
    points,
    hasInternalGain,
    hasHeatingDemand,
    hasCoolingDemand,
    hasNetLoad,
    hasData: true,
    hourCount,
  };
}
