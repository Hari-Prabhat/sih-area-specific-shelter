import { useState } from 'react';
import { MapPin, Users, Target, Zap, CheckCircle, AlertCircle, ArrowRight, ArrowLeft, Sparkles, Building2, Mountain } from 'lucide-react';
import { ClimateData, ShelterDesign } from '../utils/thermalEngine';
import { climatePresets } from '../data/climatePresets';
import { materials } from '../data/materials';
import ShelterModel3D from './ShelterModel3D';

type StudioStep = 'location' | 'mission' | 'priorities' | 'resources' | 'review' | 'generating' | 'results';

interface MissionConfig {
  occupants: number;
  purpose: string;
  deploymentType: string;
  duration: string;
  mobilityRequired: boolean;
}

interface PriorityConfig {
  thermalComfort: boolean;
  energyIndependence: boolean;
  lowCost: boolean;
  lowWeight: boolean;
  rapidDeployment: boolean;
  durability: boolean;
}

interface ResourceConfig {
  energy: string[];
  materials: string[];
}

interface GeneratedDesign {
  id: string;
  location: string;
  climate: string;
  mission: MissionConfig;
  priorities: PriorityConfig;
  resources: ResourceConfig;
  specifications: {
    floorArea: number;
    length: number;
    width: number;
    height: number;
    orientation: string;
    roofConfig: string;
    wallStrategy: string;
    insulation: string;
    glazing: string;
    thermalMass: string;
    ventilation: string;
    passiveStrategies: string[];
    materialSelection: string[];
  };
}

