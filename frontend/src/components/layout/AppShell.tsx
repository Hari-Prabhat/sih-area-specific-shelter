import React, { useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { useDesignStore } from "../../store/designStore";
import { Play, Sparkles, AlertCircle, MapPin } from "lucide-react";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const {
    selectedCity,
    setCity,
    cities,
    people,
    setPeople,
    homeType,
    setHomeType,
    fetchInitialData,
    runSimulation,
    runOptimization,
    loading,
    error,
  } = useDesignStore();

  useEffect(() => {
    fetchInitialData();
  }, []);

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Main Engineering Workstation Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Workstation Command Bar */}
        <header className="h-16 bg-slate-900/90 border-b border-slate-800/80 px-6 flex items-center justify-between shrink-0 z-20 backdrop-blur">
          {/* Global Location & Mission Selector */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-mono flex items-center gap-1">
                <MapPin className={`w-3.5 h-3.5 ${!selectedCity ? "text-amber-400 animate-bounce" : "text-sky-400"}`} />
                <span>LOCATION:</span>
              </span>
              <select
                value={selectedCity}
                onChange={(e) => setCity(e.target.value)}
                className={`rounded-lg px-3 py-1.5 font-semibold text-xs focus:outline-none cursor-pointer shadow-sm transition-all ${
                  !selectedCity
                    ? "bg-amber-950/40 border-2 border-amber-400 text-amber-300 ring-2 ring-amber-400/20"
                    : "bg-slate-950 border border-slate-700 text-sky-400 focus:border-sky-400"
                }`}
              >
                <option value="" className="bg-slate-950 text-amber-400 font-bold">
                  📍 Choose the location
                </option>
                {cities.length > 0 ? (
                  cities.map((c) => (
                    <option key={c.id} value={c.id} className="bg-slate-950 text-white">
                      {c.display}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="leh" className="bg-slate-950 text-white">🏔️ Leh, Ladakh (Cold)</option>
                    <option value="jaisalmer" className="bg-slate-950 text-white">🏜️ Jaisalmer (Hot-Dry)</option>
                    <option value="chennai" className="bg-slate-950 text-white">🌊 Chennai (Humid)</option>
                    <option value="delhi" className="bg-slate-950 text-white">🏙️ Delhi (Composite)</option>
                    <option value="bengaluru" className="bg-slate-950 text-white">🌳 Bengaluru (Moderate)</option>
                  </>
                )}
              </select>
            </div>

            <div className="h-4 w-px bg-slate-800" />

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-mono">OCCUPANTS:</span>
              <div className="flex items-center gap-1 bg-slate-950 border border-slate-700 rounded-lg px-2 py-1">
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={people}
                  onChange={(e) => setPeople(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-8 bg-transparent text-white font-mono text-xs focus:outline-none text-center font-bold"
                />
                <span className="text-slate-500 text-[11px]">pers</span>
              </div>
            </div>

            <div className="h-4 w-px bg-slate-800" />

            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setHomeType("Temporary")}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  homeType === "Temporary"
                    ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Temporary (Modular)
              </button>
              <button
                onClick={() => setHomeType("Permanent")}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  homeType === "Permanent"
                    ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Permanent (Masonry)
              </button>
            </div>
          </div>

          {/* Primary Quick-Trigger Simulation Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => runSimulation()}
              disabled={loading.simulation || !selectedCity}
              className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-sky-400 border border-sky-500/30 rounded-lg text-xs font-semibold tracking-wide transition-all shadow-sm disabled:opacity-50 cursor-pointer"
            >
              <Play className={`w-3.5 h-3.5 ${loading.simulation ? "animate-spin" : ""}`} />
              <span>{loading.simulation ? "SIMULATING..." : "SIMULATE"}</span>
            </button>

            <button
              onClick={() => runOptimization()}
              disabled={loading.optimization || !selectedCity}
              className="flex items-center gap-2 px-4 py-1.5 bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-slate-950 rounded-lg text-xs font-bold tracking-wide transition-all shadow-md hover:shadow-sky-500/20 disabled:opacity-50 cursor-pointer"
            >
              <Sparkles className={`w-3.5 h-3.5 ${loading.optimization ? "animate-spin" : ""}`} />
              <span>{loading.optimization ? "OPTIMIZING..." : "OPTIMIZE"}</span>
            </button>
          </div>
        </header>

        {/* Global Error Banner if any */}
        {error && (
          <div className="bg-rose-950/90 border-b border-rose-800 px-6 py-2 text-rose-300 text-xs flex items-center justify-between gap-2 shadow-md">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => useDesignStore.setState({ error: null })}
              className="px-2.5 py-0.5 rounded bg-rose-900/60 hover:bg-rose-800 text-rose-200 text-[11px] font-mono cursor-pointer transition-all"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Main Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
};
