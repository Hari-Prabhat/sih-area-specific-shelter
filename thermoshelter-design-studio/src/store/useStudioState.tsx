/**
 * THERMOSHELTER — Studio State Store (D2)
 * =======================================
 * Typed React context store centralizing all cross-stage studio state:
 * workflow stage, site/climate, mission, geometry & envelope, simulation,
 * optimization, and backend health. No external state library is introduced.
 *
 * Engineering discipline: this store holds UI/presentation state and the
 * canonical API contracts ONLY. No thermal physics lives here — every
 * engineering value flows from the Python backend via services/api.ts.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';
import { ClimateData, ShelterDesign, SimulationResult as UiSimulationResult } from '../types';
import {
  CanonicalOptimizationCandidate,
  CanonicalOptimizationResult,
  DEFAULT_ACH,
  SimulationClimateProfile,
  checkApiHealth,
  describeApiError,
  runOptimizationViaApi,
  runSimulationViaApi,
} from '../services/api';
import { climatePresets } from '../data/climatePresets';
import { getMaterialByName, getUiNameByBackendId, wallMaterialKey } from '../data/materials';
import { DATA_MODE_PROVENANCE, ProvenanceValue, WORKFLOW_STAGES, WorkflowStage } from '../theme/tokens';

// ---------------------------------------------------------------------------
// Mission configuration (extracted from the retired DesignStudio mock)
// ---------------------------------------------------------------------------

export interface MissionConfig {
  occupants: number;
  purpose: string;
  deploymentType: 'Temporary' | 'Seasonal' | 'Permanent';
  durationMonths: number;
  mobilityRequired: boolean;
  priorities: {
    thermalComfort: boolean;
    energyIndependence: boolean;
    lowCost: boolean;
    lowWeight: boolean;
    rapidDeployment: boolean;
    durability: boolean;
  };
}

const DEFAULT_MISSION: MissionConfig = {
  occupants: 4,
  purpose: 'Residential',
  deploymentType: 'Permanent',
  durationMonths: 12,
  mobilityRequired: false,
  priorities: {
    thermalComfort: true,
    energyIndependence: true,
    lowCost: false,
    lowWeight: false,
    rapidDeployment: false,
    durability: true,
  },
};

// ---------------------------------------------------------------------------
// Candidate thermal-mass semantics — MUST mirror services/optimize.py
// THERMAL_MASS_LEVELS exactly (none/low/medium/high → 0/50/100/200 mm
// concrete floor core). No invented values.
// ---------------------------------------------------------------------------

const THERMAL_MASS_LEVEL_THICKNESS_CM: Record<string, number> = {
  none: 0,
  low: 5,
  medium: 10,
  high: 20,
};

/**
 * Batch 1-A: the approved D5-B prototype geometry-search bounds. These are
 * PROPOSED PROTOTYPE OPTIMIZATION BOUNDS - engineering assumptions supplied
 * for the demo, NOT DRDO/regulatory/ISO requirements. The UI presents them
 * read-only; the backend re-validates every value.
 */
export const PROTOTYPE_GEOMETRY_BOUNDS = {
  min_length_m: 4.0,
  max_length_m: 10.0,
  min_width_m: 3.0,
  max_width_m: 6.0,
  min_height_m: 2.4,
  max_height_m: 4.0,
  // Orientation-independent aspect ratio max(L/W, W/L) cap.
  max_aspect_ratio: 3.0,
} as const;

export function massLevelToDesignMass(level: string | null | undefined): {
  thermalMassEnabled: boolean;
  thermalMassThickness: number;
} {
  const cm = level ? THERMAL_MASS_LEVEL_THICKNESS_CM[level] ?? 0 : 0;
  return { thermalMassEnabled: cm > 0, thermalMassThickness: cm };
}

/**
 * D4-A WP2: pure mapping from an optimization candidate onto the canonical
 * ShelterDesign fields it governs. Extracted from applyCandidate so the
 * candidate → design → simulation-payload contract is unit-testable:
 * the applied design must reproduce the candidate's simulated envelope
 * (window area, glazing, orientation, insulation thickness, thermal mass).
 */
