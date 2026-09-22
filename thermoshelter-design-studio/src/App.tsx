import { lazy, Suspense } from 'react';
import { buildBlueprintSimulationOverlay } from './services/blueprintOverlay';
// D4-D: Engineering Report stage (eager-light; artifact sources lazy inside).
const ReportStage = lazy(() => import('./components/ReportStage'));
import { CircleDashed, Mountain } from 'lucide-react';
import { StudioStateProvider, useStudioState, activeWeatherProvenance, fallbackUsed } from './store/useStudioState';
import ClimateInput from './components/ClimateInput';
import MissionStage from './components/MissionStage';
import ShelterDesigner from './components/ShelterDesigner';
import PassiveStrategyStage from './components/PassiveStrategyStage';
import ContextStrip from './components/ui/ContextStrip';
import Stepper from './components/ui/Stepper';
import { mapStrategyDto } from './services/passiveStrategy';
import Button from './components/ui/Button';
import StageSuspense from './components/ui/StageSuspense';
import { WORKFLOW_STAGES, WorkflowStage } from './theme/tokens';

// D3 code splitting: heavyweight stage views load on demand. The initial
// shell (header, ContextStrip, Stepper, Climate/Mission/Design stages) ships
// without three.js, recharts or the CAD blueprint; each chunk is fetched the
// first time its stage opens. Shared UI primitives stay eager on purpose.
const SimulationResults = lazy(() => import('./components/SimulationResults'));
const ComparativeAnalysis = lazy(() => import('./components/ComparativeAnalysis'));
const EngineeringBlueprint = lazy(() => import('./components/EngineeringBlueprint'));
// D5 batch 1: the dedicated 3D stage renders the real digital twin (same
// component the Design stage hosts) from canonical state — no duplicate 3D.
const ShelterModel3D = lazy(() => import('./components/ShelterModel3D'));
const TwinStage = lazy(() => import('./components/TwinStage'));

/** Renders the stage's working content, or an honest placeholder for later phases. */
function StageRouter() {
  const {
    stage,
    simulation,
    optimization,
  } = useStudioState();

  switch (stage) {
    case 'site-climate':
      return <ClimateStage />;
    case 'mission':
      return <MissionStage />;
    case 'design':
      return <ShelterDesignerStage />;
    case 'passive-strategy':
      return <PassiveStrategyStage />;
    case 'digital-twin':
      return <TwinStage />;
    // D4-D: the Engineering Report is a real stage composed from canonical state.
    case 'report':
      return <ReportStage />;
    case 'simulation':
      return simulation.result ? (
        <SimulationResultsStage />
      ) : (
        <EmptyStage
          title="No Simulation Results Yet"
          message="Configure the shelter in the Design stage, then run the authoritative Python thermal simulation."
        />
      );
    case 'optimization':
      return <ComparativeStage />;
    case 'blueprint':
      return <BlueprintStage />;
    default:
      return null;
  }
}

/** Site & Climate stage: the authoritative Phase B/C climate workflow. */
function ClimateStage() {
  const { climate, climateProfile, setClimate, setClimateProfile, setStage } = useStudioState();
  return (
    <div className="space-y-6">
      <ClimateInput
        climateData={climate}
        setClimateData={setClimate}
        climateProfile={climateProfile}
        onProfileChange={setClimateProfile}
      />
      <div className="flex justify-end">
        <Button onClick={() => setStage('mission')}>Continue to Mission</Button>
      </div>
    </div>
  );
}

/** Geometry & Envelope stage: the existing designer, store-wired. */
function ShelterDesignerStage() {
  const {
    design,
    wallMaterial,
    mission,
    simulation,
    optimization,
    setDesignField,
    replaceDesign,
    setWallMaterial,
    setMissionField,
    runSimulation,
    setStage,
  } = useStudioState();

  return (
    <ShelterDesigner
      shelterDesign={design}
      setShelterDesign={replaceDesign}
      selectedMaterial={wallMaterial}
      setSelectedMaterial={setWallMaterial}
      onRunSimulation={runSimulation}
      isSimulating={simulation.loading}
      updateDesignField={setDesignField}
      missionOccupants={mission.occupants}
      onMissionOccupantsChange={(n) => setMissionField('occupants', n)}
    />
  );
}

