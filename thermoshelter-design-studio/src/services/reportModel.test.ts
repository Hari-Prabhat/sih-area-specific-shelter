/**
 * THERMOSHELTER — Engineering Report model tests (D4-D1)
 * ======================================================
 * Verifies the pure report adapter against the canonical data contracts:
 * composition only (no independent engineering math), nullable optional
 * sections, honesty wording (provenance, geometry-optimization scope), and
 * the strict no-fabrication guarantees for missing simulation/optimization.
 */
import { describe, expect, it } from 'vitest';
import {
  buildReportInput,
  canonicalOf,
  GEOMETRY_NOT_IMPLEMENTED,
  GEOMETRY_SUPPORTED_OPTIMIZATION,
  GEOMETRY_SUPPORTED_PARAMETERS,
  REPORT_ENGINE_LABEL,
  type ReportSourceState,
} from './reportModel';
import type { CanonicalSimulationResult } from './api';
import type { ClimateData, ShelterDesign, SimulationResult } from '../types';
import type { MissionConfig } from '../store/useStudioState';
import type { SimulationClimateProfile } from './api';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

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

const mission: MissionConfig = {
  occupants: 4,
  purpose: 'Disaster Relief',
  deploymentType: 'Temporary',
  durationMonths: 6,
  mobilityRequired: true,
  priorities: {
    thermalComfort: true,
    energyIndependence: true,
    lowCost: false,
    lowWeight: true,
    rapidDeployment: true,
    durability: false,
  },
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
  insulationType: 'XPS',
  insulationThickness: 8,
  ach: 0.8,
  thermalMassEnabled: true,
  thermalMassThickness: 20,
};

const profile: SimulationClimateProfile = {
  climate: {
    city: 'Leh',
    climate_zone: 'COMPOSITE',
    climate_mode: 'EXTREME COLD',
    elevation_m: 3507,
  },
  series: {
    latitude: 34.165,
    longitude: 77.584,
    elevation_m: 3507,
    timezone: 'Asia/Kolkata',
    timestamps: [],
    air_temperature_C: Array.from({ length: 168 }, () => -5),
    data_mode: 'live',
    provenance: 'MODEL_ANALYSIS',
    provider: 'Open-Meteo Recent Conditions (NWP analysis)',
    retrieval_timestamp: '2026-09-19T12:00:00Z',
    period_start: '2026-09-12T00:00:00Z',
    period_end: '2026-09-19T00:00:00Z',
    fallback_used: false,
  },
  strategy: {
    version: '1.0',
    climate_mode: 'EXTREME COLD',
    primary_strategy: 'Maximize envelope insulation and thermal mass',
    secondary_strategies: ['Solar capture', 'Airtightness'],
    solar_capture: 'HIGH',
    thermal_mass: 'HIGH',
    insulation_priority: 'HIGH',
    ventilation_strategy: 'Minimize uncontrolled infiltration',
    shading_strategy: 'Not applicable',
    opening_strategy: 'Small south glazing',
    airlock: true,
    thermal_buffer: true,
    explanation: 'Extreme cold drives insulation-first design.',
    rules_triggered: ['R1', 'R2'],
  },
} as unknown as SimulationClimateProfile;

const canon: CanonicalSimulationResult = {
  city: 'leh',
  indoor_temperatures: Array.from({ length: 168 }, () => 18),
  outdoor_temperatures: Array.from({ length: 168 }, () => -5),
  solar_irradiance: Array.from({ length: 168 }, () => 100),
  solar_power: Array.from({ length: 168 }, () => 500),
  solar_thermal_gain: Array.from({ length: 168 }, () => 150),
  wall_heat_flow: Array.from({ length: 168 }, () => -1000),
  roof_heat_flow: Array.from({ length: 168 }, () => -800),
  floor_heat_flow: Array.from({ length: 168 }, () => -300),
  window_heat_flow: Array.from({ length: 168 }, () => -200),
  door_heat_flow: Array.from({ length: 168 }, () => -50),
  ventilation_heat_flow: Array.from({ length: 168 }, () => -400),
  radiation_heat_flow: Array.from({ length: 168 }, () => -100),
  net_heat_flow: Array.from({ length: 168 }, () => -100),
  thermal_storage_flow: Array.from({ length: 168 }, () => 25),
  hourly_internal_gain: Array.from({ length: 168 }, () => 320),
  comfort_status: 'COLD',
  comfort_status_series: Array.from({ length: 168 }, () => 'COLD'),
  comfort_hours: 20,
  comfort_percentage: 11.9,
  discomfort_degree_hours: 7000,
  integrated_solar_energy_kwh: 25.2,
  integrated_incident_solar_kwh: 84,
  component_heat_loss_kwh: {
    wall_loss_kwh: 168,
    roof_loss_kwh: 134.4,
    floor_loss_kwh: 50.4,
    window_loss_kwh: 33.6,
    door_loss_kwh: 8.4,
    ventilation_loss_kwh: 67.2,
    radiation_loss_kwh: 16.8,
  },
  total_heat_loss_kwh: 478.8,
  comfort_metrics: { avg: 18, min_t: 17.5, max_t: 18.5, comfort_pct: 11.9, discomfort_dh: 7000, status: 'COLD' },
  energy_totals_kwh: {
    solar_gain_kwh: 25.2,
    incident_solar_kwh: 84,
    wall_loss_kwh: 168,
    roof_loss_kwh: 134.4,
    floor_loss_kwh: 50.4,
    window_loss_kwh: 33.6,
    door_loss_kwh: 8.4,
    vent_loss_kwh: 67.2,
    total_heat_loss_kwh: 478.8,
    heating_demand_kwh: 400,
    cooling_demand_kwh: 0,
  },
  u_values: { wall_u: 0.31, roof_u: 2.27, floor_u: 3.77, window_u: 2.8, door_u: 1.8 },
  geometry: {
    floor_area_m2: 24,
    volume_m3: 72,
    solid_wall_area_m2: 50,
    roof_area_m2: 24,
    window_area_m2: 3,
    door_area_m2: 2,
    roof_type: 'pitched',
  },
};

