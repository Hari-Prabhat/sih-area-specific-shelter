import React from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { SquareDashedBottom, Compass, Maximize2 } from "lucide-react";

export const FloorplanPage: React.FC = () => {
  const { design, updateDesign, selectedCity } = useDesignStore();

  const L = design.length;
  const W = design.width;
  const floorArea = (L * W).toFixed(1);
  const winW = Math.min(L * 0.7, Math.max(1.2, design.windowArea / 1.3));

  // SVG Scaled coordinates
  const scale = 40; // 40px per meter
  const padding = 80;
  const svgW = L * scale + padding * 2;
  const svgH = W * scale + padding * 2;
  const x0 = padding;
  const y0 = padding;
  const wallThick = 0.23 * scale; // 230mm brick wall

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="2D Architectural Floor Plan & Fenestration Layout"
        subtitle="1:1 scale architectural drafting blueprint derived from active design dimensions, wall assemblies, and solar orientation."
        badge={`${L.toFixed(1)}m × ${W.toFixed(1)}m · ${floorArea} m²`}
      />

      {/* SVG Architectural Blueprint */}
      <div className="eng-panel p-6 flex flex-col items-center justify-center bg-slate-950/80 border-slate-800">
        <div className="overflow-x-auto w-full flex justify-center py-4">
          <svg
            width={svgW}
            height={svgH}
            className="select-none font-mono"
            style={{ filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.5))" }}
          >
            {/* Blueprint Grid Lines */}
            <defs>
              <pattern
                id="blueprintGrid"
                width={scale}
                height={scale}
                patternUnits="userSpaceOnUse"
              >
                <path
                  d={`M ${scale} 0 L 0 0 0 ${scale}`}
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth="0.8"
                />
              </pattern>
            </defs>
            <rect width={svgW} height={svgH} fill="url(#blueprintGrid)" />

            {/* Exterior Wall Outer Boundary */}
            <rect
              x={x0}
              y={y0}
              width={L * scale}
              height={W * scale}
              fill="#0f172a"
              stroke="#38bdf8"
              strokeWidth="4"
              rx="2"
            />

            {/* Interior Space Boundary (Cavity) */}
            <rect
              x={x0 + wallThick}
              y={y0 + wallThick}
              width={L * scale - wallThick * 2}
              height={W * scale - wallThick * 2}
              fill="#070a13"
              stroke="#475569"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />

            {/* South Glazed Fenestration (Window at Bottom, Z+) */}
            {/* Centered along length */}
            {(() => {
              const winStart = x0 + (L * scale - winW * scale) / 2;
              return (
                <g>
                  {/* Glass Cutout / Frame */}
                  <rect
                    x={winStart}
                    y={y0 + W * scale - wallThick - 3}
                    width={winW * scale}
                    height={wallThick + 6}
                    fill="#0284c7"
                    stroke="#38bdf8"
                    strokeWidth="2"
                  />
                  <line
                    x1={winStart}
                    y1={y0 + W * scale - wallThick / 2}
                    x2={winStart + winW * scale}
                    y2={y0 + W * scale - wallThick / 2}
                    stroke="#ffffff"
                    strokeWidth="2"
                  />
                  <text
                    x={winStart + (winW * scale) / 2}
                    y={y0 + W * scale + 24}
                    fill="#38bdf8"
                    fontSize="11"
                    textAnchor="middle"
                    fontWeight="bold"
                  >
                    Primary South Glazing ({design.windowArea.toFixed(1)} m²)
                  </text>
                </g>
              );
            })()}

            {/* Entry Door & Arc (West side of South wall) */}
            {(() => {
              const doorW = 0.9 * scale;
              const doorStart = x0 + 0.3 * scale;
              return (
                <g>
                  {/* Door Opening in wall */}
                  <rect
                    x={doorStart}
                    y={y0 + W * scale - wallThick - 2}
                    width={doorW}
                    height={wallThick + 4}
                    fill="#070a13"
                  />
                  {/* Door Leaf (Angled) */}
                  <line
                    x1={doorStart}
                    y1={y0 + W * scale}
                    x2={doorStart + doorW * 0.7}
                    y2={y0 + W * scale - doorW * 0.7}
                    stroke="#f97316"
                    strokeWidth="3"
                  />
                  {/* Door Swing Arc */}
                  <path
                    d={`M ${doorStart + doorW} ${y0 + W * scale} A ${doorW} ${doorW} 0 0 0 ${doorStart + doorW * 0.7} ${y0 + W * scale - doorW * 0.7}`}
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="1.2"
                    strokeDasharray="3 3"
                  />
                  <text
                    x={doorStart + doorW / 2}
                    y={y0 + W * scale + 24}
                    fill="#fb923c"
                    fontSize="11"
                    textAnchor="middle"
                  >
                    Door 0.9m
                  </text>
                </g>
              );
            })()}

            {/* Internal Label & Area */}
            <text
              x={x0 + (L * scale) / 2}
              y={y0 + (W * scale) / 2 - 8}
              fill="#f8fafc"
              fontSize="14"
              fontWeight="bold"
              textAnchor="middle"
            >
              Main Habitable Living Zone
            </text>
            <text
              x={x0 + (L * scale) / 2}
              y={y0 + (W * scale) / 2 + 14}
              fill="#38bdf8"
              fontSize="12"
              textAnchor="middle"
            >
              Net Usable: {floorArea} m² ({L.toFixed(1)}m × {W.toFixed(1)}m)
            </text>

            {/* North Indicator Arrow (Upper Right) */}
            <g transform={`translate(${x0 + L * scale + 35}, ${y0 + 20})`}>
              <circle cx="0" cy="0" r="16" fill="#1e293b" stroke="#334155" />
              <line x1="0" y1="12" x2="0" y2="-12" stroke="#ef4444" strokeWidth="2.5" />
              <polygon points="0,-14 -5,-4 5,-4" fill="#ef4444" />
              <text x="0" y="-18" fill="#ef4444" fontSize="11" fontWeight="bold" textAnchor="middle">
                N
              </text>
            </g>

            {/* Dimension Line: Top (Length) */}
            <line
              x1={x0}
              y1={y0 - 20}
              x2={x0 + L * scale}
              y2={y0 - 20}
              stroke="#64748b"
              strokeWidth="1.2"
            />
            <line x1={x0} y1={y0 - 26} x2={x0} y2={y0 - 14} stroke="#64748b" strokeWidth="1.2" />
            <line
              x1={x0 + L * scale}
              y1={y0 - 26}
              x2={x0 + L * scale}
              y2={y0 - 14}
              stroke="#64748b"
              strokeWidth="1.2"
            />
            <text
              x={x0 + (L * scale) / 2}
              y={y0 - 26}
              fill="#94a3b8"
              fontSize="11"
              textAnchor="middle"
            >
              {L.toFixed(2)} m
            </text>

            {/* Dimension Line: Left (Width) */}
            <line
              x1={x0 - 20}
              y1={y0}
              x2={x0 - 20}
              y2={y0 + W * scale}
              stroke="#64748b"
              strokeWidth="1.2"
            />
            <line x1={x0 - 26} y1={y0} x2={x0 - 14} y2={y0} stroke="#64748b" strokeWidth="1.2" />
            <line
              x1={x0 - 26}
              y1={y0 + W * scale}
              x2={x0 - 14}
              y2={y0 + W * scale}
              stroke="#64748b"
              strokeWidth="1.2"
            />
            <text
              x={x0 - 32}
              y={y0 + (W * scale) / 2}
              fill="#94a3b8"
              fontSize="11"
              textAnchor="middle"
              transform={`rotate(-90 ${x0 - 32} ${y0 + (W * scale) / 2})`}
            >
              {W.toFixed(2)} m
            </text>
          </svg>
        </div>
      </div>

      {/* Floorplan Specifications Strip */}
      <div className="eng-panel p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
        <div>
          <span className="text-slate-500 block text-[10px]">WALL THICKNESS</span>
          <span className="text-white font-bold">230 mm Masonry Core</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">GLAZING APERTURE</span>
          <span className="text-sky-400 font-bold">{winW.toFixed(1)} m South Opening</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">PASSIVE SOLAR</span>
          <span className="text-emerald-400 font-bold">South Solar Direct Gain</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">DOOR CLEARANCE</span>
          <span className="text-amber-400 font-bold">900 mm × 2000 mm Swing</span>
        </div>
      </div>
    </div>
  );
};