export default function DesignStudio() {
  const [currentStep, setCurrentStep] = useState<StudioStep>('location');
  const [selectedLocation, setSelectedLocation] = useState<ClimateData | null>(null);
  const [mission, setMission] = useState<MissionConfig>({
    occupants: 4,
    purpose: 'Residential',
    deploymentType: 'Permanent',
    duration: '12',
    mobilityRequired: false,
  });
  const [priorities, setPriorities] = useState<PriorityConfig>({
    thermalComfort: true,
    energyIndependence: true,
    lowCost: false,
    lowWeight: false,
    rapidDeployment: false,
    durability: true,
  });
  const [resources, setResources] = useState<ResourceConfig>({
    energy: ['Solar'],
    materials: ['Rammed Earth (Stabilized)', 'AAC Block (Autoclaved Aerated Concrete)'],
  });
  const [generatedDesign, setGeneratedDesign] = useState<GeneratedDesign | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const steps = [
    { id: 'location', label: 'Location', icon: MapPin },
    { id: 'mission', label: 'Mission', icon: Users },
    { id: 'priorities', label: 'Priorities', icon: Target },
    { id: 'resources', label: 'Resources', icon: Zap },
    { id: 'review', label: 'Review', icon: CheckCircle },
  ];

  const validateCurrentStep = (): boolean => {
    const errors: string[] = [];
    if (currentStep === 'location' && !selectedLocation) errors.push('Please select a location');
    if (currentStep === 'mission') {
      if (mission.occupants < 1) errors.push('Occupants must be at least 1');
      if (!mission.purpose) errors.push('Please select a shelter purpose');
    }
    if (currentStep === 'priorities' && !Object.values(priorities).some((v) => v)) {
      errors.push('Select at least one priority');
    }
    if (currentStep === 'resources') {
      if (resources.energy.length === 0) errors.push('Select at least one energy source');
      if (resources.materials.length === 0) errors.push('Select at least one material');
    }
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleNext = () => {
    if (!validateCurrentStep()) return;
    const stepOrder: StudioStep[] = ['location', 'mission', 'priorities', 'resources', 'review', 'generating', 'results'];
    const currentIndex = stepOrder.indexOf(currentStep);
    if (currentIndex < stepOrder.length - 1) setCurrentStep(stepOrder[currentIndex + 1]);
  };

  const handleBack = () => {
    const stepOrder: StudioStep[] = ['location', 'mission', 'priorities', 'resources', 'review', 'generating', 'results'];
    const currentIndex = stepOrder.indexOf(currentStep);
    if (currentIndex > 0) setCurrentStep(stepOrder[currentIndex - 1]);
  };

  const handleGenerateDesign = () => {
    if (!selectedLocation) return;
    setCurrentStep('generating');
    setTimeout(() => {
      const design: GeneratedDesign = {
        id: `THERMOCORE-${selectedLocation.location.split(',')[0].toUpperCase().replace(/\s+/g, '-')}-01`,
        location: selectedLocation.location,
        climate:
          selectedLocation.altitude > 3000
            ? 'Alpine Severe Cold'
            : selectedLocation.altitude > 1500
            ? 'Mountain Cold'
            : 'Temperate',
        mission,
        priorities,
        resources,
        specifications: {
          floorArea: mission.occupants * 6,
          length: Math.ceil(Math.sqrt(mission.occupants * 6) * 1.5),
          width: Math.ceil(Math.sqrt(mission.occupants * 6)),
          height: 3.0,
          orientation: 'South (180°)',
          roofConfig: 'Pitched roof (30°) with integrated solar mounting',
          wallStrategy: 'High-performance insulated envelope',
          insulation: 'Polyurethane Foam (PUF) - 100mm',
          glazing: 'Triple glazing with low-E coating',
          thermalMass: 'High - Trombe wall system',
          ventilation: 'Controlled mechanical ventilation with heat recovery',
          passiveStrategies: [
            'Solar capture through south-facing glazing',
            'Thermal mass for temperature stabilization',
            'Airlock entry system',
            'Controlled ventilation',
            'Windbreak integration',
          ],
          materialSelection: resources.materials,
        },
      };
      setGeneratedDesign(design);
      setCurrentStep('results');
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold">ThermoShelter Design Studio</h2>
          <p className="text-sm text-slate-400">Professional shelter design workflow</p>
        </div>
      </div>

      {currentStep !== 'generating' && currentStep !== 'results' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted =
                steps.findIndex((s) => s.id === step.id) < steps.findIndex((s) => s.id === currentStep);
              return (
                <div key={step.id} className="flex items-center flex-1">
                  <div
                    className={`flex items-center gap-2 ${
                      isActive ? 'text-indigo-400' : isCompleted ? 'text-green-400' : 'text-slate-500'
                    }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                        isActive
                          ? 'border-indigo-400 bg-indigo-500/20'
                          : isCompleted
                          ? 'border-green-400 bg-green-500/20'
                          : 'border-slate-600 bg-slate-700/30'
                      }`}
                    >
                      {isCompleted ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                    </div>
                    <span className="text-xs font-medium hidden md:block">{step.label}</span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-2 ${isCompleted ? 'bg-green-400' : 'bg-slate-700'}`}></div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {validationErrors.length > 0 && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              {validationErrors.map((error, i) => (
                <p key={i} className="text-sm text-red-300">
                  {error}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {currentStep === 'location' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-indigo-400" /> Select Location
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
            {climatePresets.map((preset) => (
              <button
                key={preset.location}
                onClick={() => setSelectedLocation(preset)}
                className={`p-4 rounded-lg border transition-all text-left ${
                  selectedLocation?.location === preset.location
                    ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                    : 'bg-slate-700/30 border-slate-600/30 text-slate-300 hover:bg-slate-700/50'
                }`}
              >
                <p className="font-semibold text-sm">{preset.location}</p>
                <p className="text-xs text-slate-400 mt-1">
                  {preset.altitude}m | {preset.avgAmbientTemp}°C avg
                </p>
              </button>
            ))}
          </div>
          {selectedLocation && (
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/40 rounded-xl border border-slate-700/30 p-6 mt-6">
              <h4 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <Mountain className="w-4 h-4 text-indigo-400" /> Site Profile
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase">Location</p>
                  <p className="text-sm font-semibold text-white mt-1">{selectedLocation.location}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase">Elevation</p>
                  <p className="text-sm font-semibold text-white mt-1">{selectedLocation.altitude}m</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase">Climate</p>
                  <p className="text-sm font-semibold text-white mt-1">
                    {selectedLocation.altitude > 3000 ? 'Alpine Severe Cold' : 'Temperate'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase">Solar Resource</p>
                  <p className="text-sm font-semibold text-white mt-1">
                    {selectedLocation.solarIrradiance > 1900 ? 'High' : 'Good'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {currentStep === 'mission' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6 space-y-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" /> Shelter Mission
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">Number of Occupants</label>
              <input
                type="number"
                min="1"
                max="50"
                value={mission.occupants}
                onChange={(e) => setMission({ ...mission, occupants: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">Duration (months)</label>
              <input
                type="number"
                min="1"
                value={mission.duration}
                onChange={(e) => setMission({ ...mission, duration: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">Shelter Purpose</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                'Disaster Relief',
                'Military',
                'Research',
                'Residential',
                'Medical',
                'Storage',
                'Command / Operations',
                'Temporary Accommodation',
              ].map((purpose) => (
                <button
                  key={purpose}
                  onClick={() => setMission({ ...mission, purpose })}
                  className={`px-3 py-2 rounded-lg text-xs font-medium transition ${
                    mission.purpose === purpose
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/50'
                      : 'bg-slate-700/30 text-slate-400 border border-slate-600/30 hover:bg-slate-700/50'
                  }`}
                >
                  {purpose}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">Deployment Type</label>
            <div className="grid grid-cols-3 gap-2">
              {['Temporary', 'Seasonal', 'Permanent'].map((type) => (
                <button
                  key={type}
                  onClick={() => setMission({ ...mission, deploymentType: type })}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    mission.deploymentType === type
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/50'
                      : 'bg-slate-700/30 text-slate-400 border border-slate-600/30 hover:bg-slate-700/50'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={mission.mobilityRequired}
              onChange={(e) => setMission({ ...mission, mobilityRequired: e.target.checked })}
              className="w-4 h-4 accent-indigo-500"
            />
            <span className="text-sm text-slate-300">Mobility required (relocatable shelter)</span>
          </label>
        </div>
      )}

      {currentStep === 'priorities' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-indigo-400" /> Design Priorities
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { key: 'thermalComfort', label: 'Thermal Comfort', description: 'Maintain comfortable indoor temperatures' },
              { key: 'energyIndependence', label: 'Energy Independence', description: 'Minimize external energy dependency' },
              { key: 'lowCost', label: 'Low Cost', description: 'Minimize construction and operational costs' },
              { key: 'lowWeight', label: 'Low Weight', description: 'Lightweight structure for transport' },
              { key: 'rapidDeployment', label: 'Rapid Deployment', description: 'Quick assembly and setup time' },
              { key: 'durability', label: 'Durability', description: 'Long-term structural integrity' },
            ].map((option) => (
              <button
                key={option.key}
                onClick={() =>
                  setPriorities({ ...priorities, [option.key]: !priorities[option.key as keyof PriorityConfig] })
                }
                className={`p-4 rounded-lg border transition-all text-left ${
                  priorities[option.key as keyof PriorityConfig]
                    ? 'bg-indigo-500/20 border-indigo-500/50'
                    : 'bg-slate-700/30 border-slate-600/30 hover:bg-slate-700/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p
                      className={`font-semibold text-sm ${
                        priorities[option.key as keyof PriorityConfig] ? 'text-indigo-300' : 'text-slate-300'
                      }`}
                    >
                      {option.label}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">{option.description}</p>
                  </div>
                  {priorities[option.key as keyof PriorityConfig] && (
                    <CheckCircle className="w-5 h-5 text-indigo-400 flex-shrink-0" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {currentStep === 'resources' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6 space-y-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-400" /> Available Resources
          </h3>
          <div>
            <label className="text-sm font-medium text-slate-300 mb-3 block">Energy Sources</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {['Solar', 'Grid', 'Diesel / Generator', 'None'].map((energy) => (
                <button
                  key={energy}
                  onClick={() =>
                    setResources({
                      ...resources,
                      energy: resources.energy.includes(energy)
                        ? resources.energy.filter((e) => e !== energy)
                        : [...resources.energy, energy],
                    })
                  }
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    resources.energy.includes(energy)
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/50'
                      : 'bg-slate-700/30 text-slate-400 border border-slate-600/30 hover:bg-slate-700/50'
                  }`}
                >
                  {energy}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-300 mb-3 block">Available Materials</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {materials
                .filter((m) => m.category !== 'Insulation')
                .map((material) => (
                  <button
                    key={material.name}
                    onClick={() =>
                      setResources({
                        ...resources,
                        materials: resources.materials.includes(material.name)
                          ? resources.materials.filter((m) => m !== material.name)
                          : [...resources.materials, material.name],
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-xs font-medium transition text-left ${
                      resources.materials.includes(material.name)
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/50'
                        : 'bg-slate-700/30 text-slate-400 border border-slate-600/30 hover:bg-slate-700/50'
                    }`}
                  >
                    {material.name}
                  </button>
                ))}
            </div>
          </div>
        </div>
      )}

      {currentStep === 'review' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-indigo-400" /> Design Review
          </h3>
          <div className="space-y-6">
            <div className="border-l-2 border-indigo-500 pl-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Site</p>
              <p className="text-lg font-semibold text-white">{selectedLocation?.location}</p>
              <p className="text-sm text-slate-400">{selectedLocation?.altitude}m elevation</p>
            </div>
            <div className="border-l-2 border-indigo-500 pl-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Mission</p>
              <p className="text-lg font-semibold text-white">{mission.deploymentType} Shelter</p>
              <p className="text-sm text-slate-400">
                {mission.purpose} • {mission.occupants} occupants
              </p>
            </div>
            <div className="border-l-2 border-indigo-500 pl-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Priorities</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {Object.entries(priorities)
                  .filter(([_, v]) => v)
                  .map(([key]) => (
                    <span
                      key={key}
                      className="px-3 py-1 bg-indigo-500/20 text-indigo-300 text-xs font-medium rounded-full"
                    >
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </span>
                  ))}
              </div>
            </div>
            <div className="border-l-2 border-indigo-500 pl-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Energy</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {resources.energy.map((energy) => (
                  <span
                    key={energy}
                    className="px-3 py-1 bg-indigo-500/20 text-indigo-300 text-xs font-medium rounded-full"
                  >
                    {energy}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {currentStep === 'generating' && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-12 text-center">
          <div className="animate-pulse">
            <Sparkles className="w-16 h-16 text-indigo-400 mx-auto mb-4" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Generating Design</h3>
          <p className="text-sm text-slate-400">Analyzing climate data and optimizing shelter parameters...</p>
        </div>
      )}

      {currentStep === 'results' && generatedDesign && (
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent border border-indigo-500/20 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <Building2 className="w-5 h-5 text-indigo-400" />
              <h3 className="text-lg font-semibold">Design DNA</h3>
              <span className="ml-auto px-3 py-1 bg-indigo-500/20 text-indigo-300 text-xs font-mono rounded-full">
                {generatedDesign.id}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Site</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.location}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Geometry</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.floorArea} m²</p>
                  <p className="text-xs text-slate-400">
                    {generatedDesign.specifications.length} × {generatedDesign.specifications.width} ×{' '}
                    {generatedDesign.specifications.height}m
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Orientation</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.orientation}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Envelope</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.wallStrategy}</p>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Insulation</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.insulation}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Glazing</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.glazing}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Thermal Mass</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.thermalMass}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase mb-1">Ventilation</p>
                  <p className="text-sm font-semibold text-white">{generatedDesign.specifications.ventilation}</p>
                </div>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-indigo-500/20">
              <p className="text-xs text-slate-500 uppercase mb-3">Passive Strategies</p>
              <div className="flex flex-wrap gap-2">
                {generatedDesign.specifications.passiveStrategies.map((strategy, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-indigo-500/20 text-indigo-300 text-xs font-medium rounded-full"
                  >
                    {strategy}
                  </span>
                ))}
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-indigo-500/20">
              <p className="text-xs text-slate-500 uppercase mb-3">Material Selection</p>
              <div className="flex flex-wrap gap-2">
                {generatedDesign.specifications.materialSelection.map((material, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-slate-700/50 text-slate-300 text-xs font-medium rounded-full"
                  >
                    {material}
                  </span>
                ))}
              </div>
            </div>
          </div>
          {/* 3D Shelter Visualization */}
          <ShelterModel3D
            design={{
              length: generatedDesign.specifications.length,
              width: generatedDesign.specifications.width,
              height: generatedDesign.specifications.height,
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
            } as ShelterDesign}
            materialName={generatedDesign.specifications.materialSelection[0] || 'Rammed Earth (Stabilized)'}
          />
        </div>
      )}

      {currentStep !== 'generating' && currentStep !== 'results' && (
        <div className="flex justify-between pt-4">
          <button
            onClick={handleBack}
            disabled={currentStep === 'location'}
            className="px-6 py-2.5 bg-slate-700 text-white font-medium rounded-lg hover:bg-slate-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          {currentStep === 'review' ? (
            <button
              onClick={handleGenerateDesign}
              className="px-8 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold rounded-lg hover:from-indigo-400 hover:to-purple-500 transition flex items-center gap-2 shadow-lg shadow-indigo-500/20"
            >
              <Sparkles className="w-4 h-4" /> Generate Design
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-6 py-2.5 bg-indigo-500 text-white font-medium rounded-lg hover:bg-indigo-400 transition flex items-center gap-2"
            >
              Next <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {currentStep === 'results' && (
        <div className="flex justify-center pt-4">
          <button
            onClick={() => {
              setCurrentStep('location');
              setGeneratedDesign(null);
              setSelectedLocation(null);
            }}
            className="px-6 py-2.5 bg-slate-700 text-white font-medium rounded-lg hover:bg-slate-600 transition"
          >
            Start New Design
          </button>
        </div>
      )}
    </div>
  );
}
