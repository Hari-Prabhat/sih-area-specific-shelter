import React from 'react';
import { useDesignStudio } from '../../context';
import type { MissionPurpose, DeploymentType, DeploymentDuration } from '../../types';
import {
  Users,
  Shield,
  HeartPulse,
  Microscope,
  Home,
  Package,
  Radio,
  Tent,
  Clock,
  Calendar,
} from 'lucide-react';

const PURPOSES: { id: MissionPurpose; label: string; icon: React.ElementType; desc: string }[] = [
  {
    id: 'Military',
    label: 'Military',
    icon: Shield,
    desc: 'High-altitude border outposts, checkpoints, forward bases',
  },
  {
    id: 'Disaster Relief',
    label: 'Disaster Relief',
    icon: HeartPulse,
    desc: 'Rapid emergency humanitarian response & crisis refuge',
  },
  {
    id: 'Research',
    label: 'Research',
    icon: Microscope,
    desc: 'High-altitude climatological, ecological & astronomical labs',
  },
  {
    id: 'Residential',
    label: 'Residential',
    icon: Home,
    desc: 'Permanent vernacular living spaces & family habitations',
  },
  {
    id: 'Medical',
    label: 'Medical',
    icon: HeartPulse,
    desc: 'Field clinics, triage shelters & pharmaceutical temperature control',
  },
  {
    id: 'Storage',
    label: 'Storage',
    icon: Package,
    desc: 'Cold-chain equipment, dry rations, and sensitive battery caches',
  },
  {
    id: 'Command / Operations',
    label: 'Command / Operations',
    icon: Radio,
    desc: 'Tactical comms hub, server nodes, mission briefing headquarters',
  },
  {
    id: 'Temporary Accommodation',
    label: 'Temporary Accommodation',
    icon: Tent,
    desc: 'Seasonal migration, mountaineering camps, transit dormitories',
  },
];

const DEPLOYMENT_TYPES: { id: DeploymentType; label: string; desc: string }[] = [
  {
    id: 'Temporary',
    label: 'Temporary',
    desc: 'Modular lightweight panels, rapid field assembly (< 48 hrs)',
  },
  {
    id: 'Seasonal',
    label: 'Seasonal',
    desc: 'Semi-permanent structures rated for harsh winter or summer cycles',
  },
  {
    id: 'Permanent',
    label: 'Permanent',
    desc: 'High thermal inertia masonry or heavy envelope for decades',
  },
];

const DURATIONS: { id: DeploymentDuration; label: string }[] = [
  { id: 'Days', label: 'Days' },
  { id: 'Weeks', label: 'Weeks' },
  { id: 'Months', label: 'Months' },
  { id: 'Years', label: 'Years' },
];

export const Step2Mission: React.FC = () => {
  const { mission, setMissionField, errors } = useDesignStudio();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
          STEP 2 of 5 — OPERATIONAL MISSION
        </div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Define Occupancy & Mission Objectives
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Specify mission scope to automatically scale habitability volume and structural longevity constraints.
        </p>
      </div>

      {/* Occupancy Counter */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5">
        <label className="block text-xs font-mono-data uppercase text-slate-300 mb-2">
          Number of Occupants (Design Capacity):
        </label>
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-slate-950 border border-slate-700 rounded overflow-hidden">
            <button
              type="button"
              onClick={() => setMissionField('occupants', Math.max(1, mission.occupants - 1))}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-mono-data text-base font-bold transition-colors cursor-pointer"
            >
              −
            </button>
            <input
              type="number"
              min={1}
              max={100}
              value={mission.occupants}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                setMissionField('occupants', isNaN(val) ? 1 : Math.max(1, val));
              }}
              className="w-20 text-center bg-transparent py-2 text-white font-mono-data font-bold text-lg outline-none"
            />
            <button
              type="button"
              onClick={() => setMissionField('occupants', mission.occupants + 1)}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-mono-data text-base font-bold transition-colors cursor-pointer"
            >
              +
            </button>
          </div>

          <div className="text-xs text-slate-400 font-mono-data">
            <Users className="w-4 h-4 text-sky-400 inline mr-1" />
            Baseline Sizing: <b>{(Math.max(12, mission.occupants * 4.5)).toFixed(1)} m²</b> floor space
            (4.5 m²/person per SP 41 human habitability standards)
          </div>
        </div>
        {errors.occupants && (
          <p className="text-xs text-rose-400 font-mono-data font-semibold mt-2">
            ⚠ {errors.occupants}
          </p>
        )}
      </div>

      {/* Shelter Purpose Grid */}
      <div>
        <label className="block text-xs font-mono-data uppercase text-slate-300 mb-2">
          Shelter Operational Purpose:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {PURPOSES.map((item) => {
            const Icon = item.icon;
            const isSelected = mission.purpose === item.id;
            return (
              <div
                key={item.id}
                onClick={() => setMissionField('purpose', item.id)}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-sky-950/40 border-sky-500 ring-1 ring-sky-500/50 shadow-md shadow-sky-950/30'
                    : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className={`p-1.5 rounded ${
                      isSelected ? 'bg-sky-500/20 text-sky-400' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="font-bold text-sm text-white font-mono-data">{item.label}</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">{item.desc}</p>
              </div>
            );
          })}
        </div>
        {errors.purpose && (
          <p className="text-xs text-rose-400 font-mono-data font-semibold mt-1.5">
            ⚠ {errors.purpose}
          </p>
        )}
      </div>

      {/* Deployment Type & Duration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Deployment Type */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-2">
          <label className="block text-xs font-mono-data uppercase text-slate-300">
            Deployment Permanence:
          </label>
          <div className="space-y-2">
            {DEPLOYMENT_TYPES.map((dtype) => {
              const isSelected = mission.deploymentType === dtype.id;
              return (
                <div
                  key={dtype.id}
                  onClick={() => setMissionField('deploymentType', dtype.id)}
                  className={`p-2.5 rounded border cursor-pointer transition-all flex items-start justify-between ${
                    isSelected
                      ? 'bg-sky-950/40 border-sky-500'
                      : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="font-bold text-xs text-white font-mono-data">{dtype.label}</div>
                    <div className="text-[11px] text-slate-400">{dtype.desc}</div>
                  </div>
                  {isSelected && <span className="text-sky-400 text-xs font-bold font-mono-data">●</span>}
                </div>
              );
            })}
          </div>
          {errors.deploymentType && (
            <p className="text-xs text-rose-400 font-mono-data font-semibold">
              ⚠ {errors.deploymentType}
            </p>
          )}
        </div>

        {/* Deployment Duration */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-2">
          <label className="block text-xs font-mono-data uppercase text-slate-300">
            Intended Deployment Duration:
          </label>
          <div className="grid grid-cols-2 gap-2">
            {DURATIONS.map((dur) => {
              const isSelected = mission.duration === dur.id;
              return (
                <button
                  key={dur.id}
                  type="button"
                  onClick={() => setMissionField('duration', dur.id)}
                  className={`p-3 rounded border text-center transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-sky-950/40 border-sky-500 text-sky-300 font-bold'
                      : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <Calendar className="w-4 h-4 mx-auto mb-1 text-slate-400" />
                  <span className="text-xs font-mono-data uppercase">{dur.label}</span>
                </button>
              );
            })}
          </div>

          <div className="pt-2 text-[11px] font-mono-data text-slate-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span>Configured: {mission.duration} horizon</span>
          </div>
          {errors.duration && (
            <p className="text-xs text-rose-400 font-mono-data font-semibold">
              ⚠ {errors.duration}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