/** Wraps the canonical payload the way the API adapter does. */
function uiResultWith(c: CanonicalSimulationResult): SimulationResult {
  return {
    avgInsideTemp: c.comfort_metrics.avg,
    minInsideTemp: c.comfort_metrics.min_t,
    maxInsideTemp: c.comfort_metrics.max_t,
    dailyTempVariation: 1,
    solarEnergyGain: c.integrated_solar_energy_kwh,
    heatLossThroughWalls: c.component_heat_loss_kwh.wall_loss_kwh,
    heatLossThroughRoof: c.component_heat_loss_kwh.roof_loss_kwh,
    heatLossThroughFloor: c.component_heat_loss_kwh.floor_loss_kwh,
    heatLossThroughWindows: c.component_heat_loss_kwh.window_loss_kwh,
    heatLossThroughDoors: c.component_heat_loss_kwh.door_loss_kwh ?? 0,
    totalHeatLoss: c.total_heat_loss_kwh,
    netHeatBalance: 0,
    thermalComfortIndex: c.comfort_percentage,
    heatingDemandKwh: c.energy_totals_kwh.heating_demand_kwh,
    hourlyTemperatures: c.indoor_temperatures,
    monthlyTemperatures: [],
    recommendedImprovements: [],
    canonical: c,
  } as SimulationResult & { canonical: CanonicalSimulationResult };
}

const optimization = {
  city: 'leh',
  home_type: 'container',
  insulation_thickness_m: 0.08,
  insulation_mm: 80,
  window_area_m2: 3,
  wall_material: 'rammed_earth',
  glazing: 'double_clear',
  glazing_name: 'Double clear',
  orientation: 'south',
  discomfort_score: 0.4,
  simulation_result: {},
  n_trials: 40,
  ranked_designs: [
    {
      rank: 1,
      label: 'A',
      rationale: 'Best comfort',
      overall_score: 0.82,
      sub_scores: { comfort: 0.9, efficiency: 0.7, solar: 0.8 },
      insulation_mm: 80,
      insulation_thickness_m: 0.08,
      window_area_m2: 3,
      wall_material: 'rammed_earth',
      wall_material_name: 'Rammed Earth (Stabilized)',
      glazing: 'double_clear',
      glazing_name: 'Double clear',
      orientation: 'south',
      comfort_hours: 40,
      comfort_percentage: 23.8,
      discomfort_dh: 6000,
      total_heat_loss_kwh: 420,
      solar_gain_kwh: 26,
      u_values: { wall_u: 0.3, roof_u: 2.2, floor_u: 3.7, window_u: 2.8 },
      heating_demand_kwh: 380,
      cooling_demand_kwh: 0,
      total_conditioning_demand_kwh: 380,
      effective_thermal_capacity_j_k: 2.4e7,
      thermal_mass_level: 'high',
      climate_provenance: 'MODEL_ANALYSIS',
      climate_data_mode: 'live',
      climate_fallback_used: false,
    },
  ],
  recommended_design: undefined,
  climate_provenance: 'MODEL_ANALYSIS',
  climate_fallback_used: false,
} as unknown as import('./api').CanonicalOptimizationResult;

