import { Settings, Play, Compass, Ruler, LayoutGrid } from 'lucide-react';
import { ShelterDesign, ClimateData } from '../utils/thermalEngine';
import { materials } from '../data/materials';
import ShelterModel3D from './ShelterModel3D';

interface ShelterDesignerProps {
  shelterDesign: ShelterDesign;
  setShelterDesign: (design: ShelterDesign) => void;
  selectedMaterial: string;
  setSelectedMaterial: (material: string) => void;
  onRunSimulation: () => void;
  climateData?: ClimateData;
}

export default function ShelterDesigner({
  shelterDesign,
  setShelterDesign,
  selectedMaterial,
  setSelectedMaterial,
  onRunSimulation,
  climateData,
}: ShelterDesignerProps) {
  const updateField = (field: keyof ShelterDesign, value: any) => {
    setShelterDesign({ ...shelterDesign, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
            <Settings className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Shelter Design Configuration</h2>
            <p className="text-sm text-slate-400">Configure dimensions, shape, materials, and thermal properties</p>
          </div>
        </div>
        <button
          onClick={onRunSimulation}
          className="px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-lg flex items-center gap-2 shadow-lg shadow-green-500/20"
        >
          <Play className="w-4 h-4" /> Run Simulation
        </button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <LayoutGrid className="w-4 h-4 text-purple-400" /> Shelter Shape
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {(['rectangular', 'cylindrical', 'dome', 'pyramid'] as const).map((shape) => (
              <button
                key={shape}
                onClick={() => updateField('shape', shape)}
                className={`p-4 rounded-lg border transition-all ${
                  shelterDesign.shape === shape
                    ? 'bg-purple-500/20 border-purple-500/50 text-purple-300'
                    : 'bg-slate-700/30 border-slate-600/30 text-slate-400 hover:bg-slate-700/50'
                }`}
              >
                <p className="text-xs font-medium mt-2 capitalize">{shape}</p>
              </button>
            ))}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Ruler className="w-4 h-4 text-blue-400" /> Dimensions
          </h3>
          <div className="space-y-3">
            {[
              { label: 'Length (m)', field: 'length', min: 2, max: 30 },
              { label: 'Width (m)', field: 'width', min: 2, max: 20 },
              { label: 'Height (m)', field: 'height', min: 2, max: 8 },
              { label: 'Wall Thickness (m)', field: 'wallThickness', min: 0.1, max: 1 },
            ].map((input) => (
              <div key={input.field} className="space-y-1.5">
                <label className="text-xs text-slate-400">{input.label}</label>
                <input
                  type="number"
                  value={shelterDesign[input.field as keyof ShelterDesign] as number}
                  min={input.min}
                  max={input.max}
                  step={input.field === 'wallThickness' ? 0.05 : 1}
                  onChange={(e) => updateField(input.field as keyof ShelterDesign, Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500/50"
                />
              </div>
            ))}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Compass className="w-4 h-4 text-amber-400" /> Orientation
          </h3>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-xs text-slate-400">Orientation (° from North)</label>
              <input
                type="range"
                min={0}
                max={360}
                value={shelterDesign.orientation}
                onChange={(e) => updateField('orientation', Number(e.target.value))}
                className="w-full accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>N (0°)</span>
                <span className="text-amber-400 font-semibold">{shelterDesign.orientation}°</span>
                <span>N (360°)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Wall Material</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
          {materials
            .filter((m) => m.category !== 'Insulation')
            .map((material) => (
              <button
                key={material.name}
                onClick={() => setSelectedMaterial(material.name)}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-all text-left ${
                  selectedMaterial === material.name
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                }`}
              >
                <span className="block truncate">{material.name}</span>
                <span className="text-[10px] text-slate-500">k={material.thermalConductivity}</span>
              </button>
            ))}
        </div>
      </div>
      {/* Live 3D Preview */}
      <ShelterModel3D
        design={shelterDesign}
        materialName={selectedMaterial}
        climateData={climateData}
        locationName={climateData?.location}
      />
      <div className="flex justify-center">
        <button
          onClick={onRunSimulation}
          className="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold rounded-xl flex items-center gap-3 shadow-lg shadow-green-500/20 text-lg"
        >
          <Play className="w-5 h-5" /> Run Thermal Simulation
        </button>
      </div>
    </div>
  );
}
