import React from 'react';
import type { AppViewMode } from '../../types';
import {
  CloudSun,
  Cpu,
  GitCompare,
  Layers,
  FileCode,
  FileSpreadsheet,
  ArrowRight,
  Shield,
} from 'lucide-react';

interface PlaceholderPageProps {
  view: AppViewMode;
  onNavigateToDesign: () => void;
}

const PLACEHOLDER_DETAILS: Record<
  Exclude<AppViewMode, 'design'>,
  {
    title: string;
    subtitle: string;
    icon: React.ElementType;
    backendModule: string;
    description: string;
    capabilities: string[];
  }
> = {
  climate: {
    title: 'Climate & Microclimate Analysis Engine',
    subtitle: 'High-altitude diurnal solar radiation & EPW meteorological viewer',
    icon: CloudSun,
    backendModule: 'services/climate_service.py',
    description:
      'Provides high-resolution seasonal solar angles, hourly ambient temperatures, wind rose vectors, and heating/cooling degree-day calculations for Ladakh and multi-climatic target regions.',
    capabilities: [
      'Direct Normal Irradiance (DNI) and Diffuse Horizontal Irradiance (DHI) analysis',
      'EPW weather dataset inspector across Leh, Kargil, Srinagar, Delhi, and Jaisalmer',
      'Diurnal temperature range (DTR) extreme fluctuation modeling',
      'Passive heating requirement index (PHRI) calculations',
    ],
  },
  simulation: {
    title: 'Transient Thermal Simulation Workbench',
    subtitle: '168-Hour Forward Euler Single-Zone ODE Solver',
    icon: Cpu,
    backendModule: 'services/simulation_service.py & services/thermal.py',
    description:
      'Solves dynamic heat balance across envelope boundaries, internal air volume, infiltration losses, solar heat gains through fenestration, and thermal mass capacitance over continuous 7-day cycles.',
    capabilities: [
      'Hourly indoor operative temperature profile curves',
      'Comfort hour band validation (18°C–24°C thermal envelope)',
      'Sub-zero freeze vulnerability and degree-hours computation',
      'Transient wall heat flux and nocturnal radiant exchange breakdown',
    ],
  },
  compare: {
    title: 'Parametric Comparison & Multi-Model Benchmarking',
    subtitle: 'Baseline vs Optimized Envelope Evaluation',
    icon: GitCompare,
    backendModule: 'services/optimize.py & services/comfort.py',
    description:
      'Benchmarks alternative structural morphologies, roof angles, and insulation packages side-by-side against baseline military and emergency relief standard shelters.',
    capabilities: [
      'Optuna TPE Bayesian multi-objective optimization results display',
      'Discomfort degree-hours reduction delta comparison',
      'Material cost vs thermal resistance trade-off frontier (Pareto curve)',
      'Prefabricated modular panel vs vernacular high-mass performance',
    ],
  },
  materials: {
    title: 'Envelope Materials & Assembly Database',
    subtitle: 'IS 3792 / ASHRAE Thermophysical Property Catalog',
    icon: Layers,
    backendModule: 'services/material_service.py & data/materials/materials.json',
    description:
      'Explores physical properties including thermal conductivity (k), volumetric density (ρ), specific heat capacity (Cp), and surface emissivity across indigenous and engineered materials.',
    capabilities: [
      'Ladakh mud brick, rammed earth, and stone masonry thermophysical profiles',
      'Polyurethane (PUF), EPS, rockwool, and aerogel insulation catalogs',
      'Double and triple low-e argon-filled glazing assemblies (U-value & SHGC)',
      'Embodied carbon and regional logistical availability ratings',
    ],
  },
  blueprint: {
    title: 'Architectural Blueprint & Engineering Schematics',
    subtitle: 'Dimensioned CAD Detailing & Construction Vector Graphics',
    icon: FileCode,
    backendModule: 'Future CAD Vector Generator (ShelterDesign Contract)',
    description:
      'Generates exact structural orthographic projections, wall section drawings, passive ventilation stack details, and foundation anchoring schedules directly from synthesized shelter specifications.',
    capabilities: [
      'Parametric floor plans with interior functional zoning',
      'South-facing Trombe wall and fenestration framing details',
      'Snow-shedding 40° pitched roof truss connection schedules',
      'DXF / SVG vector export for field fabrication',
    ],
  },
  report: {
    title: 'Executive Engineering Report & Audit Export',
    subtitle: 'Standardized Passive Shelter Certification Documentation',
    icon: FileSpreadsheet,
    backendModule: 'Future PDF/Docx Synthesis Pipeline',
    description:
      'Compiles the complete shelter specification, site profile, compliance audits (SP 41 & ECBC-R standards), and thermal risk assessments into a publication-grade engineering audit report.',
    capabilities: [
      'Complete ShelterDesign specification audit trail',
      'Thermal comfort compliance certification',
      'Bill of materials (BOM) estimation and transport volume breakdown',
      'Field deployment checklists and winterization protocols',
    ],
  },
};

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  view,
  onNavigateToDesign,
}) => {
  if (view === 'design') return null;

  const info = PLACEHOLDER_DETAILS[view];
  const Icon = info.icon;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="bg-slate-900/80 border border-slate-700/80 rounded-xl p-8 shadow-2xl space-y-6">
        {/* Module Header */}
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 shrink-0">
            <Icon className="w-8 h-8" />
          </div>
          <div>
            <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
              ENGINEERING MODULE BOUNDARY
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white font-mono-data tracking-tight">
              {info.title}
            </h2>
            <p className="text-xs text-slate-400 font-mono-data mt-0.5">
              {info.subtitle}
            </p>
          </div>
        </div>

        {/* Backend coupling indicator */}
        <div className="bg-slate-950/70 border border-slate-800 rounded p-3 text-xs font-mono-data text-slate-300 flex items-center gap-2">
          <Shield className="w-4 h-4 text-sky-400 shrink-0" />
          <span>Backend Target Integration: <code className="text-sky-300">{info.backendModule}</code></span>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed">{info.description}</p>

        {/* Planned Capabilities */}
        <div>
          <h4 className="text-xs font-mono-data uppercase text-slate-400 tracking-wider mb-2">
            Planned Technical Capabilities:
          </h4>
          <ul className="space-y-2">
            {info.capabilities.map((cap, idx) => (
              <li
                key={idx}
                className="text-xs font-mono-data text-slate-300 flex items-start gap-2 bg-slate-950/40 p-2 rounded border border-slate-800/60"
              >
                <span className="text-sky-400 font-bold">›</span>
                <span>{cap}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Navigation Action */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono-data text-slate-500">
            Current Active Studio: <b>Design</b>
          </span>

          <button
            type="button"
            onClick={onNavigateToDesign}
            className="flex items-center gap-2 px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white font-mono-data text-xs font-bold transition-colors cursor-pointer"
          >
            <span>GO TO DESIGN STUDIO</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