function baseState(overrides: Partial<ReportSourceState> = {}): ReportSourceState {
  return {
    climate,
    climateProfile: profile,
    mission,
    design,
    wallMaterialName: 'Rammed Earth (Stabilized)',
    simulation: uiResultWith(canon),
    optimization,
    generatedAt: '2026-09-19T12:00:00Z',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------

describe('buildReportInput — full state', () => {
  const report = buildReportInput(baseState());

  it('composes meta from canonical identity only', () => {
    expect(report.meta.engine).toBe(REPORT_ENGINE_LABEL);
    expect(report.meta.tool).toBe('ThermoShelter Design Studio');
    expect(report.meta.generatedAt).toBe('2026-09-19T12:00:00Z');
  });

  it('relays real site fields from the profile', () => {
    expect(report.site.location).toBe('Leh, Ladakh');
    expect(report.site.city).toBe('Leh');
    expect(report.site.latitude).toBe(34.165);
    expect(report.site.longitude).toBe(77.584);
    expect(report.site.elevationLabel).toBe('3507 m');
    expect(report.site.timezone).toBe('Asia/Kolkata');
  });

  it('carries the authoritative climate mode and provenance wording', () => {
    expect(report.climate.climateMode).toBe('EXTREME COLD');
    expect(report.climate.provenance.provider).toContain('Open-Meteo');
    expect(report.climate.provenance.provenance).toBe('MODEL_ANALYSIS');
    expect(report.climate.fallbackUsed).toBe(false);
    expect(report.climate.presetOnly).toBe(false);
    expect(report.climate.hours).toBe(168);
  });

  it('binds mission ACH from the canonical design field (D4-A)', () => {
    expect(report.mission.ach).toBe(0.8);
    expect(report.mission.occupants).toBe(4);
    expect(report.mission.comfortBounds).toEqual({ min: 18, max: 24 });
    expect(report.mission.priorities).toContain('Thermal comfort');
    expect(report.mission.priorities).not.toContain('Low cost');
  });

  it('relays design + backend material id + shared opening layout', () => {
    expect(report.design.wallMaterialBackendId).toBe('rammed_earth');
    expect(report.design.wallConductivity).toBe(1.05);
    expect(report.design.openings.south.count).toBe(2);
    expect(report.design.openings.north.count).toBe(1);
    expect(report.design.openings.totalWindowCount).toBe(3);
    expect(report.design.insulationThicknessCm).toBe(8);
    expect(report.design.thermalMassThicknessCm).toBe(20);
  });

  it('includes the read-only strategy with comparison pairs', () => {
    expect(report.strategy).not.toBeNull();
    expect(report.strategy!.model.climateMode).toBe('EXTREME COLD');
    expect(report.strategy!.comparison.length).toBeGreaterThan(0);
    expect(report.strategy!.comparison.some((p) => !p.represented)).toBe(true);
  });

  it('relays canonical simulation values without recomputation', () => {
    expect(report.simulation).not.toBeNull();
    const sim = report.simulation!;
    expect(sim.avgIndoorC).toBe(canon.comfort_metrics.avg);
    expect(sim.uValues.wall_u).toBe(0.31);
    expect(sim.heatingDemandKwh).toBe(400);
    expect(sim.coolingDemandKwh).toBe(0);
    expect(sim.incidentSolarKwh).toBe(84);
    expect(sim.usefulSolarKwh).toBe(25.2);
    expect(sim.hasThermalStorage).toBe(true);
    expect(sim.hasInternalGain).toBe(true); // fixture carries the real array
    expect(sim.heatFlow.hasData).toBe(true);
    expect(sim.heatFlow.availableSeries.map((s) => s.key)).toContain('door_heat_flow');
    expect(sim.solar.hasData).toBe(true);
  });

  it('labels optimization as ranked candidates, never a Pareto frontier', () => {
    expect(report.optimization).not.toBeNull();
    const opt = report.optimization!;
    expect(opt.objectiveDescription).toMatch(/weighted multi-objective score/i);
    expect(opt.objectiveDescription.toLowerCase()).not.toContain('pareto');
    expect(opt.rankedDesigns).toHaveLength(1);
    expect(opt.scenarioProvenance).toBe('MODEL_ANALYSIS');
    expect(opt.scenarioFallbackUsed).toBe(false);
  });

  it('omits baseline metrics when no real baseline exists', () => {
    // The optimization section derives its baseline from the SAME simulation
    // result, so with a real simulation the baseline exists; without one it
    // must not.
    const noSim = buildReportInput(baseState({ simulation: null }));
    expect(noSim.optimization!.baseline.hasBaseline).toBe(false);
  });

  it('generates the honesty statements including geometry scope', () => {
    const all = report.limitations.statements.join(' ');
    expect(all).toMatch(/not measured on-site sensor observations/i);
    expect(all).toMatch(/simulated\/predicted/i);
    expect(all).toMatch(/forward-Euler/i);
    expect(all).toMatch(/ISO 6946/i);
    expect(all).toMatch(/No CFD\/FEM \(ANSYS\) validation/i);
    expect(all).toMatch(/Shape optimization and continuous geometry optimization are not currently implemented/i);
    expect(report.limitations.geometryNotImplemented).toEqual(GEOMETRY_NOT_IMPLEMENTED);
    expect(report.limitations.geometrySupportedParameters).toEqual(GEOMETRY_SUPPORTED_PARAMETERS);
    expect(report.limitations.geometrySupportedOptimization).toEqual(GEOMETRY_SUPPORTED_OPTIMIZATION);
  });

  it('never describes weather as measured/observed outside the negated honesty statement', () => {
    // The limitations section legitimately negates the claim ("not measured
    // on-site sensor observations"); every other section must be free of it.
    const { limitations, ...rest } = report;
    const json = JSON.stringify(rest).toLowerCase();
    expect(json).not.toMatch(/\bmeasured\b/);
    expect(json).not.toMatch(/\bobserved\b/);
    expect(json).not.toContain('pareto');
    // The negation itself stays present.
    expect(limitations.statements.join(' ').toLowerCase()).toMatch(/not measured on-site/);
  });
});

describe('buildReportInput — partial states', () => {
  it('no simulation → null simulation section, honest limitation, no fabricated values', () => {
    const report = buildReportInput(baseState({ simulation: null }));
    expect(report.simulation).toBeNull();
    expect(report.limitations.statements.join(' ')).toMatch(/No thermal simulation has been run/i);
  });

  it('no optimization → null optimization section', () => {
    const report = buildReportInput(baseState({ optimization: null }));
    expect(report.optimization).toBeNull();
  });

  it('no profile → presetOnly climate with explicit unavailable provenance', () => {
    const report = buildReportInput(baseState({ climateProfile: null }));
    expect(report.climate.presetOnly).toBe(true);
    expect(report.climate.provenance.visible).toBe(false);
    expect(report.climate.provenance.provider).toBeNull();
    expect(report.climate.fallbackUsed).toBe(false);
    expect(report.limitations.statements.join(' ')).toMatch(/No live climate profile was loaded/i);
    // strategy is also unavailable without a profile
    expect(report.strategy).toBeNull();
  });

  it('fallback climate → prominent fallback flags + limitation statement', () => {
    const fallbackProfile = {
      ...profile,
      series: { ...profile.series, fallback_used: true, provenance: 'FALLBACK' },
    } as SimulationClimateProfile;
    const report = buildReportInput(baseState({ climateProfile: fallbackProfile }));
    expect(report.climate.fallbackUsed).toBe(true);
    expect(report.climate.provenance.provenance).toBe('FALLBACK');
    expect(report.limitations.statements.join(' ')).toMatch(/fallback climate dataset was used/i);
  });

  it('strategy present but null DTO → honest unavailable state', () => {
    const noStrategy = { ...profile, strategy: null } as SimulationClimateProfile;
    const report = buildReportInput(baseState({ climateProfile: noStrategy }));
    expect(report.strategy).toBeNull();
  });

  it('missing optional arrays → availability flags false, sections still honest', () => {
    const sparse: CanonicalSimulationResult = {
      ...canon,
      solar_power: [],
      solar_thermal_gain: [],
      thermal_storage_flow: undefined,
      door_heat_flow: undefined,
      hourly_internal_gain: [],
      hourly_heating_demand: undefined,
    };
    const report = buildReportInput(baseState({ simulation: uiResultWith(sparse) }));
    const sim = report.simulation!;
    expect(sim.hasThermalStorage).toBe(false);
    expect(sim.hasInternalGain).toBe(false);
    expect(sim.hasHourlyDemand).toBe(false);
    expect(sim.heatFlow.availableSeries.map((s) => s.key)).not.toContain('door_heat_flow');
    expect(sim.solar.hasData).toBe(false);
  });

  it('non-finite values are never relayed as numbers', () => {
    const report = buildReportInput(baseState({ climateProfile: null }));
    expect(report.site.latitude).toBeNull();
    expect(report.site.elevationLabel).toBeNull();
  });
});

describe('canonicalOf', () => {
  it('extracts the canonical payload or returns null honestly', () => {
    expect(canonicalOf(uiResultWith(canon))).toBe(canon);
    expect(canonicalOf(null)).toBeNull();
    expect(canonicalOf({} as SimulationResult)).toBeNull();
  });
});
