import { CheckCircle, Target, Users, Zap, AlertCircle } from 'lucide-react';
import Card from './ui/Card';
import Button from './ui/Button';
import { useStudioState, MissionConfig } from '../store/useStudioState';

const PURPOSES = [
  'Disaster Relief',
  'Military',
  'Research',
  'Residential',
  'Medical',
  'Storage',
  'Command / Operations',
  'Temporary Accommodation',
] as const;

const DEPLOYMENT_TYPES: MissionConfig['deploymentType'][] = ['Temporary', 'Seasonal', 'Permanent'];

const PRIORITY_OPTIONS: { key: keyof MissionConfig['priorities']; label: string; description: string }[] = [
  { key: 'thermalComfort', label: 'Thermal Comfort', description: 'Maintain comfortable indoor temperatures' },
  { key: 'energyIndependence', label: 'Energy Independence', description: 'Minimize external energy dependency' },
  { key: 'lowCost', label: 'Low Cost', description: 'Minimize construction and operational costs' },
  { key: 'lowWeight', label: 'Low Weight', description: 'Lightweight structure for transport' },
  { key: 'rapidDeployment', label: 'Rapid Deployment', description: 'Quick assembly and setup time' },
  { key: 'durability', label: 'Durability', description: 'Long-term structural integrity' },
];

/**
 * Mission stage (D2). The useful concepts of the retired DesignStudio mock —
 * occupants, purpose, deployment type, mobility, design priorities — now edit
 * the SHARED studio state. Occupants feed the canonical simulation and
 * optimization payloads directly; the mock's fabricated "Generate Design"
 * simulation (setTimeout + invented specification) is gone.
 */
export default function MissionStage() {
  const { mission, setMissionField, togglePriority, design, setStage } = useStudioState();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
          <Users className="w-5 h-5 text-amber-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Mission Requirements</h2>
          <p className="text-sm text-slate-400">
            Operational purpose, occupancy and design priorities for this shelter
          </p>
        </div>
      </div>

      <Card ariaLabel="Occupancy and deployment">
        <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <Users className="w-4 h-4 text-amber-400" /> Occupancy & Deployment
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label htmlFor="mission-occupants" className="text-xs font-medium text-slate-400">
              Number of Occupants
            </label>
            <input
              id="mission-occupants"
              type="number"
              min={1}
              max={50}
              value={mission.occupants}
              onChange={(e) => setMissionField('occupants', Math.max(1, parseInt(e.target.value, 10) || 1))}
              className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 focus:outline-none focus:border-amber-500/60"
            />
            <p className="text-xs text-slate-500">
              Drives internal heat gains and ventilation sizing in the Python simulation.
            </p>
          </div>
          <div className="space-y-1.5">
            <label htmlFor="mission-duration" className="text-xs font-medium text-slate-400">
              Deployment Duration (months)
            </label>
            <input
              id="mission-duration"
              type="number"
              min={1}
              value={mission.durationMonths}
              onChange={(e) => setMissionField('durationMonths', Math.max(1, parseInt(e.target.value, 10) || 1))}
              className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-slate-100 focus:outline-none focus:border-amber-500/60"
            />
          </div>
        </div>

        <div className="mt-5">
          <p className="text-sm font-medium text-slate-300 mb-2">Shelter Purpose</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2" role="group" aria-label="Shelter purpose">
            {PURPOSES.map((purpose) => (
              <button
                key={purpose}
                type="button"
                onClick={() => setMissionField('purpose', purpose)}
                aria-pressed={mission.purpose === purpose}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                  mission.purpose === purpose
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                    : 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                }`}
              >
                {purpose}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-5">
          <p className="text-sm font-medium text-slate-300 mb-2">Deployment Type</p>
          <div className="grid grid-cols-3 gap-2" role="group" aria-label="Deployment type">
            {DEPLOYMENT_TYPES.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setMissionField('deploymentType', type)}
                aria-pressed={mission.deploymentType === type}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                  mission.deploymentType === type
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                    : 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <label className="mt-5 flex items-center gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={mission.mobilityRequired}
            onChange={(e) => setMissionField('mobilityRequired', e.target.checked)}
            className="w-4 h-4 accent-amber-500"
          />
          <span className="text-sm text-slate-200">Mobility required (relocatable shelter)</span>
        </label>
      </Card>

      <Card ariaLabel="Design priorities">
        <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <Target className="w-4 h-4 text-amber-400" /> Design Priorities
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {PRIORITY_OPTIONS.map((option) => {
            const active = mission.priorities[option.key];
            return (
              <button
                key={option.key}
                type="button"
                onClick={() => togglePriority(option.key)}
                aria-pressed={active}
                className={`p-4 rounded-lg border transition-all text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                  active ? 'bg-amber-500/15 border-amber-500/40' : 'bg-slate-700/30 border-slate-600/30 hover:bg-slate-700/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className={`font-semibold text-sm ${active ? 'text-amber-300' : 'text-slate-300'}`}>
                      {option.label}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">{option.description}</p>
                  </div>
                  {active && <CheckCircle className="w-5 h-5 text-amber-400 shrink-0" aria-hidden="true" />}
                </div>
              </button>
            );
          })}
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Priorities are recorded with the mission and shown on the engineering report; optimization
          weights remain under your direct control in the Optimization stage.
        </p>
      </Card>

      <Card ariaLabel="Mission summary">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" /> Mission Summary
        </h3>
        <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <dt className="text-xs text-slate-500 uppercase">Occupants</dt>
            <dd className="text-slate-100 font-semibold mt-1">{mission.occupants} persons</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500 uppercase">Purpose</dt>
            <dd className="text-slate-100 font-semibold mt-1">{mission.purpose}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500 uppercase">Deployment</dt>
            <dd className="text-slate-100 font-semibold mt-1">{mission.deploymentType}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500 uppercase">Baseline Geometry</dt>
            <dd className="text-slate-100 font-semibold mt-1">
              {design.length} × {design.width} × {design.height} m
            </dd>
          </div>
        </dl>
      </Card>

      <div className="flex justify-end">
        <Button onClick={() => setStage('design')}>Continue to Geometry &amp; Envelope</Button>
      </div>
    </div>
  );
}
