import React, { useState } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import {
  Sparkles,
  MapPin,
  Users,
  Building2,
  Layers,
  ArrowRight,
  Compass,
} from "lucide-react";

export const NewDesignPage: React.FC = () => {
  const { cities, selectedCity, people, homeType, resetToNewDesign } =
    useDesignStore();

  const [targetCity, setTargetCity] = useState(selectedCity || "leh");
  const [targetPeople, setTargetPeople] = useState(people || 4);
  const [targetHomeType, setTargetHomeType] = useState<"Permanent" | "Temporary">(
    homeType || "Permanent"
  );
  const [archetype, setArchetype] = useState<"recommended" | "standard" | "compact" | "solar">(
    "recommended"
  );
  const [isInitializing, setIsInitializing] = useState(false);

  const handleCreate = async () => {
    setIsInitializing(true);
    try {
      await resetToNewDesign({
        city: targetCity,
        people: targetPeople,
        homeType: targetHomeType,
        archetype,
      });
    } finally {
      setIsInitializing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <SectionHeader
        title="Initialize New Shelter Engineering Project"
        subtitle="Configure target location, occupancy requirements, and initial envelope archetype to initialize a verified parametric design session."
        badge="PROJECT SETUP"
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Step 1: Location */}
        <div className="eng-panel p-5 space-y-4">
          <div className="flex items-center gap-2 text-sky-400 font-bold text-xs uppercase tracking-wider border-b border-slate-800 pb-2">
            <MapPin className="w-4 h-4" />
            <span>1. Deployment Station</span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Select target climatic zone for IMD and EPW weather series coupling.
          </p>

          <div className="space-y-2">
            {cities.map((c) => (
              <button
                key={c.id}
                onClick={() => setTargetCity(c.id)}
                className={`w-full text-left p-3 rounded-lg border text-xs transition-all ${
                  targetCity === c.id
                    ? "bg-sky-500/15 border-sky-400 text-white font-semibold"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>{c.display}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700">
                    {c.badge}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  HDD: {c.hdd} | Alt: {c.elevation}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Requirements */}
        <div className="eng-panel p-5 space-y-4">
          <div className="flex items-center gap-2 text-sky-400 font-bold text-xs uppercase tracking-wider border-b border-slate-800 pb-2">
            <Users className="w-4 h-4" />
            <span>2. Mission Requirements</span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Occupancy count and structure permanence define envelope sizing and internal thermal mass.
          </p>

          {/* Occupants */}
          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-300 block">Occupancy Count:</label>
            <div className="grid grid-cols-4 gap-2">
              {[2, 4, 6, 8].map((n) => (
                <button
                  key={n}
                  onClick={() => setTargetPeople(n)}
                  className={`py-2 text-xs font-mono font-bold rounded-lg border transition-all ${
                    targetPeople === n
                      ? "bg-sky-500/20 border-sky-400 text-sky-300"
                      : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  {n} pers
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs font-mono text-slate-400">Custom:</span>
              <input
                type="number"
                min="1"
                max="16"
                value={targetPeople}
                onChange={(e) => setTargetPeople(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-16 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs font-mono text-white text-center"
              />
              <span className="text-xs text-slate-500">persons</span>
            </div>
          </div>

          {/* Home Typology */}
          <div className="space-y-2 pt-3 border-t border-slate-800">
            <label className="text-xs font-mono text-slate-300 block">Permanence Typology:</label>
            <div className="space-y-2">
              <button
                onClick={() => setTargetHomeType("Permanent")}
                className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                  targetHomeType === "Permanent"
                    ? "bg-sky-500/15 border-sky-400 text-white font-semibold"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <div className="font-bold flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-sky-400" />
                  <span>Permanent (Masonry / Stone)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  High thermal mass envelope damping extreme diurnal temperature swings.
                </p>
              </button>

              <button
                onClick={() => setTargetHomeType("Temporary")}
                className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                  targetHomeType === "Temporary"
                    ? "bg-sky-500/15 border-sky-400 text-white font-semibold"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <div className="font-bold flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-amber-400" />
                  <span>Temporary (Modular / Prefab)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Rapid deployment insulated panels with lightweight construction.
                </p>
              </button>
            </div>
          </div>
        </div>

        {/* Step 3: Initial Archetype */}
        <div className="eng-panel p-5 space-y-4">
          <div className="flex items-center gap-2 text-sky-400 font-bold text-xs uppercase tracking-wider border-b border-slate-800 pb-2">
            <Compass className="w-4 h-4" />
            <span>3. Envelope Archetype</span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Select starting architectural template to seed parametric dimensions and materials.
          </p>

          <div className="space-y-2">
            <button
              onClick={() => setArchetype("recommended")}
              className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                archetype === "recommended"
                  ? "bg-emerald-500/15 border-emerald-400 text-white font-semibold"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-emerald-300 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  Climate Recommended
                </span>
                <span className="text-[9px] font-mono bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-800">
                  Recommended
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Auto-sizes floor area and pairs climate-optimal envelope thermal resistance.
              </p>
            </button>

            <button
              onClick={() => setArchetype("standard")}
              className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                archetype === "standard"
                  ? "bg-sky-500/15 border-sky-400 text-white font-semibold"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <div className="font-bold text-slate-200">Standard Code Baseline</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Standard rectilinear envelope conforming to NBC norms.
              </p>
            </button>

            <button
              onClick={() => setArchetype("compact")}
              className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                archetype === "compact"
                  ? "bg-sky-500/15 border-sky-400 text-white font-semibold"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <div className="font-bold text-slate-200">Compact Modular Unit</div>
              <p className="text-[11px] text-slate-400 mt-1">
                High envelope surface-to-volume ratio for rapid alpine installation.
              </p>
            </button>

            <button
              onClick={() => setArchetype("solar")}
              className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                archetype === "solar"
                  ? "bg-sky-500/15 border-sky-400 text-white font-semibold"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <div className="font-bold text-slate-200">Passive Direct Solar Gain</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Extended South-facing glazed facade maximizing winter solar capture.
              </p>
            </button>
          </div>
        </div>
      </div>

      {/* Summary and Launch Action */}
      <div className="eng-panel p-6 bg-gradient-to-r from-slate-900 via-slate-900 to-sky-950/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-mono text-sky-400 font-semibold mb-1">
            PROJECT SPECIFICATION READY
          </div>
          <div className="text-sm font-bold text-white">
            {targetCity.toUpperCase()} Station · {targetPeople} Occupants · {targetHomeType} Typology
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Initializes geometry, resets previous simulation cache, and configures engineering bounds.
          </p>
        </div>

        <button
          onClick={handleCreate}
          disabled={isInitializing}
          className="px-6 py-3 bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-slate-950 font-bold rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-sky-500/25 transition-all cursor-pointer shrink-0 disabled:opacity-50"
        >
          <span>{isInitializing ? "INITIALIZING..." : "LAUNCH SHELTER DESIGNER"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
