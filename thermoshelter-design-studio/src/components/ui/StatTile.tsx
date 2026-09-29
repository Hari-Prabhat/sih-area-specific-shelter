import { ReactNode } from 'react';

interface StatTileProps {
  icon?: ReactNode;
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  /** Tailwind color accent for the icon, e.g. 'text-amber-400'. */
  accent?: string;
}

/**
 * D1 primitive: one key-performance tile. Used by the Results KPI row and the
 * persistent context strip so metric presentation is consistent studio-wide.
 */
export default function StatTile({ icon, label, value, sub, accent = 'text-amber-400' }: StatTileProps) {
  return (
    <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-4">
      {icon && <div className={`mb-2 ${accent}`}>{icon}</div>}
      <p className="text-xs text-slate-300 uppercase tracking-wider font-medium">{label}</p>
      <p className="text-xl font-bold text-slate-100 mt-1">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}
