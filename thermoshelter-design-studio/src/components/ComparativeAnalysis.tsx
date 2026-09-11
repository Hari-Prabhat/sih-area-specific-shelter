import { useState } from 'react';
import { Layers, Plus } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ClimateData, ShelterDesign, SimulationResult, runSimulation } from '../utils/thermalEngine';
import { runSimulationViaApi } from '../services/api';
import { materials, getMaterialByName } from '../data/materials';

interface ComparativeAnalysisProps {
  climateData: ClimateData;
  shelterDesign: ShelterDesign;
}

interface ComparisonEntry {
  id: string;
  label: string;
  result: SimulationResult;
}

export default function ComparativeAnalysis({ climateData, shelterDesign }: ComparativeAnalysisProps) {
  const [comparisons, setComparisons] = useState<ComparisonEntry[]>([]);
  const [newMaterial, setNewMaterial] = useState(materials[0].name);
  const [isLoading, setIsLoading] = useState(false);

  const addComparison = async () => {
    const material = materials.find((m) => m.name === newMaterial);
    if (!material) return;
    const insulation = getMaterialByName(shelterDesign.insulationType);
    setIsLoading(true);
    try {
      const result = await runSimulationViaApi(climateData, shelterDesign, material, insulation);
      setComparisons(prev => [...prev, { id: Date.now().toString(), label: newMaterial, result }]);
    } catch {
      const result = runSimulation(climateData, shelterDesign, material, insulation);
      setComparisons(prev => [...prev, { id: Date.now().toString(), label: newMaterial, result }]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickCompare = async () => {
    const quickMaterials = [
      'Mud/Adobe',
      'Rammed Earth (Stabilized)',
      'AAC Block (Autoclaved Aerated Concrete)',
      'Brick (Solid)',
      'Trombe Wall (Concrete + Glass)',
      'SIP Panel (Structural Insulated Panel)',
    ];
    const insulation = getMaterialByName(shelterDesign.insulationType);
    setIsLoading(true);
    try {
      const entries = await Promise.all(
        quickMaterials.map(async (matName, i) => {
          const material = materials.find((m) => m.name === matName);
          if (!material) return null;
          try {
            const result = await runSimulationViaApi(climateData, shelterDesign, material, insulation);
            return { id: `quick-${i}`, label: matName, result };
          } catch {
            const result = runSimulation(climateData, shelterDesign, material, insulation);
            return { id: `quick-${i}`, label: matName, result };
          }
        })
      );
      setComparisons(entries.filter(Boolean) as ComparisonEntry[]);
    } finally {
      setIsLoading(false);
    }
  };


  const chartData = comparisons.map((c) => ({
    name: c.label.length > 15 ? c.label.substring(0, 15) + '...' : c.label,
    'Avg Temp (°C)': c.result.avgInsideTemp,
    Comfort: c.result.thermalComfortIndex,
    'Efficiency (%)': c.result.energyEfficiency,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-indigo-500/20 rounded-lg flex items-center justify-center">
          <Layers className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Comparative Analysis</h2>
          <p className="text-sm text-slate-400">Compare different materials and designs</p>
        </div>
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Add Design to Compare</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select
            value={newMaterial}
            onChange={(e) => setNewMaterial(e.target.value)}
            className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white"
          >
            {materials
              .filter((m) => m.category !== 'Insulation')
              .map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
          </select>
          <button
            onClick={addComparison}
            className="px-4 py-2 bg-indigo-500 text-white font-medium rounded-lg hover:bg-indigo-400 flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" /> Add
          </button>
          <button
            onClick={quickCompare}
            className="px-4 py-2 bg-slate-700 text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-600"
          >
            Quick Compare (6 materials)
          </button>
        </div>
      </div>
      {comparisons.length >= 2 && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Performance Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-20} textAnchor="end" height={60} />
              <YAxis stroke="#64748b" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="Avg Temp (°C)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Comfort" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Efficiency (%)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {comparisons.length === 0 && (
        <div className="text-center py-16 bg-slate-800/30 rounded-xl border border-slate-700/20">
          <Layers className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-400 mb-2">No Comparisons Yet</h3>
          <p className="text-sm text-slate-500 mb-4">Add designs to compare or use Quick Compare</p>
          <button
            onClick={quickCompare}
            className="px-6 py-2 bg-indigo-500 text-white font-medium rounded-lg hover:bg-indigo-400"
          >
            Quick Compare
          </button>
        </div>
      )}
    </div>
  );
}
