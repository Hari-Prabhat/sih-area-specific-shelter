import { useState, lazy, Suspense } from 'react';
import {
  Layers,
  Plus,
  Sparkles,
  Award,
  TrendingUp,
  Check,
  ChevronRight,
  Shield,
  Sun,
  Flame,
  Zap,
  Sliders,
  Eye,
  Info,
  ArrowUpRight,
  ArrowDownRight,
  RotateCcw,
  Loader2,
  AlertCircle,
  Ruler,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { ClimateData, ShelterDesign, SimulationResult } from '../types';
import {
  runSimulationViaApi,
  describeApiError,
  ApiError,
  CanonicalOptimizationResult,
  CanonicalOptimizationCandidate,
} from '../services/api';import { materials, getMaterialByName } from '../data/materials';
import { deriveBaselineMetrics } from '../services/baselineMetrics';
import StageSuspense from './ui/StageSuspense';
import Button from './ui/Button';
import ProvenanceChip from './ui/ProvenanceChip';

// D3: lazy three.js digital twin — see ShelterDesigner.
const ShelterModel3D = lazy(() => import('./ShelterModel3D'));

// D3: the optimization result carries the climate scenario provenance it was
// evaluated against (Phase C contract: climate_provenance on the response).
// Surfacing it here keeps OPTIMIZED results visibly distinct from weather data.
function ClimateProvenanceBadge({ result }: { result: CanonicalOptimizationResult }) {
  if (!result.climate_provenance) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <ProvenanceChip
        value={result.climate_provenance}
        fallbackUsed={result.climate_fallback_used ?? false}
      />
      <span className="text-xs text-slate-400">climate scenario used for optimization</span>
    </div>
  );
}

interface ComparativeAnalysisProps {
  climateData: ClimateData;
  shelterDesign: ShelterDesign;
  selectedMaterial?: string;
  baselineResult?: SimulationResult | null;
  optimizationResult?: CanonicalOptimizationResult | null;
  isOptimizing?: boolean;
  onRunOptimization?: (
    weights?: { comfort: number; efficiency: number; solar: number },
    nTrials?: number,
    homeType?: string,
    // Batch 1-A: progressive-disclosure geometry search (fixed prototype bounds).
    optimizeGeometry?: boolean
  ) => Promise<void>;
  onApplyCandidate?: (candidate: CanonicalOptimizationCandidate) => void;
  /** H: apply the separate comfort-first recommendation as the canonical design. */
  onApplyRecommendation?: (candidate: CanonicalOptimizationCandidate) => void;
  onNavigateToDesign?: () => void;
}

interface ComparisonEntry {
  id: string;
  label: string;
  result: SimulationResult;
}

