/**
 * THERMOSHELTER AI - Central API Client Service
 * ==============================================
 * Connects the React Design Studio directly to the FastAPI Python backend.
 * Python remains the SINGLE scientific source of truth for all thermal physics,
 * ISO 6946 multi-layer conduction models, and numerical forward Euler simulations.
 */

import { ClimateData, ShelterDesign, MaterialProperties, SimulationResult as UiSimulationResult } from '../types';
import { wallMaterialKey } from '../data/materials';
// D4-B: re-export the typed passive-strategy contract so consumers can import
// the whole climate/strategy surface from the single API module.
export type { PassiveStrategyDto, PassiveStrategyModel, StrategyComparisonPair } from './passiveStrategy';
// D4-C1: canonical backend material-ID mapping — the single authority for
// UI selection -> backend-resolvable material keys (physics integrity).
export { MATERIAL_BACKEND_MAP, resolveBackendMaterialId, wallMaterialKey } from '../data/materials';

const API_BASE_URL = (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_BASE_URL) || '';

/**
 * Canonical Python Simulation Result Structure from /api/simulation/run
 */
export interface CanonicalSimulationResult {
  city: string;
  indoor_temperatures: number[];
  outdoor_temperatures: number[];
  solar_irradiance: number[];
  solar_power: number[];
  solar_thermal_gain: number[];
  wall_heat_flow: number[];
  roof_heat_flow: number[];
  floor_heat_flow: number[];
  window_heat_flow: number[];
  /** Optional on the backend contract (services/contracts.py SimulationResult.door_heat_flow). */
  door_heat_flow?: number[];
  ventilation_heat_flow: number[];
  radiation_heat_flow: number[];
  net_heat_flow: number[];
  thermal_storage_flow?: number[];
  /** D4-C3: backend hourly arrays (services/contracts.py SimulationResult).
   * hourly_internal_gain: W sensible internal gain (occupants × per-person W).
   * hourly_heating/cooling_demand & hourly_net_load: auxiliary conditioning
   * power per hour (W); hourly_net_load = heating − cooling per hour. */
  hourly_internal_gain: number[];
  hourly_heating_demand?: number[];
  hourly_cooling_demand?: number[];
  hourly_net_load?: number[];
  comfort_status: string;
  comfort_status_series: string[];
  comfort_hours: number;
  comfort_percentage: number;
  discomfort_degree_hours: number;
  integrated_solar_energy_kwh: number;
  integrated_incident_solar_kwh: number;
  component_heat_loss_kwh: {
    wall_loss_kwh: number;
    roof_loss_kwh: number;
    floor_loss_kwh: number;
    window_loss_kwh: number;
    door_loss_kwh?: number;
    ventilation_loss_kwh: number;
    radiation_loss_kwh: number;
  };
  total_heat_loss_kwh: number;
  comfort_metrics: {
    avg: number;
    min_t: number;
    max_t: number;
    comfort_pct: number;
    discomfort_dh: number;
    status: string;
  };
  energy_totals_kwh: {
    solar_gain_kwh: number;
    incident_solar_kwh: number;
    wall_loss_kwh: number;
    roof_loss_kwh: number;
    floor_loss_kwh: number;
    window_loss_kwh: number;
    door_loss_kwh?: number;
    vent_loss_kwh: number;
    total_heat_loss_kwh: number;
    heating_demand_kwh: number;
    cooling_demand_kwh: number;
  };
  u_values: {
    wall_u: number;
    roof_u: number;
    floor_u: number;
    window_u: number;
    door_u?: number;
  };
  geometry: {
    floor_area_m2: number;
    volume_m3: number;
    solid_wall_area_m2: number;
    roof_area_m2: number;
    window_area_m2: number;
    door_area_m2?: number;
    roof_type: string;
  };
}

/**
 * Health check response schema (GET /api/health)
 */
export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  canonical_contracts: boolean;
  physics_engine: string;
  subsystems?: Record<string, string>;
}

// ==========================================================================
// CLIMATE & LOCATION INTELLIGENCE (Phase B)
// ==========================================================================

/**
 * Candidate location returned by GET /api/climate/geocode.
 * Coordinates are the operative values - the architecture works from
 * coordinates, never from a hardcoded city list.
 */
