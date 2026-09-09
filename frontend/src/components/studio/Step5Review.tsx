import React from 'react';
import { useDesignStudio } from '../../context';
import {
  MapPin,
  Users,
  Target,
  Clock,
  Sliders,
  Boxes,
  Edit3,
  Sparkles,
  ShieldAlert,
} from 'lucide-react';

export const Step5Review: React.FC = () => {
  const {
    location,
    mission,
    priorities,
    resources,
    isDemoScenario,
    goToStep,
    handleGenerateDesign,
    isLoading,
  } = useDesignStudio();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
          STEP 5 of 5 — CONTRACT SYNTHESIS & REVIEW
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-bold text-white tracking-tight">
            Review Design Requirements Specification
          </h2>

          {isDemoScenario && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-950/60 border border-amber-500/50 rounded text-amber-300 font-mono-data text-xs font-bold uppercase tracking-wider animate-pulse">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>DEMO SCENARIO PRELOADED</span>
            </div>
          )}
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Validate high-level operational requirements before compiling the structured shelter design payload.
        </p>
      </div>

      {/* Review Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Location */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 relative group">
          <button
            type="button"
            onClick={() => goToStep(1)}
            className="absolute top-3.5 right-3.5 text-xs font-mono-data text-sky-400 hover:text-sky-300 flex items-center gap-1 bg-slate-950/80 border border-slate-700 px-2 py-1 rounded cursor-pointer"
          >
            <Edit3 className="w-3 h-3" />
            <span>EDIT</span>
          </button>

          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase mb-2">
            <MapPin className="w-4 h-4" />
            LOCATION
          </div>

          <div className="space-y-1">
            <div className="text-base font-bold text-white font-mono-data">
              {location.displayName}
            </div>
            <div className="text-xs text-slate-400 font-mono-data">
              Selection Mode: <span className="text-slate-200 capitalize">{location.mode}</span>
              {location.elevationM && ` • Altitude: ${location.elevationM} m`}
            </div>
          </div>
        </div>

        {/* Card 2: Mission */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 relative group">
          <button
            type="button"
            onClick={() => goToStep(2)}
            className="absolute top-3.5 right-3.5 text-xs font-mono-data text-sky-400 hover:text-sky-300 flex items-center gap-1 bg-slate-950/80 border border-slate-700 px-2 py-1 rounded cursor-pointer"
          >
            <Edit3 className="w-3 h-3" />
            <span>EDIT</span>
          </button>

          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase mb-2">
            <Target className="w-4 h-4" />
            MISSION
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono-data">
            <div>
              <span className="text-slate-500 block">OCCUPANTS</span>
              <span className="text-slate-100 font-bold flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-sky-400" />
                {mission.occupants} Persons
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">PURPOSE</span>
              <span className="text-slate-100 font-bold">{mission.purpose}</span>
            </div>
            <div>
              <span className="text-slate-500 block">DEPLOYMENT TYPE</span>
              <span className="text-slate-100 font-bold">{mission.deploymentType}</span>
            </div>
            <div>
              <span className="text-slate-500 block">DURATION</span>
              <span className="text-slate-100 font-bold flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                {mission.duration}
              </span>
            </div>
          </div>
        </div>

        {/* Card 3: Priorities */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 relative group">
          <button
            type="button"
            onClick={() => goToStep(3)}
            className="absolute top-3.5 right-3.5 text-xs font-mono-data text-sky-400 hover:text-sky-300 flex items-center gap-1 bg-slate-950/80 border border-slate-700 px-2 py-1 rounded cursor-pointer"
          >
            <Edit3 className="w-3 h-3" />
            <span>EDIT</span>
          </button>

          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase mb-2">
            <Sliders className="w-4 h-4" />
            PRIORITIES
          </div>

          <div className="flex flex-wrap gap-1.5">
            {priorities.map((item) => (
              <span
                key={item.priority}
                className="px-2.5 py-1 rounded bg-slate-950 border border-slate-700 text-xs font-mono-data text-slate-200 flex items-center gap-1.5"
              >
                <span>{item.priority}</span>
                <span className="text-[10px] text-sky-400 font-bold uppercase">
                  ({item.importance})
                </span>
              </span>
            ))}
          </div>
        </div>

        {/* Card 4: Available Resources */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 relative group">
          <button
            type="button"
            onClick={() => goToStep(4)}
            className="absolute top-3.5 right-3.5 text-xs font-mono-data text-sky-400 hover:text-sky-300 flex items-center gap-1 bg-slate-950/80 border border-slate-700 px-2 py-1 rounded cursor-pointer"
          >
            <Edit3 className="w-3 h-3" />
            <span>EDIT</span>
          </button>

          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase mb-2">
            <Boxes className="w-4 h-4" />
            AVAILABLE RESOURCES
          </div>

          <div className="space-y-1.5 text-xs font-mono-data">
            <div>
              <span className="text-slate-500">ENERGY: </span>
              <span className="text-slate-200 font-medium">
                {resources.energy.length > 0 ? resources.energy.join(', ') : 'None specified (Optional)'}
              </span>
            </div>
            <div>
              <span className="text-slate-500">MATERIALS: </span>
              <span className="text-slate-200 font-medium">
                {resources.materials.length > 0
                  ? resources.materials.join(', ')
                  : 'Standard catalog (Optional)'}
              </span>
            </div>
            {resources.customMaterialNotes && (
              <div className="text-[11px] text-slate-400 italic">
                Notes: {resources.customMaterialNotes}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => goToStep(1)}
          className="flex items-center gap-2 px-4 py-2.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono-data text-xs font-semibold transition-colors cursor-pointer"
        >
          <Edit3 className="w-4 h-4" />
          <span>EDIT REQUIREMENTS</span>
        </button>

        <button
          type="button"
          onClick={handleGenerateDesign}
          disabled={isLoading}
          className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-slate-950 font-mono-data text-sm font-bold tracking-wider uppercase shadow-lg shadow-sky-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          <span>GENERATE DESIGN</span>
        </button>
      </div>
    </div>
  );
};
