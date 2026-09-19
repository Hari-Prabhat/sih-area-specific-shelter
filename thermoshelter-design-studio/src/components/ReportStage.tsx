/**
 * THERMOSHELTER — Engineering Report stage (D4-D2)
 * ================================================
 * Continuous engineering document composed from the canonical studio state
 * via services/reportModel.ts (D4-D1). Artifacts are captured from the
 * EXISTING EngineeringBlueprint SVG (D4-C capture hooks) and the existing
 * 3D twin canvas (preserveDrawingBuffer snapshot) — no drawing or physics
 * logic is duplicated here.
 *
 * Export is the browser's native print-to-PDF (reportPrint.css: A4
 * pagination, application shell hidden, artifacts preserved).
 *
 * Honesty rules inherited from the report model: simulated/predicted outputs
 * are labelled as such, weather keeps the canonical provenance vocabulary,
 * absent data renders honest empty states, and no value is fabricated.
 */

import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useStudioState } from '../store/useStudioState';
import { buildReportInput } from '../services/reportModel';
import {
  captureBlueprintSvgs,
  captureTwinPng,
  type BlueprintArtifact,
} from '../services/artifactCapture';
import { PROVENANCE_DESCRIPTORS } from '../theme/tokens';
import ProvenanceChip from './ui/ProvenanceChip';
import Button from './ui/Button';
import StatTile from './ui/StatTile';
import StageSuspense from './ui/StageSuspense';
import { Printer, Copy, Check, AlertTriangle, Info } from 'lucide-react';
import '../report/reportPrint.css';

// D3 discipline: heavyweight artifact sources load on demand, reusing the
// existing chunks — ReportStage itself stays eager-light.
const EngineeringBlueprint = lazy(() => import('./EngineeringBlueprint'));
const ShelterModel3D = lazy(() => import('./ShelterModel3D'));

/**
 * Screen-only wrapper rendering the hidden artifact sources: one hidden
 * Blueprint per drawing view (the component shows one view at a time, so a
 * dedicated instance per view makes all three drawings capturable) plus the
 * live 3D twin whose canvas carries the snapshot hook.
 */
