/**
 * THERMOSHELTER — Engineering Report input model (D4-D1)
 * ======================================================
 * PURE adapter composing the existing canonical data into presentation
 * groupings for the Engineering Report stage. This is NOT a second
 * engineering engine: every number relayed here already exists in a
 * canonical/backend result (SimulationResult.canonical, OptimizationResult,
 * ClimateProfile, ShelterDesign, material DB mappings) or in an existing
 * single-source derivation (provenanceView, passiveStrategy,
 * baselineMetrics, openingLayout, heatFlowChart builders).
 *
 * Honesty contract:
 *  - No U-values, heat flows, demands, solar energies, temperatures or
 *    optimization scores are ever computed here.
 *  - Absent inputs yield null/omitted sections — never fabricated values.
 *  - Weather is described with the canonical Phase C provenance vocabulary
 *    only (never "measured"/"observed").
 *  - Geometry/shape optimization honesty per SIH coverage rules: design
 *    parameters and orientation optimization are supported; shape and
 *    continuous geometry optimization are NOT implemented.
 */

import type {
  CanonicalOptimizationCandidate,
  CanonicalOptimizationResult,
  CanonicalSimulationResult,
  SimulationClimateProfile,
} from './api';
import type { ClimateData, ShelterDesign, SimulationResult } from '../types';
import type { MissionConfig } from '../store/useStudioState';
import { activeWeatherProvenance, fallbackUsed } from '../store/useStudioState';
import { formatProvenanceView } from './provenanceView';
import type { ProvenanceView } from './provenanceView';
import {
  buildStrategyComparison,
  mapStrategyDto,
  NOT_REPRESENTED,
} from './passiveStrategy';
import type { PassiveStrategyModel, StrategyComparisonPair } from './passiveStrategy';
import { deriveBaselineMetrics } from './baselineMetrics';
import type { BaselineMetrics } from './baselineMetrics';
import { deriveOpeningLayout } from './openingLayout';
import type { OpeningLayout } from './openingLayout';
import { getMaterialByName, resolveBackendMaterialId } from '../data/materials';
import { DISPLAY_COMFORT_BOUNDS } from '../theme/tokens';
import {
  buildHeatFlowChartData,
  buildSolarChartData,
  buildThermalStorageChartData,
} from './heatFlowChart';
import type { HeatFlowChartData, SolarChartData } from './heatFlowChart';

/** Canonical engine identity reported by GET /api/health (relay, not invention). */
export const REPORT_ENGINE_LABEL = 'Python 1D Forward Euler + ISO 6946 (Authoritative)';

/** Geometry-optimization honesty (SIH coverage corrections). */
export const GEOMETRY_SUPPORTED_PARAMETERS = [
  'length',
  'width',
  'height',
  'shape',
  'roof pitch',
  'orientation',
] as const;

export const GEOMETRY_SUPPORTED_OPTIMIZATION = [
  'orientation',
  'wall material',
  'insulation thickness',
  'glazing',
  'thermal mass',
] as const;

export const GEOMETRY_NOT_IMPLEMENTED = [
  'shape optimization',
  'continuous geometry optimization',
] as const;

/** The plain state slices the adapter needs (mirrors the studio store). */
export interface ReportSourceState {
  climate: ClimateData;
  climateProfile: SimulationClimateProfile | null;
  mission: MissionConfig;
  design: ShelterDesign;
  /** Currently selected wall material name (canonical UI selection). */
  wallMaterialName: string;
  /** UI simulation result carrying the attached canonical payload. */
  simulation: SimulationResult | null;
  optimization: CanonicalOptimizationResult | null;
  /** Injectable for deterministic tests; defaults to generation time. */
  generatedAt?: string;
}

// ---------------------------------------------------------------------------
// Section models
// ---------------------------------------------------------------------------

export interface ReportMeta {
  generatedAt: string;
  engine: string;
  tool: string;
}

export interface ReportSite {
  location: string;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  elevationLabel: string | null;
  timezone: string | null;
}

export interface ReportClimate {
  /** Full provenance view derived by the existing D4-B pure helper. */
  provenance: ProvenanceView;
  /** Authoritative classification — strategy.climate_mode when present. */
  climateMode: string | null;
  fallbackUsed: boolean;
  /** True when no live profile exists and only the preset ClimateData is shown. */
  presetOnly: boolean;
  hours: number | null;
}

