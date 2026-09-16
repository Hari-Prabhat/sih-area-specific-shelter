import { Check, ChevronLeft, ChevronRight, Lock } from 'lucide-react';
import { WORKFLOW_STAGES, WorkflowStage } from '../../theme/tokens';
import Button from './Button';

interface StepperProps {
  current: WorkflowStage;
  onNavigate: (stage: WorkflowStage) => void;
  /** Guided mode shows Next/Back and disables direct jumps; expert mode is free navigation. */
  expertMode: boolean;
}

/**
 * D1 primitive: workflow navigation for the 9-stage studio.
 * Guided mode: sequential stepper with Next/Back.
 * Expert mode: every available stage is directly clickable.
 * Unavailable stages render disabled with a lock icon (honest, not hidden).
 */
export default function Stepper({ current, onNavigate, expertMode }: StepperProps) {
  const index = WORKFLOW_STAGES.findIndex((s) => s.id === current);
  const prev = index > 0 ? WORKFLOW_STAGES[index - 1] : null;
  const next = index < WORKFLOW_STAGES.length - 1 ? WORKFLOW_STAGES[index + 1] : null;
  // Guided Next may only move to an available stage.
  const nextNavigable = next && next.available ? next : null;

  return (
    <nav aria-label="Workflow stages" className="bg-slate-800/50 border border-slate-700/30 rounded-xl px-4 py-3">
      <ol className="flex items-center gap-1 overflow-x-auto">
        {WORKFLOW_STAGES.map((stage, i) => {
          const isCurrent = stage.id === current;
          const isCompleted = i < index;
          const clickable = expertMode && stage.available && !isCurrent;

          return (
            <li key={stage.id} className="flex items-center shrink-0">
              <button
                type="button"
                onClick={() => clickable && onNavigate(stage.id)}
                disabled={!clickable}
                aria-current={isCurrent ? 'step' : undefined}
                title={stage.available ? stage.fullLabel : `${stage.fullLabel} — coming in a later phase`}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap
                  ${isCurrent ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : ''}
                  ${!isCurrent && isCompleted ? 'text-emerald-300 hover:bg-slate-700/50' : ''}
                  ${!isCurrent && !isCompleted && stage.available ? 'text-slate-300 hover:bg-slate-700/50' : ''}
                  ${!stage.available ? 'text-slate-500 cursor-not-allowed' : ''}
                  ${clickable ? 'cursor-pointer' : 'cursor-default'}
                  focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border
                    ${isCurrent ? 'border-amber-400 bg-amber-500/30 text-amber-200' : ''}
                    ${!isCurrent && isCompleted ? 'border-emerald-400/60 bg-emerald-500/15 text-emerald-300' : ''}
                    ${!isCurrent && !isCompleted && stage.available ? 'border-slate-600 bg-slate-700/40 text-slate-300' : ''}
                    ${!stage.available ? 'border-slate-700 bg-slate-800/60 text-slate-600' : ''}`}
                >
                  {isCompleted ? <Check className="w-3 h-3" aria-hidden="true" /> : !stage.available ? <Lock className="w-2.5 h-2.5" aria-hidden="true" /> : i + 1}
                </span>
                {stage.shortLabel}
              </button>
              {i < WORKFLOW_STAGES.length - 1 && (
                <span className="w-4 h-px bg-slate-700 mx-1" aria-hidden="true" />
              )}
            </li>
          );
        })}
      </ol>

      {!expertMode && (
        <div className="flex justify-between mt-3 pt-3 border-t border-slate-700/40">
          <Button
            variant="secondary"
            onClick={() => prev && onNavigate(prev.id)}
            disabled={!prev}
            icon={<ChevronLeft className="w-4 h-4" aria-hidden="true" />}
          >
            Back
          </Button>
          <Button
            onClick={() => nextNavigable && onNavigate(nextNavigable.id)}
            disabled={!nextNavigable}
            icon={<ChevronRight className="w-4 h-4" aria-hidden="true" />}
          >
            Next: {nextNavigable ? nextNavigable.shortLabel : '—'}
          </Button>
        </div>
      )}
    </nav>
  );
}
