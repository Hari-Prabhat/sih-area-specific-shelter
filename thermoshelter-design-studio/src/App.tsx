import { useState } from 'react';
import { Shield, Sun, Thermometer, Wind, Mountain, Settings, BarChart3, Layers, ChevronRight, Sparkles } from 'lucide-react';
import ClimateInput from './components/ClimateInput';
import ShelterDesigner from './components/ShelterDesigner';
import SimulationResults from './components/SimulationResults';
import ComparativeAnalysis from './components/ComparativeAnalysis';
import DesignStudio from './components/DesignStudio';
import { ClimateData, ShelterDesign, SimulationResult, runSimulation } from './utils/thermalEngine';
import { getMaterialByName } from './data/materials';
import { climatePresets } from './data/climatePresets';

type TabType = 'studio' | 'dashboard' | 'climate' | 'design' | 'results' | 'compare';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('studio');
  const [climateData, setClimateData] = useState<ClimateData>(climatePresets[0]);
  const [shelterDesign, setShelterDesign] = useState<ShelterDesign>({
    length: 6,
    width: 4,
    height: 3,
    shape: 'rectangular',
    orientation: 180,
    roofAngle: 30,
    wallThickness: 0.3,
    windowArea: 3,
    windowGlazing: 'double',
    doorArea: 2,
    insulationType: 'EPS',
    thermalMassEnabled: true,
    thermalMassThickness: 20,
  });
  const [selectedMaterial, setSelectedMaterial] = useState('Rammed Earth (Stabilized)');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);

  const handleRunSimulation = () => {
    const material = getMaterialByName(selectedMaterial);
    const insulation = getMaterialByName(shelterDesign.insulationType);
    if (material) {
      const result = runSimulation(climateData, shelterDesign, material, insulation);
      setSimulationResult(result);
      setActiveTab('results');
    }
  };

  const tabs = [
    { id: 'studio' as TabType, label: 'Design Studio', icon: Sparkles },
    { id: 'dashboard' as TabType, label: 'Dashboard', icon: Shield },
    { id: 'climate' as TabType, label: 'Climate Data', icon: Thermometer },
    { id: 'design' as TabType, label: 'Shelter Design', icon: Settings },
    { id: 'results' as TabType, label: 'Results', icon: BarChart3 },
    { id: 'compare' as TabType, label: 'Compare', icon: Layers },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
              <Mountain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
                ThermoShelter Design Studio
              </h1>
              <p className="text-xs text-slate-400">Area-Specific Shelter Design for Thermal Comfort</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Shield className="w-4 h-4 text-amber-500" />
            <span>SIH 2026 | DRDO</span>
          </div>
        </div>
      </header>

      <nav className="bg-slate-800/50 border-b border-slate-700/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto py-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'studio' && <DesignStudio />}
        {activeTab === 'dashboard' && <DashboardTab onNavigate={setActiveTab} climateData={climateData} />}
        {activeTab === 'climate' && <ClimateInput climateData={climateData} setClimateData={setClimateData} />}
        {activeTab === 'design' && (
          <ShelterDesigner
            shelterDesign={shelterDesign}
            setShelterDesign={setShelterDesign}
            selectedMaterial={selectedMaterial}
            setSelectedMaterial={setSelectedMaterial}
            onRunSimulation={handleRunSimulation}
          />
        )}
        {activeTab === 'results' && simulationResult && (
          <SimulationResults
            result={simulationResult}
            climateData={climateData}
            shelterDesign={shelterDesign}
            materialName={selectedMaterial}
          />
        )}
        {activeTab === 'results' && !simulationResult && (
          <div className="text-center py-20">
            <BarChart3 className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-400 mb-2">No Results Yet</h3>
            <button
              onClick={() => setActiveTab('climate')}
              className="px-6 py-2 bg-amber-500 text-black rounded-lg font-medium"
            >
              Get Started
            </button>
          </div>
        )}
        {activeTab === 'compare' && <ComparativeAnalysis climateData={climateData} shelterDesign={shelterDesign} />}
      </main>

      <footer className="bg-slate-900/80 border-t border-slate-700/30 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
          <p>ThermoShelter Design Studio | SIH 2026 | SIH26051 | DRDO</p>
        </div>
      </footer>
    </div>
  );
}

function DashboardTab({
  onNavigate,
  climateData,
}: {
  onNavigate: (tab: TabType) => void;
  climateData: ClimateData;
}) {
  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-amber-500/10 via-orange-500/5 to-transparent border border-amber-500/20 p-8">
        <h2 className="text-3xl font-bold mb-3">
          Area-Specific Shelter Design for{' '}
          <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
            Thermal Comfort
          </span>
        </h2>
        <p className="text-slate-300 max-w-2xl mb-6">
          Design energy-efficient, self-sustained passive shelters optimized for specific climatic conditions.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => onNavigate('studio')}
            className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-lg flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> Launch Design Studio
          </button>
          <button
            onClick={() => onNavigate('climate')}
            className="px-6 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-black font-semibold rounded-lg"
          >
            Manual Design <ChevronRight className="w-4 h-4 inline" />
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/5 border border-blue-500/20 rounded-xl p-4">
          <Mountain className="w-5 h-5 text-blue-400 mb-2" />
          <p className="text-xs text-slate-400">Location</p>
          <p className="text-sm font-semibold">{climateData.location}</p>
        </div>
        <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border border-orange-500/20 rounded-xl p-4">
          <Thermometer className="w-5 h-5 text-orange-400 mb-2" />
          <p className="text-xs text-slate-400">Avg Temp</p>
          <p className="text-sm font-semibold">{climateData.avgAmbientTemp}°C</p>
        </div>
        <div className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border border-yellow-500/20 rounded-xl p-4">
          <Sun className="w-5 h-5 text-yellow-400 mb-2" />
          <p className="text-xs text-slate-400">Solar</p>
          <p className="text-sm font-semibold">{climateData.solarIrradiance} kWh/m²/yr</p>
        </div>
        <div className="bg-gradient-to-br from-green-500/20 to-green-600/5 border border-green-500/20 rounded-xl p-4">
          <Wind className="w-5 h-5 text-green-400 mb-2" />
          <p className="text-xs text-slate-400">Altitude</p>
          <p className="text-sm font-semibold">{climateData.altitude}m</p>
        </div>
      </div>
    </div>
  );
}

export default App;