export interface ReportMission {
  occupants: number;
  ach: number;
  /** Mission purpose label (relayed from MissionConfig). */
  purpose?: string;
  deploymentType?: string;
  durationMonths?: number;
  mobilityRequired: boolean;
  /** Human-selected mission priorities (true flags only). */
  priorities: string[];
  comfortBounds: { min: number; max: number };
}

export interface ReportDesign {
  length: number;
  width: number;
  height: number;
  shape: string;
  orientationDeg: number;
  roofPitchDeg: number;
  wallThicknessM: number;
  windowAreaM2: number;
  doorAreaM2: number;
  glazing: string;
  insulationType: string;
  insulationThicknessCm: number;
  thermalMassEnabled: boolean;
  thermalMassThicknessCm: number;
  wallMaterialName: string;
  /** Backend material DB id the physics engine resolves (D4-C mapping). */
  wallMaterialBackendId: string;
  /** Backend-DB-aligned material properties (k, ρ, c_p). */
  wallConductivity: number | null;
  wallDensity: number | null;
  wallSpecificHeat: number | null;
  /** Shared deterministic opening layout (identical in Blueprint and 3D). */
  openings: OpeningLayout;
}

export interface ReportStrategy {
  model: PassiveStrategyModel;
  comparison: StrategyComparisonPair[];
}

export interface ReportSimulation {
  avgIndoorC: number;
  minIndoorC: number;
  maxIndoorC: number;
  comfortPct: number;
  comfortHours: number;
  discomfortDegreeHours: number;
  uValues: CanonicalSimulationResult['u_values'];
  componentLossesKwh: CanonicalSimulationResult['component_heat_loss_kwh'];
  totalHeatLossKwh: number;
  heatingDemandKwh: number;
  coolingDemandKwh: number;
  incidentSolarKwh: number;
  usefulSolarKwh: number;
  /** REAL hourly chart data built by the existing D4-B pure builders. */
  heatFlow: HeatFlowChartData;
  solar: SolarChartData;
  /** Optional thermal-storage series (+stored / −released). */
  hasThermalStorage: boolean;
  /** Optional backend arrays' availability for honest omission. */
  hasInternalGain: boolean;
  hasHourlyDemand: boolean;
}

export interface ReportOptimization {
  nTrials: number;
  homeType: string;
  objectiveDescription: string;
  /** Ranked candidate designs (weighted multi-objective score) — NOT a Pareto frontier. */
  rankedDesigns: CanonicalOptimizationCandidate[];
  recommended: CanonicalOptimizationCandidate | null;
  baseline: BaselineMetrics;
  scenarioProvenance: string | null;
  scenarioFallbackUsed: boolean | null;
}

export interface ReportLimitations {
  statements: string[];
  geometrySupportedParameters: readonly string[];
  geometrySupportedOptimization: readonly string[];
  geometryNotImplemented: readonly string[];
}

export interface ReportInput {
  meta: ReportMeta;
  site: ReportSite;
  climate: ReportClimate;
  mission: ReportMission;
  design: ReportDesign;
  strategy: ReportStrategy | null;
  simulation: ReportSimulation | null;
  optimization: ReportOptimization | null;
  limitations: ReportLimitations;
}

// ---------------------------------------------------------------------------
// Helpers — formatting/relaying only, no engineering math
// ---------------------------------------------------------------------------

