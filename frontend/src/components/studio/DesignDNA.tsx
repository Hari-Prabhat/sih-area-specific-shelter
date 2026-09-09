import React from 'react';
import type { ShelterDesign } from '../../types';
import { Dna, Compass, Box, ShieldCheck, ThermometerSnowflake, Wind, SunMedium, Sparkles } from 'lucide-react';
import { DataStatusBadge } from '../common/DataStatusBadge';

interface DesignDNAProps {
  design: ShelterDesign;
  className?: string;
}

export const DesignDNA: React.FC<DesignDNAProps> = ({ design, className = '' }) => {
  const { dna, status } = design;

  const DNA_METRICS = [
    {
      label: 'CLIMATE',
      value: dna.climate,
      icon: ThermometerSnowflake,
      hint: 'Target thermal macroclimate categorization',
    },
    {
      label: 'STRATEGY',
      value: dna.strategy,
      icon: SunMedium,
      hint: 'Primary thermodynamic bioclimatic driver',
    },
    {
      label: 'GEOMETRY',
      value: dna.geometry,
      icon: Box,
      hint: 'Surface-area to volume ratio envelope archetype',
    },
    {
      label: 'ORIENTATION',
      value: dna.orientation,
      icon: Compass,
      hint: 'Solar azimuth aperture targeting',
    },
    {
      label: 'ENVELOPE',
      value: dna.envelope,
      icon: ShieldCheck,
      hint: 'Composite thermal resistance boundary grade',
    },
    {
      label: 'THERMAL MASS',
      value: dna.thermalMass,
      icon: Sparkles,
      hint: 'Internal capacitance diurnal damping capability',
    },
    {
      label: 'VENTILATION',
      value: dna.ventilation,
      icon: Wind,
      hint: 'Air-exchange and infiltration control architecture',
    },
  ];

  return (
    <div
      className={`bg-slate-900/90 border border-slate-700/80 rounded-lg p-5 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Dna className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono-data tracking-widest text-sky-400">
              Bioclimatic Specification Pattern
            </div>
            <h3 className="text-lg font-bold tracking-tight text-white font-mono-data">
              {dna.code || design.designId}
            </h3>
          </div>
        </div>

        <DataStatusBadge status={status} size="sm" />
      </div>

      {/* Structured DNA Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {DNA_METRICS.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="bg-slate-950/60 border border-slate-800 rounded p-3 hover:border-slate-700 transition-colors"
              title={item.hint}
            >
              <div className="flex items-center gap-1.5 text-[11px] font-mono-data uppercase tracking-wider text-slate-400 mb-1">
                <Icon className="w-3.5 h-3.5 text-sky-400" />
                <span>{item.label}</span>
              </div>
              <div className="text-sm font-semibold text-slate-100 font-mono-data">
                {item.value}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
