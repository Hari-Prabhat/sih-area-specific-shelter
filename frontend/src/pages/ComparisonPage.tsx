import React, { useEffect } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { ShelterModel3D } from "../components/shelter/ShelterModel3D";
import { Scale, ArrowDown, ArrowUp, ShieldCheck, Flame, Sun, Layers } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceArea,
} from "recharts";

export const ComparisonPage: React.FC = () => {
  const {
    selectedCity,
    people,
    homeType,
    comparisonResult,
    runComparison,
    loading,
  } = useDesignStore();

  useEffect(() => {
    if (!comparisonResult) {
      runComparison();
    }
  }, [selectedCity, people, homeType]);

  const comp = comparisonResult;
  const sBase = comp?.baseline;
  const sOpt = comp?.optimized;
  const rInfo = comp?.recommendation;

  // Compute Delta improvements
  const comfortHoursDelta = sOpt && sBase ? sOpt.comfort_hours - sBase.comfort_hours : 0;
  const comfortPctDelta = sOpt && sBase ? sOpt.comfort_percentage - sBase.comfort_percentage : 0;
  const dhReduction =
    sOpt && sBase
      ? ((sBase.discomfort_degree_hours - sOpt.discomfort_degree_hours) /
          Math.max(0.01, sBase.discomfort_degree_hours)) *
        100
      : 0;
  const lossReduction =
    sOpt && sBase
      ? ((sBase.total_heat_loss_kwh - sOpt.total_heat_loss_kwh) /
          Math.max(0.01, sBase.total_heat_loss_kwh)) *
        100
      : 0;

  // Timeseries overlay data for Recharts
  const overlayData = [];
  if (sBase && sOpt) {
    const hours = Math.min(168, sOpt.indoor_temperature.length);
    for (let i = 0; i < hours; i++) {
      overlayData.push({
        hour: `H${i + 1}`,
        outdoor: parseFloat(sBase.outdoor_temperature[i]?.toFixed(1) || "0"),
        baseline: parseFloat(sBase.indoor_temperature[i]?.toFixed(1) || "0"),
        optimized: parseFloat(sOpt.indoor_temperature[i]?.toFixed(1) || "0"),
      });
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Baseline vs AI-Optimized Comparative Benchmark"
        subtitle="Evaluating thermal comfort gains and energy loss reductions between a standard uninsulated baseline and the climate-optimized design under strictly identical geometry and boundary conditions."
        badge={`${homeType.toUpperCase()} · ${selectedCity.toUpperCase()}`}
        action={
          <button
            onClick={() => runComparison()}
            disabled={loading.comparison}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-500/30 rounded-xl text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
          >
            <Scale className="w-3.5 h-3.5" />
            <span>{loading.comparison ? "COMPUTING..." : "RE-RUN BENCHMARK"}</span>
          </button>
        }
      />

      {/* Delta Performance Highlights */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="eng-panel p-4 border-emerald-500/40">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Comfort Hours Gain
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              +{comfortHoursDelta.toFixed(0)} h
            </span>
            <span className="text-xs text-slate-400">/ 168 h</span>
          </div>
          <span className="text-xs text-emerald-300 flex items-center gap-1 mt-1 font-mono">
            <ArrowUp className="w-3 h-3" />
            +{comfortPctDelta.toFixed(1)}% Comfort Band
          </span>
        </div>

        <div className="eng-panel p-4 border-emerald-500/40">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Discomfort Cut
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              -{dhReduction.toFixed(1)}%
            </span>
          </div>
          <span className="text-xs text-slate-400 block mt-1 font-mono">
            Reduced to {sOpt?.discomfort_degree_hours.toFixed(1) ?? 0} °C·h
          </span>
        </div>

        <div className="eng-panel p-4 border-emerald-500/40">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Envelope Heat Loss Cut
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              -{lossReduction.toFixed(1)}%
            </span>
          </div>
          <span className="text-xs text-slate-400 block mt-1 font-mono">
            Saved {(sBase && sOpt ? sBase.total_heat_loss_kwh - sOpt.total_heat_loss_kwh : 0).toFixed(1)} kWh/wk
          </span>
        </div>

        <div className="eng-panel p-4 border-sky-500/40">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            U-Value Improvement
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-sky-400">
              {sOpt?.u_values.wall_u.toFixed(2) ?? "0.38"}
            </span>
            <span className="text-xs text-slate-400">W/m²K</span>
          </div>
          <span className="text-xs text-slate-400 block mt-1 font-mono">
            vs {sBase?.u_values.wall_u.toFixed(2) ?? "1.92"} W/m²K Baseline
          </span>
        </div>
      </div>

      {/* Dual Side-by-Side Design Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PANEL A: CONVENTIONAL BASELINE DESIGN */}
        <div className="eng-panel p-6 border-slate-700/60 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-rose-400 uppercase font-bold block">
                CONVENTIONAL BENCHMARK
              </span>
              <h3 className="text-base font-bold text-white">
                Standard Uninsulated Design
              </h3>
            </div>
            <span className="px-2.5 py-1 bg-rose-950/70 text-rose-400 border border-rose-800 rounded font-mono text-xs font-bold">
              Baseline
            </span>
          </div>

          {/* Mini 3D Preview */}
          <div className="h-56 w-full rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
            {sBase && (
              <ShelterModel3D
                length={sBase.geometry.length_m || 4.5}
                width={sBase.geometry.width_m || 3.2}
                height={2.8}
                roofType="flat"
                wallMaterial="brick"
                windowArea={2.0}
                orientation="south"
                showLabels={false}
              />
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">WALL ASSEMBLY</span>
              <span className="font-semibold text-slate-200">
                {homeType === "Permanent" ? "230mm Brick Masonry" : "Single Timber Panel"}
              </span>
              <span className="text-rose-400 block text-[10px] font-mono">0 mm Insulation</span>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">ASSEMBLY U-VALUE</span>
              <span className="font-semibold text-rose-400 font-mono">
                {sBase?.u_values.wall_u.toFixed(3) ?? "1.920"} W/m²K
              </span>
              <span className="text-slate-500 block text-[10px] font-mono">High Heat Leak</span>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">COMFORT HOURS</span>
              <span className="font-semibold text-white font-mono">
                {sBase?.comfort_hours.toFixed(0) ?? 0} / 168 h ({sBase?.comfort_percentage.toFixed(1) ?? 0}%)
              </span>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">WEEKLY LOSS</span>
              <span className="font-semibold text-rose-400 font-mono">
                {sBase?.total_heat_loss_kwh.toFixed(1) ?? 0} kWh
              </span>
            </div>
          </div>
        </div>

        {/* PANEL B: AI-OPTIMIZED DESIGN */}
        <div className="eng-panel p-6 border-sky-500/40 bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/20 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block">
                BAYESIAN OPTIMIZED
              </span>
              <h3 className="text-base font-bold text-white">
                Climate-Adapted Envelope
              </h3>
            </div>
            <span className="px-2.5 py-1 bg-emerald-950/70 text-emerald-400 border border-emerald-800 rounded font-mono text-xs font-bold">
              AI Optimized
            </span>
          </div>

          {/* Mini 3D Preview */}
          <div className="h-56 w-full rounded-xl overflow-hidden bg-slate-950 border border-sky-500/20">
            {rInfo && (
              <ShelterModel3D
                length={rInfo.geometry.length_m}
                width={rInfo.geometry.width_m}
                height={rInfo.geometry.height_m}
                roofType={rInfo.materials.roof_type}
                wallMaterial={rInfo.optimal_wall_material}
                windowArea={rInfo.optimal_window_area_m2}
                orientation={rInfo.optimal_orientation}
                showLabels={false}
              />
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">WALL ASSEMBLY</span>
              <span className="font-semibold text-slate-200 capitalize">
                {rInfo?.optimal_wall_material ?? "Brick"} + PUF
              </span>
              <span className="text-emerald-400 block text-[10px] font-mono">
                {rInfo?.optimal_insulation_mm.toFixed(0) ?? 60} mm PUF Core
              </span>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">ASSEMBLY U-VALUE</span>
              <span className="font-semibold text-emerald-400 font-mono">
                {sOpt?.u_values.wall_u.toFixed(3) ?? "0.380"} W/m²K
              </span>
              <span className="text-emerald-400 block text-[10px] font-mono">Insulated Envelope</span>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">COMFORT HOURS</span>
              <span className="font-semibold text-emerald-400 font-mono">
                {sOpt?.comfort_hours.toFixed(0) ?? 0} / 168 h ({sOpt?.comfort_percentage.toFixed(1) ?? 0}%)
              </span>
            </div>
            <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 text-[10px] block">WEEKLY LOSS</span>
              <span className="font-semibold text-emerald-400 font-mono">
                {sOpt?.total_heat_loss_kwh.toFixed(1) ?? 0} kWh
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 168-Hour Overlaid Thermal Response Curve */}
      <div className="eng-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              168-Hour Thermal Response Overlay (Baseline vs Optimized)
            </h3>
            <p className="text-xs text-slate-400">
              Direct hourly comparison of internal temperatures against the 18–24°C comfort envelope
            </p>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={overlayData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} unit="°C" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
              <ReferenceArea y1={18} y2={24} fill="#22c55e" fillOpacity={0.12} stroke="#22c55e" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="outdoor"
                name="Outdoor Ambient (°C)"
                stroke="#64748b"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="baseline"
                name="Baseline Indoor (°C)"
                stroke="#f43f5e"
                strokeWidth={2.2}
                strokeDasharray="3 3"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="optimized"
                name="AI-Optimized Indoor (°C)"
                stroke="#38bdf8"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
