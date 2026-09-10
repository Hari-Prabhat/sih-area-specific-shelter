import React, { useState } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { ShelterModel3D } from "../components/shelter/ShelterModel3D";
import {
  Play,
  Sparkles,
  Layers,
  Maximize2,
  Compass,
  Sun,
  ShieldAlert,
  ChevronDown,
} from "lucide-react";

export const DesignStudioPage: React.FC = () => {
  const {
    design,
    updateDesign,
    selectedCity,
    people,
    homeType,
    runSimulation,
    runOptimization,
    simulationResult,
    loading,
  } = useDesignStore();

  const [activeControlTab, setActiveControlTab] = useState<
    "geometry" | "envelope" | "glazing" | "passive"
  >("geometry");

  const sim = simulationResult;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Shelter Engineering Design Studio"
        subtitle="Parametric split-screen architectural modeling workstation with real-time 3D geometry and ISO 6946 thermal physics coupling."
        badge={`${homeType.toUpperCase()} SHELTER · ${selectedCity.toUpperCase()}`}
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={() => runSimulation()}
              disabled={loading.simulation}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-sky-400 border border-sky-500/40 rounded-xl text-xs font-bold tracking-wide transition-all shadow-md cursor-pointer disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${loading.simulation ? "animate-spin" : ""}`} />
              <span>{loading.simulation ? "SIMULATING..." : "SIMULATE ENVELOPE"}</span>
            </button>

            <button
              onClick={() => runOptimization()}
              disabled={loading.optimization}
              className="flex items-center gap-2 px-5 py-2 bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-slate-950 font-extrabold rounded-xl text-xs tracking-wide transition-all shadow-lg hover:shadow-sky-500/25 cursor-pointer disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${loading.optimization ? "animate-spin" : ""}`} />
              <span>{loading.optimization ? "SEARCHING..." : "OPTIMIZE ENVELOPE"}</span>
            </button>
          </div>
        }
      />

      {/* Split-Screen Studio: Left Controls (5 cols), Right 3D Digital Twin (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Parametric Engineering Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Sub-tab Switcher */}
          <div className="flex rounded-xl bg-slate-900 p-1 border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setActiveControlTab("geometry")}
              className={`flex-1 py-1.5 rounded-lg transition-all ${
                activeControlTab === "geometry"
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Geometry
            </button>
            <button
              onClick={() => setActiveControlTab("envelope")}
              className={`flex-1 py-1.5 rounded-lg transition-all ${
                activeControlTab === "envelope"
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Materials
            </button>
            <button
              onClick={() => setActiveControlTab("glazing")}
              className={`flex-1 py-1.5 rounded-lg transition-all ${
                activeControlTab === "glazing"
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Glazing
            </button>
            <button
              onClick={() => setActiveControlTab("passive")}
              className={`flex-1 py-1.5 rounded-lg transition-all ${
                activeControlTab === "passive"
                  ? "bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Passive
            </button>
          </div>

          {/* TAB 1: GEOMETRY CONTROLS */}
          {activeControlTab === "geometry" && (
            <div className="eng-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                  Dimensional Parameters
                </span>
                <span className="text-xs font-mono text-sky-400">
                  Floor: {(design.length * design.width).toFixed(1)} m²
                </span>
              </div>

              {/* Length Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Length (L):</span>
                  <span className="text-white font-bold">{design.length.toFixed(1)} m</span>
                </div>
                <input
                  type="range"
                  min="2.5"
                  max="10.0"
                  step="0.1"
                  value={design.length}
                  onChange={(e) => updateDesign({ length: parseFloat(e.target.value) })}
                  className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Width Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Width (W):</span>
                  <span className="text-white font-bold">{design.width.toFixed(1)} m</span>
                </div>
                <input
                  type="range"
                  min="2.0"
                  max="8.0"
                  step="0.1"
                  value={design.width}
                  onChange={(e) => updateDesign({ width: parseFloat(e.target.value) })}
                  className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Height Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Ceiling Height (H):</span>
                  <span className="text-white font-bold">{design.height.toFixed(1)} m</span>
                </div>
                <input
                  type="range"
                  min="2.0"
                  max="4.0"
                  step="0.1"
                  value={design.height}
                  onChange={(e) => updateDesign({ height: parseFloat(e.target.value) })}
                  className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Roof Form Selector */}
              <div className="space-y-1.5 pt-2 border-t border-slate-800">
                <span className="text-xs font-mono text-slate-400">Roof Profile:</span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => updateDesign({ roofType: "flat" })}
                    className={`py-2 rounded-lg text-xs font-medium border transition-all ${
                      design.roofType === "flat"
                        ? "bg-sky-500/20 text-sky-400 border-sky-500/40 font-bold"
                        : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                    }`}
                  >
                    Flat Roof (Modular)
                  </button>
                  <button
                    onClick={() => updateDesign({ roofType: "pitched" })}
                    className={`py-2 rounded-lg text-xs font-medium border transition-all ${
                      design.roofType === "pitched"
                        ? "bg-sky-500/20 text-sky-400 border-sky-500/40 font-bold"
                        : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                    }`}
                  >
                    Pitched 30° (Alpine Snow)
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ENVELOPE & MATERIALS */}
          {activeControlTab === "envelope" && (
            <div className="eng-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                  Assembly Material & Core Insulation
                </span>
                <span className="text-xs font-mono text-sky-400">
                  U-wall: {sim?.u_values?.wall_u?.toFixed(3) ?? "0.450"} W/m²K
                </span>
              </div>

              {/* Structural Wall Substrate */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-slate-400">Wall Assembly Substrate:</label>
                <select
                  value={design.wallMaterial}
                  onChange={(e) => updateDesign({ wallMaterial: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 text-xs font-medium focus:outline-none focus:border-sky-400"
                >
                  <option value="brick">Fired Clay Brick (High Thermal Mass)</option>
                  <option value="stone">Granite Stone Masonry (Very High Inertia)</option>
                  <option value="concrete">Reinforced Concrete (Structural Dense)</option>
                  <option value="mud">Mud / Adobe Brick (Vernacular Passive)</option>
                  <option value="puf_insulation">PUF Sandwich Panel (Lightweight Prefab)</option>
                  <option value="wood">Timber Pine Frame (Rapid Modular)</option>
                </select>
              </div>

              {/* Added Insulation Layer (mm) */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Core Insulation Layer:</span>
                  <span className="text-sky-400 font-bold">{design.insulationThicknessMm} mm PUF</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="200"
                  step="10"
                  value={design.insulationThicknessMm}
                  onChange={(e) =>
                    updateDesign({ insulationThicknessMm: parseInt(e.target.value) })
                  }
                  className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>0mm (Uninsulated)</span>
                  <span>100mm (Code Norm)</span>
                  <span>200mm (Passivhaus)</span>
                </div>
              </div>

              {/* Thermal R-Value Feedback */}
              <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 space-y-1 text-xs">
                <div className="flex justify-between font-mono">
                  <span className="text-slate-400">Total Wall R-Value:</span>
                  <span className="text-emerald-400 font-bold">
                    {sim?.u_values?.wall_r_total?.toFixed(2) ?? "2.22"} m²K/W
                  </span>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-400">Total Roof R-Value:</span>
                  <span className="text-emerald-400 font-bold">
                    {sim?.u_values?.roof_r_total?.toFixed(2) ?? "2.85"} m²K/W
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: GLAZING & FENESTRATION */}
          {activeControlTab === "glazing" && (
            <div className="eng-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                  Fenestration & Solar Aperture
                </span>
                <span className="text-xs font-mono text-amber-400">
                  {((design.windowArea / (design.length * design.width)) * 100).toFixed(1)}% WWR
                </span>
              </div>

              {/* Window Area */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Glazing Aperture Area:</span>
                  <span className="text-sky-400 font-bold">{design.windowArea.toFixed(1)} m²</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="8.0"
                  step="0.2"
                  value={design.windowArea}
                  onChange={(e) => updateDesign({ windowArea: parseFloat(e.target.value) })}
                  className="w-full accent-sky-400 bg-slate-800 rounded-lg cursor-pointer"
                />
              </div>

              {/* Glazing Specification */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-slate-400">Glazing Assembly Spec:</label>
                <select
                  value={design.glazing}
                  onChange={(e) => updateDesign({ glazing: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 text-xs font-medium focus:outline-none focus:border-sky-400"
                >
                  <option value="single_clear">Single Clear 6mm (U=5.80, SHGC=0.82)</option>
                  <option value="double_clear">Double Clear Glazed 4-12-4 (U=2.80, SHGC=0.70)</option>
                  <option value="double_low_e">Double Low-E Argon (U=1.80, SHGC=0.50)</option>
                  <option value="triple_low_e">Triple Low-E Argon (U=1.00, SHGC=0.35)</option>
                </select>
              </div>

              {/* Facade Orientation */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-slate-400">Primary Glazing Facade:</label>
                <select
                  value={design.orientation}
                  onChange={(e) => updateDesign({ orientation: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 text-xs font-medium focus:outline-none focus:border-sky-400"
                >
                  <option value="south">South (Maximum Winter Passive Direct Gain)</option>
                  <option value="north">North (Consistent Diffuse Daylight)</option>
                  <option value="east">East (Morning Solar Preheating)</option>
                  <option value="west">West (Late Afternoon Heat Gain)</option>
                </select>
              </div>
            </div>
          )}

          {/* TAB 4: PASSIVE SYSTEMS */}
          {activeControlTab === "passive" && (
            <div className="eng-panel p-5 space-y-3">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wide block border-b border-slate-800 pb-2">
                Passive Strategy & Solar Shading
              </span>

              <div className="space-y-2 text-xs">
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="font-semibold text-amber-400 mb-1 flex items-center gap-1.5">
                    <Sun className="w-3.5 h-3.5" />
                    <span>Solar Orientation</span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    South orientation aligns primary glazed aperture normal to low-angle winter
                    noon sun in Leh (altitude ~32°), delivering up to 350 W/m² useful heating flux.
                  </p>
                </div>

                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="font-semibold text-sky-400 mb-1 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5" />
                    <span>Seasonal Overhang Shading</span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    A 0.45m horizontal overhang provides 100% shading during high summer sun (altitude ~78°),
                    preventing interior overheating while admitting 100% of winter radiation.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Live Quick Thermal Telemetry Card */}
          <div className="eng-panel p-4 bg-slate-900/60 border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between mb-2">
              <span>INSTANT ENVELOPE FEEDBACK</span>
              <span className="text-emerald-400 font-bold">168-HR METRICS</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2 bg-slate-950 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">COMFORT</span>
                <span className="text-emerald-400 font-bold font-mono">
                  {sim?.comfort_percentage.toFixed(0) ?? 0}%
                </span>
              </div>
              <div className="p-2 bg-slate-950 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">AVG TEMP</span>
                <span className="text-white font-bold font-mono">
                  {sim?.comfort_metrics?.avg.toFixed(1) ?? 0}°C
                </span>
              </div>
              <div className="p-2 bg-slate-950 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">WEEKLY LOSS</span>
                <span className="text-rose-400 font-bold font-mono">
                  {sim?.total_heat_loss_kwh.toFixed(0) ?? 0} kWh
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Interactive 3D Digital Twin Viewer (7 cols) */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          <div className="eng-panel p-2 flex flex-col h-[520px]">
            <ShelterModel3D
              length={design.length}
              width={design.width}
              height={design.height}
              roofType={design.roofType}
              wallMaterial={design.wallMaterial}
              windowArea={design.windowArea}
              orientation={design.orientation}
              className="w-full h-full"
            />
          </div>

          {/* Bottom Specifications strip */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-slate-500 text-[10px] block">TOTAL ENVELOPE</span>
              <span className="font-semibold text-white font-mono">
                {(
                  2 * (design.length + design.width) * design.height +
                  design.length * design.width * 2
                ).toFixed(1)}{" "}
                m²
              </span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block">INTERNAL VOLUME</span>
              <span className="font-semibold text-white font-mono">
                {(design.length * design.width * design.height).toFixed(1)} m³
              </span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block">ACTIVE CLIMATE</span>
              <span className="font-semibold text-sky-400 font-mono uppercase">
                {selectedCity} (Leh Station)
              </span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block">SOLAR EFFICIENCY</span>
              <span className="font-semibold text-amber-400 font-mono">
                {sim
                  ? (
                      (sim.integrated_solar_energy_kwh /
                        Math.max(0.01, sim.integrated_incident_solar_kwh)) *
                      100
                    ).toFixed(1)
                  : "38.2"}
                %
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
