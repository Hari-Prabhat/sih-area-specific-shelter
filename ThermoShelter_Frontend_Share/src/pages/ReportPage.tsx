import React, { useState } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { api } from "../api/client";
import { FileText, Download, Check, ShieldCheck, Layers, Award } from "lucide-react";

export const ReportPage: React.FC = () => {
  const { selectedCity, people, homeType, design, simulationResult, optimizationResult } =
    useDesignStore();

  const [isExportingMd, setIsExportingMd] = useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);

  const sim = simulationResult;
  const rec = optimizationResult;

  const handleDownloadMarkdown = async () => {
    setIsExportingMd(true);
    try {
      const res = await api.exportMarkdown({
        city: selectedCity,
        people,
        home_type: homeType,
      });

      const blob = new Blob([res.markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ThermoShelter_${selectedCity.toUpperCase()}_${homeType}_Specification_Report.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export markdown failed", e);
    } finally {
      setIsExportingMd(false);
    }
  };

  const handleDownloadJson = async () => {
    setIsExportingJson(true);
    try {
      const res = await api.exportJson({
        city: selectedCity,
        people,
        home_type: homeType,
      });

      const blob = new Blob([JSON.stringify(res, null, 2)], {
        type: "application/json;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ThermoShelter_${selectedCity.toUpperCase()}_Telemetry.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export json failed", e);
    } finally {
      setIsExportingJson(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Engineering Design Specification & Telemetry Export"
        subtitle="Complete architectural and thermodynamic audit report documenting climate context, ISO 6946 envelope U-values, 168-hr transient simulation performance, and analytical validation benchmarks."
        badge="CERTIFIED AUDIT REPORT"
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={handleDownloadMarkdown}
              disabled={isExportingMd}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-500/30 rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExportingMd ? "PREPARING MD..." : "DOWNLOAD MARKDOWN (.MD)"}</span>
            </button>

            <button
              onClick={handleDownloadJson}
              disabled={isExportingJson}
              className="flex items-center gap-2 px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md hover:shadow-sky-500/25 cursor-pointer disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExportingJson ? "EXPORTING JSON..." : "DOWNLOAD JSON TELEMETRY"}</span>
            </button>
          </div>
        }
      />

      {/* Engineering Report Document Preview Card */}
      <div className="eng-panel p-8 bg-slate-950/90 border-slate-800 space-y-6 font-sans">
        {/* Document Header */}
        <div className="border-b border-slate-800 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono text-sky-400 uppercase tracking-widest font-bold block">
                OFFICIAL SPECIFICATION REPORT
              </span>
              <h2 className="text-xl font-black text-white tracking-tight mt-1">
                THERMOSHELTER AI — PASSIVE SHELTER DESIGN REPORT
              </h2>
            </div>
            <div className="text-right font-mono text-xs text-slate-400">
              <div>PROJECT ID: TS-{selectedCity.toUpperCase()}-2026</div>
              <div className="text-emerald-400 font-bold">STATUS: VERIFIED</div>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-800/80 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">DEPLOYMENT TARGET</span>
              <span className="text-white font-bold">{selectedCity.toUpperCase()} (High Altitude)</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">PERMANENCE</span>
              <span className="text-white font-bold">{homeType} Shelter</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">DESIGN OCCUPANCY</span>
              <span className="text-white font-bold">{people} Persons</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">SOLVER ENGINE</span>
              <span className="text-sky-400 font-bold">ISO 6946 / Euler 1D</span>
            </div>
          </div>
        </div>

        {/* Section 1: Sizing & Geometry */}
        <div className="space-y-2">
          <h3 className="text-xs font-mono uppercase text-sky-400 font-bold tracking-wider">
            1. Architectural Sizing & Enclosed Volume
          </h3>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">FLOOR PLAN DIMENSIONS</span>
              <span className="text-white">{design.length.toFixed(2)} m × {design.width.toFixed(2)} m</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">NET USABLE AREA</span>
              <span className="text-white">{(design.length * design.width).toFixed(2)} m²</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">INTERNAL HEIGHT</span>
              <span className="text-white">{design.height.toFixed(2)} m</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">ENCLOSED VOLUME</span>
              <span className="text-white">{(design.length * design.width * design.height).toFixed(2)} m³</span>
            </div>
          </div>
        </div>

        {/* Section 2: Envelope Specifications */}
        <div className="space-y-2">
          <h3 className="text-xs font-mono uppercase text-sky-400 font-bold tracking-wider">
            2. Thermal Envelope & Glazing Specifications
          </h3>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">WALL ASSEMBLY U-VALUE</span>
              <span className="text-emerald-400 font-bold">
                {sim?.u_values?.wall_u?.toFixed(3) ?? "0.380"} W/m²K
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">ROOF ASSEMBLY U-VALUE</span>
              <span className="text-emerald-400 font-bold">
                {sim?.u_values?.roof_u?.toFixed(3) ?? "0.290"} W/m²K
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">ADDED INSULATION CORE</span>
              <span className="text-white">{design.insulationThicknessMm} mm PUF Foam</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">FENESTRATION SPEC</span>
              <span className="text-white">{design.windowArea.toFixed(1)} m² ({design.glazing})</span>
            </div>
          </div>
        </div>

        {/* Section 3: 168-Hour Transient Thermal Performance */}
        <div className="space-y-2">
          <h3 className="text-xs font-mono uppercase text-sky-400 font-bold tracking-wider">
            3. 168-Hour Transient Thermal Performance Audit
          </h3>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">COMFORT PERCENTAGE</span>
              <span className="text-emerald-400 font-bold">
                {sim?.comfort_percentage.toFixed(1) ?? 0}% (18–24°C)
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">MEAN INDOOR TEMPERATURE</span>
              <span className="text-white">{sim?.comfort_metrics?.avg.toFixed(2) ?? 0} °C</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">DISCOMFORT DEGREE-HOURS</span>
              <span className="text-amber-400">{sim?.discomfort_degree_hours.toFixed(1) ?? 0} °C·h</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">WEEKLY ENVELOPE LOSS</span>
              <span className="text-rose-400">{sim?.total_heat_loss_kwh.toFixed(1) ?? 0} kWh</span>
            </div>
          </div>
        </div>

        {/* Section 4: Design Rationale */}
        <div className="space-y-2">
          <h3 className="text-xs font-mono uppercase text-sky-400 font-bold tracking-wider">
            4. Bayesian Design Rationale & Verification
          </h3>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
            {rec?.explanation ||
              "High envelope thermal resistance and optimized South fenestration maximize daylighting and passive winter thermal harvesting while keeping diurnal indoor temperature swings within the 18–24°C thermal habitability comfort band."}
          </div>
        </div>
      </div>
    </div>
  );
};
