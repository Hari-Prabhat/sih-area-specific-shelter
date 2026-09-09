import React from 'react';
import { useDesignStudio } from '../../context';
import type { EnergyResource, MaterialResource } from '../../types';
import { Sun, Zap, Fuel, Ban, Mountain, TreePine, Shield, Layers, HelpCircle, Sparkles } from 'lucide-react';

const ENERGY_OPTIONS: { id: EnergyResource; label: string; icon: React.ElementType }[] = [
  { id: 'Solar', label: 'Solar PV / Thermal', icon: Sun },
  { id: 'Grid', label: 'Municipal / Regional Grid', icon: Zap },
  { id: 'Diesel Generator', label: 'Diesel Generator Backup', icon: Fuel },
  { id: 'None', label: 'None (Pure 100% Passive)', icon: Ban },
];

const MATERIAL_OPTIONS: { id: MaterialResource; label: string; icon: React.ElementType }[] = [
  { id: 'Local Stone', label: 'Local Stone / Mud Brick', icon: Mountain },
  { id: 'Timber', label: 'Timber / Wood Framing', icon: TreePine },
  { id: 'Steel', label: 'Light-Gauge Steel Truss', icon: Shield },
  { id: 'Insulation Panels', label: 'PUF / EPS Insulation Panels', icon: Layers },
  { id: 'Other', label: 'Other Local Aggregates', icon: HelpCircle },
];

export const Step4Resources: React.FC = () => {
  const {
    resources,
    toggleEnergyResource,
    toggleMaterialResource,
    setCustomMaterialNotes,
  } = useDesignStudio();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
          STEP 4 of 5 — LOGISTICAL FEASIBILITY
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-xl font-bold text-white tracking-tight">
            Available On-Site Resources
          </h2>
          <span className="text-[11px] font-mono-data uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            OPTIONAL
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Optionally designate localized energy grids or indigenous material supply available within the deployment sector.
        </p>
      </div>

      {/* Energy Infrastructure */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-mono-data uppercase text-slate-300">
            Available Energy Infrastructure (Optional):
          </label>
          <span className="text-[10px] font-mono-data text-slate-500 uppercase">
            Multi-select supported
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {ENERGY_OPTIONS.map((item) => {
            const Icon = item.icon;
            const isSelected = resources.energy.includes(item.id);

            return (
              <div
                key={item.id}
                onClick={() => toggleEnergyResource(item.id)}
                className={`p-3 rounded border cursor-pointer transition-all flex items-center gap-2.5 ${
                  isSelected
                    ? 'bg-sky-950/40 border-sky-500 text-sky-300 shadow-sm'
                    : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-xs font-mono-data font-semibold">{item.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Local Materials */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-mono-data uppercase text-slate-300">
            Available Localized Building Materials (Optional):
          </label>
          <span className="text-[10px] font-mono-data text-slate-500 uppercase">
            Multi-select supported
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {MATERIAL_OPTIONS.map((item) => {
            const Icon = item.icon;
            const isSelected = resources.materials.includes(item.id);

            return (
              <div
                key={item.id}
                onClick={() => toggleMaterialResource(item.id)}
                className={`p-3 rounded border cursor-pointer transition-all flex items-center gap-2.5 ${
                  isSelected
                    ? 'bg-sky-950/40 border-sky-500 text-sky-300 shadow-sm'
                    : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-xs font-mono-data font-semibold">{item.label}</span>
              </div>
            );
          })}
        </div>

        {/* Custom notes */}
        <div className="pt-2">
          <label className="block text-[11px] font-mono-data text-slate-400 uppercase mb-1">
            Site Material Constraints / Vernacular Notes (Optional):
          </label>
          <input
            type="text"
            value={resources.customMaterialNotes || ''}
            onChange={(e) => setCustomMaterialNotes(e.target.value)}
            placeholder="e.g. Local granite quarry nearby, road access limited to 3-ton trucks"
            className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 rounded px-3 py-2 text-xs font-mono-data text-slate-200 outline-none placeholder-slate-600"
          />
        </div>
      </div>

      <div className="p-3 bg-slate-950/50 border border-slate-800 rounded flex items-center gap-2 text-xs font-mono-data text-slate-400">
        <Sparkles className="w-4 h-4 text-sky-400 shrink-0" />
        <span>
          Selections here will guide the backend recommender to prioritize matching materials from the database (e.g. mud brick vs PUF panels).
        </span>
      </div>
    </div>
  );
};
