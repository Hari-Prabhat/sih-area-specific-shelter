import React from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { MetricCard } from "../components/common/MetricCard";
import {
  Sparkles,
  Check,
  ShieldCheck,
  Flame,
  Sun,
  Layers,
  Award,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export const OptimizationPage: React.FC = () => {
  const {
    selectedCity,
    people,
    homeType,
    optimizationResult,
    runOptimization,
    applyOptimizationRecommendation,
    setActiveTab,
    loading,
  } = useDesignStore();

  const rec = optimizationResult;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Bayesian Multi-Objective Envelope Optimization"
        subtitle="Optuna Tree-structured Parzen Estimator (TPE) exploring parametric combinations of thermal insulation, window aperture area, orientation, and glazing specs."
        badge={`OPTUNA TPE · ${selectedCity.toUpperCase()}`}
        action={
          <button
            onClick={() => runOptimization(35)}
            disabled={loading.optimization}
            className="flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-lg hover:shadow-sky-500/25 cursor-pointer disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${loading.optimization ? "animate-spin" : ""}`} />
            <span>{loading.optimization ? "SEARCHING PARAMETER SPACE..." : "RUN BAYESIAN SEARCH"}</span>
          </button>
        }
      />

      {!rec ? (
        <div className="p-12 eng-panel text-center max-w-xl mx-auto space-y-4">
          <Award className="w-12 h-12 text-sky-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Ready for Optimization Search</h2>
          <p className="text-xs text-slate-400">
            Click above to launch Bayesian multi-objective optimization across the design
            space for {selectedCity.toUpperCase()} ({homeType} shelter, {people} occupants).
          </p>
          <button
            onClick={() => runOptimization(35)}
            className="px-5 py-2 bg-sky-500 text-slate-950 font-bold rounded-lg text-xs cursor-pointer"
          >
            Start 35-Trial TPE Search
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* RECOMMENDED DESIGN HERO CARD */}
          <div className="eng-panel p-6 border-sky-500/50 bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/30 relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-mono text-sky-400 font-bold mb-1">
                  <Award className="w-4 h-4 text-emerald-400" />
                  <span>AI RECOMMENDED SPECIFICATION (#1 RANKED)</span>
                </div>
                <h2 className="text-xl font-black text-white tracking-tight">
                  Optimal Envelope for {selectedCity.toUpperCase()} ({homeType} Shelter)
                </h2>
              </div>

              {/* PRIMARY CTA: APPLY RECOMMENDED DESIGN */}
              <button
                onClick={() => {
                  applyOptimizationRecommendation();
                  setActiveTab("designer");
                }}
                className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-black rounded-xl text-xs tracking-wider transition-all shadow-lg hover:shadow-emerald-500/25 flex items-center gap-2 cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>APPLY RECOMMENDED DESIGN</span>
              </button>
            </div>

            {/* Key Performance Indicators */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">
                  Comfort Performance
                </span>
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {rec.simulation_result.comfort_percentage.toFixed(1)}%
                </span>
                <span className="text-[11px] text-slate-400 block font-mono">
                  {rec.simulation_result.comfort_hours.toFixed(0)} of 168 hours
                </span>
              </div>

              <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">
                  Discomfort Score
                </span>
                <span className="text-xl font-bold font-mono text-amber-400">
                  {rec.discomfort_score.toFixed(1)}
                </span>
                <span className="text-[11px] text-slate-400 block font-mono">
                  Degree-Hours (°C·h)
                </span>
              </div>

              <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">
                  Weekly Heat Loss
                </span>
                <span className="text-xl font-bold font-mono text-rose-400">
                  {rec.simulation_result.total_heat_loss_kwh.toFixed(1)}
                </span>
                <span className="text-[11px] text-slate-400 block font-mono">
                  kWh Envelope Loss
                </span>
              </div>

              <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">
                  Solar Gain
                </span>
                <span className="text-xl font-bold font-mono text-amber-400">
                  {rec.simulation_result.integrated_solar_energy_kwh.toFixed(1)}
                </span>
                <span className="text-[11px] text-slate-400 block font-mono">
                  Useful Direct Gain (kWh)
                </span>
              </div>
            </div>

            {/* Key Recommended Design Parameters */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs mb-6">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">WALL MATERIAL</span>
                <span className="font-semibold text-white capitalize">
                  {rec.optimal_wall_material}
                </span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">ADDED INSULATION</span>
                <span className="font-semibold text-sky-400 font-mono">
                  {rec.optimal_insulation_mm.toFixed(0)} mm PUF
                </span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">WINDOW APERTURE</span>
                <span className="font-semibold text-white font-mono">
                  {rec.optimal_window_area_m2.toFixed(2)} m²
                </span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">GLAZING SPEC</span>
                <span className="font-semibold text-sky-400">
                  {rec.optimal_glazing_name}
                </span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 text-[10px] block">ORIENTATION</span>
                <span className="font-semibold text-emerald-400 capitalize">
                  {rec.optimal_orientation} Facade
                </span>
              </div>
            </div>

            {/* Quantitative Explanation and Tradeoff Rationales */}
            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
              <span className="text-xs font-bold text-sky-400 font-mono uppercase tracking-wide block">
                Engineering Rationale & Physical Justification
              </span>
              <div className="text-xs text-slate-300 leading-relaxed space-y-1.5">
                {rec.explanation.split("\n").map((line, idx) => (
                  <p key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 shrink-0 mt-0.5">•</span>
                    <span>{line.replace(/✓/g, "").trim()}</span>
                  </p>
                ))}
              </div>
            </div>
          </div>

          {/* CANDIDATE DESIGNS RANKING TABLE */}
          {rec.ranked_designs && rec.ranked_designs.length > 0 && (
            <div className="eng-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-sky-400" />
                    <span>Top-Ranked Optimization Candidate Designs</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Multivariate candidate evaluation sorted by composite multi-objective score
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse font-sans">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px]">
                      <th className="py-2.5 px-3">Rank</th>
                      <th className="py-2.5 px-3">Wall Assembly</th>
                      <th className="py-2.5 px-3">Insulation</th>
                      <th className="py-2.5 px-3">Window</th>
                      <th className="py-2.5 px-3">Glazing Spec</th>
                      <th className="py-2.5 px-3">Orientation</th>
                      <th className="py-2.5 px-3">Comfort %</th>
                      <th className="py-2.5 px-3">Discomfort DH</th>
                      <th className="py-2.5 px-3">Heat Loss</th>
                      <th className="py-2.5 px-3">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {rec.ranked_designs.map((candidate, idx) => (
                      <tr
                        key={idx}
                        className={`hover:bg-slate-900/60 transition-all ${
                          idx === 0 ? "bg-sky-500/10 font-bold" : ""
                        }`}
                      >
                        <td className="py-2.5 px-3 font-bold text-sky-400">
                          {candidate.label}
                        </td>
                        <td className="py-2.5 px-3 text-slate-200 capitalize font-sans">
                          {candidate.wall_material_name}
                        </td>
                        <td className="py-2.5 px-3 text-white">
                          {candidate.insulation_mm.toFixed(0)} mm
                        </td>
                        <td className="py-2.5 px-3 text-white">
                          {candidate.window_area_m2.toFixed(1)} m²
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 font-sans">
                          {candidate.glazing_name}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 capitalize font-sans">
                          {candidate.orientation}
                        </td>
                        <td className="py-2.5 px-3 text-emerald-400 font-bold">
                          {candidate.comfort_percentage.toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3 text-amber-400">
                          {candidate.discomfort_dh.toFixed(1)}
                        </td>
                        <td className="py-2.5 px-3 text-rose-400">
                          {candidate.total_heat_loss_kwh.toFixed(0)} kWh
                        </td>
                        <td className="py-2.5 px-3 font-bold text-sky-400">
                          {candidate.overall_score.toFixed(1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
