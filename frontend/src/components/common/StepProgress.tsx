import React from 'react';
import { MapPin, Target, Sliders, Boxes, CheckCircle2, ChevronRight } from 'lucide-react';

export interface StepProgressProps {
  currentStep: number;
  onStepClick: (step: number) => void;
  maxAccessibleStep: number;
}

const STEPS = [
  { step: 1, label: 'LOCATION', short: 'Loc', icon: MapPin },
  { step: 2, label: 'MISSION', short: 'Mission', icon: Target },
  { step: 3, label: 'PRIORITIES', short: 'Priorities', icon: Sliders },
  { step: 4, label: 'AVAILABLE RESOURCES', short: 'Resources', icon: Boxes },
  { step: 5, label: 'REVIEW', short: 'Review', icon: CheckCircle2 },
];

export const StepProgress: React.FC<StepProgressProps> = ({
  currentStep,
  onStepClick,
  maxAccessibleStep,
}) => {
  return (
    <nav aria-label="Design Studio Multi-Step Progress" className="w-full">
      <div className="bg-slate-900/90 border border-slate-700/80 rounded-lg p-2.5 shadow-md flex items-center justify-between overflow-x-auto gap-2">
        {STEPS.map((item, index) => {
          const Icon = item.icon;
          const isActive = currentStep === item.step;
          const isCompleted = currentStep > item.step;
          const isClickable = item.step <= maxAccessibleStep;

          return (
            <React.Fragment key={item.step}>
              <button
                type="button"
                onClick={() => isClickable && onStepClick(item.step)}
                disabled={!isClickable}
                className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono-data transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/50 font-bold shadow-sm'
                    : isCompleted
                    ? 'text-emerald-400 hover:bg-slate-800/80 cursor-pointer font-medium'
                    : isClickable
                    ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 cursor-pointer'
                    : 'text-slate-600 cursor-not-allowed opacity-60'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isActive
                      ? 'bg-sky-400 text-slate-950'
                      : isCompleted
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {isCompleted ? '✓' : item.step}
                </span>

                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span className="hidden md:inline uppercase tracking-wider">{item.label}</span>
                <span className="md:hidden uppercase tracking-wider">{item.short}</span>
              </button>

              {index < STEPS.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-slate-700 shrink-0 hidden sm:block" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </nav>
  );
};
