import React from 'react';
import type { ClimateProfile } from '../../types';
import { MapPin, Mountain, Sun, Snowflake, ArrowUpDown, ShieldCheck } from 'lucide-react';
import { DataStatusBadge } from '../common/DataStatusBadge';

interface SiteProfileProps {
  profile: ClimateProfile;
  className?: string;
  isCompact?: boolean;
}

export const SiteProfile: React.FC<SiteProfileProps> = ({
  profile,
  className = '',
  isCompact = false,
}) => {
  const confidenceColor =
    profile.dataConfidence === 'High'
      ? 'text-emerald-400 border-emerald-500/40 bg-emerald-950/40'
      : profile.dataConfidence === 'Medium'
      ? 'text-amber-400 border-amber-500/40 bg-amber-950/40'
      : 'text-rose-400 border-rose-500/40 bg-rose-950/40';

  return (
    <div
      className={`bg-slate-900/90 border border-slate-700/80 rounded-lg p-5 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-800">
        <div>
          <div className="text-[10px] uppercase font-mono-data tracking-widest text-sky-400">
            Geographic Boundary Analysis
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-1.5">
              <MapPin className="w-4 h-4 text-sky-400" />
              SITE PROFILE: {profile.name}
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <DataStatusBadge status={profile.status} size="sm" />
          <span
            className={`text-[11px] font-mono-data font-semibold uppercase px-2 py-0.5 rounded border ${confidenceColor}`}
            title="Meteorological dataset fidelity and station distance confidence"
          >
            CONFIDENCE: {profile.dataConfidence}
          </span>
        </div>
      </div>

      {/* Profile Metrics Grid */}
      <div
        className={`grid gap-3 ${
          isCompact
            ? 'grid-cols-2 sm:grid-cols-3'
            : 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6'
        }`}
      >
        {/* Elevation */}
        <div className="bg-slate-950/60 border border-slate-800 rounded p-2.5">
          <div className="flex items-center gap-1 text-[11px] font-mono-data text-slate-400 uppercase mb-0.5">
            <Mountain className="w-3.5 h-3.5 text-sky-400" />
            Elevation
          </div>
          <div className="text-sm font-semibold font-mono-data text-slate-100">
            {profile.elevationM !== null && profile.elevationM !== undefined
              ? `${profile.elevationM} m`
              : '—'}
          </div>
        </div>

        {/* Climate Type */}
        <div className="bg-slate-950/60 border border-slate-800 rounded p-2.5 sm:col-span-2">
          <div className="flex items-center gap-1 text-[11px] font-mono-data text-slate-400 uppercase mb-0.5">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            Climate Classification
          </div>
          <div className="text-sm font-semibold text-slate-100 truncate" title={profile.climateType}>
            {profile.climateType}
          </div>
        </div>

        {/* Solar Resource */}
        <div className="bg-slate-950/60 border border-slate-800 rounded p-2.5">
          <div className="flex items-center gap-1 text-[11px] font-mono-data text-slate-400 uppercase mb-0.5">
            <Sun className="w-3.5 h-3.5 text-amber-400" />
            Solar Resource
          </div>
          <div className="text-sm font-semibold font-mono-data text-slate-100">
            {profile.solarResource}
          </div>
        </div>

        {/* Winter Severity */}
        <div className="bg-slate-950/60 border border-slate-800 rounded p-2.5">
          <div className="flex items-center gap-1 text-[11px] font-mono-data text-slate-400 uppercase mb-0.5">
            <Snowflake className="w-3.5 h-3.5 text-cyan-300" />
            Winter Severity
          </div>
          <div className="text-sm font-semibold font-mono-data text-slate-100">
            {profile.winterSeverity}
          </div>
        </div>

        {/* Diurnal Variation */}
        <div className="bg-slate-950/60 border border-slate-800 rounded p-2.5">
          <div className="flex items-center gap-1 text-[11px] font-mono-data text-slate-400 uppercase mb-0.5">
            <ArrowUpDown className="w-3.5 h-3.5 text-indigo-400" />
            Diurnal Variation
          </div>
          <div className="text-sm font-semibold font-mono-data text-slate-100">
            {profile.diurnalVariation}
          </div>
        </div>
      </div>

      {profile.sourceNote && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] font-mono-data text-slate-500">
          Source Baseline: {profile.sourceNote}
        </div>
      )}
    </div>
  );
};
