import React from "react";
import { useDesignStore } from "../../store/designStore";
import {
  Home,
  CloudSun,
  Hammer,
  Activity,
  Cpu,
  Scale,
  Layers,
  TrendingUp,
  Box,
  SquareDashedBottom,
  CheckCircle2,
  FileText,
  Thermometer,
} from "lucide-react";

interface NavGroup {
  label: string;
  items: {
    id: string;
    label: string;
    icon: React.ReactNode;
    badge?: string;
  }[];
}

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, selectedCity, simulationResult, design, loading } =
    useDesignStore();

  const navGroups: NavGroup[] = [
    {
      label: "PROJECT",
      items: [{ id: "overview", label: "Overview", icon: <Home className="w-4 h-4" /> }],
    },
    {
      label: "DESIGN",
      items: [
        { id: "climate", label: "Climate", icon: <CloudSun className="w-4 h-4" /> },
        { id: "designer", label: "Shelter Designer", icon: <Hammer className="w-4 h-4" /> },
      ],
    },
    {
      label: "ANALYZE",
      items: [
        { id: "simulation", label: "Simulation", icon: <Activity className="w-4 h-4" /> },
        { id: "optimization", label: "Optimization", icon: <Cpu className="w-4 h-4" />, badge: "AI" },
        { id: "compare", label: "Compare", icon: <Scale className="w-4 h-4" /> },
        { id: "materials", label: "Materials", icon: <Layers className="w-4 h-4" /> },
        { id: "sensitivity", label: "Sensitivity", icon: <TrendingUp className="w-4 h-4" /> },
      ],
    },
    {
      label: "VISUALIZE",
      items: [
        { id: "twin3d", label: "3D Digital Twin", icon: <Box className="w-4 h-4" /> },
        { id: "floorplan", label: "Floorplan", icon: <SquareDashedBottom className="w-4 h-4" /> },
      ],
    },
    {
      label: "VERIFY",
      items: [
        { id: "validation", label: "Validation", icon: <CheckCircle2 className="w-4 h-4" />, badge: "ISO" },
      ],
    },
    {
      label: "DELIVER",
      items: [
        { id: "report", label: "Engineering Report", icon: <FileText className="w-4 h-4" /> },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col h-screen shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-black tracking-wider text-sky-400">
              THERMOSHELTER
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-mono tracking-tight mt-0.5">
            SIH Passive Shelter Engineering
          </p>
        </div>
        <span className="px-2 py-0.5 bg-sky-950/70 border border-sky-800/60 rounded text-[10px] font-mono text-sky-400 font-semibold">
          v2.4
        </span>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1">
            <div className="px-3 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              {group.label}
            </div>
            {group.items.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={isActive ? "text-sky-400" : "text-slate-500"}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono font-bold bg-sky-950 text-sky-400 border border-sky-800/60 px-1.5 py-0.2 rounded">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Persistent Bottom Status Panel */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40 text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Thermometer className="w-3.5 h-3.5 text-sky-400" />
            <span>Climate:</span>
          </span>
          <span
            className={`font-semibold uppercase font-mono px-2 py-0.5 rounded border text-[11px] ${
              selectedCity
                ? "text-white bg-slate-800 border-slate-700"
                : "text-amber-400 bg-amber-950/40 border-amber-800/80 animate-pulse"
            }`}
          >
            {selectedCity ? selectedCity : "Choose location"}
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span>Design status:</span>
          <span className="text-sky-300 font-mono text-[11px]">
            {design.length.toFixed(1)}m × {design.width.toFixed(1)}m ({design.roofType})
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span>Simulation:</span>
          {loading.simulation ? (
            <span className="text-amber-400 font-mono text-[11px] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
              Computing...
            </span>
          ) : simulationResult ? (
            <span className="text-emerald-400 font-mono text-[11px] font-semibold">
              {simulationResult.comfort_percentage.toFixed(0)}% Comfort
            </span>
          ) : (
            <span className="text-slate-500 font-mono text-[11px]">
              {selectedCity ? "Ready to simulate" : "Awaiting location"}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
};
