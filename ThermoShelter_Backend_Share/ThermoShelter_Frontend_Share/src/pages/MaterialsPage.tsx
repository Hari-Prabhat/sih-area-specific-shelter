import React, { useState, useEffect } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { api } from "../api/client";
import { MaterialComparisonItem } from "../types";
import { Layers, Check, Activity, Sparkles, Thermometer } from "lucide-react";
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

export const MaterialsPage: React.FC = () => {
  const { selectedCity, design, updateDesign, runSimulation } = useDesignStore();
  const [materialData, setMaterialData] = useState<MaterialComparisonItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [insulationMm, setInsulationMm] = useState(60);
  const [windowArea, setWindowArea] = useState(2.5);

  const fetchMaterialsBenchmark = async () => {
    setLoading(true);
    try {
      const res = await api.runMaterialComparison({
        city: selectedCity,
        insulation_mm: insulationMm,
        window_area: windowArea,
        occupants: 4,
      });
      setMaterialData(res.materials);
    } catch (e) {
      console.error("Failed to load material comparison", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterialsBenchmark();
  }, [selectedCity, insulationMm, windowArea]);

  // Build multi-material timeseries data for Recharts
  const chartData = [];
  if (materialData.length > 0) {
    const hours = Math.min(168, materialData[0].indoor_temps?.length || 0);
    for (let i = 0; i < hours; i++) {
      const pt: any = { hour: `H${i + 1}`, outdoor: materialData[0].outdoor_temps[i] };
      materialData.forEach((m) => {
        pt[m.name] = parseFloat((m.indoor_temps[i] || 0).toFixed(1));
      });
      chartData.push(pt);
    }
  }

  const seriesColors = [
    "#38bdf8",
    "#f43f5e",
    "#10b981",
    "#fbbf24",
    "#a78bfa",
    "#f472b6",
    "#22d3ee",
    "#a3e635",
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Multi-Material Envelope Benchmarking Studio"
        subtitle="Evaluating candidate structural and thermal mass materials under strictly identical geometry and environmental boundary conditions."
        badge={`${selectedCity.toUpperCase()} BOUNDARY CONDITIONS`}
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchMaterialsBenchmark()}
              disabled={loading}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-500/30 rounded-xl text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
            >
              {loading ? "COMPUTING..." : "RE-RUN BENCHMARK"}
            </button>
          </div>
        }
      />

      {/* Parametric Controls Strip */}
      <div className="eng-panel p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        <div className="space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Added Insulation Cap:</span>
            <span className="text-sky-400 font-bold">{insulationMm} mm PUF</span>
          </div>
          <input
            type="range"
            min="0"
            max="150"
            step="10"
            value={insulationMm}
            onChange={(e) => setInsulationMm(parseInt(e.target.value))}
            className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-slate-400">
            <span>Window Aperture Area:</span>
            <span className="text-sky-400 font-bold">{windowArea} m² South</span>
          </div>
          <input
            type="range"
            min="1.0"
            max="5.0"
            step="0.5"
            value={windowArea}
            onChange={(e) => setWindowArea(parseFloat(e.target.value))}
            className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>
      </div>

      {/* Multi-Material Thermal Curves Chart */}
      <div className="eng-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-sky-400" />
              <span>168-Hour Indoor Temperature Response Across Envelope Materials</span>
            </h3>
            <p className="text-xs text-slate-400">
              Identical dimensions (4.5m × 3.2m × 2.8m), same solar exposure and occupancy
            </p>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
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
                name="Outdoor (°C)"
                stroke="#64748b"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
              {materialData.map((m, idx) => (
                <Line
                  key={m.name}
                  type="monotone"
                  dataKey={m.name}
                  stroke={seriesColors[idx % seriesColors.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Visual Material Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {materialData.map((mat) => {
          const isSelected = design.wallMaterial === mat.key;
          return (
            <div
              key={mat.key}
              className={`eng-panel p-5 space-y-3 transition-all relative ${
                isSelected ? "border-sky-400 bg-sky-950/20 shadow-lg shadow-sky-950/40" : "hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase tracking-tight truncate">
                  {mat.name}
                </span>
                {isSelected && (
                  <span className="p-1 bg-sky-500 rounded-full text-slate-950">
                    <Check className="w-3 h-3" />
                  </span>
                )}
              </div>

              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between text-slate-400">
                  <span>Conductivity (k):</span>
                  <span className="text-white">{mat.conductivity} W/mK</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Assembly U-val:</span>
                  <span className="text-sky-400 font-bold">{mat.wall_u.toFixed(3)} W/m²K</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Comfort Hours:</span>
                  <span className="text-emerald-400 font-bold">{mat.comfort_hrs.toFixed(0)} h ({mat.comfort_pct.toFixed(0)}%)</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Weekly Heat Loss:</span>
                  <span className="text-rose-400">{mat.total_loss_kwh.toFixed(1)} kWh</span>
                </div>
              </div>

              <button
                onClick={() => {
                  updateDesign({ wallMaterial: mat.key });
                  runSimulation();
                }}
                className={`w-full py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  isSelected
                    ? "bg-sky-500 text-slate-950 cursor-default"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                }`}
              >
                {isSelected ? "ACTIVE WALL MATERIAL" : "SELECT MATERIAL"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