export interface ClimateLocationCandidate {
  place_name: string;
  latitude: number;
  longitude: number;
  elevation?: number | null;
  timezone?: string | null;
  country?: string | null;
  region?: string | null;
  source?: string | null;
}

/** Data mode of a fetched weather dataset. Never conflated by the backend. */
export type WeatherDatasetMode = 'live' | 'forecast' | 'historical' | 'design' | 'fallback';

/**
 * Typed hourly weather series (GET /api/climate/weather and the `series`
 * element of /api/climate/simulation-profile). Mirrors the backend
 * HourlyWeatherSeries contract; raw provider JSON never reaches the client.
 */
export interface HourlyWeatherSeriesDto {
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  timezone?: string | null;
  timestamps: string[];
  air_temperature_C: number[];
  relative_humidity_percent?: number[] | null;
  wind_speed_mps?: number[] | null;
  wind_direction_deg?: number[] | null;
  precipitation_mm?: number[] | null;
  cloud_cover_percent?: number[] | null;
  solar_global_W_m2?: number[] | null;
  solar_direct_W_m2?: number[] | null;
  solar_diffuse_W_m2?: number[] | null;
  data_mode: WeatherDatasetMode;
  provenance: string;
  provider: string;
  retrieval_timestamp: string;
  period_start: string;
  period_end: string;
  fallback_used: boolean;
  notes?: string;
}

/**
 * Response of GET /api/climate/simulation-profile: the full
 * location -> weather -> canonical ClimateProfile -> strategy pipeline.
 * `climate` is the canonical profile dict the simulation endpoint accepts.
 */
export interface SimulationClimateProfile {
  climate: {
    city?: string;
    climate_zone?: string;
    data_provenance?: string;
    data_source?: string;
    elevation_m?: number | null;
    timestamps?: string[];
    hourly_temperature: number[];
    hourly_direct_solar?: number[] | null;
    hourly_diffuse_solar?: number[] | null;
    [key: string]: unknown;
  };
  series: HourlyWeatherSeriesDto;
  strategy: Record<string, unknown> | null;
}

/**
 * Maps a climate API failure into user-facing text. Reuses the Phase A
 * ApiError classification - only a genuinely unreachable backend reports
 * "service unavailable"; invalid locations and provider failures keep
 * their own distinct, actionable messages.
 */
export function describeClimateError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.kind) {
      case 'unavailable':
        return 'Climate service unavailable. Start the FastAPI backend and try again.';
      case 'invalid_input':
      case 'simulation_failed':
      case 'http':
        return error.message;
    }
  }
  return error instanceof Error ? error.message : String(error);
}

/**
 * Resolves a free-text place query (city, district, state, or 'lat, lon')
 * into candidate locations for disambiguation. Never sends user text to
 * any provider other than the backend's allowlisted geocoder.
 */
export async function geocodeLocations(query: string, count: number = 5): Promise<ClimateLocationCandidate[]> {
  const url = `${API_BASE_URL}/api/climate/geocode?query=${encodeURIComponent(query)}&count=${count}`;
  let response: Response;
  try {
    response = await fetch(url, { headers: { Accept: 'application/json' } });
  } catch (error: any) {
    throw toApiError(error);
  }
  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
  const body = await response.json();
  return (body?.results ?? []) as ClimateLocationCandidate[];
}

/**
 * Runs the full backend climate pipeline for a location:
 * location -> coordinates -> hourly weather -> canonical ClimateProfile
 * -> passive strategy inputs. The returned `climate` object plugs directly
 * into /api/simulation/run, keeping Python the sole physics authority.
 */
