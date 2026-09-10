import React from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { ShelterModel3D } from "../components/shelter/ShelterModel3D";
import { Box, Compass, Layers, RotateCcw } from "lucide-react";

export const DigitalTwinPage: React.FC = () => {
  const { design, updateDesign, selectedCity } = useDesignStore();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="3D Digital Twin Architectural Viewer"
        subtitle="1:1 scale parametric WebGL digital twin rendering actual shelter dimensions, pitched/flat roof form, and south-facing fenestration."
        badge={`${design.length.toFixed(1)}m × ${design.width.toFixed(1)}m · ${selectedCity.toUpperCase()}`}
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                updateDesign({
                  length: 4.5,
                  width: 3.2,
                  height: 2.8,
                  roofType: "pitched",
                })
              }
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono transition-all cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Dims</span>
            </button>
          </div>
        }
      />

      {/* Large Immersive 3D Viewer (Full width / height) */}
      <div className="eng-panel p-2 h-[580px] w-full relative">
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

      {/* Interactive Live Dimension Sliders under the 3D Twin */}
      <div className="eng-panel p-6 space-y-4">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
          Parametric Geometry Controls (Live 3D Deformation)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-xs font-mono">
          {/* Length */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Length (L):</span>
              <span className="text-sky-400 font-bold">{design.length.toFixed(1)} m</span>
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

          {/* Width */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Width (W):</span>
              <span className="text-sky-400 font-bold">{design.width.toFixed(1)} m</span>
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

          {/* Height */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Height (H):</span>
              <span className="text-sky-400 font-bold">{design.height.toFixed(1)} m</span>
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

          {/* Roof Profile */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Roof Geometry:</span>
              <span className="text-sky-400 font-bold capitalize">{design.roofType}</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => updateDesign({ roofType: "flat" })}
                className={`py-1.5 rounded text-[11px] font-bold border transition-all ${
                  design.roofType === "flat"
                    ? "bg-sky-500/20 text-sky-400 border-sky-500/40"
                    : "bg-slate-950 text-slate-400 border-slate-800"
                }`}
              >
                Flat Roof
              </button>
              <button
                onClick={() => updateDesign({ roofType: "pitched" })}
                className={`py-1.5 rounded text-[11px] font-bold border transition-all ${
                  design.roofType === "pitched"
                    ? "bg-sky-500/20 text-sky-400 border-sky-500/40"
                    : "bg-slate-950 text-slate-400 border-slate-800"
                }`}
              >
                Pitched 30°
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