/** Simulation stage content. */
function SimulationResultsStage() {
  const { simulation, climate, design, wallMaterial, climateProfile } = useStudioState();
  return (
    <SimulationResults
      result={simulation.result!}
      climateData={climate}
      shelterDesign={design}
      materialName={wallMaterial}
      climateProfile={climateProfile}
    />
  );
}

/** Optimization stage content. */
function ComparativeStage() {
  const { climate, design, wallMaterial, simulation, optimization, runOptimization, applyCandidate, applyRecommendation, setStage } =
    useStudioState();
  return (
    <ComparativeAnalysis
      climateData={climate}
      shelterDesign={design}
      selectedMaterial={wallMaterial}
      baselineResult={simulation.result}
      optimizationResult={optimization.result}
      isOptimizing={optimization.loading}
      onRunOptimization={runOptimization}
      onApplyCandidate={applyCandidate}
      onApplyRecommendation={applyRecommendation}
      onNavigateToDesign={() => setStage('design')}
    />
  );
}

/** Blueprint stage content. */
function BlueprintStage() {
  const { design, wallMaterial, climate, simulation } = useStudioState();
  // D4-C1: pass the REAL canonical result as optional evidence overlay. The
  // Blueprint displays only genuine engine outputs and only when they belong
  // to the current design run; otherwise the overlay is absent — never fabricated.
  const canonical = (simulation.result as { canonical?: import('./services/api').CanonicalSimulationResult } | null)?.canonical;
  const overlay = buildBlueprintSimulationOverlay(canonical ?? null);
  return (
    <EngineeringBlueprint
      design={design}
      materialName={wallMaterial}
      locationName={climate.location}
      simulation={overlay}
    />
  );
}

/** Honest placeholder for stages delivered in later phases. */
function DeferredStage({ stage }: { stage: WorkflowStage }) {
  const def = WORKFLOW_STAGES.find((s) => s.id === stage)!;
  return (
    <div className="text-center py-24">
      <CircleDashed className="w-14 h-14 text-slate-600 mx-auto mb-4" aria-hidden="true" />
      <h3 className="text-xl font-semibold text-slate-300 mb-2">{def.fullLabel}</h3>
      <p className="text-sm text-slate-500 max-w-md mx-auto">
        This stage is part of the planned studio workflow and will be delivered in a later phase.
        Current data for this stage remains available where it exists today.
      </p>
    </div>
  );
}

/** Empty-state with a helpful next action. */
function EmptyStage({ title, message }: { title: string; message: string }) {
  const { setStage } = useStudioState();
  return (
    <div className="text-center py-20">
      <CircleDashed className="w-14 h-14 text-slate-600 mx-auto mb-4" aria-hidden="true" />
      <h3 className="text-xl font-semibold text-slate-400 mb-2">{title}</h3>
      <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">{message}</p>
      <Button onClick={() => setStage('design')}>Go to Geometry &amp; Envelope</Button>
    </div>
  );
}

/** Persistent engineering-context strip values derived from real state only. */
function ContextStripBinding() {
  const {
    climate,
    climateProfile,
    design,
    wallMaterial,
    backendHealth,
  } = useStudioState();

  const provenance = activeWeatherProvenance(climateProfile);

  // Session 2: when a resolved climate profile is active, its canonical city
  // is the authoritative location label — not the preset dropdown selection.
  const resolvedLocation = climateProfile?.climate?.city ?? climate.location;

  // Authoritative classification: the backend strategy's climate_mode (annual
  // climatological profile). The climate dict's coarse climate_zone is a
  // provenance-only description of the current weather window — rendered with
  // an explicit scope label so the two concepts are never conflated.
  const strategyMode = mapStrategyDto(climateProfile?.strategy)?.climateMode ?? null;
  const windowZone =
    (climateProfile?.climate as { climate_zone?: string } | undefined)?.climate_zone ?? null;

  return (
    <ContextStrip
      data={{
        location: resolvedLocation,
        climateZone: strategyMode,
        windowZoneLabel: windowZone,
        provenance,
        fallbackUsed: fallbackUsed(climateProfile),
        windowHours: climateProfile ? climateProfile.series.air_temperature_C.length : null,
        materialName: wallMaterial,
        insulationLabel:
          design.insulationType && design.insulationType !== 'None' ? `${design.insulationType} insulation` : 'No insulation',
        orientationDeg: design.orientation,
        geometryLabel: `${design.length} × ${design.width} × ${design.height} m`,
        backendHealth,
      }}
    />
  );
}