export function candidateDesignPatch(
  prev: ShelterDesign,
  candidate: CanonicalOptimizationCandidate,
): Partial<ShelterDesign> {
  const mass = massLevelToDesignMass(candidate.thermal_mass_level);
  const patch: Partial<ShelterDesign> = {
    windowArea: candidate.window_area_m2,
    windowGlazing: glazingToUi(candidate.glazing),
    orientation: orientationToDegrees(candidate.orientation),
    // Restore the candidate's actual insulation thickness (mm → cm) so the
    // applied design reproduces the candidate's simulated U-values; keep the
    // selected insulation product when the candidate carries insulation.
    insulationThickness: Math.round(candidate.insulation_thickness_m * 100),
    insulationType:
      candidate.insulation_thickness_m <= 0
        ? 'None'
        : prev.insulationType === 'None'
          ? 'EPS'
          : prev.insulationType,
    thermalMassEnabled: mass.thermalMassEnabled,
    thermalMassThickness: mass.thermalMassThickness,
  };
  // D5-A: geometry is carried ONLY when the candidate actually reports it
  // (the backend populates these from engine-measured values). Legacy
  // candidates without geometry must not touch the design dimensions.
  if (
    typeof candidate.length_m === 'number' &&
    typeof candidate.width_m === 'number' &&
    typeof candidate.height_m === 'number'
  ) {
    patch.length = candidate.length_m;
    patch.width = candidate.width_m;
    patch.height = candidate.height_m;
  }
  return patch;
}

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

export interface SimulationState {
  result: UiSimulationResult | null;
  loading: boolean;
  error: string | null;
  /** Batch 2A: the design/climate this result was computed from — used to
   *  detect a stale baseline before offering candidate comparisons. */
  design?: unknown;
  climateProfile?: unknown;
}

export interface OptimizationState {
  result: CanonicalOptimizationResult | null;
  loading: boolean;
  error: string | null;
  selectedCandidate: CanonicalOptimizationCandidate | null;
}

export interface StudioState {
  // Navigation
  stage: WorkflowStage;
  expertMode: boolean;

  // Site & climate
  climate: ClimateData;
  climateProfile: SimulationClimateProfile | null;

  // Mission
  mission: MissionConfig;

  // Geometry & envelope
  design: ShelterDesign;
  wallMaterial: string;

  // Simulation
  simulation: SimulationState;

  // Optimization
  optimization: OptimizationState;

  // Health
  backendHealth: 'connecting' | 'connected' | 'unavailable';
}

export interface StudioActions {
  setStage: (stage: WorkflowStage) => void;
  setExpertMode: (expert: boolean) => void;
  setClimate: (climate: ClimateData) => void;
  setClimateProfile: (profile: SimulationClimateProfile | null) => void;
  setMissionField: <K extends keyof MissionConfig>(field: K, value: MissionConfig[K]) => void;
  togglePriority: (key: keyof MissionConfig['priorities']) => void;
  setDesignField: <K extends keyof ShelterDesign>(field: K, value: ShelterDesign[K]) => void;
  /** Whole-design replacement (used by legacy whole-object setters). */
  replaceDesign: (design: ShelterDesign) => void;
  setWallMaterial: (name: string) => void;
  runSimulation: () => Promise<void>;
  runOptimization: (
    weights?: { comfort: number; efficiency: number; solar: number },
    nTrials?: number,
    homeType?: string,
  ) => Promise<void>;
  selectCandidate: (candidate: CanonicalOptimizationCandidate | null) => void;
  applyCandidate: (candidate: CanonicalOptimizationCandidate) => void;
  clearSimulationError: () => void;
  clearOptimizationError: () => void;
}

export type StudioStore = StudioState & StudioActions;

const StudioContext = createContext<StudioStore | null>(null);

// ---------------------------------------------------------------------------
// Helpers (moved verbatim from App.tsx — identical payloads, same endpoints)
// ---------------------------------------------------------------------------

function mapGlazingKey(glazing: ShelterDesign['windowGlazing']): string {
  if (glazing === 'single') return 'single_clear';
  if (glazing === 'triple') return 'triple_low_e';
  return 'double_clear';
}

/** Maps an orientation string ("south"/"north"/…) to canonical azimuth degrees. */
export function orientationToDegrees(orientation: string): number {
  const o = orientation.toLowerCase();
  if (o.includes('north') && !o.includes('south')) return 0;
  if (o.includes('east')) return 90;
  if (o.includes('west') && !o.includes('south')) return 270;
  return 180;
}

