import { lazy, Suspense } from 'react';
import { useStudioState } from '../store/useStudioState';
import StageSuspense from './ui/StageSuspense';

/**
 * D5 batch 1: dedicated 3D Digital Twin stage.
 *
 * Hosts the SAME parametric ShelterModel3D component used inside the Design
 * stage — the twin is always derived from canonical studio state (design +
 * wall material + last simulation result when present). No second 3D
 * renderer, no duplicate state.
 */
const ShelterModel3D = lazy(() => import('./ShelterModel3D'));

export default function TwinStage() {
  const { design, wallMaterial, simulation } = useStudioState();
  const result = simulation.result;
  const canonical = result as
    | { canonical?: import('../services/api').CanonicalSimulationResult }
    | null;
  const comfortPct = canonical?.canonical?.comfort_percentage;
  const avgIndoor = canonical?.canonical?.comfort_metrics?.avg;

  return (
    <section aria-label="3D Digital Twin" className="space-y-4">
      <header>
        <h2 className="text-xl font-semibold text-slate-100">3D Digital Twin</h2>
        <p className="text-xs text-slate-400 mt-1">
          Illustrative parameter-driven digital twin; engineering values are
          specified in the Design Description.
        </p>
      </header>
      <Suspense fallback={<StageSuspense label="Loading 3D twin…" />}>
        <ShelterModel3D
          design={design}
          materialName={wallMaterial ?? 'Unknown material'}
          comfortIndex={comfortPct}
          avgTemp={avgIndoor}
        />
      </Suspense>
    </section>
  );
}
