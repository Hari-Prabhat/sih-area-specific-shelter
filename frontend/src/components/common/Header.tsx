import React from 'react';
import { useDesignStudio } from '../../context';
import { Sparkles, Activity, Terminal } from 'lucide-react';

export const Header: React.FC = () => {
  const { loadGoldenDemo, isDemoScenario } = useDesignStudio();

  return (
    <header className="bg-slate-950/90 border-b border-slate-800 sticky top-0 z-40 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Technical Subtitle */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-500 to-blue-700 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-sky-500/20">
            <Terminal className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold text-white tracking-tight font-mono-data">
                THERMOSHELTER
              </span>
              <span className="text-[10px] font-mono-data px-1.5 py-0.2 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30 font-semibold">
                DIGITAL TWIN
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono-data hidden sm:block">
              Area-Specific Passive Shelter Optimizer & Building Physics Engine
            </p>
          </div>
        </div>

        {/* Global Action Bar: Golden Demo & System Status */}
        <div className="flex items-center gap-3">
          {/* Section 3: Golden Demo Scenario Quick-Load */}
          <button
            type="button"
            onClick={loadGoldenDemo}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono-data font-bold tracking-wider uppercase transition-all shadow-sm cursor-pointer ${
              isDemoScenario
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                : 'bg-slate-900 hover:bg-slate-800 text-sky-400 hover:text-white border border-sky-500/40 hover:border-sky-400'
            }`}
            title="Preload Golden Demo Scenario (Leh, Ladakh • 4 Occupants • Permanent • Thermal Comfort & Energy Independence)"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>LOAD DEMO (LEH, LADAKH)</span>
          </button>

          {/* System Mode Telemetry Indicator */}
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono-data text-slate-400">
            <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span>CALIBRATION: <b>IMD / ASHRAE 2026</b></span>
          </div>
        </div>
      </div>
    </header>
  );
};
