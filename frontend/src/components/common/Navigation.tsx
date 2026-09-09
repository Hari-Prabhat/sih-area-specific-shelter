import React from 'react';
import type { AppViewMode } from '../../types';
import {
  Compass,
  CloudSun,
  Cpu,
  GitCompare,
  Layers,
  FileCode,
  FileSpreadsheet,
} from 'lucide-react';

interface NavigationProps {
  currentView: AppViewMode;
  onViewChange: (view: AppViewMode) => void;
}

const NAV_ITEMS: { id: AppViewMode; label: string; icon: React.ElementType; isPrimary?: boolean }[] = [
  { id: 'design', label: 'Design', icon: Compass, isPrimary: true },
  { id: 'climate', label: 'Climate', icon: CloudSun },
  { id: 'simulation', label: 'Simulation', icon: Cpu },
  { id: 'compare', label: 'Compare', icon: GitCompare },
  { id: 'materials', label: 'Materials', icon: Layers },
  { id: 'blueprint', label: 'Blueprint', icon: FileCode },
  { id: 'report', label: 'Report', icon: FileSpreadsheet },
];

export const Navigation: React.FC<NavigationProps> = ({ currentView, onViewChange }) => {
  return (
    <nav className="bg-slate-950 border-b border-slate-800 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto flex items-center space-x-1 overflow-x-auto py-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onViewChange(item.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono-data font-semibold tracking-wider uppercase transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
              {item.isPrimary && (
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 inline-block" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
