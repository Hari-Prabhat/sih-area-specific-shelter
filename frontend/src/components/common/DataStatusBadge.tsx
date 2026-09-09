import React from 'react';
import type { DataStatus } from '../../types';
import { Database, ShieldAlert, Cpu, Sparkles, Activity, Clock } from 'lucide-react';

interface DataStatusBadgeProps {
  status: DataStatus;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

const STATUS_CONFIG: Record<
  DataStatus,
  {
    label: string;
    description: string;
    bgClass: string;
    borderClass: string;
    textClass: string;
    icon: React.ElementType;
  }
> = {
  MEASURED: {
    label: 'MEASURED',
    description: 'Actual physical sensor or live telemetric observation',
    bgClass: 'bg-emerald-950/70',
    borderClass: 'border-emerald-500/60',
    textClass: 'text-emerald-300',
    icon: Activity,
  },
  HISTORICAL: {
    label: 'HISTORICAL',
    description: 'Calibrated historical meteorological dataset (EPW / IMD / ASHRAE)',
    bgClass: 'bg-blue-950/70',
    borderClass: 'border-blue-500/60',
    textClass: 'text-blue-300',
    icon: Clock,
  },
  ESTIMATED: {
    label: 'ESTIMATED',
    description: 'Derived or spatially interpolated geographic data',
    bgClass: 'bg-amber-950/70',
    borderClass: 'border-amber-500/60',
    textClass: 'text-amber-300',
    icon: Database,
  },
  SIMULATED: {
    label: 'SIMULATED',
    description: 'Modeled transient building physics results (Forward Euler ODE)',
    bgClass: 'bg-purple-950/70',
    borderClass: 'border-purple-500/60',
    textClass: 'text-purple-300',
    icon: Cpu,
  },
  OPTIMIZED: {
    label: 'OPTIMIZED',
    description: 'Produced by multi-objective Bayesian optimization engine',
    bgClass: 'bg-cyan-950/70',
    borderClass: 'border-cyan-500/60',
    textClass: 'text-cyan-300',
    icon: Sparkles,
  },
  DEMO_MOCK: {
    label: 'DEMO / MOCK DATA',
    description: 'Development synthetic mock specification — not live field readings',
    bgClass: 'bg-rose-950/70',
    borderClass: 'border-rose-500/60',
    textClass: 'text-rose-300',
    icon: ShieldAlert,
  },
};

export const DataStatusBadge: React.FC<DataStatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.DEMO_MOCK;
  const Icon = config.icon;

  const sizeClass =
    size === 'sm'
      ? 'text-[10px] px-2 py-0.5 tracking-wider'
      : 'text-xs px-2.5 py-1 tracking-widest';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono-data font-semibold rounded border uppercase ${config.bgClass} ${config.borderClass} ${config.textClass} ${sizeClass}`}
      title={`${config.label}: ${config.description}`}
    >
      {showIcon && <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{config.label}</span>
    </span>
  );
};
