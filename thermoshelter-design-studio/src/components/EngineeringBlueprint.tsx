/**
 * THERMOSHELTER AI - 2D Engineering Blueprint Viewer
 * ====================================================
 * Parametric, CAD-style 2D architectural blueprint rendering engine.
 * Fully synchronized with the authoritative frontend design state.
 * Supports:
 *   1. Floor Plan (Plan A-A) with North Arrow, Opening Apertures, Dimensioning
 *   2. Cross Section (Section B-B) with Floor, Walls, Roof Pitch, Clear Height
 *   3. Principal Elevation (Solar-Facing Facade) with Windows & Doors
 *   4. Multi-Layer Envelope Assembly Detail (ISO 6946 layer sequence)
 */

import React, { useState } from 'react';
import { Compass, Layers, Maximize2, Ruler, Eye } from 'lucide-react';
import { ShelterDesign } from '../utils/thermalEngine';

interface BlueprintProps {
  design: ShelterDesign;
  materialName: string;
  locationName?: string;
}

type BlueprintView = 'plan' | 'section' | 'elevation' | 'envelope';

export default function EngineeringBlueprint({ design, materialName, locationName = 'Leh, Ladakh' }: BlueprintProps) {
  const [activeView, setActiveView] = useState<BlueprintView>('plan');

  const {
    length,
    width,
    height,
    wallThickness,
    windowArea,
    windowGlazing,
    roofAngle,
    orientation,
    insulationType,
    thermalMassEnabled,
    thermalMassThickness,
  } = design;

  // Derive dynamic opening dimensions from windowArea
  const numWindows = 2;
  const singleWinArea = windowArea / numWindows;
  const winWidth = Math.max(0.6, Math.min(2.5, Math.round(Math.sqrt(singleWinArea * 1.2) * 100) / 100));
  const winHeight = Math.max(0.6, Math.min(2.0, Math.round((singleWinArea / winWidth) * 100) / 100));

  // Envelope thickness calculations in mm
  const wallThickMm = Math.round(wallThickness * 1000);
  const insThickMm = insulationType && insulationType !== 'None' ? 50 : 0;
  const massThickMm = thermalMassEnabled ? thermalMassThickness * 10 : 0;

  // Title Block Metadata
  const floorArea = (length * width).toFixed(1);
  const volume = (length * width * height).toFixed(1);

  return (
    <div className="space-y-6">
      {/* View Selector Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/80 p-4 rounded-xl border border-cyan-500/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center border border-cyan-500/40">
            <Ruler className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
              Architectural & Engineering Blueprint
              <span className="text-xs font-mono font-normal px-2 py-0.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded">
                ISO 6946 / SIH 2026
              </span>
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              Scale: 1:50 Parametric Vector | Units: SI (m, mm, °) | Location: {locationName}
            </p>
          </div>
        </div>

        {/* View Switcher Buttons */}
        <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-lg border border-slate-700">
          {(
            [
              { id: 'plan', label: '1. Floor Plan' },
              { id: 'section', label: '2. Section B-B' },
              { id: 'elevation', label: '3. Front Elevation' },
              { id: 'envelope', label: '4. Envelope Detail' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
                activeView === tab.id
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Blueprint Canvas Container */}
      <div className="relative bg-[#07111e] rounded-xl border-2 border-cyan-500/40 shadow-2xl overflow-hidden p-6">
        {/* Subtle CAD Background Grid */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(to right, #00f2fe 1px, transparent 1px),
              linear-gradient(to bottom, #00f2fe 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />

        {/* VIEW 1: FLOOR PLAN */}
        {activeView === 'plan' && (
          <div className="relative">
            <div className="text-xs font-mono text-cyan-400 mb-2 flex justify-between items-center">
              <span>DRAWING: PLAN A-A (TOP-DOWN VIEW)</span>
              <span>AZIMUTH: {orientation}° FROM NORTH</span>
            </div>

            <svg viewBox="0 0 800 500" className="w-full h-auto max-h-[500px]">
              <defs>
                <marker id="dim-arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#00f2fe" />
                </marker>
                <marker id="dim-arrow-rev" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#00f2fe" />
                </marker>
              </defs>

              {/* Center Group */}
              <g transform="translate(400, 240)">
                {/* Outer Perimeter Dimensions */}
                {/* Base visual scaling */}
                {(() => {
                  const scale = Math.min(480 / Math.max(length, 1), 320 / Math.max(width, 1), 50);
                  const wSvg = length * scale;
                  const hSvg = width * scale;
                  const tSvg = Math.max(8, wallThickness * scale);

                  return (
                    <g>
                      {/* Orientation Compass Box */}
                      <g transform="translate(-320, -160)">
                        <circle cx="30" cy="30" r="28" fill="#0b192c" stroke="#00f2fe" strokeWidth="1.5" />
                        <g transform={`rotate(${-(orientation)}, 30, 30)`}>
                          {/* North pointer */}
                          <polygon points="30,8 35,30 25,30" fill="#ef4444" />
                          <polygon points="30,52 35,30 25,30" fill="#64748b" />
                        </g>
                        <text x="30" y="5" fill="#ef4444" fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                          N
                        </text>
                        <text x="30" y="70" fill="#94a3b8" fontSize="9" textAnchor="middle" fontFamily="monospace">
                          {orientation}° ORIENTATION
                        </text>
                      </g>

                      {/* Outer Wall Boundary */}
                      <rect
                        x={-wSvg / 2}
                        y={-hSvg / 2}
                        width={wSvg}
                        height={hSvg}
                        fill="#0d233a"
                        stroke="#00f2fe"
                        strokeWidth="2"
                      />

                      {/* Inner Wall Boundary */}
                      <rect
                        x={-wSvg / 2 + tSvg}
                        y={-hSvg / 2 + tSvg}
                        width={Math.max(20, wSvg - 2 * tSvg)}
                        height={Math.max(20, hSvg - 2 * tSvg)}
                        fill="#071424"
                        stroke="#00f2fe"
                        strokeWidth="1.5"
                        strokeDasharray="4 2"
                      />

                      {/* Insulation Boundary Layer */}
                      {insThickMm > 0 && (
                        <rect
                          x={-wSvg / 2 + tSvg * 0.7}
                          y={-hSvg / 2 + tSvg * 0.7}
                          width={Math.max(10, wSvg - 1.4 * tSvg)}
                          height={Math.max(10, hSvg - 1.4 * tSvg)}
                          fill="none"
                          stroke="#eab308"
                          strokeWidth="1"
                          strokeDasharray="2 2"
                        />
                      )}

                      {/* Thermal Mass Area (Trombe / Internal Slab) */}
                      {thermalMassEnabled && (
                        <g>
                          <rect
                            x={-wSvg / 4}
                            y={hSvg / 2 - tSvg - 12}
                            width={wSvg / 2}
                            height={12}
                            fill="#3b82f6"
                            fillOpacity="0.4"
                            stroke="#60a5fa"
                            strokeWidth="1"
                          />
                          <text x="0" y={hSvg / 2 - tSvg - 3} fill="#93c5fd" fontSize="9" fontFamily="monospace" textAnchor="middle">
                            THERMAL MASS STORAGE ({massThickMm}mm)
                          </text>
                        </g>
                      )}

                      {/* Front Window Openings (South side) */}
                      <g>
                        {/* Window 1 */}
                        <rect
                          x={-wSvg / 3 - (winWidth * scale) / 2}
                          y={hSvg / 2 - tSvg - 2}
                          width={winWidth * scale}
                          height={tSvg + 4}
                          fill="#38bdf8"
                          fillOpacity="0.8"
                          stroke="#ffffff"
                          strokeWidth="1.5"
                        />
                        {/* Window 2 */}
                        <rect
                          x={wSvg / 3 - (winWidth * scale) / 2}
                          y={hSvg / 2 - tSvg - 2}
                          width={winWidth * scale}
                          height={tSvg + 4}
                          fill="#38bdf8"
                          fillOpacity="0.8"
                          stroke="#ffffff"
                          strokeWidth="1.5"
                        />
                        <text x={-wSvg / 3} y={hSvg / 2 + 18} fill="#38bdf8" fontSize="9" fontFamily="monospace" textAnchor="middle">
                          W1 ({winWidth}m)
                        </text>
                        <text x={wSvg / 3} y={hSvg / 2 + 18} fill="#38bdf8" fontSize="9" fontFamily="monospace" textAnchor="middle">
                          W2 ({winWidth}m)
                        </text>
                      </g>

                      {/* Main Entry Door */}
                      <rect
                        x={-15}
                        y={-hSvg / 2 - 2}
                        width={30}
                        height={tSvg + 4}
                        fill="#f97316"
                        fillOpacity="0.8"
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                      <text x="0" y={-hSvg / 2 - 8} fill="#fb923c" fontSize="9" fontFamily="monospace" textAnchor="middle">
                        DOOR (1.0m)
                      </text>

                      {/* Center Space Label */}
                      <text x="0" y="-10" fill="#e2e8f0" fontSize="12" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                        OCCUPIED HABITABLE ZONE
                      </text>
                      <text x="0" y="10" fill="#94a3b8" fontSize="10" fontFamily="monospace" textAnchor="middle">
                        Area = {floorArea} m² | Vol = {volume} m³
                      </text>

                      {/* Horizontal Dimension: LENGTH */}
                      <g transform={`translate(0, ${-hSvg / 2 - 35})`}>
                        <line x1={-wSvg / 2} y1="0" x2={wSvg / 2} y2="0" stroke="#00f2fe" strokeWidth="1.2" markerStart="url(#dim-arrow-rev)" markerEnd="url(#dim-arrow)" />
                        <line x1={-wSvg / 2} y1="-10" x2={-wSvg / 2} y2="10" stroke="#00f2fe" strokeWidth="0.8" />
                        <line x1={wSvg / 2} y1="-10" x2={wSvg / 2} y2="10" stroke="#00f2fe" strokeWidth="0.8" />
                        <rect x="-40" y="-10" width="80" height="20" fill="#07111e" />
                        <text x="0" y="4" fill="#00f2fe" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                          L = {length.toFixed(2)} m
                        </text>
                      </g>

                      {/* Vertical Dimension: WIDTH */}
                      <g transform={`translate(${wSvg / 2 + 35}, 0)`}>
                        <line x1="0" y1={-hSvg / 2} x2="0" y2={hSvg / 2} stroke="#00f2fe" strokeWidth="1.2" markerStart="url(#dim-arrow-rev)" markerEnd="url(#dim-arrow)" />
                        <line x1="-10" y1={-hSvg / 2} x2="10" y2={-hSvg / 2} stroke="#00f2fe" strokeWidth="0.8" />
                        <line x1="-10" y1={hSvg / 2} x2="10" y2={hSvg / 2} stroke="#00f2fe" strokeWidth="0.8" />
                        <rect x="-10" y="-12" width="60" height="24" fill="#07111e" />
                        <text x="20" y="4" fill="#00f2fe" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                          W = {width.toFixed(2)} m
                        </text>
                      </g>

                      {/* Wall Thickness Callout */}
                      <g transform={`translate(${-wSvg / 2 - 20}, 0)`}>
                        <text x="-10" y="4" fill="#facc15" fontSize="10" fontFamily="monospace" textAnchor="end">
                          Wall = {wallThickMm} mm
                        </text>
                      </g>
                    </g>
                  );
                })()}
              </g>
            </svg>
          </div>
        )}

        {/* VIEW 2: CROSS SECTION */}
        {activeView === 'section' && (
          <div className="relative">
            <div className="text-xs font-mono text-cyan-400 mb-2 flex justify-between items-center">
              <span>DRAWING: SECTION B-B (TRANSVERSE SECTION)</span>
              <span>ROOF PITCH: {roofAngle}°</span>
            </div>

            <svg viewBox="0 0 800 500" className="w-full h-auto max-h-[500px]">
              <defs>
                <marker id="dim-arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#00f2fe" />
                </marker>
                <marker id="dim-arrow-rev" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#00f2fe" />
                </marker>
              </defs>

              <g transform="translate(400, 360)">
                {(() => {
                  const scale = Math.min(450 / Math.max(width, 1), 220 / Math.max(height, 1), 50);
                  const wSvg = width * scale;
                  const hSvg = height * scale;
                  const tSvg = Math.max(8, wallThickness * scale);
                  const pitchRad = (roofAngle * Math.PI) / 180;
                  const roofRise = Math.tan(pitchRad) * (wSvg / 2);

                  return (
                    <g>
                      {/* Ground Line */}
                      <line x1="-350" y1="0" x2="350" y2="0" stroke="#475569" strokeWidth="2" strokeDasharray="8 4" />
                      <text x="320" y="-8" fill="#64748b" fontSize="9" fontFamily="monospace">±0.00 GRADE</text>

                      {/* Concrete Foundation & Floor Slab */}
                      <rect x={-wSvg / 2 - 10} y="0" width={wSvg + 20} height="20" fill="#1e293b" stroke="#00f2fe" strokeWidth="1.5" />
                      <text x="0" y="14" fill="#94a3b8" fontSize="9" fontFamily="monospace" textAnchor="middle">
                        REINFORCED CONCRETE GROUND SLAB (150mm)
                      </text>

                      {/* Left Wall Section */}
                      <rect x={-wSvg / 2} y={-hSvg} width={tSvg} height={hSvg} fill="#0d233a" stroke="#00f2fe" strokeWidth="1.5" />
                      {/* Right Wall Section */}
                      <rect x={wSvg / 2 - tSvg} y={-hSvg} width={tSvg} height={hSvg} fill="#0d233a" stroke="#00f2fe" strokeWidth="1.5" />

                      {/* Insulation Callout layer on Wall */}
                      {insThickMm > 0 && (
                        <g>
                          <rect x={-wSvg / 2 + tSvg - 4} y={-hSvg} width="4" height={hSvg} fill="#eab308" />
                          <rect x={wSvg / 2 - tSvg} y={-hSvg} width="4" height={hSvg} fill="#eab308" />
                        </g>
                      )}

                      {/* Pitched or Flat Roof */}
                      {roofRise > 5 ? (
                        <g>
                          {/* Left Rafter */}
                          <polygon
                            points={`${-wSvg / 2 - 15},${-hSvg + 10} 0,${-hSvg - roofRise} 0,${-hSvg - roofRise - 16} ${-wSvg / 2 - 15},${-hSvg - 6}`}
                            fill="#0d233a"
                            stroke="#00f2fe"
                            strokeWidth="1.5"
                          />
                          {/* Right Rafter */}
                          <polygon
                            points={`${wSvg / 2 + 15},${-hSvg + 10} 0,${-hSvg - roofRise} 0,${-hSvg - roofRise - 16} ${wSvg / 2 + 15},${-hSvg - 6}`}
                            fill="#0d233a"
                            stroke="#00f2fe"
                            strokeWidth="1.5"
                          />
                          {/* Roof Pitch Annotation */}
                          <path d={`M ${wSvg / 4},${-hSvg} A 30 30 0 0 0 ${wSvg / 4 + 25},${-hSvg - 12}`} fill="none" stroke="#f59e0b" strokeWidth="1" />
                          <text x={wSvg / 4 + 35} y={-hSvg - 8} fill="#f59e0b" fontSize="10" fontFamily="monospace">
                            ∠ {roofAngle}°
                          </text>
                        </g>
                      ) : (
                        <rect x={-wSvg / 2 - 15} y={-hSvg - 18} width={wSvg + 30} height="18" fill="#0d233a" stroke="#00f2fe" strokeWidth="1.5" />
                      )}

                      {/* Interior Labels */}
                      <text x="0" y={-hSvg / 2} fill="#e2e8f0" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                        INTERIOR CLEARANCE
                      </text>
                      <text x="0" y={-hSvg / 2 + 16} fill="#94a3b8" fontSize="10" fontFamily="monospace" textAnchor="middle">
                        Height = {height.toFixed(2)} m
                      </text>

                      {/* Vertical Height Dimension Line */}
                      <g transform={`translate(${wSvg / 2 + 45}, 0)`}>
                        <line x1="0" y1="0" x2="0" y2={-hSvg} stroke="#00f2fe" strokeWidth="1.2" markerStart="url(#dim-arrow-rev)" markerEnd="url(#dim-arrow)" />
                        <line x1="-8" y1="0" x2="8" y2="0" stroke="#00f2fe" strokeWidth="0.8" />
                        <line x1="-8" y1={-hSvg} x2="8" y2={-hSvg} stroke="#00f2fe" strokeWidth="0.8" />
                        <text x="15" y={-hSvg / 2} fill="#00f2fe" fontSize="11" fontWeight="bold" fontFamily="monospace">
                          H = {height.toFixed(2)} m
                        </text>
                      </g>

                      {/* Horizontal Width Dimension Line */}
                      <g transform="translate(0, 45)">
                        <line x1={-wSvg / 2} y1="0" x2={wSvg / 2} y2="0" stroke="#00f2fe" strokeWidth="1.2" markerStart="url(#dim-arrow-rev)" markerEnd="url(#dim-arrow)" />
                        <line x1={-wSvg / 2} y1="-8" x2={-wSvg / 2} y2="8" stroke="#00f2fe" strokeWidth="0.8" />
                        <line x1={wSvg / 2} y1="-8" x2={wSvg / 2} y2="8" stroke="#00f2fe" strokeWidth="0.8" />
                        <text x="0" y="16" fill="#00f2fe" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                          W = {width.toFixed(2)} m
                        </text>
                      </g>
                    </g>
                  );
                })()}
              </g>
            </svg>
          </div>
        )}

        {/* VIEW 3: FRONT ELEVATION */}
        {activeView === 'elevation' && (
          <div className="relative">
            <div className="text-xs font-mono text-cyan-400 mb-2 flex justify-between items-center">
              <span>DRAWING: SOUTH / PRINCIPAL ELEVATION</span>
              <span>SOLAR APERTURE FACADE</span>
            </div>

            <svg viewBox="0 0 800 500" className="w-full h-auto max-h-[500px]">
              <defs>
                <marker id="dim-arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#00f2fe" />
                </marker>
                <marker id="dim-arrow-rev" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#00f2fe" />
                </marker>
              </defs>

              <g transform="translate(400, 360)">
                {(() => {
                  const scale = Math.min(480 / Math.max(length, 1), 220 / Math.max(height, 1), 50);
                  const lSvg = length * scale;
                  const hSvg = height * scale;
                  const pitchRad = (roofAngle * Math.PI) / 180;
                  const roofRise = Math.tan(pitchRad) * (width * scale * 0.25);

                  return (
                    <g>
                      {/* Ground Line */}
                      <line x1="-350" y1="0" x2="350" y2="0" stroke="#475569" strokeWidth="2" strokeDasharray="8 4" />

                      {/* Main Facade Wall */}
                      <rect
                        x={-lSvg / 2}
                        y={-hSvg}
                        width={lSvg}
                        height={hSvg}
                        fill="#0d233a"
                        stroke="#00f2fe"
                        strokeWidth="2"
                      />

                      {/* Roof Fascia */}
                      <polygon
                        points={`${-lSvg / 2 - 15},${-hSvg} ${lSvg / 2 + 15},${-hSvg} ${lSvg / 2 + 15},${-hSvg - Math.max(16, roofRise)} ${-lSvg / 2 - 15},${-hSvg - Math.max(16, roofRise)}`}
                        fill="#1e293b"
                        stroke="#00f2fe"
                        strokeWidth="1.5"
                      />

                      {/* Windows */}
                      <rect
                        x={-lSvg / 3 - (winWidth * scale) / 2}
                        y={-hSvg / 2 - (winHeight * scale) / 2}
                        width={winWidth * scale}
                        height={winHeight * scale}
                        fill="#38bdf8"
                        fillOpacity="0.4"
                        stroke="#00f2fe"
                        strokeWidth="1.5"
                      />
                      <rect
                        x={lSvg / 3 - (winWidth * scale) / 2}
                        y={-hSvg / 2 - (winHeight * scale) / 2}
                        width={winWidth * scale}
                        height={winHeight * scale}
                        fill="#38bdf8"
                        fillOpacity="0.4"
                        stroke="#00f2fe"
                        strokeWidth="1.5"
                      />

                      {/* Door */}
                      <rect
                        x={-20}
                        y={-90}
                        width={40}
                        height={90}
                        fill="#f97316"
                        fillOpacity="0.3"
                        stroke="#f97316"
                        strokeWidth="1.5"
                      />

                      {/* Dimension: Length */}
                      <g transform="translate(0, 35)">
                        <line x1={-lSvg / 2} y1="0" x2={lSvg / 2} y2="0" stroke="#00f2fe" strokeWidth="1.2" markerStart="url(#dim-arrow-rev)" markerEnd="url(#dim-arrow)" />
                        <text x="0" y="15" fill="#00f2fe" fontSize="11" fontWeight="bold" fontFamily="monospace" textAnchor="middle">
                          Facade Length = {length.toFixed(2)} m
                        </text>
                      </g>

                      {/* Dimension: Height */}
                      <g transform={`translate(${lSvg / 2 + 35}, 0)`}>
                        <line x1="0" y1="0" x2="0" y2={-hSvg} stroke="#00f2fe" strokeWidth="1.2" markerStart="url(#dim-arrow-rev)" markerEnd="url(#dim-arrow)" />
                        <text x="15" y={-hSvg / 2} fill="#00f2fe" fontSize="11" fontWeight="bold" fontFamily="monospace">
                          H = {height.toFixed(2)} m
                        </text>
                      </g>
                    </g>
                  );
                })()}
              </g>
            </svg>
          </div>
        )}

        {/* VIEW 4: MULTI-LAYER ENVELOPE ASSEMBLY DETAIL */}
        {activeView === 'envelope' && (
          <div className="space-y-4">
            <div className="text-xs font-mono text-cyan-400 mb-2 flex justify-between items-center">
              <span>DETAIL D-01: ISO 6946 MULTI-LAYER WALL ASSEMBLY</span>
              <span>HEAT TRANSFER: 1D STEADY STATE CONDUCTION</span>
            </div>

            <div className="bg-slate-900/90 rounded-lg p-5 border border-cyan-500/20 font-mono text-xs">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-center mb-4">
                <div className="bg-slate-800 p-3 rounded border border-slate-700">
                  <span className="text-slate-400 block text-[10px] uppercase">1. Exterior Film</span>
                  <span className="text-white font-bold block mt-1">R_se = 0.04</span>
                  <span className="text-slate-500 text-[10px]">m²·K/W</span>
                </div>
                <div className="bg-amber-950/40 p-3 rounded border border-amber-600/40">
                  <span className="text-amber-400 block text-[10px] uppercase">2. Base Wall Masonry</span>
                  <span className="text-white font-bold block mt-1">{materialName}</span>
                  <span className="text-amber-300 text-[10px]">{wallThickMm} mm thickness</span>
                </div>
                <div className="bg-yellow-950/40 p-3 rounded border border-yellow-600/40">
                  <span className="text-yellow-400 block text-[10px] uppercase">3. Thermal Insulation</span>
                  <span className="text-white font-bold block mt-1">{insulationType || 'None'}</span>
                  <span className="text-yellow-300 text-[10px]">{insThickMm} mm (k ≈ 0.025)</span>
                </div>
                <div className="bg-blue-950/40 p-3 rounded border border-blue-600/40">
                  <span className="text-blue-400 block text-[10px] uppercase">4. Thermal Mass Layer</span>
                  <span className="text-white font-bold block mt-1">{thermalMassEnabled ? 'Sensible Mass Core' : 'Standard'}</span>
                  <span className="text-blue-300 text-[10px]">{thermalMassEnabled ? `${massThickMm} mm` : '0 mm'}</span>
                </div>
                <div className="bg-slate-800 p-3 rounded border border-slate-700">
                  <span className="text-slate-400 block text-[10px] uppercase">5. Interior Film</span>
                  <span className="text-white font-bold block mt-1">R_si = 0.13</span>
                  <span className="text-slate-500 text-[10px]">m²·K/W</span>
                </div>
              </div>

              {/* Layer Graphic Schematic */}
              <div className="relative h-28 bg-slate-950 rounded border border-slate-700 flex overflow-hidden">
                <div className="w-[10%] bg-blue-900/30 flex items-center justify-center text-[10px] text-blue-300 border-r border-slate-700">
                  EXT AIR
                </div>
                <div className="w-[40%] bg-amber-800/60 flex flex-col items-center justify-center text-[10px] text-amber-100 border-r border-slate-700 font-bold">
                  <span>WALL SUBSTRATE</span>
                  <span className="text-[9px] font-normal">{wallThickMm} mm</span>
                </div>
                {insThickMm > 0 && (
                  <div className="w-[20%] bg-yellow-500/80 flex flex-col items-center justify-center text-[10px] text-slate-950 border-r border-slate-700 font-bold">
                    <span>PUF / EPS</span>
                    <span className="text-[9px] font-normal">{insThickMm} mm</span>
                  </div>
                )}
                {thermalMassEnabled && (
                  <div className="w-[20%] bg-indigo-700/60 flex flex-col items-center justify-center text-[10px] text-indigo-100 border-r border-slate-700 font-bold">
                    <span>MASS SLAB</span>
                    <span className="text-[9px] font-normal">{massThickMm} mm</span>
                  </div>
                )}
                <div className="flex-1 bg-green-950/40 flex items-center justify-center text-[10px] text-green-300">
                  INT AIR
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Blueprint Title Block (Bottom Right) */}
        <div className="mt-6 pt-4 border-t border-cyan-500/30 flex flex-wrap justify-between items-end text-[10px] font-mono text-slate-400">
          <div>
            <span className="text-cyan-400 font-bold">PROJECT:</span> THERMOSHELTER AI DEFENSE & RELIEF SHELTER<br />
            <span className="text-cyan-400 font-bold">DISCIPLINE:</span> ARCHITECTURAL & THERMAL PHYSICS SPECIFICATION
          </div>
          <div className="text-right">
            <span>DRAWING NO: TS-2026-AR-001</span> | <span>REV: 2.0.0</span><br />
            <span>AUTHORITATIVE CORE: PYTHON FASTAPI REST ENGINE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
