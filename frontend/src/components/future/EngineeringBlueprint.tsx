import React from 'react';
import type { ShelterDesign } from '../../types';
import { Ruler, Download, Grid } from 'lucide-react';
import { DataStatusBadge } from '../common/DataStatusBadge';

interface EngineeringBlueprintProps {
  design: ShelterDesign;
  className?: string;
}

/**
 * Architectural Boundary Component for Future 2D CAD Blueprint Generation.
 * Strictly consumes structured ShelterDesign without fabricating measurements.
 */
export const EngineeringBlueprint: React.FC<EngineeringBlueprintProps> = ({
  design,
  className = '',
}) => {
  const { geometry } = design;

  return (
    <div className={`bg-slate-900/90 border border-slate-700/80 rounded-lg p-5 shadow-xl ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Ruler className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono-data tracking-widest text-amber-400">
              Technical Drafting Boundary
            </div>
            <h4 className="text-base font-bold text-white font-mono-data">
              Engineering Blueprint & Dimensioned Schematics
            </h4>
          </div>
        </div>

        <DataStatusBadge status={design.status} size="sm" />
      </div>

      {/* Blueprint Grid Canvas Area */}
      <div className="relative aspect-video sm:aspect-21/9 bg-[#0b1b2b] border border-cyan-900/60 rounded-lg p-6 flex flex-col items-center justify-center text-center overflow-hidden">
        {/* Blueprint Graph Lines Pattern */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(to right, rgba(56, 189, 248, 0.4) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(56, 189, 248, 0.4) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px',
          }}
        />

        <div className="relative z-10 max-w-md">
          <div className="inline-flex p-3 rounded-full bg-cyan-950/80 border border-cyan-700/50 text-cyan-400 mb-3">
            <Grid className="w-7 h-7" />
          </div>

          <h5 className="text-sm font-semibold text-cyan-200 uppercase font-mono-data tracking-wider mb-1">
            2D CAD Vector Blueprint Export Boundary
          </h5>

          <p className="text-xs text-cyan-300/70 leading-relaxed mb-4">
            Component prepared to ingest <code className="text-cyan-200 font-mono-data">ShelterDesign</code> for
            SVG / DXF architectural floor plans, wall section detailing, and glazing schedule dimensioning.
          </p>

          {/* Bound Engineering Blueprint Dimensions */}
          <div className="inline-grid grid-cols-2 sm:grid-cols-4 gap-2 bg-cyan-950/60 border border-cyan-800/60 rounded p-2.5 text-left font-mono-data text-[11px] text-cyan-100">
            <div>
              <span className="text-cyan-400/70 block text-[10px]">FLOOR AREA</span>
              <span className="font-bold">{geometry.footprintM2} m²</span>
            </div>
            <div>
              <span className="text-cyan-400/70 block text-[10px]">ASPECT RATIO</span>
              <span className="font-bold">{geometry.aspectRatio}:1</span>
            </div>
            <div>
              <span className="text-cyan-400/70 block text-[10px]">WINDOW APERTURE</span>
              <span className="font-bold">{geometry.windowAreaM2} m²</span>
            </div>
            <div>
              <span className="text-cyan-400/70 block text-[10px]">INTERNAL VOLUME</span>
              <span className="font-bold">{geometry.volumeM3} m³</span>
            </div>
          </div>
        </div>

        {/* Blueprint Action Button Placeholder */}
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          <button
            type="button"
            disabled
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono-data bg-cyan-950/80 border border-cyan-800 text-cyan-400/60 rounded cursor-not-allowed"
            title="CAD export will activate once 2D drafting engine is integrated"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT DXF/SVG</span>
          </button>
        </div>
      </div>
    </div>
  );
};