export async function fetchSimulationClimateProfile(
  location: string,
  mode: WeatherDatasetMode = 'live',
  hours: number = 168,
): Promise<SimulationClimateProfile> {
  const params = new URLSearchParams({ location, mode, hours: String(hours) });
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/climate/simulation-profile?${params.toString()}`, {
      headers: { Accept: 'application/json' },
    });
  } catch (error: any) {
    throw toApiError(error);
  }
  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
  return response.json();
}

/**
 * Classified API failure kinds.
 * 'unavailable'  — backend unreachable (network error, connection refused, proxy down)
 * 'invalid_input'— request rejected by validation (HTTP 400/422)
 * 'simulation_failed' — simulation calculation failure on the server (HTTP 500)
 * 'http'         — any other non-OK HTTP response
 */
export type ApiErrorKind = 'unavailable' | 'invalid_input' | 'simulation_failed' | 'http';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly detail?: unknown;

  constructor(kind: ApiErrorKind, message: string, status?: number, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Extracts a short human-readable reason from a FastAPI error body.
 * Handles both {detail: {error, message}} shapes and native
 * {detail: [{loc, msg}, ...]} validation arrays.
 */
function extractApiReason(errData: any): string | undefined {
  const detail = errData?.detail;
  if (!detail) return undefined;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => {
        const loc = Array.isArray(d?.loc) ? d.loc.join('.') : d?.loc;
        return loc ? `${loc}: ${d?.msg ?? ''}` : (d?.msg ?? '');
      })
      .filter(Boolean)
      .join('; ');
  }
  if (typeof detail === 'object') {
    return detail.message ?? detail.error;
  }
  return String(detail);
}

function truncate(text: string, maxLen: number = 160): string {
  return text.length > maxLen ? `${text.slice(0, maxLen)}…` : text;
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  let errData: any = null;
  try {
    errData = await response.json();
  } catch {
    // Non-JSON error body
  }
  const reason = extractApiReason(errData);
  if (response.status === 400 || response.status === 422) {
    return new ApiError(
      'invalid_input',
      `Invalid design input${reason ? `: ${truncate(reason)}` : ''}`,
      response.status,
      errData,
    );
  }
  if (response.status >= 500) {
    // A genuine FastAPI 5xx always serializes a JSON body. A 5xx with a
    // non-JSON body comes from the transport layer (e.g. the Vite proxy
    // responding ECONNREFUSED when the backend process is down), so it is
    // classified as an unreachable backend rather than a simulation failure.
    if (!errData) {
      return new ApiError(
        'unavailable',
        `Backend unreachable (HTTP ${response.status})`,
        response.status,
      );
    }
    return new ApiError(
      'simulation_failed',
      `Simulation failed${reason ? `: ${truncate(reason)}` : ''}`,
      response.status,
      errData,
    );
  }
  return new ApiError(
    'http',
    `Request failed (HTTP ${response.status})${reason ? `: ${truncate(reason)}` : ''}`,
    response.status,
    errData,
  );
}

function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  // fetch() rejects with TypeError on network failure / connection refused
  if (error instanceof TypeError) {
    return new ApiError('unavailable', `Backend unreachable: ${error.message}`);
  }
  const msg = error instanceof Error ? error.message : String(error);
  return new ApiError('http', msg);
}

/**
 * Maps an error thrown by the API client into user-facing text.
 * Only a genuinely unreachable backend reports "service unavailable";
 * validation and simulation failures keep their own distinct messages.
 * Full technical detail remains available on the console via the caller.
 */
export function describeApiError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.kind) {
      case 'unavailable':
        return 'Simulation service unavailable. Start the FastAPI backend and try again.';
      case 'invalid_input':
      case 'simulation_failed':
      case 'http':
        return error.message;
    }
  }
  return error instanceof Error ? error.message : String(error);
}

/**
 * Check backend API health
 */
export async function checkApiHealth(): Promise<HealthStatus> {
  const url = `${API_BASE_URL}/api/health`;
  let response: Response;
  try {
    response = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
  } catch (error: any) {
    throw toApiError(error);
  }
  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
  return response.json();
}

/**
 * Maps frontend UI entities into the canonical request payload for /api/simulation/run
 *
 * When a backend-derived climate profile is supplied (Phase B), its canonical
 * dict overrides the preset-city lookup so the simulation runs on real
 * provider weather for the selected location.
 */
/**
 * Canonical solver configuration for direct simulations — mirrors the backend
 * SimulationInput defaults (services/contracts.py: substeps=60,
 * initial_indoor_temp=20.0).
 *
 * Fidelity architecture (INTENTIONAL, backend-owned — services/optimize.py):
 *   - Optimizer trials evaluate candidates at substeps=15 (search speed).
 *   - The backend then re-verifies the best design at substeps=60
 *     ("final authoritative simulation", optimize.py).
 *   - Ranked-candidate verification sims also run at substeps=15.
 *   - Direct simulation always runs at the canonical substeps=60.
 * This two-tier fidelity is deliberate optimizer performance engineering,
 * not an inconsistency — do not "unify" it from the frontend.
 */
const CANONICAL_DIRECT_SIMULATION = {
  substeps: 60,
  initial_indoor_temp: 20.0,
} as const;

/** Backend air-changes-per-hour preset (services/formula_constants.py DEFAULT_ACH). */
export const DEFAULT_ACH = 0.5;

export function buildCanonicalSimulationPayload(
  climate: ClimateData,
  design: ShelterDesign,
  material?: MaterialProperties,
  insulation?: MaterialProperties,
  hoursToSimulate: number = 168,
  climateProfile?: SimulationClimateProfile,
  /** D4-A WP1: occupancy from the mission requirements drives internal gains. */
  occupants: number = 2,
  /** D4-A WP1: air changes per hour — explicit design state (DEFAULT_ACH preset). */
  ach: number = DEFAULT_ACH,
) {
  // Map glazing
  let glazingKey = 'double_clear';
  if (design.windowGlazing === 'single') glazingKey = 'single_clear';
  else if (design.windowGlazing === 'triple') glazingKey = 'triple_low_e';

  // D4-A WP2: insulation thickness is explicit design state (cm → m). The
  // authoritative condition is the design state itself (insulationType /
  // insulationThickness) — a caller may still pass a previously selected
  // insulation material for conductivity without implying insulation exists.
  const insThick =
    design.insulationType !== 'None' && design.insulationThickness > 0
      ? design.insulationThickness / 100.0
      : 0.0;

  // Resolve city name from location string (e.g. "Leh, Ladakh" -> "leh")
  const cityName = climateProfile?.climate?.city
    ?? climate.location.split(',')[0].toLowerCase().trim();

  return {
    city: cityName,
    design: {
      length: design.length,
      width: design.width,
      height: design.height,
      // Product-hardening pass: the canonical form reaches the engine —
      // a dome is simulated AS a dome (curved envelope), never flattened.
      shape: design.shape,
      wall_material: wallMaterialKey(material?.name),
      wall_thickness_m: design.wallThickness,
      insulation_thickness_m: insThick,
      insulation_conductivity: insulation ? insulation.thermalConductivity : 0.025,
      window_area: design.windowArea,
      door_area: design.doorArea ?? 2.0,
      glazing: glazingKey,
      orientation: design.orientation,
      roof_type: (design.roofAngle && design.roofAngle > 0) ? 'pitched' : 'flat',
      pitch_angle_deg: design.roofAngle || 0.0,
      // D4-A WP1: the canonical design field is authoritative; the loose
      // parameter remains only as a fallback for legacy callers.
      ach: design.ach ?? ach,
      occupants: Math.max(1, Math.round(occupants)),
      thermal_mass_enabled: design.thermalMassEnabled,
      thermal_mass_thickness_m: design.thermalMassEnabled ? design.thermalMassThickness / 100.0 : 0.0,
    },
    hours_to_simulate: hoursToSimulate,
    substeps: CANONICAL_DIRECT_SIMULATION.substeps,
    initial_indoor_temp: CANONICAL_DIRECT_SIMULATION.initial_indoor_temp,
    ...(climateProfile ? { climate: climateProfile.climate } : {}),
  };
}

/**
 * Transforms canonical Python SimulationResult into the UI format expected by
 * SimulationResults.tsx and ComparativeAnalysis.tsx, while attaching the raw result.
 */
export function adaptCanonicalToUiResult(
  canon: CanonicalSimulationResult,
  design: ShelterDesign
): UiSimulationResult & { canonical: CanonicalSimulationResult } {
  const avgIn = Math.round(canon.comfort_metrics.avg * 10) / 10;
  const minIn = Math.round(canon.comfort_metrics.min_t * 10) / 10;
  const maxIn = Math.round(canon.comfort_metrics.max_t * 10) / 10;
  const variation = Math.round((maxIn - minIn) * 10) / 10;

  // Recommendations derived from physical results
  const recommendations: string[] = [];
  const roofLoss = canon.component_heat_loss_kwh.roof_loss_kwh;
  const wallLoss = canon.component_heat_loss_kwh.wall_loss_kwh;

  if (roofLoss > wallLoss * 0.4) {
    recommendations.push('Increase roof insulation to mitigate significant roof conduction losses.');
  }
  if (canon.comfort_percentage < 60) {
    recommendations.push('Indoor thermal comfort is below optimal. Increase envelope insulation thickness or upgrade glazing to low-E.');
  }
  if (design.orientation < 135 || design.orientation > 225) {
    recommendations.push('Reorient principal glazing towards South (180°) for enhanced passive solar harvesting in winter.');
  }
  if (recommendations.length === 0) {
    recommendations.push('Design is well-balanced for the targeted climatic conditions.');
  }

  // Monthly diurnal projection is unavailable for standard 168-hour simulation horizons.
  // Avoid synthetic offset extrapolation to prevent misleading engineering evaluations.
  const monthlyTemperatures: number[] = [];

  return {
    avgInsideTemp: avgIn,
    minInsideTemp: minIn,
    maxInsideTemp: maxIn,
    dailyTempVariation: variation,
    solarEnergyGain: Math.round(canon.integrated_solar_energy_kwh * 10) / 10,
    heatLossThroughWalls: Math.round(canon.component_heat_loss_kwh.wall_loss_kwh),
    heatLossThroughRoof: Math.round(canon.component_heat_loss_kwh.roof_loss_kwh),
    heatLossThroughFloor: Math.round(canon.component_heat_loss_kwh.floor_loss_kwh),
    heatLossThroughWindows: Math.round(canon.component_heat_loss_kwh.window_loss_kwh),
    heatLossThroughDoors: Math.round(canon.component_heat_loss_kwh.door_loss_kwh || 0),
    totalHeatLoss: Math.round(canon.total_heat_loss_kwh),
    netHeatBalance: Math.round((canon.energy_totals_kwh.solar_gain_kwh - canon.total_heat_loss_kwh) * 10) / 10,
    thermalComfortIndex: Math.round(canon.comfort_percentage),
    heatingDemandKwh: Math.round(canon.energy_totals_kwh.heating_demand_kwh),
    hourlyTemperatures: canon.indoor_temperatures.slice(0, 24).map(t => Math.round(t * 10) / 10),
    monthlyTemperatures,
    recommendedImprovements: recommendations,
    canonical: canon,
  };
}

/**
 * Executes a physically rigorous thermal simulation by dispatching to FastAPI.
 * Fallback to client-side prototype if backend is unavailable.
 */
export async function runSimulationViaApi(
  climate: ClimateData,
  design: ShelterDesign,
  material?: MaterialProperties,
  insulation?: MaterialProperties,
  hoursToSimulate: number = 168,
  climateProfile?: SimulationClimateProfile,
  occupants: number = 2,
  ach: number = DEFAULT_ACH,
): Promise<UiSimulationResult> {
  const payload = buildCanonicalSimulationPayload(climate, design, material, insulation, hoursToSimulate, climateProfile, occupants, ach);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/simulation/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (error: any) {
    const apiError = toApiError(error);
    console.warn('[ThermoShelter API] Could not connect to FastAPI backend:', apiError.message);
    throw apiError;
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const canonResult: CanonicalSimulationResult = await response.json();
  return adaptCanonicalToUiResult(canonResult, design);
}

/**
 * Optimization Candidate structure from /api/optimization/run
 */
export interface CanonicalOptimizationCandidate {
  rank: number;
  label: string;
  rationale: string;
  overall_score: number;
  sub_scores: {
    comfort: number;
    efficiency: number;
    solar: number;
  };
  insulation_mm: number;
  insulation_thickness_m: number;
  window_area_m2: number;
  wall_material: string;
  wall_material_name: string;
  glazing: string;
  glazing_name: string;
  orientation: string;
  comfort_hours: number;
  comfort_percentage: number;
  discomfort_dh: number;
  total_heat_loss_kwh: number;
  solar_gain_kwh: number;
  u_values: {
    wall_u: number;
    roof_u: number;
    floor_u: number;
    window_u: number;
  };
  heating_demand_kwh: number;
  cooling_demand_kwh: number;
  total_conditioning_demand_kwh: number;
  effective_thermal_capacity_j_k: number;
  /** Phase C: candidate thermal-mass level (none | low | medium | high). */
  thermal_mass_level?: string;
  /** Phase C: provenance of the climate scenario this candidate was evaluated against. */
  climate_provenance?: string | null;
  climate_data_mode?: string | null;
  climate_fallback_used?: boolean | null;
  // ------------------------------------------------------------------
  // D5-A geometry contract (optional; populated by the backend from its
  // own engine-reported values). When absent (legacy candidates) consumers
  // MUST NOT invent geometry - Apply keeps the current design dimensions.
  // ------------------------------------------------------------------
  length_m?: number | null;
  width_m?: number | null;
  height_m?: number | null;
  floor_area_m2?: number | null;
  /** Thermal-relevant gross envelope area / enclosed volume (1/m). */
  surface_to_volume_ratio?: number | null;
  /** The candidate's ACTUAL simulated shelter form (rectangular/cylindrical/dome/pyramid).
   *  Null on legacy records; always populated by the current optimizer. */
  shape?: string | null;
  /** Set on the baseline user-design candidate included in the comfort-first ranking. */
  is_baseline?: boolean | null;
  canonical_design?: any;
}  /**
 * Dual-output optimization (E2): the separate comfort-first recommendation
 * pass. Same authoritative simulation/feasibility/bounds as the
 * user-constrained run - only the objective differs (maximize simulated
 * comfort hours). status='no_comfort_feasible' is an honest search outcome,
 * NOT an execution failure.
 */
export interface ComfortFirstRecommendation {
  status: 'ok' | 'no_comfort_feasible' | 'error';
  message?: string;
  recommendation?: CanonicalOptimizationCandidate | null;
  n_trials?: number | null;
  n_pruned?: number | null;
}

/**
 * Optimization Result structure from /api/optimization/run
 */
export interface CanonicalOptimizationResult {
  city: string;
  home_type: string;
  insulation_thickness_m: number;
  insulation_mm: number;
  window_area_m2: number;
  wall_material: string;
  glazing: string;
  glazing_name: string;
  orientation: string;
  discomfort_score: number;
  simulation_result: any;
  ranked_designs: CanonicalOptimizationCandidate[];
  recommended_design?: CanonicalOptimizationCandidate;
  n_trials: number;
  /** D5-B: candidates rejected by pre-simulation geometry feasibility. */
  n_pruned?: number;
  explanation?: string;
  /** Phase C provenance of the climate scenario the optimization ran against. */
  climate_provenance?: string | null;
  climate_fallback_used?: boolean | null;
  /** E2: separate comfort-first recommendation pass output (optional). */
  recommendation?: ComfortFirstRecommendation | null;
}

/**
 * Dispatches a multi-objective Bayesian design optimization request to FastAPI.
 */
export async function runOptimizationViaApi(payload: {
  city?: string;
  home_type?: string;
  design?: any;
  climate?: any;
  n_trials?: number;
  substeps?: number;
  hours_to_simulate?: number;
  weights?: { comfort: number; efficiency: number; solar: number };
  // D5-A/D5-B geometry optimization. Undefined/absent keeps current
  // fixed-geometry behaviour end-to-end. All bounds are PROPOSED PROTOTYPE
  // ENGINEERING ASSUMPTIONS supplied by the caller - never invented here.
  optimize_geometry?: boolean;
  min_length_m?: number;
  max_length_m?: number;
  min_width_m?: number;
  max_width_m?: number;
  min_height_m?: number;
  max_height_m?: number;
  /** Orientation-independent aspect ratio max(L/W, W/L) bounds (optional). */
  min_aspect_ratio?: number;
  max_aspect_ratio?: number;
}): Promise<CanonicalOptimizationResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/optimization/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (error: any) {
    throw toApiError(error);
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return response.json();
}