/** Error banners for global failures (simulation / optimization). */
function ErrorBanners() {
  const { simulation, optimization, clearSimulationError, clearOptimizationError } = useStudioState();
  return (
    <>
      {simulation.error && (
        <div className="mb-6 p-4 bg-red-950/60 border border-red-500/50 rounded-xl flex items-start gap-3 text-red-200" role="alert">
          <div className="flex-1">
            <h4 className="font-semibold text-sm text-red-300">Simulation Error</h4>
            <p className="text-xs text-red-200 mt-0.5">{simulation.error}</p>
          </div>
          <button
            onClick={clearSimulationError}
            className="text-red-400 hover:text-red-200 text-xs font-semibold px-2 py-1 rounded bg-red-900/40 hover:bg-red-900/60"
          >
            Dismiss
          </button>
        </div>
      )}
      {optimization.error && (
        <div className="mb-6 p-4 bg-red-950/60 border border-red-500/50 rounded-xl flex items-start gap-3 text-red-200" role="alert">
          <div className="flex-1">
            <h4 className="font-semibold text-sm text-red-300">Optimization Error</h4>
            <p className="text-xs text-red-200 mt-0.5">{optimization.error}</p>
          </div>
          <button
            onClick={clearOptimizationError}
            className="text-red-400 hover:text-red-200 text-xs font-semibold px-2 py-1 rounded bg-red-900/40 hover:bg-red-900/60"
          >
            Dismiss
          </button>
        </div>
      )}
    </>
  );
}

function StudioShell() {
  const { stage, setStage, expertMode, setExpertMode, maxVisitedIndex } = useStudioState();

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a1220] via-[#0a1424] to-[#070d16] text-slate-100 engineering-grid-bg">
      {/* Header */}
      <header className="bg-[#0a1220]/90 backdrop-blur-md border-b border-cyan-500/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-sky-700 rounded-lg flex items-center justify-center shadow-md shadow-cyan-500/20">
              <Mountain className="w-6 h-6 text-white" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">
                ThermoShelter <span className="text-cyan-400">Design Studio</span>
              </h1>
              <p className="text-xs text-slate-400">Area-Specific Passive Shelter Digital Twin & Thermal Design Optimization</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Mode toggle: guided stepper vs expert free navigation */}
            <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={expertMode}
                onChange={(e) => setExpertMode(e.target.checked)}
                className="w-4 h-4 accent-cyan-500"
              />
              Expert mode
            </label>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>SIH 2026 | DRDO</span>
            </div>
          </div>
        </div>
      </header>

      {/* Persistent context strip — real state only */}
      <div className="max-w-7xl mx-auto px-4 pt-4">
        <ContextStripBinding />
      </div>

      {/* Workflow navigation */}
      <div className="max-w-7xl mx-auto px-4 pt-3">
        <Stepper current={stage} onNavigate={setStage} expertMode={expertMode} maxVisitedIndex={maxVisitedIndex} />
      </div>

      {/* Main stage content — heavyweight views resolve through Suspense */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <ErrorBanners />
        <Suspense fallback={<StageSuspense />}>
          <StageRouter />
        </Suspense>
      </main>

      <footer className="bg-[#0a1220]/80 border-t border-cyan-500/10 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
          <p>ThermoShelter Design Studio | SIH 2026 | SIH26051 | DRDO</p>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <StudioStateProvider>
      <StudioShell />
    </StudioStateProvider>
  );
}
