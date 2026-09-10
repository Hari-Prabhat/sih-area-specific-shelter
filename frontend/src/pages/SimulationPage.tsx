import React, { useState } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { MetricCard } from "../components/common/MetricCard";
import {
  Thermometer,
  ShieldCheck,
  Flame,
  Sun,
  Activity,
  BarChart3,
  Layers,
  Sparkles,
  Play,
  Lightbulb,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceArea,
  AreaChart,
  Area,
} from "recharts";

export const SimulationPage: React.FC = () => {
  const { simulationResult, selectedCity, design, runSimulation, loading } =
    useDesignStore();
  const [activeChartTab, setActiveChartTab] = useState<
    "temp" | "solar" | "heatflow" | "balance"
  >("temp");

  const sim = simulationResult;

  if (!sim) {
    return (
      <div className="flex flex-col items-center justify-center p-16 eng-panel text-center max-w-xl mx-auto space-y-4">
        <Activity className="w-12 h-12 text-sky-400 animate-bounce" />
        <h2 className="text-lg font-bold text-white">No Simulation Results Cached</h2>
        <p className="text-xs text-slate-400">
          Run the 168-hour transient forward Euler simulation to calculate hourly indoor temperatures,
          solar harvesting, and component heat losses for {selectedCity.toUpperCase()}.
        </p>
        <button
          onClick={() => runSimulation()}
          className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-xl text-xs cursor-pointer"
        >
          Run 168-Hour Simulation
        </button>
      </div>
    );
  }

  const indoorTemps = sim.indoor_temperature || [];
  const outdoorTemps = sim.outdoor_temperature || [];
  const solarGain = sim.solar_thermal_gain || [];
  const solarPower = sim.solar_power || [];
  const wallLoss = sim.wall_heat_flow || [];
  const roofLoss = sim.roof_heat_flow || [];
  const floorLoss = sim.floor_heat_flow || [];
  const windowLoss = sim.window_heat_flow || [];
  const ventLoss = sim.ventilation_heat_flow || [];

  // Build hourly dataset for Recharts
  const timeseriesData = [];
  const hoursCount = Math.min(168, indoorTemps.length);
  for (let i = 0; i < hoursCount; i++) {
    timeseriesData.push({
      hour: `H${i + 1}`,
      indoor: parseFloat((indoorTemps[i] ?? 0).toFixed(2)),
      outdoor: parseFloat((outdoorTemps[i] ?? 0).toFixed(2)),
      solarGain: parseFloat((solarGain[i] ?? 0).toFixed(1)),
      solarPower: parseFloat((solarPower[i] ?? 0).toFixed(1)),
      wall: parseFloat((wallLoss[i] ?? 0).toFixed(1)),
      roof: parseFloat((roofLoss[i] ?? 0).toFixed(1)),
      floor: parseFloat((floorLoss[i] ?? 0).toFixed(1)),
      window: parseFloat((windowLoss[i] ?? 0).toFixed(1)),
      vent: parseFloat((ventLoss[i] ?? 0).toFixed(1)),
    });
  }

  // Energy Balance Bar Chart dataset
  const cl = sim.component_heat_loss_kwh || {
    wall_loss_kwh: 0,
    roof_loss_kwh: 0,
    floor_loss_kwh: 0,
    window_loss_kwh: 0,
    ventilation_loss_kwh: 0,
    radiation_loss_kwh: 0,
    total_heat_loss_kwh: 0,
  };

  const balanceData = [
    { name: "Solar Harvest", kwh: parseFloat((sim.integrated_solar_energy_kwh || 0).toFixed(1)), fill: "#f59e0b" },
    { name: "Wall Conduction", kwh: parseFloat(cl.wall_loss_kwh.toFixed(1)), fill: "#38bdf8" },
    { name: "Roof Conduction", kwh: parseFloat(cl.roof_loss_kwh.toFixed(1)), fill: "#818cf8" },
    { name: "Floor Ground", kwh: parseFloat(cl.floor_loss_kwh.toFixed(1)), fill: "#94a3b8" },
    { name: "Glazing Loss", kwh: parseFloat(cl.window_loss_kwh.toFixed(1)), fill: "#f43f5e" },
    { name: "Ventilation Air", kwh: parseFloat((cl.vent_loss_kwh || cl.ventilation_loss_kwh || 0).toFixed(1)), fill: "#a855f7" },
  ];

  // Dynamic Engineering Interpretation from actual numbers
  const generateEngineeringInterpretation = () => {
    const comfortHours = sim.comfort_hours;
    const discomfortHours = 168 - comfortHours;
    const losses = [
      { name: "the roof", val: cl.roof_loss_kwh },
      { name: "the exterior walls", val: cl.wall_loss_kwh },
      { name: "fenestration glazing", val: cl.window_loss_kwh },
      { name: "air infiltration/ventilation", val: cl.vent_loss_kwh || cl.ventilation_loss_kwh || 0 },
      { name: "the floor foundation", val: cl.floor_loss_kwh },
    ];
    losses.sort((a, b) => b.val - a.val);
    const largestLoss = losses[0];
    const secondLoss = losses[1];

    let comfortAssessment = "";
    if (comfortHours >= 140) {
      comfortAssessment = `Optimal passive comfort is achieved for ${comfortHours} of 168 hours (${sim.comfort_percentage.toFixed(1)}%).`;
    } else {
      comfortAssessment = `Your shelter remains outside the 18–24°C comfort target for ${discomfortHours.toFixed(0)} hours, accumulating ${sim.discomfort_degree_hours.toFixed(1)} °C·h of discomfort.`;
    }

    return `${comfortAssessment} The largest thermal loss is through ${largestLoss.name} (${largestLoss.val.toFixed(1)} kWh, ${((largestLoss.val / Math.max(0.1, sim.total_heat_loss_kwh)) * 100).toFixed(0)}% of total envelope loss), followed by ${secondLoss.name} (${secondLoss.val.toFixed(1)} kWh). South solar harvesting admitted ${sim.integrated_solar_energy_kwh.toFixed(1)} kWh of natural solar heat to offset these losses.`;
  };

  const interpretation = generateEngineeringInterpretation();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Transient Building Energy & Thermal Simulation Dashboard"
        subtitle="Forward Euler numerical integration (Δt=60s) over 168 continuous hours applying ISO 6946 multi-layer envelope physics."
        badge={`${sim.comfort_status.toUpperCase()} · ${selectedCity.toUpperCase()}`}
        action={
          <button
            onClick={() => runSimulation()}
            disabled={loading.simulation}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-500/30 rounded-xl text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${loading.simulation ? "animate-spin" : ""}`} />
            <span>{loading.simulation ? "SIMULATING..." : "RE-RUN 168-HR"}</span>
          </button>
        }
      />

      {/* Hero Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Indoor Temperature"
          value={sim.comfort_metrics.avg.toFixed(1)}
          unit="°C"
          delta={`Min ${sim.comfort_metrics.min_t.toFixed(1)}°C | Max ${sim.comfort_metrics.max_t.toFixed(1)}°C`}
          icon={<Thermometer className="w-4 h-4 text-sky-400" />}
          accentColor="cyan"
          subtext="168-Hour Mean"
        />

        <MetricCard
          label="Comfort Target Hours"
          value={`${sim.comfort_hours.toFixed(0)}`}
          unit="/ 168 h"
          delta={`${sim.comfort_percentage.toFixed(1)}% of week in 18–24°C`}
          deltaType={sim.comfort_percentage >= 70 ? "positive" : "negative"}
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
          accentColor={sim.comfort_percentage >= 70 ? "green" : "red"}
        />

        <MetricCard
          label="Total Envelope Loss"
          value={sim.total_heat_loss_kwh.toFixed(1)}
          unit="kWh"
          delta={`U-wall: ${sim.u_values.wall_u.toFixed(2)} W/m²K`}
          icon={<Flame className="w-4 h-4 text-rose-400" />}
          accentColor="red"
          subtext="168h Cumulative Loss"
        />

        <MetricCard
          label="Solar Heat Admitted"
          value={sim.integrated_solar_energy_kwh.toFixed(1)}
          unit="kWh"
          delta={`${((sim.integrated_solar_energy_kwh / Math.max(0.1, sim.integrated_incident_solar_kwh)) * 100).toFixed(1)}% Harvesting Eff`}
          deltaType="positive"
          icon={<Sun className="w-4 h-4 text-amber-400" />}
          accentColor="orange"
          subtext="Useful Direct Thermal Gain"
        />
      </div>

      {/* Interactive Visualization Tabs */}
      <div className="eng-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" />
              <span>168-Hour Transient Thermodynamic Visualizations</span>
            </h2>
            <p className="text-xs text-slate-400">
              Interactive time-series curves with ASHRAE 55 thermal comfort envelope
            </p>
          </div>

          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveChartTab("temp")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                activeChartTab === "temp"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Temperature
            </button>
            <button
              onClick={() => setActiveChartTab("solar")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                activeChartTab === "solar"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Solar Dynamics
            </button>
            <button
              onClick={() => setActiveChartTab("heatflow")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                activeChartTab === "heatflow"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Component Heat Flows
            </button>
            <button
              onClick={() => setActiveChartTab("balance")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                activeChartTab === "balance"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Energy Balance
            </button>
          </div>
        </div>

        {/* 1. INDOOR VS OUTDOOR TEMPERATURE CHART */}
        {activeChartTab === "temp" && (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeseriesData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
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
                {/* 18-24°C Comfort Zone Band */}
                <ReferenceArea y1={18} y2={24} fill="#22c55e" fillOpacity={0.12} stroke="#22c55e" strokeDasharray="3 3" />
                <Line
                  type="monotone"
                  dataKey="outdoor"
                  name="Outdoor Ambient (°C)"
                  stroke="#94a3b8"
                  strokeWidth={1.8}
                  strokeDasharray="4 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="indoor"
                  name="Indoor Predicted (°C)"
                  stroke="#38bdf8"
                  strokeWidth={3}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 2. SOLAR DYNAMICS CHART */}
        {activeChartTab === "solar" && (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseriesData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} unit="W" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                <Area
                  type="monotone"
                  dataKey="solarPower"
                  name="Incident Aperture Power (W)"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="solarGain"
                  name="Admitted Thermal Gain (W)"
                  stroke="#f43f5e"
                  fill="#f43f5e"
                  fillOpacity={0.3}
                  strokeWidth={2.5}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 3. COMPONENT HEAT FLOWS */}
        {activeChartTab === "heatflow" && (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeseriesData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} unit="W" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                <Line type="monotone" dataKey="wall" name="Wall Conduction (W)" stroke="#38bdf8" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="roof" name="Roof Conduction (W)" stroke="#818cf8" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="window" name="Glazing (W)" stroke="#f43f5e" strokeWidth={1.8} dot={false} />
                <Line type="monotone" dataKey="vent" name="Ventilation (W)" stroke="#a855f7" strokeWidth={1.8} strokeDasharray="3 3" dot={false} />
                <Line type="monotone" dataKey="floor" name="Floor Ground (W)" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="2 2" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 4. ENERGY BALANCE BAR CHART */}
        {activeChartTab === "balance" && (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={balanceData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} unit=" kWh" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="kwh" name="Cumulative Energy (kWh / 168h)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* CONCISE ENGINEERING INTERPRETATION BOX */}
      <div className="eng-panel p-5 border-sky-500/30 bg-slate-900/90 space-y-2">
        <div className="flex items-center gap-2 text-sky-400">
          <Lightbulb className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Physics Engineering Interpretation
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          {interpretation}
        </p>
      </div>
    </div>
  );
};
