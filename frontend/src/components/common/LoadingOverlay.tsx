import React from 'react';
import { Loader2, ShieldAlert } from 'lucide-react';

export interface LoadingOverlayProps {
  stageText: string;
  isMockMode?: boolean;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  stageText,
  isMockMode = true,
}) => {
  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full shadow-2xl text-center space-y-4">
        {/* Engineering Spinner */}
        <div className="relative inline-flex items-center justify-center">
          <div className="w-16 h-16 rounded-full border-2 border-slate-800 border-t-sky-400 animate-spin" />
          <Loader2 className="w-6 h-6 text-sky-400 absolute animate-pulse" />
        </div>

        <div>
          <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
            ThermoShelter Computation Engine
          </div>
          <h4 className="text-base font-bold text-white font-mono-data">
            {stageText}
          </h4>
        </div>

        {/* Technical progress bar animation */}
        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
          <div className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full w-2/3 animate-[pulse_1.5s_ease-in-out_infinite]" />
        </div>

        {/* Mock/Demo Transparency Banner */}
        {isMockMode && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-950/40 border border-amber-500/30 rounded text-amber-300 text-xs font-mono-data">
            <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
            <span>Simulated Synthesis (Frontend Prototype Demo Mode)</span>
          </div>
        )}
      </div>
    </div>
  );
};
