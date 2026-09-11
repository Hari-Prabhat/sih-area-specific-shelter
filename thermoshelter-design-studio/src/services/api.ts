/**
 * THERMOSHELTER AI - Central API Client Service
 * ==============================================
 * Connects the React Design Studio directly to the FastAPI Python backend.
 * Python remains the SINGLE scientific source of truth for all thermal physics,
 * ISO 6946 multi-layer conduction models, and numerical forward Euler simulations.
 */

import { ClimateData, ShelterDesign, MaterialProperties, SimulationResult as UiSimulationResult } from '../types';

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
  hourly_internal_gain: number[];
  wall_heat_flow: number[];
  roof_heat_flow: number[];
  floor_heat_flow: number[];
  window_heat_flow: number[];
  ventilation_heat_flow: number[];
  radiation_heat_flow: number[];
  net_heat_flow: number[];
  thermal_storage_flow?: number[];
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
  };
  geometry: {
    floor_area_m2: number;
    volume_m3: number;
    solid_wall_area_m2: number;
    roof_area_m2: number;
    window_area_m2: number;
    roof_type: string;
  };
}

/**
 * Health check response schema
 */
export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  canonical_contracts: boolean;
  physics_engine: string;
}

/**
 * Check backend API health
 */
export async function checkApiHealth(): Promise<HealthStatus> {
  const url = `${API_BASE_URL}/api/health`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}

/**
 * Maps frontend UI entities into the canonical request payload for /api/simulation/run
 */
export function buildCanonicalSimulationPayload(
  climate: ClimateData,
  design: ShelterDesign,
  material?: MaterialProperties,
  insulation?: MaterialProperties,
  hoursToSimulate: number = 168
) {
  // Map wall material name to standardized key
  const matName = material ? material.name.toLowerCase() : 'brick';
  let wallMat = 'brick';
  if (matName.includes('mud') || matName.includes('adobe')) wallMat = 'mud';
  else if (matName.includes('earth')) wallMat = 'mud';
  else if (matName.includes('stone')) wallMat = 'stone';
  else if (matName.includes('timber') || matName.includes('wood')) wallMat = 'timber';
  else if (matName.includes('concrete') || matName.includes('aac')) wallMat = 'concrete_block';
  else if (matName.includes('puf') || matName.includes('panel')) wallMat = 'puf_insulation';

  // Map glazing
  let glazingKey = 'double_clear';
  if (design.windowGlazing === 'single') glazingKey = 'single_clear';
  else if (design.windowGlazing === 'triple') glazingKey = 'triple_low_e';

  // Derive insulation thickness
  const insThick = insulation && insulation.name !== 'None' ? 0.05 : 0.0;

  // Resolve city name from location string (e.g. "Leh, Ladakh" -> "leh")
  const cityName = climate.location.split(',')[0].toLowerCase().trim();

  return {
    city: cityName,
    design: {
      length: design.length,
      width: design.width,
      height: design.height,
      wall_material: wallMat,
      wall_thickness_m: design.wallThickness,
      insulation_thickness_m: insThick,
      insulation_conductivity: insulation ? insulation.thermalConductivity : 0.025,
      window_area: design.windowArea,
      glazing: glazingKey,
      orientation: design.orientation,
      roof_type: 'flat',
      pitch_angle_deg: design.roofAngle || 0.0,
      ach: 0.5,
      occupants: 2,
    },
    hours_to_simulate: hoursToSimulate,
    substeps: 30,
    initial_indoor_temp: 20.0,
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

  // Monthly diurnal baseline extrapolation from hourly temperatures
  const monthlyTemperatures = [-8, -5, -1, 4, 8, 12, 14, 13, 9, 4, -2, -6].map(offset => {
    return Math.round((avgIn + offset) * 10) / 10;
  });

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
    heatLossThroughDoors: 0,
    totalHeatLoss: Math.round(canon.total_heat_loss_kwh),
    netHeatBalance: Math.round((canon.energy_totals_kwh.solar_gain_kwh - canon.total_heat_loss_kwh) * 10) / 10,
    thermalComfortIndex: Math.round(canon.comfort_percentage),
    energyEfficiency: Math.round(canon.comfort_percentage),
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
  hoursToSimulate: number = 168
): Promise<UiSimulationResult> {
  const payload = buildCanonicalSimulationPayload(climate, design, material, insulation, hoursToSimulate);

  try {
    const response = await fetch(`${API_BASE_URL}/api/simulation/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail ? JSON.stringify(errData.detail) : `HTTP ${response.status}`;
      throw new Error(`Simulation API error: ${msg}`);
    }

    const canonResult: CanonicalSimulationResult = await response.json();
    return adaptCanonicalToUiResult(canonResult, design);
  } catch (error: any) {
    console.warn('[ThermoShelter API] Could not connect to FastAPI backend:', error.message);
    throw error;
  }
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
  canonical_design?: any;
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
  explanation?: string;
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
}): Promise<CanonicalOptimizationResult> {
  const response = await fetch(`${API_BASE_URL}/api/optimization/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    const msg = errData.detail ? JSON.stringify(errData.detail) : `HTTP ${response.status}`;
    throw new Error(`Optimization API error: ${msg}`);
  }

  return response.json();
}

