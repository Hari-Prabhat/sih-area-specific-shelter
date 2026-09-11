import { Settings, Play, Compass, Ruler, LayoutGrid, Layers, ShieldCheck, Wind, Users, Loader2, Sparkles } from 'lucide-react';
import { ShelterDesign } from '../types';
import { materials } from '../data/materials';
import ShelterModel3D from './ShelterModel3D';

interface ShelterDesignerProps {
  shelterDesign: ShelterDesign;
  setShelterDesign: (design: ShelterDesign) => void;
  selectedMaterial: string;
  setSelectedMaterial: (material: string) => void;
  onRunSimulation: () => void;
  isSimulating?: boolean;
  onRunOptimization?: () => void;
  isOptimizing?: boolean;
  onNavigateToCompare?: () => void;
}

export default function ShelterDesigner({
  shelterDesign,
  setShelterDesign,
  selectedMaterial,
  setSelectedMaterial,
  onRunSimulation,
  isSimulating = false,
  onRunOptimization,
  isOptimizing = false,
  onNavigateToCompare,
}: ShelterDesignerProps) {
  const updateField = (field: keyof ShelterDesign, value: any) => {
    setShelterDesign({ ...shelterDesign, [field]: value });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
            <Settings className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Engineering Design Studio</h2>
            <p className="text-sm text-slate-400">
              Parametric shelter architecture & envelope specification for ISO 6946 forward simulation
            </p>
          </div>
        </div>
        <button
          onClick={onRunSimulation}
          disabled={isSimulating}
          className="px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-lg flex items-center gap-2 shadow-lg shadow-green-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {isSimulating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Run Simulation</span>
            </>
          )}
        </button>
      </div>

      {/* Row 1: Shape, Dimensions, Orientation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Shape */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <LayoutGrid className="w-4 h-4 text-purple-400" /> Shelter Shape & Form
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {(['rectangular', 'cylindrical', 'dome', 'pyramid'] as const).map((shape) => (
              <button
                key={shape}
                onClick={() => updateField('shape', shape)}
                className={`p-4 rounded-lg border transition-all text-center ${
                  shelterDesign.shape === shape
                    ? 'bg-purple-500/20 border-purple-500/50 text-purple-300 shadow-sm'
                    : 'bg-slate-700/30 border-slate-600/30 text-slate-400 hover:bg-slate-700/50'
                }`}
              >
                <p className="text-xs font-medium capitalize">{shape}</p>
              </button>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/30 flex justify-between text-xs text-slate-400">
            <span>Floor Area: {(shelterDesign.length * shelterDesign.width).toFixed(1)} m²</span>
            <span>Vol: {(shelterDesign.length * shelterDesign.width * shelterDesign.height).toFixed(1)} m³</span>
          </div>
        </div>

        {/* Primary Dimensions */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Ruler className="w-4 h-4 text-blue-400" /> Primary Geometry (m)
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Length (m)', field: 'length', min: 2, max: 30, step: 0.5 },
              { label: 'Width (m)', field: 'width', min: 2, max: 20, step: 0.5 },
              { label: 'Clear Height (m)', field: 'height', min: 2, max: 8, step: 0.1 },
              { label: 'Wall Thickness (m)', field: 'wallThickness', min: 0.1, max: 1, step: 0.05 },
            ].map((input) => (
              <div key={input.field} className="space-y-1">
                <label className="text-[11px] text-slate-400">{input.label}</label>
                <input
                  type="number"
                  value={shelterDesign[input.field as keyof ShelterDesign] as number}
                  min={input.min}
                  max={input.max}
                  step={input.step}
                  onChange={(e) => updateField(input.field as keyof ShelterDesign, Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500/50"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Orientation & Solar Facade */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Compass className="w-4 h-4 text-amber-400" /> Solar Azimuth & Orientation
          </h3>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Azimuth Angle</span>
                <span className="text-amber-400 font-bold">{shelterDesign.orientation}°</span>
              </div>
              <input
                type="range"
                min={0}
                max={360}
                step={5}
                value={shelterDesign.orientation}
                onChange={(e) => updateField('orientation', Number(e.target.value))}
                className="w-full accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>N (0°)</span>
                <span>E (90°)</span>
                <span className="text-amber-300">S (180° Optimal)</span>
                <span>W (270°)</span>
                <span>N (360°)</span>
              </div>
            </div>
            <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-700/50 text-[11px] text-slate-300">
              <p className="flex items-center gap-1.5 text-amber-300 font-medium mb-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Passive Solar Alignment
              </p>
              Glazing facing 180° (True South) maximizes direct solar heat gain in cold high-altitude conditions.
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Openings, Roof, Insulation & Passive Thermal Mass */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Openings & Glazing */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" /> Fenestration & Openings
          </h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Window Area (m²)</label>
                <input
                  type="number"
                  min={0.5}
                  max={25}
                  step={0.5}
                  value={shelterDesign.windowArea}
                  onChange={(e) => updateField('windowArea', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400">Door Area (m²)</label>
                <input
                  type="number"
                  min={0.5}
                  max={6}
                  step={0.5}
                  value={shelterDesign.doorArea}
                  onChange={(e) => updateField('doorArea', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] text-slate-400">Glazing Assembly</label>
              <select
                value={shelterDesign.windowGlazing}
                onChange={(e) => updateField('windowGlazing', e.target.value as any)}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="single">Single Glazed (U ≈ 5.8 W/m²·K, SHGC 0.85)</option>
                <option value="double">Double Glazed Clear (U ≈ 2.8 W/m²·K, SHGC 0.70)</option>
                <option value="triple">Triple Glazed Low-E (U ≈ 0.8 W/m²·K, SHGC 0.50)</option>
              </select>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">Roof Pitch Angle</span>
                <span className="text-cyan-400 font-bold">{shelterDesign.roofAngle}°</span>
              </div>
              <input
                type="range"
                min={0}
                max={60}
                step={5}
                value={shelterDesign.roofAngle}
                onChange={(e) => updateField('roofAngle', Number(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* Insulation & Thermal Mass */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> Insulation & Thermal Mass
          </h3>
          <div className="space-y-4">
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400">Envelope Insulation Layer</label>
              <select
                value={shelterDesign.insulationType}
                onChange={(e) => updateField('insulationType', e.target.value)}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="None">None (Uninsulated)</option>
                <option value="EPS">Expanded Polystyrene (EPS, k=0.038)</option>
                <option value="XPS">Extruded Polystyrene (XPS, k=0.030)</option>
                <option value="PUF Board">Rigid Polyurethane Foam (PUF, k=0.024)</option>
                <option value="Glass Wool">Glass Wool (k=0.040)</option>
                <option value="Rock Wool">Rock Wool (k=0.038)</option>
              </select>
            </div>

            <div className="pt-2 border-t border-slate-700/30 space-y-2">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={shelterDesign.thermalMassEnabled}
                  onChange={(e) => updateField('thermalMassEnabled', e.target.checked)}
                  className="rounded bg-slate-700 border-slate-600 text-amber-500 focus:ring-0 w-4 h-4"
                />
                <span className="text-xs text-slate-200 font-medium">Enable Sensible Thermal Mass Storage</span>
              </label>

              {shelterDesign.thermalMassEnabled && (
                <div className="pl-6 space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Mass Core Thickness</span>
                    <span className="text-amber-400 font-bold">{shelterDesign.thermalMassThickness} cm</span>
                  </div>
                  <input
                    type="range"
                    min={5}
                    max={40}
                    step={5}
                    value={shelterDesign.thermalMassThickness}
                    onChange={(e) => updateField('thermalMassThickness', Number(e.target.value))}
                    className="w-full accent-amber-500"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Occupancy & Ventilation Engineering Contracts */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Wind className="w-4 h-4 text-blue-400" /> Ventilation & Occupancy
          </h3>
          <div className="space-y-3 text-xs">
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50 flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-slate-300">
                <Users className="w-4 h-4 text-indigo-400" />
                <span>Internal Occupants</span>
              </div>
              <span className="font-mono font-bold text-white">2 Persons (140 W gain)</span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50 flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-slate-300">
                <Wind className="w-4 h-4 text-sky-400" />
                <span>Infiltration / ACH</span>
              </div>
              <span className="font-mono font-bold text-white">0.5 h⁻¹ (Air Changes)</span>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
              Authoritative Python simulation models continuous infiltration losses & human metabolic latent/sensible gains in the Forward Euler equation.
            </p>
          </div>
        </div>
      </div>

      {/* Wall Material Palette */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-slate-300">Structural Wall Substrate Material</h3>
          <span className="text-xs text-slate-500">ISO 6946 R-value calculated via thickness/k</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2.5">
          {materials
            .filter((m) => m.category !== 'Insulation')
            .map((material) => (
              <button
                key={material.name}
                onClick={() => setSelectedMaterial(material.name)}
                className={`p-3 rounded-lg text-xs font-medium transition-all text-left ${
                  selectedMaterial === material.name
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow-sm'
                    : 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                }`}
              >
                <span className="block font-semibold truncate">{material.name}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">k = {material.thermalConductivity} W/m·K</span>
                <span className="text-[10px] text-slate-500 block">ρ = {material.density} kg/m³</span>
              </button>
            ))}
        </div>
      </div>

      {/* Live 3D Preview */}
      <ShelterModel3D design={shelterDesign} materialName={selectedMaterial} />

      {/* Bottom Action Buttons */}
      <div className="flex flex-wrap justify-center gap-4 pt-2">
        <button
          onClick={onRunSimulation}
          disabled={isSimulating}
          className="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold rounded-xl flex items-center gap-3 shadow-lg shadow-green-500/20 text-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {isSimulating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Simulating with Python Backend...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Run Thermal Simulation</span>
            </>
          )}
        </button>

        {onRunOptimization && (
          <button
            onClick={onNavigateToCompare || onRunOptimization}
            disabled={isOptimizing}
            className="px-8 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold rounded-xl flex items-center gap-3 shadow-lg shadow-indigo-500/20 text-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {isOptimizing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Optimizing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Optimize Design</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