function finiteOrNull(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

function stringOrNull(v: unknown): string | null {
  return typeof v === 'string' && v.trim() !== '' ? v : null;
}

/** Canonical result accessor — the UI result attaches `canonical` when fresh. */
export function canonicalOf(result: SimulationResult | null | undefined): CanonicalSimulationResult | null {
  return (result as { canonical?: CanonicalSimulationResult } | null | undefined)?.canonical ?? null;
}

const PRIORITY_LABELS: Record<keyof MissionConfig['priorities'], string> = {
  thermalComfort: 'Thermal comfort',
  energyIndependence: 'Energy independence',
  lowCost: 'Low cost',
  lowWeight: 'Low weight',
  rapidDeployment: 'Rapid deployment',
  durability: 'Durability',
};

// ---------------------------------------------------------------------------
// The pure adapter
// ---------------------------------------------------------------------------

export function buildReportInput(state: ReportSourceState): ReportInput {
  const { climate, climateProfile, mission, design, wallMaterialName, simulation, optimization } = state;

  // --- Site ---------------------------------------------------------------
  const series = climateProfile?.series;
  const site: ReportSite = {
    location: climate.location,
    city: stringOrNull(climateProfile?.climate?.city),
    latitude: finiteOrNull(series?.latitude),
    longitude: finiteOrNull(series?.longitude),
    elevationLabel:
      typeof climateProfile?.climate?.elevation_m === 'number'
        ? `${Math.round(climateProfile.climate.elevation_m)} m`
        : typeof series?.elevation_m === 'number'
          ? `${Math.round(series.elevation_m)} m`
          : null,
    timezone: stringOrNull(series?.timezone),
  };

  // --- Climate (provenance via the existing D4-B view; never "measured") ---
  const provenance = formatProvenanceView(climateProfile, false);
  const strategyModel = mapStrategyDto(climateProfile?.strategy ?? null);
  const climateMode =
    strategyModel?.climateMode ??
    (typeof climateProfile?.climate?.climate_mode === 'string'
      ? (climateProfile.climate.climate_mode as string)
      : null);
  const climateSection: ReportClimate = {
    provenance,
    climateMode,
    fallbackUsed: fallbackUsed(climateProfile),
    presetOnly: climateProfile === null,
    hours: provenance.hours,
  };

  // --- Mission -------------------------------------------------------------
  const missionSection: ReportMission = {
    occupants: mission.occupants,
    // D4-A WP1: the canonical design ACH field is authoritative.
    ach: design.ach,
    purpose: mission.purpose,
    deploymentType: mission.deploymentType,
    durationMonths: mission.durationMonths,
    mobilityRequired: mission.mobilityRequired,
    priorities: (Object.keys(PRIORITY_LABELS) as Array<keyof MissionConfig['priorities']>)
      .filter((k) => mission.priorities[k])
      .map((k) => PRIORITY_LABELS[k]),
    comfortBounds: { ...DISPLAY_COMFORT_BOUNDS },
  };

  // --- Design ---------------------------------------------------------------
  const material = getMaterialByName(wallMaterialName);
  const backendId = resolveBackendMaterialId(wallMaterialName);
  const designSection: ReportDesign = {
    length: design.length,
    width: design.width,
    height: design.height,
    shape: design.shape,
    orientationDeg: design.orientation,
    roofPitchDeg: design.roofAngle,
    wallThicknessM: design.wallThickness,
    windowAreaM2: design.windowArea,
    doorAreaM2: design.doorArea ?? 2,
    glazing: design.windowGlazing,
    insulationType: design.insulationType,
    insulationThicknessCm: design.insulationThickness,
    thermalMassEnabled: design.thermalMassEnabled,
    thermalMassThicknessCm: design.thermalMassThickness,
    wallMaterialName,
    wallMaterialBackendId: backendId ?? 'unresolved',
    wallConductivity: material ? material.thermalConductivity : null,
    wallDensity: material ? material.density : null,
    wallSpecificHeat: material ? material.specificHeat : null,
    openings: deriveOpeningLayout(design.windowArea, design.doorArea ?? 2),
  };

  // --- Passive strategy (read-only; never mutates design) -------------------
  const strategySection: ReportStrategy | null = strategyModel
    ? {
        model: strategyModel,
        comparison: buildStrategyComparison(strategyModel, design),
      }
    : null;

  // --- Simulation (canonical results only) ----------------------------------
  const canon = canonicalOf(simulation);
  let simulationSection: ReportSimulation | null = null;
  if (canon) {
    const heatFlow = buildHeatFlowChartData(canon);
    const solar = buildSolarChartData(canon);
    const storage = buildThermalStorageChartData(canon, heatFlow.hourCount || solar.points.length);
    simulationSection = {
      avgIndoorC: canon.comfort_metrics.avg,
      minIndoorC: canon.comfort_metrics.min_t,
      maxIndoorC: canon.comfort_metrics.max_t,
      comfortPct: canon.comfort_percentage,
      comfortHours: canon.comfort_hours,
      discomfortDegreeHours: canon.discomfort_degree_hours,
      uValues: canon.u_values,
      componentLossesKwh: canon.component_heat_loss_kwh,
      totalHeatLossKwh: canon.total_heat_loss_kwh,
      heatingDemandKwh: canon.energy_totals_kwh.heating_demand_kwh,
      coolingDemandKwh: canon.energy_totals_kwh.cooling_demand_kwh,
      incidentSolarKwh: canon.integrated_incident_solar_kwh,
      usefulSolarKwh: canon.integrated_solar_energy_kwh,
      heatFlow,
      solar,
      hasThermalStorage: storage.hasData,
      hasInternalGain:
        Array.isArray(canon.hourly_internal_gain) && canon.hourly_internal_gain.length > 0,
      hasHourlyDemand:
        (Array.isArray(canon.hourly_heating_demand) && canon.hourly_heating_demand.length > 0) ||
        (Array.isArray(canon.hourly_cooling_demand) && canon.hourly_cooling_demand.length > 0),
    };
  }

  // --- Optimization (ranked candidates — never "Pareto") ---------------------
  let optimizationSection: ReportOptimization | null = null;
  if (optimization) {
    const baseline = deriveBaselineMetrics(simulation);
    optimizationSection = {
      nTrials: optimization.n_trials,
      homeType: optimization.home_type,
      objectiveDescription:
        'Weighted multi-objective score over comfort, efficiency and solar sub-scores',
      rankedDesigns: Array.isArray(optimization.ranked_designs) ? optimization.ranked_designs : [],
      recommended: optimization.recommended_design ?? null,
      baseline,
      scenarioProvenance: stringOrNull(optimization.climate_provenance),
      scenarioFallbackUsed:
        typeof optimization.climate_fallback_used === 'boolean'
          ? optimization.climate_fallback_used
          : null,
    };
  }

  // --- Limitations (generated from ACTUAL state; no irrelevant claims) -------
  const statements: string[] = [
    'Weather inputs are model/forecast/design/fallback data provided by atmospheric model products, not measured on-site sensor observations.',
    'All thermal outputs in this report are simulated/predicted values produced by the ThermoShelter Python engine; none are field measurements.',
    `Thermal modelling uses the ${REPORT_ENGINE_LABEL} engine (1D forward-Euler hourly thermal balance).`,
    'Envelope U-values use the existing ISO 6946 steady-state layer methodology as implemented by the engine; full-standard certification is not claimed.',
    'No CFD/FEM (ANSYS) validation has been performed in this prototype.',
    'Shape optimization and continuous geometry optimization are not currently implemented; geometry and shape values are user-selected design parameters, and optimization covers orientation, material, insulation, glazing and thermal mass only.',
    'The 3D visualization is an engineering visualization of the canonical design, not a high-fidelity CFD/FEM result.',
  ];
  if (climateSection.fallbackUsed) {
    statements.push('A fallback climate dataset was used for this run; results reflect that dataset.');
  }
  if (climateSection.presetOnly) {
    statements.push('No live climate profile was loaded; site/climate values reflect the selected design preset.');
  }
  if (!simulationSection) {
    statements.push('No thermal simulation has been run in this session; thermal result sections are omitted.');
  }

  return {
    meta: {
      generatedAt: state.generatedAt ?? new Date().toISOString(),
      engine: REPORT_ENGINE_LABEL,
      tool: 'ThermoShelter Design Studio',
    },
    site,
    climate: climateSection,
    mission: missionSection,
    design: designSection,
    strategy: strategySection,
    simulation: simulationSection,
    optimization: optimizationSection,
    limitations: {
      statements,
      geometrySupportedParameters: GEOMETRY_SUPPORTED_PARAMETERS,
      geometrySupportedOptimization: GEOMETRY_SUPPORTED_OPTIMIZATION,
      geometryNotImplemented: GEOMETRY_NOT_IMPLEMENTED,
    },
  };
}

/** Honest marker re-exported for the report UI (single source). */
export { NOT_REPRESENTED };