export default function ComparativeAnalysis({
  climateData,
  shelterDesign,
  selectedMaterial = 'Rammed Earth (Stabilized)',
  baselineResult,
  optimizationResult,
  isOptimizing = false,
  onRunOptimization,
  onApplyCandidate,
  onApplyRecommendation,
  onNavigateToDesign,
}: ComparativeAnalysisProps) {
  // Mode selection: Bayesian Optimization vs Material Sweeps
  const [activeMode, setActiveMode] = useState<'optimization' | 'sweep'>('optimization');

  // Multi-objective weights configuration
  const [weights, setWeights] = useState({ comfort: 0.5, efficiency: 0.3, solar: 0.2 });
  const [nTrials, setNTrials] = useState<number>(20);
  const [homeType, setHomeType] = useState<'Permanent' | 'Temporary'>('Permanent');
  // Batch 1-A: geometry+envelope search is OPT-IN. Default preserves the
  // pre-D5 fixed-geometry workflow exactly (no geometry fields sent).
  const [optimizeGeometry, setOptimizeGeometry] = useState<boolean>(false);
  // D: variables actually enabled in the most recent optimization run —
  // recorded when the run is triggered so the explanation never invents scope.
  const [lastRunConfig, setLastRunConfig] = useState<{
    geometry: boolean;
    trials: number;
    weights: { comfort: number; efficiency: number; solar: number };
  } | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CanonicalOptimizationCandidate | null>(null);
  const [previewCandidateDesign, setPreviewCandidateDesign] = useState<ShelterDesign | null>(null);
  const [appliedCandidateRank, setAppliedCandidateRank] = useState<number | null>(null);

  // Manual material comparisons
  const [comparisons, setComparisons] = useState<ComparisonEntry[]>([]);
  const [newMaterial, setNewMaterial] = useState(materials[0].name);
  const [isLoading, setIsLoading] = useState(false);
  const [sweepError, setSweepError] = useState<string | null>(null);

  // Set initial selected candidate when optimization result arrives
  const candidates: CanonicalOptimizationCandidate[] = optimizationResult?.ranked_designs || [];
  const activeCandidate = selectedCandidate || (candidates.length > 0 ? candidates[0] : null);

  // D4-A WP4: baseline metrics derive from a REAL simulation result only.
  // The former fabricated fallbacks (60 / 500*0.7 / 600 / 250) are gone —
  // without a baseline the UI renders a truthful empty state instead.
  const baseline = deriveBaselineMetrics(baselineResult);

  // E2: the separate comfort-first recommendation pass output.
  const recPayload = optimizationResult?.recommendation ?? null;
  const recommendation = recPayload?.recommendation ?? null;

  // Deltas vs the baseline — computed only when a real baseline exists.
  const recommended = optimizationResult?.recommended_design;
  const comfortDelta =
    baseline.hasBaseline && recommended && baseline.comfortPct != null
      ? recommended.comfort_percentage - baseline.comfortPct
      : null;
  const heatingDelta =
    baseline.hasBaseline && recommended && baseline.heatingDemandKwh != null
      ? baseline.heatingDemandKwh - recommended.heating_demand_kwh
      : null;
  const heatLossDelta =
    baseline.hasBaseline && recommended && baseline.totalHeatLossKwh != null
      ? baseline.totalHeatLossKwh - recommended.total_heat_loss_kwh
      : null;

  // Update weights
  const handleWeightChange = (key: 'comfort' | 'efficiency' | 'solar', val: number) => {
    setWeights((prev) => ({ ...prev, [key]: val }));
  };

  // Run Bayesian optimization handler
  const handleTriggerOptimization = async () => {
    if (onRunOptimization) {
      setAppliedCandidateRank(null);
      setLastRunConfig({ geometry: optimizeGeometry, trials: nTrials, weights: { ...weights } });
      await onRunOptimization(weights, nTrials, homeType, optimizeGeometry);
    }
  };

  // Apply a candidate design to the project
  const handleApply = (candidate: CanonicalOptimizationCandidate) => {
    setAppliedCandidateRank(candidate.rank);
    if (onApplyCandidate) {
      onApplyCandidate(candidate);
    }
  };

  // Inspect / preview candidate in 3D
  const handlePreview = (candidate: CanonicalOptimizationCandidate) => {
    setSelectedCandidate(candidate);
    // Build a ShelterDesign representation for previewing
    const previewDesign: ShelterDesign = {
      ...shelterDesign,
      // Batch 1-B: carry the candidate's own geometry when it reports one,
      // so the preview reflects the simulated envelope.
      ...(typeof candidate.length_m === 'number' &&
      typeof candidate.width_m === 'number' &&
      typeof candidate.height_m === 'number'
        ? { length: candidate.length_m, width: candidate.width_m, height: candidate.height_m }
        : {}),
      wallThickness: candidate.insulation_thickness_m > 0 ? shelterDesign.wallThickness : 0.3,
      windowArea: candidate.window_area_m2,
      windowGlazing: (candidate.glazing.includes('triple')
        ? 'triple'
        : candidate.glazing.includes('double')
        ? 'double'
        : 'single') as any,
      orientation:
        candidate.orientation.toLowerCase() === 'south'
          ? 180
          : candidate.orientation.toLowerCase() === 'north'
          ? 0
          : candidate.orientation.toLowerCase() === 'east'
          ? 90
          : 270,
      insulationType: candidate.insulation_thickness_m > 0 ? 'EPS' : 'None',
    };
    setPreviewCandidateDesign(previewDesign);
  };

  // Add manual material comparison via FastAPI backend only
  const addComparison = async () => {
    const material = materials.find((m) => m.name === newMaterial);
    if (!material) return;
    const insulation = getMaterialByName(shelterDesign.insulationType);
    setIsLoading(true);
    setSweepError(null);
    try {
      const result = await runSimulationViaApi(climateData, shelterDesign, material, insulation);
      setComparisons((prev) => [...prev, { id: Date.now().toString(), label: newMaterial, result }]);
    } catch (err: any) {
      console.error('Material comparison simulation failed:', err);
      setSweepError(describeApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  // Quick compare across 6 materials via FastAPI backend only
  const quickCompare = async () => {
    const quickMaterials = [
      'Mud/Adobe',
      'Rammed Earth (Stabilized)',
      'AAC Block (Autoclaved Aerated Concrete)',
      'Brick (Solid)',
      'Trombe Wall (Concrete + Glass)',
      'SIP Panel (Structural Insulated Panel)',
    ];
    const insulation = getMaterialByName(shelterDesign.insulationType);
    setIsLoading(true);
    setSweepError(null);
    try {
      const entries = await Promise.all(
        quickMaterials.map(async (matName, i) => {
          const material = materials.find((m) => m.name === matName);
          if (!material) return null;
          try {
            const result = await runSimulationViaApi(climateData, shelterDesign, material, insulation);
            return { id: `quick-${i}`, label: matName, result };
          } catch (err) {
            console.error(`Simulation failed for ${matName}:`, err);
            return null;
          }
        })
      );
      const successfulEntries = entries.filter(Boolean) as ComparisonEntry[];
      if (successfulEntries.length === 0) {
        setSweepError(describeApiError(new ApiError('unavailable', 'All quick-compare simulations failed')));
      } else {
        setComparisons(successfulEntries);
      }
    } catch (err: any) {
      console.error('Quick compare failed:', err);
      setSweepError(describeApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  // Chart data for optimization candidate comparison. D4-A WP4: the
  // Baseline series appears ONLY when a real baseline simulation exists —
  // the fabricated baseline bar was removed.
  const candidateChartData = [
    ...(baseline.hasBaseline
      ? [
          {
            name: 'Baseline',
            'Comfort (%)': baseline.comfortPct ?? 0,
            'Heat Loss (kWh)': baseline.totalHeatLossKwh ?? 0,
            'Heating Demand (kWh)': baseline.heatingDemandKwh ?? 0,
            'Solar Gain (kWh)': baseline.solarGainKwh ?? 0,
          },
        ]
      : []),
    ...candidates.slice(0, 4).map((c) => ({
      name: `#${c.rank} ${c.label}`,
      'Comfort (%)': Math.round(c.comfort_percentage),
      'Heat Loss (kWh)': Math.round(c.total_heat_loss_kwh),
      'Heating Demand (kWh)': Math.round(c.heating_demand_kwh),
      'Solar Gain (kWh)': Math.round(c.solar_gain_kwh),
    })),
  ];

  // D4-A WP4: the radar shows ONLY the optimizer's genuine sub-scores
  // (backend-computed, normalized 0–100). The former "Baseline" series
  // invented normalized values from heuristic formulas — baselines have no
  // optimizer sub-scores, so none are plotted.
  const radarData = activeCandidate
    ? [
        {
          subject: 'Comfort',
          Candidate: Math.round(activeCandidate.sub_scores.comfort * 100),
          fullMark: 100,
        },
        {
          subject: 'Efficiency',
          Candidate: Math.round(activeCandidate.sub_scores.efficiency * 100),
          fullMark: 100,
        },
        {
          subject: 'Solar',
          Candidate: Math.round(activeCandidate.sub_scores.solar * 100),
          fullMark: 100,
        },
        {
          subject: 'Overall',
          Candidate: Math.round(activeCandidate.overall_score * 100),
          fullMark: 100,
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* Header & Mode Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Optimization & Design Comparison</h2>
            <p className="text-sm text-slate-400">
              Multi-objective Bayesian optimization via Python Optuna TPE & 1D Forward Euler simulation
            </p>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex bg-slate-800/80 p-1 rounded-xl border border-slate-700/50">
          <button
            onClick={() => setActiveMode('optimization')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeMode === 'optimization'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Bayesian Optimizer
          </button>
          <button
            onClick={() => setActiveMode('sweep')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeMode === 'sweep'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Material Sweep
          </button>
        </div>
      </div>

      {activeMode === 'optimization' && (
        <div className="space-y-6">
          {/* Optimization Controls Panel */}
          <div className="bg-slate-800/60 rounded-xl border border-slate-700/40 p-6 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/40 pb-4">
              <div>
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-indigo-400" />
                  Optimization Problem Configuration
                </h3>
                <p className="text-xs text-slate-400">
                  Target location: <span className="text-amber-400 font-semibold">{climateData.location}</span> | Baseline Wall: <span className="text-white font-medium">{selectedMaterial}</span>
                </p>
              </div>

              {/* Permanence & Trials Selector */}
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-400">Shelter Permanence:</label>
                  <select
                    value={homeType}
                    onChange={(e) => setHomeType(e.target.value as any)}
                    className="px-3 py-1.5 bg-slate-700/60 border border-slate-600/50 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Permanent">Permanent (High Thermal Mass)</option>
                    <option value="Temporary">Temporary (Lightweight / Rapid)</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-400">Optuna Trials:</label>
                  <select
                    value={nTrials}
                    onChange={(e) => setNTrials(Number(e.target.value))}
                    className="px-3 py-1.5 bg-slate-700/60 border border-slate-600/50 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value={10}>10 Trials (~2 sec)</option>
                    <option value={20}>20 Trials (~4 sec, Recommended)</option>
                    <option value={30}>30 Trials (~6 sec)</option>
                    <option value={50}>50 Trials (~10 sec)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Objective Weights Sliders */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" />
                    Thermal Comfort Weight
                  </span>
                  <span className="font-mono text-emerald-400 font-bold">{Math.round(weights.comfort * 100)}%</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={0.8}
                  step={0.05}
                  value={weights.comfort}
                  onChange={(e) => handleWeightChange('comfort', parseFloat(e.target.value))}
                  className="w-full accent-emerald-500"
                />
                <p className="text-[11px] text-slate-400">Maximizes hours within the 18°C–24°C adaptive comfort zone.</p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-blue-400" />
                    Envelope Efficiency Weight
                  </span>
                  <span className="font-mono text-blue-400 font-bold">{Math.round(weights.efficiency * 100)}%</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={0.8}
                  step={0.05}
                  value={weights.efficiency}
                  onChange={(e) => handleWeightChange('efficiency', parseFloat(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <p className="text-[11px] text-slate-400">Minimizes weekly conditioning demand (kWh) and conduction heat loss.</p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium flex items-center gap-1.5">
                    <Sun className="w-3.5 h-3.5 text-amber-400" />
                    Passive Solar Harvesting Weight
                  </span>
                  <span className="font-mono text-amber-400 font-bold">{Math.round(weights.solar * 100)}%</span>
                </div>
                <input
                  type="range"
                  min={0.05}
                  max={0.6}
                  step={0.05}
                  value={weights.solar}
                  onChange={(e) => handleWeightChange('solar', parseFloat(e.target.value))}
                  className="w-full accent-amber-500"
                />
                <p className="text-[11px] text-slate-400">Optimizes window fenestration & solar orientation for winter solar gain.</p>
              </div>
            </div>

            {/* Batch 1-A: geometry + envelope search (progressive disclosure, opt-in) */}
            <div className="border border-slate-700/40 rounded-xl bg-slate-900/40">
              <label className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 cursor-pointer">
                <span className="flex items-center gap-2.5">
                  <Ruler className="w-4 h-4 text-violet-400" aria-hidden="true" />
                  <span>
                    <span className="text-sm font-semibold text-white">Optimize Geometry + Envelope</span>
                    <span className="block text-[11px] text-slate-400">
                      Adds length, width and clear height to the search alongside the six envelope dimensions.
                    </span>
                  </span>
                </span>
                <input
                  type="checkbox"
                  checked={optimizeGeometry}
                  onChange={(e) => setOptimizeGeometry(e.target.checked)}
                  aria-label="Optimize geometry and envelope"
                  className="w-4 h-4 accent-violet-500 focus-visible:ring-2 focus-visible:ring-violet-400"
                />
              </label>
              {optimizeGeometry && (
                <div className="px-4 pb-3 pt-1 space-y-2">
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
                    <span className="text-slate-400">Length:</span>
                    <span className="font-mono text-slate-200">4.0–10.0 m</span>
                    <span className="text-slate-400">Width:</span>
                    <span className="font-mono text-slate-200">3.0–6.0 m</span>
                    <span className="text-slate-400">Height:</span>
                    <span className="font-mono text-slate-200">2.4–4.0 m</span>
                    <span className="text-slate-400">Aspect ratio:</span>
                    <span className="font-mono text-slate-200">≤ 3.0</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-violet-500/10 border border-violet-500/30 text-[10px] font-semibold text-violet-300 uppercase tracking-wider">
                      Prototype optimization bounds
                    </span>
                    <span className="text-[10px] text-slate-500">
                      Engineering assumptions for this prototype — not DRDO, regulatory or ISO requirements.
                    </span>
                  </div>
                  {nTrials < 30 && (
                    <p className="text-[11px] text-amber-300/90 flex items-center gap-1.5" role="note">
                      <Info className="w-3.5 h-3.5" aria-hidden="true" />
                      Geometry search benefits from 30+ trials.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* D: plain-language explanation of what optimization actually does.
                States the weighted-scalar (NOT Pareto) method and lists only the
                variables enabled in the current/last run. */}
            <div className="rounded-xl border border-slate-700/40 bg-slate-900/40 p-4 flex items-start gap-3">
              <Info className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" aria-hidden="true" />
              <div className="space-y-1.5 text-xs text-slate-300">
                <p>
                  Optimization searches the allowed design space and ranks simulated shelter
                  configurations using thermal comfort, heat-loss efficiency, and solar utilization.
                  Each candidate is evaluated with the authoritative 168-hour thermal simulation;
                  the sampler (Optuna TPE) learns which configurations score best.
                </p>
                <p className="text-slate-400">
                  Scoring is a <span className="text-slate-200 font-medium">weighted single score</span> —
                  comfort {Math.round((lastRunConfig?.weights ?? weights).comfort * 100)}% / efficiency{' '}
                  {Math.round((lastRunConfig?.weights ?? weights).efficiency * 100)}% / solar{' '}
                  {Math.round((lastRunConfig?.weights ?? weights).solar * 100)}%. It is{' '}
                  <span className="text-slate-200 font-medium">not Pareto optimization</span>.
                </p>
                <p className="text-slate-400">
                  Variables searched in this run:{' '}
                  <span className="text-slate-200 font-medium">
                    insulation thickness, window area, wall material, glazing, orientation, thermal mass
                    {(lastRunConfig?.geometry ?? optimizeGeometry) ? ', length, width, clear height' : ''}
                  </span>
                  . Door area stays fixed at the design's value and is never optimized.
                </p>
              </div>
            </div>

            {/* Launch CTA */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Info className="w-4 h-4 text-indigo-400" />
                <span>Runs Python TPE sampler across insulation thickness (0–200mm), fenestration (1–12m²), wall substrates, & orientation{optimizeGeometry ? ', plus shelter geometry (L×W×H within the prototype bounds)' : ''}.</span>
              </div>

              <Button
                onClick={handleTriggerOptimization}
                disabled={isOptimizing}
                loading={isOptimizing}
                loadingText={`Running Optuna Optimizer (${nTrials} Trials)…`}
                icon={!isOptimizing ? <Sparkles className="w-4 h-4" /> : undefined}
              >
                Run Bayesian Optimization
              </Button>
            </div>
          </div>

          {/* If No Results Yet */}
          {!optimizationResult && (
            <div className="text-center py-16 bg-slate-800/30 rounded-xl border border-slate-700/20">
              <Sparkles className="w-12 h-12 text-indigo-400/50 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-slate-300 mb-1">No Optimization Run Yet</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto mb-4">
                Click "Run Bayesian Optimization" above to search the parameter space using Optuna and discover top-performing shelter configurations.
              </p>
              <Button
                variant="secondary"
                onClick={handleTriggerOptimization}
                disabled={isOptimizing}
                icon={<Sparkles className="w-4 h-4" />}
              >
                Start Optimization
              </Button>
            </div>
          )}

          {/* Results View */}
          {optimizationResult && (
            <div className="space-y-6">
              {/* Recommended Design Highlight Banner */}
              {optimizationResult.recommended_design && (
                <div className="relative overflow-hidden bg-gradient-to-br from-indigo-900/40 via-purple-900/30 to-slate-900/80 rounded-2xl border border-indigo-500/40 p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="space-y-1.5">
                      <ClimateProvenanceBadge result={optimizationResult} />
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-500/20 border border-amber-500/30 rounded-full text-xs font-semibold text-amber-300 mb-2">
                        <Award className="w-3.5 h-3.5" />
                        Recommended Design #{optimizationResult.recommended_design.rank} — {optimizationResult.recommended_design.label}
                      </div>
                      <h3 className="text-2xl font-bold text-white">
                        {optimizationResult.recommended_design.wall_material_name} + {optimizationResult.recommended_design.insulation_mm}mm Insulation
                      </h3>
                      {typeof optimizationResult.recommended_design.length_m === 'number' &&
                        typeof optimizationResult.recommended_design.width_m === 'number' &&
                        typeof optimizationResult.recommended_design.height_m === 'number' && (
                          <p className="text-xs text-violet-300 font-medium">
                            Geometry: {optimizationResult.recommended_design.length_m.toFixed(1)} × {optimizationResult.recommended_design.width_m.toFixed(1)} × {optimizationResult.recommended_design.height_m.toFixed(1)} m
                            {typeof optimizationResult.recommended_design.floor_area_m2 === 'number'
                              ? ` · ${optimizationResult.recommended_design.floor_area_m2.toFixed(1)} m² floor`
                              : ''}
                          </p>
                        )}
                      <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                        {optimizationResult.recommended_design.rationale}
                      </p>
                    </div>

                    {/* Action Button */}
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleApply(optimizationResult.recommended_design!)}
                        className={`px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 shadow-md transition ${
                          appliedCandidateRank === optimizationResult.recommended_design.rank
                            ? 'bg-emerald-600 text-white'
                            : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-emerald-500/20'
                        }`}
                      >
                        {appliedCandidateRank === optimizationResult.recommended_design.rank ? (
                          <>
                            <Check className="w-4 h-4" /> Applied to Studio
                          </>
                        ) : (
                          <>
                            <Check className="w-4 h-4" /> Apply to Design Studio
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Recommended Key Metrics Delta */}
                  {!baseline.hasBaseline && (
                    <p className="mt-4 flex items-center gap-2 text-xs text-amber-300/90 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                      <Info className="w-3.5 h-3.5 shrink-0" />
                      No baseline comparison yet — a real simulation of the current design runs automatically with your next optimization, or run one now from the Design stage.
                    </p>
                  )}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-indigo-500/20">
                    <div className="bg-slate-900/50 p-3.5 rounded-xl border border-slate-700/40">
                      <span className="text-[11px] text-slate-400 block mb-1">Comfort Improvement</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-emerald-400">
                          {Math.round(optimizationResult.recommended_design.comfort_percentage)}%
                        </span>
                        {comfortDelta != null && (comfortDelta >= 0 ? (
                          <span className="text-xs font-semibold text-emerald-400 flex items-center">
                            <ArrowUpRight className="w-3 h-3" />
                            +{comfortDelta.toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-xs font-semibold text-red-400 flex items-center">
                            <ArrowDownRight className="w-3 h-3" />
                            {comfortDelta.toFixed(0)}%
                          </span>
                        ))}
                      </div>
                      <span className="text-[10px] text-slate-500">
                        {baseline.comfortPct != null ? `Baseline: ${baseline.comfortPct}%` : 'No baseline simulation yet'}
                      </span>
                    </div>

                    <div className="bg-slate-900/50 p-3.5 rounded-xl border border-slate-700/40">
                      <span className="text-[11px] text-slate-400 block mb-1">Heating Demand Reduction</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-blue-400">
                          {Math.round(optimizationResult.recommended_design.heating_demand_kwh)} kWh
                        </span>
                        {heatingDelta != null && heatingDelta >= 0 && (
                          <span className="text-xs font-semibold text-blue-400 flex items-center">
                            <ArrowDownRight className="w-3 h-3" />
                            -{heatingDelta.toFixed(0)}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500">
                        {baseline.heatingDemandKwh != null ? `Baseline: ${baseline.heatingDemandKwh} kWh` : 'No baseline simulation yet'}
                      </span>
                    </div>

                    <div className="bg-slate-900/50 p-3.5 rounded-xl border border-slate-700/40">
                      <span className="text-[11px] text-slate-400 block mb-1">Heat Loss Reduction</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-purple-400">
                          {Math.round(optimizationResult.recommended_design.total_heat_loss_kwh)} kWh
                        </span>
                        {heatLossDelta != null && heatLossDelta >= 0 && (
                          <span className="text-xs font-semibold text-purple-400 flex items-center">
                            <ArrowDownRight className="w-3 h-3" />
                            -{heatLossDelta.toFixed(0)}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500">
                        {baseline.totalHeatLossKwh != null ? `Baseline: ${baseline.totalHeatLossKwh} kWh` : 'No baseline simulation yet'}
                      </span>
                    </div>

                    <div className="bg-slate-900/50 p-3.5 rounded-xl border border-slate-700/40">
                      <span className="text-[11px] text-slate-400 block mb-1">Fenestration & U-Value</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-lg font-bold text-amber-400">
                          {optimizationResult.recommended_design.window_area_m2.toFixed(1)} m²
                        </span>
                        <span className="text-xs text-slate-400">
                          (U={optimizationResult.recommended_design.u_values.wall_u.toFixed(2)})
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500">
                        Facing: {optimizationResult.recommended_design.orientation}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* E/G: DUAL-OUTPUT COMPARISON — user-constrained design vs the
                  separate comfort-first ThermoShelter recommendation. */}
              {recPayload && (
                <DualOutputComparison
                  userDesign={optimizationResult.recommended_design ?? null}
                  recommendation={recommendation}
                  recStatus={recPayload.status}
                  recMessage={recPayload.message}
                  appliedRank={appliedCandidateRank}
                  onApplyRecommendation={() => {
                    if (recommendation && onApplyRecommendation) {
                      onApplyRecommendation(recommendation);
                    }
                  }}
                  onApplyUser={() => {
                    if (optimizationResult.recommended_design) handleApply(optimizationResult.recommended_design);
                  }}
                />
              )}

              {/* Ranked Candidate Cards Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    <Award className="w-4 h-4 text-indigo-400" />
                    Top Optimization Candidates Ranked by Optuna
                  </h3>
                  <span className="text-xs text-slate-400">
                    Evaluated over {optimizationResult.n_trials} trials via 168-hour forward Euler model
                    {/* Batch 1-B: honest disclosure of pre-simulation feasibility rejections. */}
                    {typeof optimizationResult.n_pruned === 'number' && optimizationResult.n_pruned > 0 && (
                      <span className="text-slate-500">
                        {' '}· {optimizationResult.n_pruned} infeasible candidate{optimizationResult.n_pruned === 1 ? '' : 's'} rejected before simulation
                      </span>
                    )}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {candidates.map((c) => {
                    const isSelected = activeCandidate?.rank === c.rank;
                    const isApplied = appliedCandidateRank === c.rank;

                    return (
                      <div
                        key={c.rank}
                        onClick={() => setSelectedCandidate(c)}
                        className={`cursor-pointer rounded-xl p-5 border transition-all ${
                          isSelected
                            ? 'bg-slate-800/90 border-indigo-500 ring-1 ring-indigo-500/50 shadow-lg shadow-indigo-500/10'
                            : 'bg-slate-800/40 border-slate-700/40 hover:border-slate-600/70 hover:bg-slate-800/60'
                        }`}
                      >
                        {/* Candidate Card Header */}
                        <div className="flex items-start justify-between gap-2 mb-3">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                c.rank === 1
                                  ? 'bg-amber-500 text-slate-900'
                                  : c.rank === 2
                                  ? 'bg-slate-300 text-slate-900'
                                  : 'bg-amber-700 text-white'
                              }`}
                            >
                              #{c.rank}
                            </span>
                            <div>
                              <h4 className="text-sm font-bold text-white">{c.label}</h4>
                              <p className="text-[10px] text-indigo-400 uppercase tracking-wider font-semibold">
                                Score: {(c.overall_score * 100).toFixed(1)} / 100
                              </p>
                            </div>
                          </div>

                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-700/60 text-slate-300 border border-slate-600/40">
                            {c.orientation}
                          </span>
                        </div>

                        {/* Card Subtitle Specs */}
                        <div className="space-y-1.5 text-xs text-slate-300 mb-4 pb-3 border-b border-slate-700/40">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Wall Substrate:</span>
                            <span className="font-medium text-white truncate max-w-[150px]">{c.wall_material_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Insulation:</span>
                            <span className="font-medium text-emerald-400">{c.insulation_mm} mm</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Glazing:</span>
                            <span className="font-medium text-cyan-300">{c.glazing_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Window Area:</span>
                            <span className="font-medium text-amber-300">{c.window_area_m2.toFixed(1)} m²</span>
                          </div>
                          {/* D5-B: candidate geometry (engine-reported). Rendered
                              only when the candidate carries geometry values. */}
                          {typeof c.length_m === 'number' && typeof c.width_m === 'number' && typeof c.height_m === 'number' && (
                            <div className="flex justify-between">
                              <span className="text-slate-400">Geometry:</span>
                              <span className="font-medium text-white">{c.length_m.toFixed(1)} × {c.width_m.toFixed(1)} × {c.height_m.toFixed(1)} m</span>
                            </div>
                          )}
                          {typeof c.floor_area_m2 === 'number' && (
                            <div className="flex justify-between">
                              <span className="text-slate-400">Floor Area:</span>
                              <span className="font-medium text-white">{c.floor_area_m2.toFixed(1)} m²</span>
                            </div>
                          )}
                          {typeof c.surface_to_volume_ratio === 'number' && (
                            <div className="flex justify-between">
                              <span className="text-slate-400">Surface / Volume:</span>
                              <span className="font-medium text-white">{c.surface_to_volume_ratio.toFixed(2)} 1/m</span>
                            </div>
                          )}
                          {c.thermal_mass_level && (
                            <div className="flex justify-between">
                              <span className="text-slate-400">Thermal Mass:</span>
                              <span className="font-medium text-orange-300 capitalize">{c.thermal_mass_level}</span>
                            </div>
                          )}
                        </div>

                        {/* Card Metrics Mini-Grid */}
                        <div className="grid grid-cols-2 gap-2 text-center mb-4">
                          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-700/30">
                            <span className="text-[10px] text-slate-400 block">Comfort</span>
                            <span className="text-sm font-bold text-emerald-400">{Math.round(c.comfort_percentage)}%</span>
                          </div>
                          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-700/30">
                            <span className="text-[10px] text-slate-400 block">Heating Demand</span>
                            <span className="text-sm font-bold text-blue-400">{Math.round(c.heating_demand_kwh)} kWh</span>
                          </div>
                          {typeof c.cooling_demand_kwh === 'number' && (
                            <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-700/30">
                              <span className="text-[10px] text-slate-400 block">Cooling Demand</span>
                              <span className="text-sm font-bold text-rose-400">{Math.round(c.cooling_demand_kwh)} kWh</span>
                            </div>
                          )}
                          <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-700/30">
                            <span className="text-[10px] text-slate-400 block">Solar Gain</span>
                            <span className="text-sm font-bold text-amber-400">{Math.round(c.solar_gain_kwh)} kWh</span>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleApply(c);
                            }}
                            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
                              isApplied
                                ? 'bg-emerald-600 text-white'
                                : 'bg-indigo-600/80 hover:bg-indigo-500 text-white'
                            }`}
                          >
                            {isApplied ? (
                              <>
                                <Check className="w-3.5 h-3.5" /> Applied
                              </>
                            ) : (
                              <>
                                <Check className="w-3.5 h-3.5" /> Apply Design
                              </>
                            )}
                          </button>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePreview(c);
                            }}
                            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-700/60 hover:bg-slate-700 text-slate-300 border border-slate-600/40 flex items-center gap-1"
                            title="Preview 3D model with this design"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Comparative Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Bar Chart: Baseline vs Top Candidates */}
                <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      Thermal Comfort vs. Energy Demand
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      {baseline.hasBaseline ? 'Baseline vs Candidates' : 'Candidates (no baseline simulation)'}
                    </span>
                  </div>

                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={candidateChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                      <YAxis stroke="#64748b" fontSize={10} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Bar dataKey="Comfort (%)" fill="#10b981" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Heating Demand (kWh)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Heat Loss (kWh)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Radar Chart: Multi-Objective Sub-Scores */}
                <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      Multi-Objective Trade-Off (Radar)
                    </h4>
                    <span className="text-[11px] text-indigo-300">
                      Comparing: {activeCandidate ? `#${activeCandidate.rank}` : '—'} (normalized sub-scores, not physical units)
                    </span>
                  </div>

                  {radarData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#334155" />
                        <PolarAngleAxis dataKey="subject" stroke="#94a3b8" fontSize={10} />
                        <PolarRadiusAxis stroke="#475569" fontSize={9} domain={[0, 100]} />
                        {/* D4-A WP4: candidate's genuine optimizer sub-scores only —
                            the fabricated "Baseline" series was removed. */}
                        <Radar
                          name={`Candidate #${activeCandidate?.rank}`}
                          dataKey="Candidate"
                          stroke="#6366f1"
                          fill="#6366f1"
                          fillOpacity={0.4}
                        />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '11px' }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[260px] flex items-center justify-center text-slate-500 text-xs">
                      No candidate selected for radar comparison
                    </div>
                  )}
                </div>
              </div>

              {/* Candidate 3D Preview Drawer / Embed */}
              {previewCandidateDesign && activeCandidate && (
                <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <Eye className="w-4 h-4 text-indigo-400" />
                        3D Architectural Preview — Candidate #{activeCandidate.rank} ({activeCandidate.label})
                      </h4>
                      <p className="text-xs text-slate-400">
                        {activeCandidate.wall_material_name} | {activeCandidate.insulation_mm}mm Insulation | {activeCandidate.window_area_m2.toFixed(1)}m² {activeCandidate.glazing_name} ({activeCandidate.orientation})
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleApply(activeCandidate)}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
                        aria-label={`Apply optimized design ${activeCandidate.rank ?? ''} to the design studio`}
                      >
                        <Check className="w-3.5 h-3.5" /> Apply This Design
                      </button>
                      <button
                        onClick={() => setPreviewCandidateDesign(null)}
                        className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs"
                      >
                        Close Preview
                      </button>
                    </div>
                  </div>

                  <Suspense fallback={<StageSuspense label="3D candidate preview" />}>
                    <ShelterModel3D design={previewCandidateDesign} materialName={activeCandidate.wall_material_name} />
                  </Suspense>
                </div>
              )}

              {/* Provenance Footer */}
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/40 flex items-center justify-between text-xs text-slate-400">
                <span>
                  Scientific Source of Truth: <strong className="text-slate-300">FastAPI /api/optimization/run</strong> (Optuna Tree-structured Parzen Estimator)
                </span>
                <span>ISO 6946 R-values + Forward Euler Thermal Simulation (168h)</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Material Sweep Mode */}
      {activeMode === 'sweep' && (
        <div className="space-y-6">
          {sweepError && (
            <div className="p-4 bg-red-950/60 border border-red-500/50 rounded-xl flex items-start gap-3 text-red-200">
              <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
              <div className="flex-1">
                <h4 className="font-semibold text-sm text-red-300">Simulation Error</h4>
                <p className="text-xs text-red-200 mt-0.5">{sweepError}</p>
              </div>
              <button
                onClick={() => setSweepError(null)}
                className="text-red-400 hover:text-red-200 text-xs font-semibold px-2 py-1 rounded bg-red-900/40 hover:bg-red-900/60"
              >
                Dismiss
              </button>
            </div>
          )}

          <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Add Material Variant to Compare</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <select
                value={newMaterial}
                onChange={(e) => setNewMaterial(e.target.value)}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white focus:outline-none"
              >
                {materials
                  .filter((m) => m.category !== 'Insulation')
                  .map((m) => (
                    <option key={m.name} value={m.name}>
                      {m.name}
                    </option>
                  ))}
              </select>
              <button
                onClick={addComparison}
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-500 text-white font-medium rounded-lg hover:bg-indigo-400 flex items-center justify-center gap-2 transition disabled:opacity-50"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Add Material
              </button>
              <button
                onClick={quickCompare}
                disabled={isLoading}
                className="px-4 py-2 bg-slate-700 text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-600 transition disabled:opacity-50"
              >
                Quick Compare (6 materials)
              </button>
            </div>
          </div>

          {comparisons.length >= 2 && (
            <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Material Sweep Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={comparisons.map((c) => ({
                    name: c.label.length > 15 ? c.label.substring(0, 15) + '...' : c.label,
                    'Avg Temp (°C)': c.result.avgInsideTemp,
                    Comfort: c.result.thermalComfortIndex,
                    'Heating Demand (kWh)': c.result.heatingDemandKwh,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-20} textAnchor="end" height={60} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="Avg Temp (°C)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Comfort" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Heating Demand (kWh)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {comparisons.length === 0 && (
            <div className="text-center py-16 bg-slate-800/30 rounded-xl border border-slate-700/20">
              <Layers className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-400 mb-2">No Material Sweeps Yet</h3>
              <p className="text-sm text-slate-500 mb-4">Add designs to compare or use Quick Compare</p>
              <button
                onClick={quickCompare}
                className="px-6 py-2 bg-indigo-500 text-white font-medium rounded-lg hover:bg-indigo-400"
              >
                Quick Compare
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =====================================================================
// E/G: DUAL-OUTPUT SIDE-BY-SIDE COMPARISON
//
// Card 1: the user's requirement-constrained best result (from the
// weighted-scalar run they configured).
// Card 2: the separate comfort-first ThermoShelter recommendation (own
// Optuna search, same engine/feasibility/bounds; objective = maximize
// simulated comfort hours, tie-break lower heat loss). NOT Pareto, NOT a
// reweighting of card 1.
// =====================================================================
function DualOutputComparison({
  userDesign,
  recommendation,
  recStatus,
  recMessage,
  appliedRank,
  onApplyRecommendation,
  onApplyUser,
}: {
  userDesign: CanonicalOptimizationCandidate | null;
  recommendation: CanonicalOptimizationCandidate | null;
  recStatus: 'ok' | 'no_comfort_feasible' | 'error';
  recMessage?: string;
  appliedRank: number | null;
  onApplyRecommendation: () => void;
  onApplyUser: () => void;
}) {
  const isRecApplied = recommendation != null && appliedRank === recommendation.rank;
  const isUserApplied = userDesign != null && appliedRank === userDesign.rank;

  // G1: explanation derived ONLY from actual parameter differences.
  const diffs: string[] = [];
  if (userDesign && recommendation) {
    if (recommendation.insulation_mm !== userDesign.insulation_mm) {
      diffs.push(
        recommendation.insulation_mm > userDesign.insulation_mm
          ? `thicker insulation (${recommendation.insulation_mm} mm vs ${userDesign.insulation_mm} mm)`
          : `thinner insulation (${recommendation.insulation_mm} mm vs ${userDesign.insulation_mm} mm)`
      );
    }
    if (Math.abs(recommendation.window_area_m2 - userDesign.window_area_m2) > 0.05) {
      diffs.push(
        recommendation.window_area_m2 < userDesign.window_area_m2
          ? `lower window area (${recommendation.window_area_m2.toFixed(1)} m² vs ${userDesign.window_area_m2.toFixed(1)} m²)`
          : `higher window area (${recommendation.window_area_m2.toFixed(1)} m² vs ${userDesign.window_area_m2.toFixed(1)} m²)`
      );
    }
    if (recommendation.wall_material !== userDesign.wall_material) {
      diffs.push(`different wall material (${recommendation.wall_material_name})`);
    }
    if (recommendation.glazing !== userDesign.glazing) {
      diffs.push(`different glazing (${recommendation.glazing_name})`);
    }
    if (recommendation.orientation.toLowerCase() !== userDesign.orientation.toLowerCase()) {
      diffs.push(`different orientation (${recommendation.orientation} vs ${userDesign.orientation})`);
    }
    if (
      typeof recommendation.length_m === 'number' &&
      typeof userDesign.length_m === 'number' &&
      (Math.abs(recommendation.length_m - userDesign.length_m) > 0.05 ||
        Math.abs((recommendation.width_m ?? 0) - (userDesign.width_m ?? 0)) > 0.05 ||
        Math.abs((recommendation.height_m ?? 0) - (userDesign.height_m ?? 0)) > 0.05)
    ) {
      diffs.push('different geometry');
    }
    if (
      recommendation.thermal_mass_level &&
      userDesign.thermal_mass_level &&
      recommendation.thermal_mass_level !== userDesign.thermal_mass_level
    ) {
      diffs.push(`different thermal mass (${recommendation.thermal_mass_level} vs ${userDesign.thermal_mass_level})`);
    }
  }

  const fmtComfort = (c: CanonicalOptimizationCandidate) => `${Math.round(c.comfort_percentage)}%`;

  return (
    <div className="rounded-2xl border border-slate-700/40 bg-slate-900/40 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <Award className="w-4 h-4 text-cyan-400" />
          Two Design Outputs
        </h3>
        <span className="text-[11px] text-slate-500">
          Same simulation engine and feasibility rules — two different objectives.
        </span>
      </div>

      {recStatus === 'no_comfort_feasible' && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-3" role="note">
          <Info className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" aria-hidden="true" />
          <div className="text-xs text-amber-200/90">
            <p className="font-semibold text-amber-200">No comfort-feasible design found</p>
            <p className="mt-0.5">
              The recommendation search completed successfully, but no configuration within the current
              prototype optimization bounds achieved simulated comfort in this climate and period.
              This is a search outcome, not an execution failure.
            </p>
          </div>
        </div>
      )}

      {recStatus === 'error' && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 flex items-start gap-3" role="alert">
          <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" aria-hidden="true" />
          <div className="text-xs text-red-200/90">
            <p className="font-semibold text-red-200">Recommendation pass failed</p>
            <p className="mt-0.5">{recMessage ?? 'An error occurred while running the comfort-first search.'}</p>
            <p className="mt-1 text-red-200/70">The user-constrained results above remain valid.</p>
          </div>
        </div>
      )}

      {recommendation && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* CARD 1 — USER DESIGN */}
          <div className="rounded-xl border border-indigo-500/30 bg-slate-800/50 p-4 space-y-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-300">Your Design</p>
              <p className="text-sm font-semibold text-white">Requirement Constrained</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Best result respecting your configured weights, materials and constraints.
              </p>
            </div>
            {userDesign ? (
              <>
                <CandidateSpecList c={userDesign} />
                <button
                  onClick={onApplyUser}
                  className={`w-full py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
                    isUserApplied ? 'bg-emerald-600 text-white' : 'bg-indigo-600/80 hover:bg-indigo-500 text-white'
                  }`}
                >
                  <Check className="w-3.5 h-3.5" /> {isUserApplied ? 'Applied to Studio' : 'Apply Your-Design Result'}
                </button>
              </>
            ) : (
              <p className="text-xs text-slate-500">No user-constrained candidate available.</p>
            )}
          </div>

          {/* CARD 2 — RECOMMENDATION */}
          <div className="rounded-xl border border-cyan-500/40 bg-gradient-to-br from-cyan-950/40 to-slate-900/60 p-4 space-y-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-cyan-300">ThermoShelter Recommendation</p>
              <p className="text-sm font-semibold text-white">Comfort First</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Model-generated configuration optimized for simulated thermal comfort within the
                available prototype engineering search space.
              </p>
            </div>
            <CandidateSpecList c={recommendation} accent="cyan" />
            {diffs.length > 0 && (
              <p className="text-[11px] text-slate-400">
                <span className="text-slate-300 font-medium">Why it differs:</span> recommendation uses{' '}
                {diffs.join('; ')}.
              </p>
            )}
            <button
              onClick={onApplyRecommendation}
              className={`w-full py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
                isRecApplied ? 'bg-emerald-600 text-white' : 'bg-cyan-600/80 hover:bg-cyan-500 text-white'
              }`}
            >
              <Check className="w-3.5 h-3.5" /> {isRecApplied ? 'Applied to Studio' : 'Apply Recommendation'}
            </button>
          </div>
        </div>
      )}

      {/* Comfort comparison strip — real values only. */}
      {userDesign && recommendation && (
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="rounded-lg border border-slate-700/40 bg-slate-900/60 p-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Your design comfort</p>
            <p className="text-lg font-bold text-indigo-300">{fmtComfort(userDesign)}</p>
          </div>
          <div className="rounded-lg border border-slate-700/40 bg-slate-900/60 p-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Recommendation comfort</p>
            <p className={`text-lg font-bold ${
              recommendation.comfort_percentage > userDesign.comfort_percentage ? 'text-cyan-300' : 'text-slate-300'
            }`}>
              {fmtComfort(recommendation)}
            </p>
          </div>
          <div className="rounded-lg border border-slate-700/40 bg-slate-900/60 p-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Advantage</p>
            <p className="text-lg font-bold text-emerald-400">
              {recommendation.comfort_percentage > userDesign.comfort_percentage
                ? `+${Math.round(recommendation.comfort_percentage - userDesign.comfort_percentage)}%`
                : recommendation.comfort_percentage === userDesign.comfort_percentage
                ? '—'
                : `${Math.round(recommendation.comfort_percentage - userDesign.comfort_percentage)}%`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function CandidateSpecList({
  c,
  accent = 'indigo',
}: {
  c: CanonicalOptimizationCandidate;
  accent?: 'indigo' | 'cyan';
}) {
  const rows: Array<[string, string]> = [
    ['Comfort hours', `${Math.round(c.comfort_hours)} h (${Math.round(c.comfort_percentage)}%)`],
    ['Geometry',
      typeof c.length_m === 'number' && typeof c.width_m === 'number' && typeof c.height_m === 'number'
        ? `${c.length_m.toFixed(1)} × ${c.width_m.toFixed(1)} × ${c.height_m.toFixed(1)} m`
        : 'Base design geometry'],
    ['Floor area', typeof c.floor_area_m2 === 'number' ? `${c.floor_area_m2.toFixed(1)} m²` : '—'],
    ['Orientation', c.orientation],
    ['Insulation', `${c.insulation_mm} mm`],
    ['Wall material', c.wall_material_name],
    ['Glazing', c.glazing_name],
    ['Window area', `${c.window_area_m2.toFixed(1)} m²`],
    ['Thermal mass', c.thermal_mass_level ?? '—'],
    ['Heat loss', `${Math.round(c.total_heat_loss_kwh)} kWh`],
    ['Useful solar', `${Math.round(c.solar_gain_kwh)} kWh`],
    ['Objective score', `${(c.overall_score * 100).toFixed(1)} / 100`],
  ];
  return (
    <dl className="space-y-1 text-xs">
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-3">
          <dt className="text-slate-400">{k}</dt>
          <dd className={`font-medium ${accent === 'cyan' ? 'text-cyan-100' : 'text-slate-100'} truncate`}>{v}</dd>
        </div>
      ))}
    </dl>
  );
}
