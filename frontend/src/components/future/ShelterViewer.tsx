import React from 'react';
import type { ShelterDesign } from '../../types';
import { Box, Eye, Layers, Maximize2, RotateCcw } from 'lucide-react';
import { DataStatusBadge } from '../common/DataStatusBadge';

interface ShelterViewerProps {
  design: ShelterDesign;
  className?: string;
}

/**
 * Architectural Boundary Component for Future 3D Digital Twin Integration.
 * Strictly consumes structured ShelterDesign without hard-coded geometries.
 * Future Architecture: ShelterDesign -> 3D WebGL/Three.js Renderer.
 */
export const ShelterViewer: React.FC<ShelterViewerProps> = ({ design, className = '' }) => {
  const { geometry } = design;

  return (
    <div className={`bg-slate-900/90 border border-slate-700/80 rounded-lg p-5 shadow-xl ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Box className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono-data tracking-widest text-sky-400">
              3D Digital Twin Viewer Boundary
            </div>
            <h4 className="text-base font-bold text-white font-mono-data">
              CAD & Spatial Envelope Viewport
            </h4>
          </div>
        </div>

        <DataStatusBadge status={design.status} size="sm" />
      </div>

      {/* Simulated 3D Viewport Placeholder Container */}
      <div className="relative aspect-video sm:aspect-21/9 bg-slate-950 border border-dashed border-slate-800 rounded-lg overflow-hidden flex flex-col items-center justify-center p-6 text-center">
        {/* Isometric Grid Background Effect */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, #38bdf8 1px, transparent 0)`,
            backgroundSize: '24px 24px',
          }}
        />

        <div className="relative z-10 max-w-md">
          <div className="inline-flex p-3 rounded-full bg-slate-900 border border-slate-700 text-sky-400 mb-3 shadow-inner">
            <Layers className="w-7 h-7 animate-pulse" />
          </div>

          <h5 className="text-sm font-semibold text-white uppercase font-mono-data tracking-wider mb-1">
            ShelterDesign 3D Renderer Integration Boundary
          </h5>

          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            Component cleanly bound to <code className="text-sky-300 font-mono-data">ShelterDesign</code>.
            Ready for Three.js / WebGL / Plotly interactive mesh stream based on dynamic calculated dimensions.
          </p>

          {/* Bound Engineering Dimensions */}
          <div className="inline-grid grid-cols-3 gap-3 bg-slate-900/80 border border-slate-800 rounded px-4 py-2 text-left font-mono-data text-[11px]">
            <div>
              <span className="text-slate-500 block">ENVELOPE</span>
              <span className="text-slate-200 font-bold">{geometry.lengthM}m × {geometry.widthM}m × {geometry.heightM}m</span>
            </div>
            <div>
              <span className="text-slate-500 block">ROOF FORM</span>
              <span className="text-slate-200 font-bold capitalize">{geometry.roofType} ({geometry.roofSlopeDeg || 0}°)</span>
            </div>
            <div>
              <span className="text-slate-500 block">ORIENTATION</span>
              <span className="text-slate-200 font-bold">{geometry.orientation}</span>
            </div>
          </div>
        </div>

        {/* Viewport Control Bar Mock */}
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded p-1 text-slate-400 text-xs">
          <button
            type="button"
            disabled
            title="Reset camera angle (Pending 3D engine)"
            className="p-1 hover:text-white rounded cursor-not-allowed"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            disabled
            title="Toggle wireframe (Pending 3D engine)"
            className="p-1 hover:text-white rounded cursor-not-allowed"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            disabled
            title="Fullscreen viewport (Pending 3D engine)"
            className="p-1 hover:text-white rounded cursor-not-allowed"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
