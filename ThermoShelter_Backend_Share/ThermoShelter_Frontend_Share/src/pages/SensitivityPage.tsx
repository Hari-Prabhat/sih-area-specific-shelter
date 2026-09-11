import React, { useState, useEffect } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { api } from "../api/client";
import { SensitivityData } from "../types";
import { TrendingUp, Sliders, ShieldCheck, Flame, Lightbulb } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

export const SensitivityPage: React.FC = () => {
  const { selectedCity, design } = useDesignStore();
  const [paramChoice, setParamChoice] = useState<"insulation" | "window_area">("insulation");
  const [sensData, setSensData] = useState<SensitivityData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSensitivity = async () => {
    setLoading(true);
    try {
      const res = await api.runSensitivity({
        city: selectedCity,
        parameter: paramChoice,
        occupants: 4,
      });
      setSensData(res);
    } catch (e) {
      console.error("Failed to run sensitivity sweep", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSensitivity();
  }, [selectedCity, paramChoice]);

  // Build chart dataset
  const chartData = [];
  if (sensData) {
    for (let i = 0; i < sensData.values.length; i++) {
      chartData.push({
        value: sensData.values[i],
        comfort: parseFloat((sensData.comfort[i] || 0).toFixed(1)),
        loss: parseFloat((sensData.loss[i] || 0).toFixed(1)),
      });
    }
  }

  const currentValue =
    paramChoice === "insulation"
      ? design.insulationThicknessMm
      : design.windowArea;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Parametric Sensitivity Analysis Studio"
        subtitle="Evaluating the thermodynamic sensitivity and diminishing marginal returns of comfort percentage and heat loss across envelope design variables."
        badge={`${selectedCity.toUpperCase()} EPW`}
        action={
          <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setParamChoice("insulation")}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                paramChoice === "insulation"
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Insulation Thickness (mm)
            </button>
            <button
              onClick={() => setParamChoice("window_area")}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                paramChoice === "window_area"
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Window Aperture (m²)
            </button>
          </div>
        }
      />

      {/* Dual Axis Sensitivity Curve */}
      <div className="eng-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-sky-400" />
              <span>
                {sensData?.parameter} vs Comfort Percentage & Total Heat Loss
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Green line represents Thermal Comfort % (left axis); Rose dashed line represents Weekly Heat Loss in kWh (right axis)
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Current Design:</span>
            <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 font-bold">
              {currentValue} {sensData?.unit}
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 15, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="value"
                stroke="#94a3b8"
                tick={{ fontSize: 11 }}
                unit={` ${sensData?.unit || ""}`}
              />
              <YAxis
                yAxisId="left"
                stroke="#10b981"
                tick={{ fontSize: 11 }}
                unit="%"
                domain={[0, 100]}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#f43f5e"
                tick={{ fontSize: 11 }}
                unit=" kWh"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />

              {/* Vertical Reference Line indicating Current Design Value */}
              <ReferenceLine
                yAxisId="left"
                x={currentValue}
                stroke="#38bdf8"
                strokeWidth={2}
                strokeDasharray="3 3"
                label={{
                  value: "Current Design",
                  fill: "#38bdf8",
                  fontSize: 11,
                  position: "top",
                }}
              />

              <Line
                yAxisId="left"
                type="monotone"
                dataKey="comfort"
                name="Comfort % (18–24°C)"
                stroke="#10b981"
                strokeWidth={3}
                dot={{ r: 4, fill: "#10b981" }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="loss"
                name="Total Heat Loss (kWh)"
                stroke="#f43f5e"
                strokeWidth={2.5}
                strokeDasharray="4 4"
                dot={{ r: 4, fill: "#f43f5e" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Physics Engineering Interpretation */}
      <div className="eng-panel p-5 border-sky-500/30 space-y-2">
        <div className="flex items-center gap-2 text-sky-400">
          <Lightbulb className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-bold uppercase tracking-wide text-slate-200">
            Diminishing Marginal Returns in Building Physics
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          {paramChoice === "insulation"
            ? "In severe cold climates like Leh, increasing PUF insulation from 0mm to 60mm cuts thermal losses dramatically by over 60%. However, beyond 120mm, the marginal comfort gain per additional centimeter of insulation flattens significantly due to residual infiltration and ground conduction boundaries. 60–100mm represents the optimal cost-to-performance sweet spot."
            : "Increasing South-facing window aperture area initially increases natural daylighting and daytime solar thermal harvest. However, because glass has a significantly higher U-value (2.8 W/m²K) than insulated walls (0.38 W/m²K), excessively large glazing (> 4.5 m²) accelerates nocturnal conductive heat loss, creating an inflection point where net discomfort starts to rise."}
        </p>
      </div>
    </div>
  );
};
