/**
 * THERMOSHELTER — Studio Design Tokens (D1)
 * =========================================
 * Single source of truth for the studio's semantic visual language and
 * workflow/stage model. PRESENTATION tokens only: no thermal physics and no
 * engineering values live here.
 */

export const semanticColors = {
  brand: 'amber',
  primary: 'amber',
  secondary: 'slate',
  success: 'emerald',
  warning: 'orange',
  error: 'red',
  info: 'sky',
  neutral: 'slate',
} as const;

export type SemanticColor = (typeof semanticColors)[keyof typeof semanticColors];

/** Stage model for the 9-stage guided workflow (D2). */
export type WorkflowStage =
  | 'site-climate'
  | 'mission'
  | 'design'
  | 'passive-strategy'
  | 'simulation'
  | 'optimization'
  | 'blueprint'
  | 'digital-twin'
  | 'report';

export interface StageDefinition {
  id: WorkflowStage;
  shortLabel: string;
  fullLabel: string;
  /** Stages that render real, working content in this release. */
  available: boolean;
}

export const WORKFLOW_STAGES: StageDefinition[] = [
  { id: 'site-climate', shortLabel: 'Site & Climate', fullLabel: 'Site & Climate', available: true },
  { id: 'mission', shortLabel: 'Mission', fullLabel: 'Mission', available: true },
  { id: 'design', shortLabel: 'Design', fullLabel: 'Geometry & Envelope', available: true },
  { id: 'passive-strategy', shortLabel: 'Passive', fullLabel: 'Passive Strategy', available: true },
  { id: 'simulation', shortLabel: 'Simulation', fullLabel: 'Thermal Simulation', available: true },
  { id: 'optimization', shortLabel: 'Optimization', fullLabel: 'Optimization', available: true },
  { id: 'blueprint', shortLabel: 'Blueprint', fullLabel: 'Engineering Blueprint', available: true },
  { id: 'digital-twin', shortLabel: '3D', fullLabel: '3D Digital Twin', available: false },
  { id: 'report', shortLabel: 'Report', fullLabel: 'Engineering Report', available: false },
];

/** Canonical provenance vocabulary (Phase C). Never invent new categories. */
export type ProvenanceValue =
  | 'MODEL_ANALYSIS'
  | 'FORECAST'
  | 'HISTORICAL_REANALYSIS'
  | 'DESIGN'
  | 'FALLBACK'
  | 'SIMULATED'
  | 'OPTIMIZED';

export interface ProvenanceDescriptor {
  label: string;
  tailwind: string;
  /** Weather provenance describes input data; result provenance describes computed outputs. */
  family: 'weather' | 'result';
}

export const PROVENANCE_DESCRIPTORS: Record<ProvenanceValue, ProvenanceDescriptor> = {
  MODEL_ANALYSIS: {
    label: 'MODEL ANALYSIS',
    tailwind: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
    family: 'weather',
  },
  FORECAST: {
    label: 'FORECAST',
    tailwind: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
    family: 'weather',
  },
  HISTORICAL_REANALYSIS: {
    label: 'HISTORICAL REANALYSIS',
    tailwind: 'bg-violet-500/15 text-violet-300 border-violet-500/40',
    family: 'weather',
  },
  DESIGN: {
    label: 'DESIGN DATA',
    tailwind: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
    family: 'weather',
  },
  FALLBACK: {
    label: 'FALLBACK DATASET',
    tailwind: 'bg-orange-500/15 text-orange-300 border-orange-500/40',
    family: 'weather',
  },
  SIMULATED: {
    label: 'SIMULATED',
    tailwind: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40',
    family: 'result',
  },
  OPTIMIZED: {
    label: 'OPTIMIZED',
    tailwind: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/40',
    family: 'result',
  },
};

/** Maps the lowercase weather data_mode strings from the Phase B API onto canonical provenance. */
export const DATA_MODE_PROVENANCE: Record<string, ProvenanceValue> = {
  live: 'MODEL_ANALYSIS',
  forecast: 'FORECAST',
  historical: 'HISTORICAL_REANALYSIS',
  design: 'DESIGN',
  fallback: 'FALLBACK',
};

/** Comfort bounds mirrored for DISPLAY ONLY — the canonical values live in
 * services/formula_constants.py (DEFAULT_COMFORT_MIN/MAX). Never compute with these. */
export const DISPLAY_COMFORT_BOUNDS = { min: 18, max: 24 } as const;