function ArtifactSources() {
  const { design, wallMaterial, simulation } = useStudioState();
  return (
    <div className="space-y-4 no-print" data-testid="artifact-sources" aria-hidden="true">
      <p className="text-xs text-slate-400 font-mono">
        Artifact sources — hidden Blueprint instances (one per drawing view) and
        the live 3D twin below feed the report artifacts via DOM/canvas capture.
      </p>
      {(['plan', 'section', 'elevation'] as const).map((view) => (
        <Suspense key={view} fallback={<StageSuspense label={`Blueprint (${view})`} />}>
          <EngineeringBlueprint design={design} materialName={wallMaterial} initialView={view} />
        </Suspense>
      ))}
      <Suspense fallback={<StageSuspense label="3D twin" />}>
        <ShelterModel3D
          design={design}
          materialName={wallMaterial}
          comfortIndex={simulation.result?.thermalComfortIndex ?? 0}
          avgTemp={simulation.result?.avgInsideTemp ?? 0}
        />
      </Suspense>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Presentation helpers — formatting/relaying only
// ---------------------------------------------------------------------------

function fmt(v: number | null | undefined, digits = 1, unit = ''): string {
  if (typeof v !== 'number' || !Number.isFinite(v)) return '—';
  const s = v.toFixed(digits);
  return unit ? `${s} ${unit}` : s;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="report-row flex justify-between gap-4 py-1 border-b border-slate-800/60">
      <span className="text-slate-400 text-sm">{label}</span>
      <span className="text-slate-200 text-sm font-mono text-right">{value}</span>
    </div>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="report-section bg-slate-900/60 border border-slate-700/40 rounded-xl p-6">
      <h2 className="text-lg font-bold text-amber-400 mb-4">{title}</h2>
      {children}
    </section>
  );
}

function EmptyNote({ children }: { children: ReactNode }) {
  return (
    <p className="report-empty text-sm text-slate-400 italic flex items-center gap-2">
      <Info size={14} className="shrink-0" aria-hidden="true" />
      {children}
    </p>
  );
}

const VIEW_TITLES: Record<BlueprintArtifact['view'], string> = {
  plan: 'Floor Plan (Plan A-A)',
  section: 'Cross Section (Section B-B)',
  elevation: 'Principal Elevation (Solar-Facing Facade)',
  envelope: 'Envelope Assembly Detail',
};

/**
 * The Engineering Report stage. Composes the canonical studio state via the
 * D4-D1 pure adapter and renders the 11-section engineering document.
 */
export default function ReportStage() {
  const {
    climate,
    climateProfile,
    mission,
    design,
    wallMaterial,
    simulation,
    optimization,
    setStage,
  } = useStudioState();

  const report = useMemo(
    () =>
      buildReportInput({
        climate,
        climateProfile,
        mission,
        design,
        wallMaterialName: wallMaterial,
        simulation: simulation.result,
        optimization: optimization.result,
      }),
    [climate, climateProfile, mission, design, wallMaterial, simulation.result, optimization.result],
  );

  const [blueprintArtifacts, setBlueprintArtifacts] = useState<BlueprintArtifact[] | null>(null);
  const [twinPng, setTwinPng] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Capture artifacts from the hidden source components after they mount.
  const capture = () => {
    const svgs = captureBlueprintSvgs();
    setBlueprintArtifacts(svgs.length > 0 ? svgs : null);
    setTwinPng(captureTwinPng());
  };

  useEffect(() => {
    // Lazy chunks + the first 3D frame need a beat before the DOM is complete.
    const t = setTimeout(capture, 2000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable — non-critical affordance, stay silent */
    }
  };

  const weatherChip = report.climate.provenance.provenance;
  const sim = report.simulation;
  const opt = report.optimization;

  return (
    <div className="space-y-6">
      {/* Screen toolbar (hidden in print) */}
      <div className="no-print flex flex-wrap items-center justify-between gap-3 bg-slate-900/70 border border-slate-700/40 rounded-xl p-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Engineering Report</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Generated from the current canonical studio state · {report.meta.tool}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={copyJson}
            icon={copied ? <Check size={15} /> : <Copy size={15} />}
            aria-label="Copy report data as JSON"
          >
            {copied ? 'Copied' : 'Copy Report Data'}
          </Button>
          <Button
            onClick={() => window.print()}
            icon={<Printer size={15} />}
            aria-label="Print or save the engineering report as PDF"
          >
            Print / Save as PDF
          </Button>
        </div>
      </div>

      {/* The printable engineering document */}
      <article className="report-document space-y-6" aria-label="Engineering report document">
        {/* 1 — Title block */}
        <Section id="report-title" title="ThermoShelter Engineering Report">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6">
            <Row label="Tool" value={report.meta.tool} />
            <Row label="Generated (UTC)" value={report.meta.generatedAt.replace('T', ' ').slice(0, 16)} />
            <Row label="Physics engine" value={report.meta.engine} />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {weatherChip && (
              <ProvenanceChip value={weatherChip} fallbackUsed={report.climate.fallbackUsed} />
            )}
            {sim && <ProvenanceChip value="SIMULATED" />}
            {opt && <ProvenanceChip value="OPTIMIZED" />}
          </div>
        </Section>

        {/* 2 — Site & Climate */}
        <Section id="report-climate" title="Site & Climate">
          {report.climate.presetOnly ? (
            <EmptyNote>Design preset — no live climate profile loaded.</EmptyNote>
          ) : (
            <>
              {report.climate.fallbackUsed && (
                <p className="mb-3 flex items-center gap-2 text-sm text-orange-300 bg-orange-500/10 border border-orange-500/40 rounded-lg p-3">
                  <AlertTriangle size={15} aria-hidden="true" />
                  Fallback climate dataset used for this run — results reflect the fallback dataset, not the requested location data.
                </p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                <Row label="Location" value={report.site.city ?? report.site.location} />
                <Row label="Coordinates" value={report.climate.provenance.coordinatesLabel ?? '—'} />
                <Row label="Elevation" value={report.site.elevationLabel ?? '—'} />
                <Row label="Timezone" value={report.site.timezone ?? '—'} />
                <Row label="Climate classification" value={report.climate.climateMode ?? '—'} />
                <Row label="Weather provider" value={report.climate.provenance.provider ?? '—'} />
                <Row label="Data mode" value={report.climate.provenance.dataMode ?? '—'} />
                <Row
                  label="Data provenance"
                  value={weatherChip ? PROVENANCE_DESCRIPTORS[weatherChip].label : '—'}
                />
                <Row label="Period" value={report.climate.provenance.periodLabel ?? '—'} />
                <Row label="Retrieved" value={report.climate.provenance.retrievedLabel ?? '—'} />
                <Row label="Hourly window" value={report.climate.hours ? `${report.climate.hours} h` : '—'} />
                <Row label="Fallback used" value={report.climate.fallbackUsed ? 'YES — see disclosure' : 'No'} />
              </div>
            </>
          )}
        </Section>

        {/* 3 — Mission Requirements */}
        <Section id="report-mission" title="Mission Requirements">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            <Row label="Occupants" value={`${report.mission.occupants} persons`} />
            <Row label="Ventilation (ACH)" value={fmt(report.mission.ach, 2, 'h⁻¹')} />
            <Row
              label="Comfort bounds (engine)"
              value={`${report.mission.comfortBounds.min}–${report.mission.comfortBounds.max} °C`}
            />
            <Row label="Purpose" value={report.mission.purpose} />
            <Row
              label="Deployment"
              value={`${report.mission.deploymentType} · ${report.mission.durationMonths} months`}
            />
            <Row label="Mobility required" value={report.mission.mobilityRequired ? 'Yes' : 'No'} />
            <Row
              label="Priorities"
              value={report.mission.priorities.length > 0 ? report.mission.priorities.join(', ') : '—'}
            />
          </div>
        </Section>

        {/* 4 — Design Description (authoritative textual specification) */}
        <Section id="report-design" title="Design Description">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            <Row
              label="Dimensions (L×W×H)"
              value={`${fmt(report.design.length, 2)} × ${fmt(report.design.width, 2)} × ${fmt(report.design.height, 2)} m`}
            />
            <Row label="Shape" value={report.design.shape} />
            <Row label="Orientation" value={`${report.design.orientationDeg}° azimuth`} />
            <Row label="Roof pitch" value={`${report.design.roofPitchDeg}°`} />
            <Row label="Wall thickness" value={`${fmt(report.design.wallThicknessM * 1000, 0)} mm`} />
            <Row
              label="Wall material"
              value={`${report.design.wallMaterialName} (backend: ${report.design.wallMaterialBackendId})`}
            />
            <Row
              label="Wall conductivity"
              value={report.design.wallConductivity !== null ? `${report.design.wallConductivity} W/m·K` : '—'}
            />
            <Row
              label="Wall density / specific heat"
              value={
                report.design.wallDensity !== null && report.design.wallSpecificHeat !== null
                  ? `${report.design.wallDensity} kg/m³ · ${report.design.wallSpecificHeat} J/kg·K`
                  : '—'
              }
            />
            <Row
              label="Insulation"
              value={
                report.design.insulationType !== 'None'
                  ? `${report.design.insulationType} — ${report.design.insulationThicknessCm} cm`
                  : 'None'
              }
            />
            <Row
              label="Thermal mass"
              value={
                report.design.thermalMassEnabled
                  ? `Enabled — ${report.design.thermalMassThicknessCm} cm floor-core mass`
                  : 'Disabled'
              }
            />
            <Row label="Glazing" value={report.design.glazing} />
            <Row
              label="Window area / door area"
              value={`${report.design.windowAreaM2} m² / ${report.design.doorAreaM2} m²`}
            />
          </div>
          <h3 className="text-sm font-semibold text-slate-300 mt-4 mb-2">
            Opening layout (shared deterministic derivation)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            {report.design.openings.south.windows.map((_, i) => (
              <Row
                key={`sw${i}`}
                label={`South window W${i + 1}`}
                value={`${report.design.openings.south.width} × ${report.design.openings.south.height} m`}
              />
            ))}
            {report.design.openings.north.windows.map((_, i) => (
              <Row
                key={`nw${i}`}
                label={`North window W${report.design.openings.south.count + i + 1}`}
                value={`${report.design.openings.north.width} × ${report.design.openings.north.height} m`}
              />
            ))}
            <Row
              label={`Door (${report.design.openings.door.facade} facade)`}
              value={`${report.design.openings.door.width} × ${report.design.openings.door.height} m`}
            />
          </div>
          <p className="mt-3 text-xs text-slate-500 italic">
            Ground floor: indicative engine-default floor build-up (not user-selected) — the engine
            applies its internal default floor construction; no floor layer is fabricated here.
          </p>
        </Section>

        {/* 5 — Passive Strategy (read-only) */}
        <Section id="report-strategy" title="Passive Strategy (climate-derived recommendation)">
          {!report.strategy ? (
            <EmptyNote>Passive strategy unavailable.</EmptyNote>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                <Row label="Climate mode (authoritative)" value={report.strategy.model.climateMode ?? '—'} />
                <Row label="Primary strategy" value={report.strategy.model.primaryStrategy ?? '—'} />
                <Row
                  label="Secondary strategies"
                  value={
                    report.strategy.model.secondaryStrategies.length > 0
                      ? report.strategy.model.secondaryStrategies.join(', ')
                      : '—'
                  }
                />
                <Row label="Ventilation strategy" value={report.strategy.model.ventilationStrategy ?? '—'} />
                <Row label="Shading strategy" value={report.strategy.model.shadingStrategy ?? '—'} />
                <Row label="Opening strategy" value={report.strategy.model.openingStrategy ?? '—'} />
                <Row
                  label="Airlock"
                  value={
                    report.strategy.model.airlock === null
                      ? '—'
                      : report.strategy.model.airlock
                        ? 'Required'
                        : 'Not required'
                  }
                />
                <Row
                  label="Thermal buffer"
                  value={
                    report.strategy.model.thermalBuffer === null
                      ? '—'
                      : report.strategy.model.thermalBuffer
                        ? 'Recommended'
                        : 'Not required'
                  }
                />
              </div>
              {report.strategy.model.explanation && (
                <p className="mt-3 text-sm text-slate-300">{report.strategy.model.explanation}</p>
              )}
              {report.strategy.model.rulesTriggered.length > 0 && (
                <p className="mt-2 text-xs font-mono text-slate-400">
                  Rules triggered: {report.strategy.model.rulesTriggered.join(' · ')}
                </p>
              )}
              <h3 className="text-sm font-semibold text-slate-300 mt-4 mb-2">
                Recommendation vs current design selection
              </h3>
              <table className="report-table w-full text-sm">
                <thead>
                  <tr>
                    <th className="text-left py-1 pr-3">Concept</th>
                    <th className="text-left py-1 pr-3">Climate-derived recommendation</th>
                    <th className="text-left py-1">Current design selection</th>
                  </tr>
                </thead>
                <tbody>
                  {report.strategy.comparison.map((pair) => (
                    <tr key={pair.concept}>
                      <td className="py-1 pr-3 text-slate-300">{pair.concept}</td>
                      <td className="py-1 pr-3 text-slate-400">{pair.recommendation ?? '—'}</td>
                      <td
                        className={`py-1 font-mono ${
                          pair.represented ? 'text-slate-200' : 'text-slate-500 italic'
                        }`}
                      >
                        {pair.current}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </Section>

        {/* 6 — Thermal Simulation */}
        <Section id="report-simulation" title="Thermal Simulation (SIMULATED / PREDICTED)">
          {!sim ? (
            <EmptyNote>Run a simulation to include thermal results.</EmptyNote>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <StatTile label="Avg indoor" value={`${fmt(sim.avgIndoorC)} °C`} accent="text-cyan-400" />
                <StatTile
                  label="Indoor range"
                  value={`${fmt(sim.minIndoorC)} – ${fmt(sim.maxIndoorC)} °C`}
                  accent="text-cyan-400"
                />
                <StatTile
                  label="Comfort"
                  value={`${fmt(sim.comfortPct, 0)}%`}
                  sub={`${sim.comfortHours} h in ${report.mission.comfortBounds.min}–${report.mission.comfortBounds.max} °C`}
                />
                <StatTile
                  label="Discomfort"
                  value={`${fmt(sim.discomfortDegreeHours, 0)} °C·h`}
                  accent="text-rose-400"
                />
              </div>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">
                Envelope transmittance (ISO 6946 layer methodology)
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <Row label="Wall U" value={`${fmt(sim.uValues.wall_u, 2)} W/m²·K`} />
                <Row label="Roof U" value={`${fmt(sim.uValues.roof_u, 2)} W/m²·K`} />
                <Row label="Floor U" value={`${fmt(sim.uValues.floor_u, 2)} W/m²·K`} />
                <Row label="Window U" value={`${fmt(sim.uValues.window_u, 2)} W/m²·K`} />
              </div>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">
                Energy balance (168 h simulated period)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                <Row label="Wall loss" value={`${fmt(sim.componentLossesKwh.wall_loss_kwh, 1)} kWh`} />
                <Row label="Roof loss" value={`${fmt(sim.componentLossesKwh.roof_loss_kwh, 1)} kWh`} />
                <Row label="Floor loss" value={`${fmt(sim.componentLossesKwh.floor_loss_kwh, 1)} kWh`} />
                <Row label="Window loss" value={`${fmt(sim.componentLossesKwh.window_loss_kwh, 1)} kWh`} />
                {typeof sim.componentLossesKwh.door_loss_kwh === 'number' && (
                  <Row label="Door loss" value={`${fmt(sim.componentLossesKwh.door_loss_kwh, 1)} kWh`} />
                )}
                <Row
                  label="Ventilation loss"
                  value={`${fmt(sim.componentLossesKwh.ventilation_loss_kwh, 1)} kWh`}
                />
                <Row
                  label="Radiation loss"
                  value={`${fmt(sim.componentLossesKwh.radiation_loss_kwh, 1)} kWh`}
                />
                <Row label="Total heat loss" value={`${fmt(sim.totalHeatLossKwh, 1)} kWh`} />
                <Row label="Heating demand" value={`${fmt(sim.heatingDemandKwh, 1)} kWh`} />
                <Row label="Cooling demand" value={`${fmt(sim.coolingDemandKwh, 1)} kWh`} />
                <Row label="Incident solar energy" value={`${fmt(sim.incidentSolarKwh, 1)} kWh`} />
                <Row label="Useful solar thermal gain" value={`${fmt(sim.usefulSolarKwh, 1)} kWh`} />
              </div>
              {(sim.hasInternalGain || sim.hasHourlyDemand) && (
                <p className="mt-3 text-xs text-slate-500">
                  Hourly internal-gain
                  {sim.hasHourlyDemand ? ' and auxiliary heating/cooling power arrays' : ' array'} are
                  available in the Simulation stage evidence charts.
                </p>
              )}
            </>
          )}
        </Section>

        {/* 7 — Heat-Flow & Solar Evidence (real arrays only) */}
        <Section id="report-heatflow" title="Heat-Flow & Solar Evidence">
          {!sim ? (
            <EmptyNote>Run a simulation to include heat-flow and solar evidence.</EmptyNote>
          ) : (
            <>
              {sim.heatFlow.hasData ? (
                <>
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">
                    Hourly component heat flows (W)
                  </h3>
                  <table className="report-table w-full text-xs mb-4">
                    <thead>
                      <tr>
                        <th className="text-left py-1 pr-2">Hour</th>
                        {sim.heatFlow.availableSeries.map((s) => (
                          <th key={s.key} className="text-right py-1 px-2">
                            {s.label}
                          </th>
                        ))}
                        {sim.heatFlow.points.some((p) => typeof p.net_heat_flow === 'number') && (
                          <th className="text-right py-1 pl-2">Net</th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {/* Every 12th hour keeps the printed table on one page; the
                          full-resolution interactive chart remains in the app. */}
                      {sim.heatFlow.points
                        .filter((_, i) => i % 12 === 0)
                        .map((p) => (
                          <tr key={p.hour}>
                            <td className="py-0.5 pr-2 font-mono text-slate-400">{p.time}</td>
                            {sim.heatFlow.availableSeries.map((s) => (
                              <td key={s.key} className="py-0.5 px-2 text-right font-mono text-slate-200">
                                {fmt(p[s.key] as number, 0)}
                              </td>
                            ))}
                            {sim.heatFlow.points.some((pp) => typeof pp.net_heat_flow === 'number') && (
                              <td className="py-0.5 pl-2 text-right font-mono text-slate-200">
                                {fmt(p.net_heat_flow, 0)}
                              </td>
                            )}
                          </tr>
                        ))}
                    </tbody>
                  </table>
                  {sim.hasThermalStorage && (
                    <p className="text-xs text-slate-500">
                      Thermal-storage flow (+ stored / − released) is included in the interactive
                      heat-flow chart; it is internal energy redistribution, not a heat loss.
                    </p>
                  )}
                </>
              ) : (
                <EmptyNote>Component heat-flow arrays are not present in this result — chart omitted.</EmptyNote>
              )}
              {sim.solar.hasData ? (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">Solar evidence (W)</h3>
                  <table className="report-table w-full text-xs">
                    <thead>
                      <tr>
                        <th className="text-left py-1 pr-2">Hour</th>
                        {sim.solar.hasIncident && <th className="text-right py-1 px-2">Incident solar</th>}
                        {sim.solar.hasThermalGain && (
                          <th className="text-right py-1 px-2">Useful thermal gain</th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {sim.solar.points
                        .filter((_, i) => i % 12 === 0)
                        .map((p) => (
                          <tr key={p.hour}>
                            <td className="py-0.5 pr-2 font-mono text-slate-400">{p.time}</td>
                            {sim.solar.hasIncident && (
                              <td className="py-0.5 px-2 text-right font-mono text-slate-200">
                                {fmt(p.incident, 0)}
                              </td>
                            )}
                            {sim.solar.hasThermalGain && (
                              <td className="py-0.5 px-2 text-right font-mono text-slate-200">
                                {fmt(p.thermalGain, 0)}
                              </td>
                            )}
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyNote>Solar arrays are not present in this result — chart omitted.</EmptyNote>
              )}
            </>
          )}
        </Section>

        {/* 8 — Optimization */}
        <Section id="report-optimization" title="Optimization (OPTIMIZED)">
          {!opt ? (
            <EmptyNote>Optimization not run.</EmptyNote>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 mb-3">
                <Row label="Trials" value={`${opt.nTrials}`} />
                <Row label="Objective" value={opt.objectiveDescription} />
                <Row label="Scenario provenance" value={opt.scenarioProvenance ?? '—'} />
                <Row
                  label="Scenario fallback"
                  value={opt.scenarioFallbackUsed === null ? '—' : opt.scenarioFallbackUsed ? 'YES' : 'No'}
                />
              </div>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">
                Ranked candidate designs (weighted multi-objective score)
              </h3>
              <table className="report-table w-full text-xs mb-3">
                <thead>
                  <tr>
                    <th className="text-left py-1 pr-2">#</th>
                    <th className="text-left py-1 pr-2">Insul. (mm)</th>
                    <th className="text-left py-1 pr-2">Windows (m²)</th>
                    <th className="text-left py-1 pr-2">Orientation</th>
                    <th className="text-left py-1 pr-2">Mass</th>
                    <th className="text-right py-1 pr-2">Comfort %</th>
                    <th className="text-right py-1 pr-2">Heat (kWh)</th>
                    <th className="text-right py-1">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {opt.rankedDesigns.slice(0, 8).map((c) => (
                    <tr key={c.rank} className={opt.recommended?.rank === c.rank ? 'text-amber-300' : ''}>
                      <td className="py-0.5 pr-2 font-mono">{c.rank}</td>
                      <td className="py-0.5 pr-2 font-mono">{c.insulation_mm}</td>
                      <td className="py-0.5 pr-2 font-mono">{c.window_area_m2}</td>
                      <td className="py-0.5 pr-2">{c.orientation}</td>
                      <td className="py-0.5 pr-2">{c.thermal_mass_level ?? '—'}</td>
                      <td className="py-0.5 pr-2 text-right font-mono">{fmt(c.comfort_percentage, 0)}</td>
                      <td className="py-0.5 pr-2 text-right font-mono">{fmt(c.heating_demand_kwh, 1)}</td>
                      <td className="py-0.5 text-right font-mono">{fmt(c.overall_score, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {opt.recommended && (
                <p className="text-sm text-slate-300">
                  Recommended: rank {opt.recommended.rank} — {opt.recommended.rationale}
                </p>
              )}
              {opt.baseline.hasBaseline ? (
                <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-x-6">
                  <Row
                    label="Baseline comfort"
                    value={opt.baseline.comfortPct !== null ? `${opt.baseline.comfortPct}%` : '—'}
                  />
                  <Row
                    label="Baseline heating"
                    value={opt.baseline.heatingDemandKwh !== null ? `${opt.baseline.heatingDemandKwh} kWh` : '—'}
                  />
                  <Row
                    label="Baseline total loss"
                    value={opt.baseline.totalHeatLossKwh !== null ? `${opt.baseline.totalHeatLossKwh} kWh` : '—'}
                  />
                </div>
              ) : (
                <p className="mt-3 text-xs text-slate-500 italic">
                  Run a baseline simulation to compare this design — no baseline metrics are shown.
                </p>
              )}
              <div className="mt-4 border-t border-slate-800 pt-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase mb-2">
                  Geometry & shape capability statement
                </h4>
                <p className="text-xs text-slate-400">
                  Supported design parameters: {report.limitations.geometrySupportedParameters.join(', ')}.
                  Supported optimization dimensions:{' '}
                  {report.limitations.geometrySupportedOptimization.join(', ')}.
                  <span className="text-orange-300">
                    {' '}
                    Not currently implemented: {report.limitations.geometryNotImplemented.join(', ')}.
                  </span>
                </p>
              </div>
            </>
          )}
        </Section>

        {/* 9 — Blueprint Artifact (captured from the existing component) */}
        <Section id="report-blueprint" title="Blueprint Artifact">
          {!blueprintArtifacts ? (
            <EmptyNote>Blueprint artifact unavailable.</EmptyNote>
          ) : (
            <div className="space-y-5">
              {blueprintArtifacts.map((a) => (
                <figure key={a.view} className="report-figure">
                  <figcaption className="text-xs font-mono text-slate-400 mb-1">
                    {VIEW_TITLES[a.view]}
                  </figcaption>
                  <div
                    className="bg-white rounded-lg p-2 border border-slate-300"
                    // Captured standalone SVG serialized verbatim from the live
                    // EngineeringBlueprint — no drawing logic is duplicated.
                    dangerouslySetInnerHTML={{ __html: a.svg }}
                  />
                </figure>
              ))}
            </div>
          )}
        </Section>

        {/* 10 — 3D Twin Snapshot */}
        <Section id="report-twin" title="3D Digital Twin Snapshot">
          {!twinPng ? (
            <EmptyNote>3D snapshot unavailable.</EmptyNote>
          ) : (
            <figure className="report-figure">
              <img
                src={twinPng}
                alt="Illustrative parameter-driven digital twin snapshot"
                className="report-twin-img rounded-lg border border-slate-300 w-full"
              />
              <figcaption className="text-xs text-slate-500 mt-1">
                Illustrative parameter-driven digital twin snapshot; engineering values are specified
                in the Design Description.
              </figcaption>
            </figure>
          )}
        </Section>

        {/* 11 — Limitations & Engineering Honesty */}
        <Section id="report-limitations" title="Limitations & Engineering Honesty">
          <ul className="space-y-2">
            {report.limitations.statements.map((s, i) => (
              <li key={i} className="text-sm text-slate-300 flex gap-2">
                <span className="text-amber-500 shrink-0" aria-hidden="true">
                  •
                </span>
                {s}
              </li>
            ))}
          </ul>
        </Section>
      </article>

      {/* Hidden artifact sources (screen-only; feed the capture hooks) */}
      <ArtifactSources />

      {/* Navigation affordance back into the workflow (screen-only) */}
      <div className="no-print text-center">
        <Button variant="ghost" onClick={() => setStage('simulation')}>
          Back to Simulation
        </Button>
      </div>
    </div>
  );
}
