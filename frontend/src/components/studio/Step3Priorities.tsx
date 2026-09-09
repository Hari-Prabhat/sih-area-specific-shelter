import React from 'react';
import { useDesignStudio } from '../../context';
import type { DesignPriority, PriorityImportance } from '../../types';
import {
  Thermometer,
  SunMedium,
  DollarSign,
  Feather,
  Zap,
  ShieldCheck,
  Star,
} from 'lucide-react';

const PRIORITIES_LIST: {
  id: DesignPriority;
  label: string;
  icon: React.ElementType;
  description: string;
}[] = [
  {
    id: 'Thermal Comfort',
    label: 'Thermal Comfort',
    icon: Thermometer,
    description: 'Stabilize indoor air between 18°C–24°C, minimize extreme cold discomfort degree hours.',
  },
  {
    id: 'Energy Independence',
    label: 'Energy Independence',
    icon: SunMedium,
    description: 'Maximize passive solar heat gain, daylighting, and eliminate fossil fuel heating reliance.',
  },
  {
    id: 'Low Cost',
    label: 'Low Cost',
    icon: DollarSign,
    description: 'Prioritize low-cost local materials, standardized components, and frugal construction.',
  },
  {
    id: 'Low Weight',
    label: 'Low Weight',
    icon: Feather,
    description: 'Lightweight composite modules suitable for helicopter or pack-animal high-altitude transport.',
  },
  {
    id: 'Rapid Deployment',
    label: 'Rapid Deployment',
    icon: Zap,
    description: 'Tool-free prefabricated flat-pack erection in under 24–48 hours by unskilled crews.',
  },
  {
    id: 'Durability',
    label: 'Durability',
    icon: ShieldCheck,
    description: 'Structural resistance to sub-zero freeze-thaw cycles, high wind buffeting, and heavy snow loads.',
  },
];

export const Step3Priorities: React.FC = () => {
  const { priorities, togglePriority, setPriorityImportance, errors } = useDesignStudio();

  const getPrioritySelection = (id: DesignPriority) =>
    priorities.find((p) => p.priority === id);

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
          STEP 3 of 5 — MULTI-OBJECTIVE WEIGHTS
        </div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Establish Design Priorities
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Select and weight the primary trade-offs guiding envelope thickness, structural materials, and fenestration aperture.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {PRIORITIES_LIST.map((item) => {
          const Icon = item.icon;
          const selection = getPrioritySelection(item.id);
          const isSelected = Boolean(selection);

          return (
            <div
              key={item.id}
              className={`p-4 rounded-lg border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-sky-950/40 border-sky-500 ring-1 ring-sky-500/50 shadow-lg'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <button
                    type="button"
                    onClick={() => togglePriority(item.id)}
                    className="flex items-center gap-2 text-left focus:outline-none cursor-pointer"
                  >
                    <div
                      className={`p-2 rounded ${
                        isSelected ? 'bg-sky-500/20 text-sky-400' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="font-bold text-sm text-white font-mono-data">
                      {item.label}
                    </span>
                  </button>

                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => togglePriority(item.id)}
                    className="mt-1.5 w-4 h-4 rounded border-slate-700 bg-slate-950 text-sky-500 focus:ring-sky-500 cursor-pointer"
                  />
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
              </div>

              {/* Relative Importance Toggle */}
              {isSelected && (
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] font-mono-data text-slate-400 uppercase">
                    Relative Weight:
                  </span>
                  <div className="flex gap-1">
                    {(['Primary', 'Secondary'] as PriorityImportance[]).map((level) => {
                      const isLevel = selection?.importance === level;
                      return (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setPriorityImportance(item.id, level)}
                          className={`px-2 py-0.5 rounded text-[10px] font-mono-data font-semibold uppercase transition-colors cursor-pointer ${
                            isLevel
                              ? level === 'Primary'
                                ? 'bg-sky-500/30 text-sky-300 border border-sky-500/60'
                                : 'bg-indigo-500/30 text-indigo-300 border border-indigo-500/60'
                              : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
                          }`}
                        >
                          {level}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {errors.priorities && (
        <p className="text-xs text-rose-400 font-mono-data font-semibold">
          ⚠ {errors.priorities}
        </p>
      )}

      <div className="bg-slate-950/60 border border-slate-800 rounded p-3 flex items-center gap-2 text-xs font-mono-data text-slate-400">
        <Star className="w-4 h-4 text-sky-400 shrink-0" />
        <span>
          Priorities are purely structured configuration inputs. Optimization solver calculations will be executed in downstream stages.
        </span>
      </div>
    </div>
  );
};