export function glazingToUi(glazing: string): 'single' | 'double' | 'triple' {
  if (glazing.includes('triple')) return 'triple';
  if (glazing.includes('single')) return 'single';
  return 'double';
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function StudioStateProvider({ children }: { children: ReactNode }) {
  // Navigation
  const [stage, setStage] = useState<WorkflowStage>('site-climate');
  const [expertMode, setExpertMode] = useState(false);

  // Site & climate
  const [climate, setClimate] = useState<ClimateData>(climatePresets[0]);
  const [climateProfile, setClimateProfile] = useState<SimulationClimateProfile | null>(null);
  // Session 2 stale-result hardening: a different climate profile invalidates
  // simulation/optimization results computed against the previous weather.
  // Wrapped in a useCallback so every consumer (ClimateInput, presets, tests)
  // gets the invalidation for free instead of each caller remembering it.
  const applyClimateProfile = useCallback(
    (profile: SimulationClimateProfile | null) => {
      setSimulation((prev) => ({ ...prev, result: null }));
      setOptimization((prev) => ({ ...prev, result: null }));
      setClimateProfile(profile);
    },
    [],
  );

  // Mission
  const [mission, setMission] = useState<MissionConfig>(DEFAULT_MISSION);

  // Geometry & envelope
  const [design, setDesign] = useState<ShelterDesign>({
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
    // D4-A WP2: explicit envelope insulation thickness (cm) — previously a
    // hardcoded 0.05 m inside the payload builders while the optimizer
    // explored 0/50/100/150 mm, so applied candidates could not reproduce
    // their simulated U-values.
    insulationThickness: 5,
    // D4-A WP1: canonical backend design field (services/contracts.py
    // ShelterDesign.ach; preset DEFAULT_ACH = 0.5). Editable in the designer.
    ach: DEFAULT_ACH,
    thermalMassEnabled: true,
    thermalMassThickness: 20,
  });
  const [wallMaterial, setWallMaterial] = useState('Rammed Earth (Stabilized)');

  // Simulation
  const [simulation, setSimulation] = useState<SimulationState>({
    result: null,
    loading: false,
    error: null,
  });

  // Optimization
  const [optimization, setOptimization] = useState<OptimizationState>({
    result: null,
    loading: false,
    error: null,
    selectedCandidate: null,
  });

  // Health (quiet probe: retry only while unreachable — DesignStudio pattern, now global)
  const [backendHealth, setBackendHealth] = useState<'connecting' | 'connected' | 'unavailable'>('connecting');
  useEffect(() => {
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    const probe = () => {
      checkApiHealth()
        .then(() => {
          if (!cancelled) setBackendHealth('connected');
        })
        .catch(() => {
          if (cancelled) return;
          setBackendHealth('unavailable');
          retryTimer = setTimeout(probe, 30000);
        });
    };
    probe();
    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, []);

  // ---- Actions ------------------------------------------------------------

  const setDesignField = useCallback(
    <K extends keyof ShelterDesign>(field: K, value: ShelterDesign[K]) => {
      setDesign((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const replaceDesign = useCallback((next: ShelterDesign) => {
    setDesign(next);
  }, []);

  const setMissionField = useCallback(
    <K extends keyof MissionConfig>(field: K, value: MissionConfig[K]) => {
      setMission((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const togglePriority = useCallback((key: keyof MissionConfig['priorities']) => {
    setMission((prev) => ({
      ...prev,
      priorities: { ...prev.priorities, [key]: !prev.priorities[key] },
    }));
  }, []);

  const runSimulation = useCallback(async () => {
    const material = getMaterialByName(wallMaterial);
    const insulation = getMaterialByName(design.insulationType);
    // Batch 1-G: an unresolvable wall material is an honest error, never a
    // silent no-op (previously the button appeared dead with no feedback).
    if (!material) {
      setSimulation((prev) => ({
        ...prev,
        loading: false,
        error: `Wall material "${wallMaterial}" is not resolvable to a simulation material. Select a wall material in the Design stage.`,
      }));
      return;
    }
    setSimulation((prev) => ({ ...prev, loading: true, error: null }));
    try {
      // Authoritative Python thermal simulation via FastAPI. When a live/
      // forecast/design climate profile was fetched, its real hourly arrays
      // override the preset-city statistics (Phase B/C contract).
      // D4-A WP1: mission occupancy drives internal gains (backend per-occupant
      // gain constant: services/formula_constants.py DEFAULT_OCCUPANT_HEAT_GAIN);
      // ACH comes from the design's canonical ach field.
      const result = await runSimulationViaApi(
        climate,
        design,
        material,
        insulation,
        168,
        climateProfile ?? undefined,
        mission.occupants,
        design.ach,
      );
      setSimulation({ result, loading: false, error: null, design, climateProfile });
      setStage('simulation');
    } catch (err) {
      setSimulation((prev) => ({
        ...prev,
        loading: false,
        error: describeApiError(err),
      }));
    }
  }, [climate, climateProfile, design, wallMaterial, mission.occupants]);

  const runOptimization = useCallback(
    async (
      weights?: { comfort: number; efficiency: number; solar: number },
      nTrials?: number,
      homeType?: string,
      // Batch 1-A: progressive-disclosure geometry search. Undefined/false
      // keeps the exact pre-D5 fixed-geometry request (no geometry fields).
      optimizeGeometry?: boolean,
    ) => {
      setOptimization((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const cityName = climateProfile?.climate?.city
          ?? climate.location.split(',')[0].toLowerCase().trim();
        const insulation = getMaterialByName(design.insulationType);
        // D4-A WP2: the optimizer seeds its search from the design's explicit
        // insulation thickness (cm → m) — not a hardcoded 0.05 m.
        const insThick =
          insulation && insulation.name !== 'None' ? design.insulationThickness / 100.0 : 0.0;

        const material = getMaterialByName(wallMaterial);
        if (!material) {
          throw new Error(
            `Wall material "${wallMaterial}" is not resolvable to a simulation material. Select a wall material in the Design stage.`,
          );
        }

        // Batch 2A: the comparison baseline is a REAL simulation of the
        // current canonical design on the SAME climate profile and simulation
        // path the candidates use — never synthetic values. Run it here when
        // missing or stale (design/climate changed since the last run), so
        // "Baseline: …" deltas are always physically comparable.
        const baselineIsStale = baselineIsOutOfDate(
          simulation.result,
          design,
          climateProfile,
        );
        let baselineResult = simulation.result;
        if (baselineIsStale) {
          const baseline = await runSimulationViaApi(
            climate,
            design,
            material,
            insulation,
            168,
            climateProfile ?? undefined,
            mission.occupants,
            design.ach,
          );
          baselineResult = baseline;
          setSimulation({ result: baseline, loading: false, error: null, design, climateProfile });
        }

        const result = await runOptimizationViaApi({
          city: cityName,
          home_type: homeType || 'Permanent',
          design: {
            length: design.length,
            width: design.width,
            height: design.height,
            wall_material: wallMaterialKey(wallMaterial),
            wall_thickness_m: design.wallThickness,
            insulation_thickness_m: insThick,
            insulation_conductivity: insulation ? insulation.thermalConductivity : 0.025,
            window_area: design.windowArea,
            door_area: design.doorArea ?? 2.0,
            glazing: mapGlazingKey(design.windowGlazing),
            orientation: design.orientation,
            roof_type: design.roofAngle && design.roofAngle > 0 ? 'pitched' : 'flat',
            pitch_angle_deg: design.roofAngle || 0.0,
            // D4-A WP1/WP2: bind to explicit design/mission state.
            ach: design.ach,
            occupants: mission.occupants,
          },
          n_trials: nTrials || 20,
          // Optimizer search fidelity (backend default, optimize.py:90). The
          // backend re-verifies the best design at substeps=60 — do not raise
          // this to 60; trial evaluation at 15 is deliberate for performance.
          substeps: 15,
          hours_to_simulate: 168,
          weights: weights || { comfort: 0.5, efficiency: 0.3, solar: 0.2 },
          // Phase C contract: when a location-derived climate profile was
          // fetched, the optimizer evaluates candidates against the SAME real
          // weather the direct simulation uses (one climate source of truth).
          ...(climateProfile ? { climate: climateProfile.climate } : {}),
          // Batch 1-A: only when the user explicitly enables geometry search.
          // Bounds are the approved prototype bounds (PROTOTYPE_GEOMETRY_BOUNDS).
          ...(optimizeGeometry ? { optimize_geometry: true, ...PROTOTYPE_GEOMETRY_BOUNDS } : {}),
        });

        setOptimization((prev) => ({
          ...prev,
          result,
          loading: false,
          error: null,
          selectedCandidate: result.ranked_designs?.[0] ?? null,
        }));
      } catch (err) {
        setOptimization((prev) => ({
          ...prev,
          loading: false,
          error: describeApiError(err),
        }));
      }
    },
    [climate, climateProfile, design, wallMaterial, mission.occupants],
  );

  const selectCandidate = useCallback((candidate: CanonicalOptimizationCandidate | null) => {
    setOptimization((prev) => ({ ...prev, selectedCandidate: candidate }));
  }, []);

  /**
   * Applies an optimized candidate to the authoritative ShelterDesign state.
   *
   * Phase D2 FIX: the candidate's thermal_mass_level is preserved through the
   * mapping (none/low/medium/high → the canonical floor-core thickness in cm,
   * mirroring services/optimize.py THERMAL_MASS_LEVELS), so the next
   * simulation runs on the candidate's actual mass — previously the level
   * was silently dropped here.
   */
  const applyCandidate = useCallback(
    (candidate: CanonicalOptimizationCandidate) => {
      // Batch 1-B/1-G: restore the UI material from the candidate's backend
      // KEY (authoritative payload value) — the display name
      // ("Rammed Earth (Stabilized / Unstabilized)") is not a UI option and
      // left runSimulation's material lookup silently unresolved.
      setWallMaterial(getUiNameByBackendId(candidate.wall_material) ?? candidate.wall_material_name);
      setDesign((prev) => ({
        ...prev,
        ...candidateDesignPatch(prev, candidate),
      }));

      // Clear the stale simulation result so the user re-runs on the new design.
      setSimulation((prev) => ({ ...prev, result: null }));
      setOptimization((prev) => ({ ...prev, selectedCandidate: candidate }));
    },
    [],
  );

  const clearSimulationError = useCallback(() => {
    setSimulation((prev) => ({ ...prev, error: null }));
  }, []);

  const clearOptimizationError = useCallback(() => {
    setOptimization((prev) => ({ ...prev, error: null }));
  }, []);

  const store = useMemo<StudioStore>(
    () => ({
      stage,
      expertMode,
      climate,
      climateProfile,
      mission,
      design,
      wallMaterial,
      simulation,
      optimization,
      backendHealth,
      setStage,
      setExpertMode,
      setClimate,
      setClimateProfile: applyClimateProfile,
      setMissionField,
      togglePriority,
      setDesignField,
      replaceDesign,
      setWallMaterial,
      runSimulation,
      runOptimization,
      selectCandidate,
      applyCandidate,
      clearSimulationError,
      clearOptimizationError,
    }),
    [
      stage,
      expertMode,
      climate,
      climateProfile,
      mission,
      design,
      wallMaterial,
      simulation,
      optimization,
      backendHealth,
      replaceDesign,
      setDesignField,
      setMissionField,
      togglePriority,
      runSimulation,
      runOptimization,
      selectCandidate,
      applyCandidate,
      clearSimulationError,
      clearOptimizationError,
    ],
  );

  return <StudioContext.Provider value={store}>{children}</StudioContext.Provider>;
}

export function useStudioState(): StudioStore {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error('useStudioState must be used within StudioStateProvider');
  return ctx;
}

// ---------------------------------------------------------------------------
// Derived selectors
// ---------------------------------------------------------------------------

/**
 * Batch 2A: pure staleness contract for the optimization comparison baseline.
 * A stored simulation result is a valid baseline ONLY when it was computed
 * from the exact same canonical ShelterDesign object and ClimateProfile that
 * optimization is about to run on. Any new design object (geometry, envelope,
 * material, glazing, orientation, thermal mass, ACH, door — any design edit)
 * or a different climate profile invalidates the baseline. Identity comparison
 * is sufficient because every design edit produces a new canonical object.
 */
export function baselineIsOutOfDate(
  result: { design?: unknown; climateProfile?: unknown } | null | undefined,
  design: unknown,
  climateProfile: unknown,
): boolean {
  return !result || result.design !== design || result.climateProfile !== climateProfile;
}

/** Provenance of the active weather dataset (or null when using presets only). */
export function activeWeatherProvenance(profile: SimulationClimateProfile | null): ProvenanceValue | null {
  if (!profile) return null;
  const raw = profile.climate?.data_provenance ?? profile.series?.provenance;
  if (raw) {
    const upper = String(raw).toUpperCase();
    if (upper === 'MODEL_ANALYSIS' || upper === 'FORECAST' || upper === 'HISTORICAL_REANALYSIS' || upper === 'DESIGN' || upper === 'FALLBACK') {
      return upper as ProvenanceValue;
    }
  }
  // Fall back to the data_mode mapping (live/forecast/historical/design/fallback)
  return profile.series?.data_mode ? DATA_MODE_PROVENANCE[profile.series.data_mode] ?? null : null;
}

export function fallbackUsed(profile: SimulationClimateProfile | null): boolean {
  return profile?.series?.fallback_used ?? false;
}

export function stageDefinition(stage: WorkflowStage) {
  return WORKFLOW_STAGES.find((s) => s.id === stage)!;
}
