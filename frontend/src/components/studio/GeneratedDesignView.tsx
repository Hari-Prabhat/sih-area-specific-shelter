import React from 'react';
import { useDesignStudio } from '../../context';
import { DesignDNA } from './DesignDNA';
import { SiteProfile } from './SiteProfile';
import { ShelterViewer } from '../future/ShelterViewer';
import { EngineeringBlueprint } from '../future/EngineeringBlueprint';
import { DataStatusBadge } from '../common/DataStatusBadge';
import {
  ArrowLeft,
  RotateCcw,
  ShieldAlert,
  Layers,
  Sparkles,
  Box,
  Compass,
  CheckCircle2,
  Info,
} from 'lucide-react';

export const GeneratedDesignView: React.FC = () => {
  const { generatedDesign, goToStep, resetStudio } = useDesignStudio();

  if (!generatedDesign) {
    return (
      <div className="p-8 text-center text-slate-400 font-mono-data">
        No synthesized design active. Please complete the design studio requirements.
      </div>
    );
  }

  const { geometry, materials, climateProfile } = generatedDesign;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Status Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => goToStep(5)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white font-mono-data text-xs transition-colors border border-slate-700"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>MODIFY REQUIREMENTS</span>
          </button>

          <button
            type="button"
            onClick={resetStudio}
            className="flex items-center gap-1 px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 font-mono-data text-xs transition-colors border border-slate-800"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>NEW DESIGN</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <DataStatusBadge status={generatedDesign.status} size="md" />
        </div>
      </div>

      {/* Main Title Banner */}
      <div className="bg-slate-900/90 border border-slate-700 rounded-xl p-6 shadow-2xl relative overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono-data uppercase tracking-widest text-sky-400">
                SYNTHESIZED PASSIVE SPECIFICATION
              </span>
              <span className="text-[10px] font-mono-data bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2 py-0.5 rounded font-bold">
                STAGE-1 PROTOTYPE
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white font-mono-data tracking-tight">
              {generatedDesign.designId}
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl">
              {generatedDesign.designName} — Engineered for {generatedDesign.requirements.mission.occupants} occupants under {generatedDesign.requirements.mission.deploymentType.toLowerCase()} deployment constraints.
            </p>
          </div>

          <div className="text-right font-mono-data text-xs text-slate-400">
            <div>TARGET REGION: <b className="text-white">{climateProfile.name}</b></div>
            <div>STATUS: <b className="text-rose-400">DEMO / MOCK DATA</b></div>
          </div>
        </div>

        {/* Prominent Demo Notice */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center gap-2 text-xs font-mono-data text-amber-300/90">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <b>NOTICE:</b> Initial synthesis payload generated via heuristic design contracts. Numerical simulation and Bayesian optimization pending backend simulation execution.
          </span>
        </div>
      </div>

      {/* Section 5: Reusable Design DNA Component */}
      <DesignDNA design={generatedDesign} />

      {/* Section 6: Reusable Site Profile Component */}
      <SiteProfile profile={climateProfile} />

      {/* Section 4 Detailed Breakdown: Climate, Strategy, Geometry, Orientation, Envelope, Insulation, Glazing, Thermal Mass, Ventilation */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Card: Passive Strategy */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase">
            <Sparkles className="w-4 h-4" />
            Passive Thermal Strategy
          </div>
          <p className="text-sm font-semibold text-slate-100 leading-snug">
            {generatedDesign.passiveStrategy}
          </p>
          <div className="text-xs text-slate-400 pt-2 border-t border-slate-800">
            Engineered to maximize thermal delay, prevent sub-zero midnight freezing, and capture solar irradiation.
          </div>
        </div>

        {/* Card: Geometry & Orientation */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase">
            <Box className="w-4 h-4" />
            Geometry & Orientation
          </div>
          <div className="space-y-1 text-xs font-mono-data">
            <div className="flex justify-between">
              <span className="text-slate-400">Dimensions:</span>
              <span className="text-slate-200 font-bold">{geometry.lengthM}m × {geometry.widthM}m × {geometry.heightM}m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Floor Area:</span>
              <span className="text-slate-200 font-bold">{geometry.footprintM2} m²</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Roof Configuration:</span>
              <span className="text-slate-200 font-bold capitalize">{geometry.roofType} ({geometry.roofSlopeDeg || 0}°)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Solar Orientation:</span>
              <span className="text-slate-200 font-bold">{geometry.orientation}</span>
            </div>
          </div>
        </div>

        {/* Card: Envelope & Insulation */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase">
            <Layers className="w-4 h-4" />
            Envelope Assembly & Insulation
          </div>
          <div className="space-y-1.5 text-xs font-mono-data">
            <div>
              <span className="text-slate-400 block text-[11px]">WALL ASSEMBLY:</span>
              <span className="text-slate-200">{materials.wallMaterial}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">INSULATION CORE:</span>
              <span className="text-slate-200 font-bold">{materials.insulationThicknessMm} mm {materials.insulationType}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">ROOF ASSEMBLY:</span>
              <span className="text-slate-200">{materials.roofMaterial}</span>
            </div>
          </div>
        </div>

        {/* Card: Glazing */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase">
            <Compass className="w-4 h-4" />
            Glazing & Fenestration
          </div>
          <p className="text-xs text-slate-200 font-mono-data">
            {materials.glazingType}
          </p>
          <div className="text-xs font-mono-data text-slate-400 pt-2 border-t border-slate-800 flex justify-between">
            <span>Aperture Area:</span>
            <span className="text-slate-200 font-bold">{geometry.windowAreaM2} m² (South Facade)</span>
          </div>
        </div>

        {/* Card: Thermal Mass */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase">
            <Sparkles className="w-4 h-4" />
            Thermal Mass Core
          </div>
          <div className="text-sm font-bold text-white font-mono-data flex items-center gap-2">
            <span>LEVEL: {materials.thermalMassLevel}</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            High volumetric heat capacity substrate dampens diurnal swings, absorbing daytime peak energy and re-radiating during night.
          </p>
        </div>

        {/* Card: Ventilation */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono-data text-sky-400 uppercase">
            <Info className="w-4 h-4" />
            Ventilation & Air Exchange
          </div>
          <p className="text-xs text-slate-200 font-mono-data">
            {generatedDesign.ventilationStrategy}
          </p>
          <p className="text-xs text-slate-400 leading-relaxed pt-1">
            Minimizes uncontrolled exfiltration while preventing moisture condensation and ensuring hygienic fresh air volume.
          </p>
        </div>
      </div>

      {/* Rationale List */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5">
        <h4 className="text-xs font-mono-data uppercase tracking-wider text-sky-400 mb-3 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          Evidence-Based Design Rationale
        </h4>
        <ul className="space-y-2">
          {generatedDesign.designRationale.map((rationale, idx) => (
            <li
              key={idx}
              className="text-xs text-slate-300 font-mono-data leading-relaxed flex items-start gap-2"
            >
              <span className="text-sky-400 font-bold shrink-0">[{idx + 1}]</span>
              <span>{rationale}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Section 17 & 18: Clean Placeholders for 3D and Blueprint */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
        <ShelterViewer design={generatedDesign} />
        <EngineeringBlueprint design={generatedDesign} />
      </div>
    </div>
  );
};
