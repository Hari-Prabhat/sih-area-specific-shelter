import React from "react";
import { useDesignStore } from "../store/designStore";
import { MetricCard } from "../components/common/MetricCard";
import { ShelterModel3D } from "../components/shelter/ShelterModel3D";
import {
  Thermometer,
  Sun,
  ShieldCheck,
  Flame,
  ArrowRight,
  Sparkles,
  Play,
  Compass,
  Cpu,
} from "lucide-react";

export const OverviewPage: React.FC = () => {
  const {
    selectedCity,
    climateData,
    design,
    simulationResult,
    optimizationResult,
    setActiveTab,
    runSimulation,
    runOptimization,
    loading,
  } = useDesignStore();

  const sim = simulationResult;
  const avgIndoor = sim?.comfort_metrics?.avg ?? 0;
  const comfortPct = sim?.comfort_percentage ?? 0;
  const heatLoss = sim?.total_heat_loss_kwh ?? 0;
  const solarGain = sim?.integrated_solar_energy_kwh ?? 0;
  const discomfort = sim?.discomfort_degree_hours ?? 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Hero Mission Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-sky-950/40 border border-sky-500/20 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/80 border border-sky-800 text-sky-400 text-xs font-mono font-semibold">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
              {climateData?.climate_description || "Area-Specific Passive Engineering Platform"}
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">
              ThermoShelter AI ·{" "}
              <span className="text-sky-400 uppercase">
                {selectedCity ? `${selectedCity} Station` : "Engineering Workstation"}
              </span>
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
              Physics-driven 168-hour transient forward Euler envelope simulation and
              Bayesian optimization for high-altitude cold and multi-climatic regions.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Primary Action Button: Run Simulation after selecting location, then Design Shelter */}
            <button
              onClick={() => {
                if (!simulationResult) {
                  runSimulation();
                } else {
                  setActiveTab("designer");
                }
              }}
              disabled={loading.simulation || !selectedCity}
              className={`px-5 py-2.5 font-bold rounded-xl text-sm transition-all shadow-lg flex items-center gap-2 cursor-pointer disabled:opacity-50 ${
                selectedCity && !simulationResult
                  ? "bg-sky-500 hover:bg-sky-400 text-slate-950 shadow-sky-500/25 animate-pulse"
                  : "bg-sky-500 hover:bg-sky-400 text-slate-950 shadow-sky-500/25"
              }`}
            >
              {loading.simulation ? (
                <span>Simulating...</span>
              ) : !simulationResult ? (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Simulation</span>
                </>
              ) : (
                <>
                  <span>Design Shelter</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            <button
              onClick={() => runOptimization()}
              disabled={loading.optimization || !selectedCity}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-500/30 font-semibold rounded-xl text-sm transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading.optimization ? "Running AI..." : "Run AI Optimizer"}</span>
            </button>
          </div>
        </div>

        {/* Visual Engineering Workflow Bar */}
        <div className="mt-8 pt-6 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-6 gap-2 text-center text-xs">
          {[
            { step: "1. CLIMATE", sub: selectedCity ? selectedCity.toUpperCase() : "CHOOSE LOCATION", tab: "climate" },
            { step: "2. DESIGN", sub: `${design.length}m × ${design.width}m`, tab: "designer" },
            { step: "3. SIMULATE", sub: sim ? `${sim.comfort_percentage.toFixed(0)}% COMFORT` : "168-HR EULER", tab: "simulation" },
            { step: "4. OPTIMIZE", sub: "OPTUNA BAYESIAN TPE", tab: "optimization" },
            { step: "5. COMPARE", sub: "BASELINE VS AI", tab: "compare" },
            { step: "6. REPORT", sub: "ISO 6946 / EXPORT", tab: "report" },
          ].map((item) => (
            <button
              key={item.step}
              onClick={() => setActiveTab(item.tab)}
              className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-sky-500/40 transition-all text-left group cursor-pointer"
            >
              <div className="text-[10px] font-mono text-slate-500 group-hover:text-sky-400">
                {item.step}
              </div>
              <div className="font-semibold text-slate-300 group-hover:text-white truncate text-[11px] mt-0.5">
                {item.sub}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Hero Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Comfort Zone (18–24°C)"
          value={sim ? `${comfortPct.toFixed(1)}` : "--"}
          unit="%"
          delta={
            sim
              ? `${sim.comfort_hours.toFixed(0)}h / 168h`
              : selectedCity
              ? "Click [Run Simulation]"
              : "Choose location in top bar"
          }
          deltaType={comfortPct >= 60 ? "positive" : "neutral"}
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
          accentColor={comfortPct >= 60 ? "green" : "cyan"}
          subtext="Target: > 75%"
        />

        <MetricCard
          label="Mean Indoor Temp"
          value={sim ? avgIndoor.toFixed(1) : "--"}
          unit="°C"
          delta={
            sim?.comfort_metrics
              ? `Range: ${sim.comfort_metrics.min_t.toFixed(1)}°C to ${sim.comfort_metrics.max_t.toFixed(1)}°C`
              : selectedCity
              ? "Awaiting simulation run"
              : "168h transient mean"
          }
          icon={<Thermometer className="w-4 h-4 text-sky-400" />}
          accentColor="cyan"
        />

        <MetricCard
          label="Weekly Heat Loss"
          value={sim ? heatLoss.toFixed(1) : "--"}
          unit="kWh"
          delta={
            sim
              ? `U-wall: ${sim.u_values.wall_u.toFixed(2)} W/m²K`
              : selectedCity
              ? "Run simulation to calculate"
              : "Envelope conduction"
          }
          icon={<Flame className="w-4 h-4 text-rose-400" />}
          accentColor="red"
          subtext="Envelope conduction"
        />

        <MetricCard
          label="Solar Harvest"
          value={sim ? solarGain.toFixed(1) : "--"}
          unit="kWh"
          delta={`${design.windowArea} m² South aperture`}
          deltaType="positive"
          icon={<Sun className="w-4 h-4 text-amber-400" />}
          accentColor="orange"
          subtext="Passive direct gain"
        />
      </div>

      {/* Dual Split Hero: Interactive 3D Shelter Model & Real-Time Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 3D Shelter Visualizer Preview (7 cols) */}
        <div className="lg:col-span-7 flex flex-col eng-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Compass className="w-4 h-4 text-sky-400" />
                <span>Interactive 3D Shelter Model</span>
              </h2>
              <p className="text-xs text-slate-400">
                Real geometry derived from current shelter design ({design.roofType} roof, {design.wallMaterial} wall)
              </p>
            </div>
            <button
              onClick={() => setActiveTab("twin3d")}
              className="text-xs text-sky-400 hover:text-sky-300 font-mono flex items-center gap-1 cursor-pointer"
            >
              <span>Full View</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 min-h-[380px] w-full rounded-xl overflow-hidden relative">
            <ShelterModel3D
              length={design.length}
              width={design.width}
              height={design.height}
              roofType={design.roofType}
              wallMaterial={design.wallMaterial}
              windowArea={design.windowArea}
              orientation={design.orientation}
            />

            {/* Awaiting Simulation Notice Overlay */}
            {selectedCity && !sim && (
              <div className="absolute bottom-4 left-4 right-4 bg-slate-900/90 backdrop-blur border border-sky-500/40 rounded-xl p-3 flex items-center justify-between shadow-xl">
                <div className="text-xs">
                  <span className="font-bold text-sky-400 uppercase font-mono block">
                    Location: {selectedCity}
                  </span>
                  <span className="text-slate-300 text-[11px]">
                    Click [Run Simulation] above to calculate indoor temperature, comfort %, and 3D thermal telemetry.
                  </span>
                </div>
                <button
                  onClick={() => runSimulation()}
                  disabled={loading.simulation}
                  className="px-3.5 py-1.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1.5 transition-all shadow cursor-pointer shrink-0 ml-3"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Simulation</span>
                </button>
              </div>
            )}

            {!selectedCity && (
              <div className="absolute bottom-4 left-4 right-4 bg-slate-900/90 backdrop-blur border border-amber-500/40 rounded-xl p-3 text-center shadow-xl">
                <span className="text-xs text-amber-300 font-medium">
                  📍 Please choose a deployment location in the top bar to initialize climate data.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Analytical Telemetry & Optimization Status (5 cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
          {/* Active Configuration Spec Card */}
          <div className="eng-panel p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                Active Shelter Specifications
              </span>
              <span className="text-[11px] font-mono text-sky-400">
                {(design.length * design.width).toFixed(1)} m² Floor
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">ENVELOPE WALL</span>
                <span className="font-semibold text-slate-200 capitalize">
                  {design.wallMaterial.replace(/_/g, " ")}
                </span>
                <span className="text-[10px] text-sky-400 block font-mono">
                  {design.insulationThicknessMm}mm PUF
                </span>
              </div>

              <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">ROOF PROFILE</span>
                <span className="font-semibold text-slate-200 capitalize">
                  {design.roofType} Profile
                </span>
                <span className="text-[10px] text-slate-400 block font-mono">
                  Insulated Sheet
                </span>
              </div>

              <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">FENESTRATION</span>
                <span className="font-semibold text-slate-200">
                  {design.windowArea} m² ({design.orientation})
                </span>
                <span className="text-[10px] text-sky-400 block font-mono capitalize">
                  {design.glazing.replace(/_/g, " ")}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">DISCOMFORT SCORE</span>
                <span className="font-semibold text-amber-400 font-mono">
                  {sim ? `${discomfort.toFixed(1)} °C·h` : "--"}
                </span>
                <span className="text-[10px] text-slate-400 block font-mono">
                  {sim ? "Cumulative DH" : "Awaiting simulation"}
                </span>
              </div>
            </div>
          </div>

          {/* Bayesian Optimization Recommendation Preview */}
          <div className="eng-panel p-5 space-y-3 flex-1 flex flex-col justify-between border-sky-500/30">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-sky-400 uppercase tracking-wide flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5" />
                  <span>AI Optimization Status</span>
                </span>
                {optimizationResult && (
                  <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">
                    Candidate #1 Active
                  </span>
                )}
              </div>

              {optimizationResult ? (
                <div className="space-y-2 text-xs">
                  <p className="text-slate-300 leading-relaxed line-clamp-3">
                    {optimizationResult.explanation.replace(/✓/g, "•")}
                  </p>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between font-mono text-[11px]">
                    <span className="text-slate-400">Optimal Wall:</span>
                    <span className="text-white capitalize">
                      {optimizationResult.optimal_wall_material} +{" "}
                      {optimizationResult.optimal_insulation_mm.toFixed(0)}mm
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400 leading-relaxed">
                  {selectedCity
                    ? `Run Bayesian Optimization to evaluate design parameter sweeps over insulation, fenestration, and orientation for ${selectedCity.toUpperCase()}.`
                    : "Choose a deployment location to evaluate design parameter sweeps."}
                </p>
              )}
            </div>

            <div className="pt-2">
              <button
                onClick={() => setActiveTab("optimization")}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded-lg text-xs font-semibold tracking-wide border border-slate-700 flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <span>View Full Optimization Studio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
