/**
 * THERMOSHELTER — Passive Strategy Stage (D4-B WP1)
 * =================================================
 * READ-ONLY presentation of the backend's authoritative PassiveStrategy
 * recommendation. This stage NEVER mutates ShelterDesign, mission, geometry,
 * materials, ACH, thermal mass, or orientation — it renders the climate
 * strategy and contrasts it with the current design selection.
 *
 * Honesty rules:
 *  - climate_mode (strategy) is the authoritative classification; the coarse
 *    168-hour-window zone in the climate dict is never shown as authoritative.
 *  - Concepts without a corresponding design parameter display the honest
 *    "Not represented in current design parameters" marker.
 *  - The classification is based on the annual climatological/statistical
 *    profile, not solely on the current 168-hour weather window.
 */

import { Compass, DoorOpen, Info, Layers, ShieldCheck, Sun, Thermometer, Wind } from 'lucide-react';
import Card from './ui/Card';
import Button from './ui/Button';
import { useStudioState } from '../store/useStudioState';
import {
  NOT_REPRESENTED,
  PassiveStrategyModel,
  buildStrategyComparison,
  mapStrategyDto,
} from '../services/passiveStrategy';
import { CircleDashed } from 'lucide-react';

/** Tailwind accent per canonical priority level (display only). */
const PRIORITY_STYLE: Record<string, string> = {
  HIGH: 'bg-red-500/15 text-red-300 border-red-500/40',
  MODERATE: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  LOW: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
  MINIMIZED: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
};

/** Climate mode accent — classification display only, mirrors the backend enum. */
const MODE_STYLE: Record<string, string> = {
  'EXTREME COLD': 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40',
  COLD: 'bg-blue-500/15 text-blue-300 border-blue-500/40',
  'HOT DRY': 'bg-orange-500/15 text-orange-300 border-orange-500/40',
  'HOT HUMID': 'bg-teal-500/15 text-teal-300 border-teal-500/40',
  TEMPERATE: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  VARIABLE: 'bg-violet-500/15 text-violet-300 border-violet-500/40',
};

function PriorityBadge({ label, value }: { label: string; value: PassiveStrategyModel['solarCapture'] }) {
  return (
    <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
      <p className="text-xs text-slate-400 uppercase tracking-wider">{label}</p>
      {value ? (
        <span
          className={`inline-block mt-1.5 px-2 py-0.5 rounded-md text-xs font-semibold border ${PRIORITY_STYLE[value] ?? 'bg-slate-500/15 text-slate-300 border-slate-500/40'}`}
        >
          {value}
        </span>
      ) : (
        <span className="block mt-1.5 text-xs text-slate-500">—</span>
      )}
    </div>
  );
}

export default function PassiveStrategyStage() {
  const { climateProfile, design, setStage } = useStudioState();

  // WP3 mapper: honest null for absent/malformed strategy DTOs.
  const model = mapStrategyDto(climateProfile?.strategy);

  // Prerequisite: no climate profile fetched yet.
  if (!climateProfile) {
    return (
      <div className="text-center py-20" role="status">
        <CircleDashed className="w-14 h-14 text-slate-600 mx-auto mb-4" aria-hidden="true" />
        <h3 className="text-xl font-semibold text-slate-400 mb-2">No Climate Profile Loaded</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
          Passive strategy recommendations are derived from the location climate profile.
          Resolve a location in Site &amp; Climate first.
        </p>
        <Button onClick={() => setStage('site-climate')}>Go to Site &amp; Climate</Button>
      </div>
    );
  }

  // Honest state: profile exists but the backend could not derive a strategy.
  if (!model) {
    return (
      <Card ariaLabel="Passive strategy unavailable">
        <div className="text-center py-14" role="status">
          <Info className="w-12 h-12 text-slate-600 mx-auto mb-4" aria-hidden="true" />
          <h3 className="text-lg font-semibold text-slate-300 mb-2">Passive strategy unavailable</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            The backend could not derive a passive strategy for the current climate profile.
            Re-resolve the location in Site &amp; Climate to retry.
          </p>
        </div>
      </Card>
    );
  }

  const comparison = buildStrategyComparison(model, design);
  const modeStyle = MODE_STYLE[model.climateMode ?? ''] ?? 'bg-slate-500/15 text-slate-300 border-slate-500/40';

  return (
    <div className="space-y-6">
      {/* Header + authoritative classification */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
          <Compass className="w-5 h-5 text-amber-400" aria-hidden="true" />
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-bold">Passive Strategy</h2>
            {model.climateMode && (
              <span className={`px-2.5 py-0.5 rounded-md text-xs font-semibold border ${modeStyle}`}>
                {model.climateMode}
              </span>
            )}
            {model.version && (
              <span className="text-[11px] text-slate-500 font-mono">contract v{model.version}</span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Climate-derived design guidance for {climateProfile.climate.city}. Read-only — your
            design selections are never changed by this stage.
          </p>
        </div>
      </div>

      {/* Classification basis note (honest methodology disclosure) */}
      <div className="bg-slate-900/60 border border-slate-700/40 rounded-lg p-3 flex items-start gap-2">
        <Info className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
        <p className="text-xs text-slate-400 leading-relaxed">
          Classification basis: the <strong className="text-slate-300">{model.climateMode ?? 'climate'}</strong> mode is derived
          from the site's annual climatological/statistical profile (NBC/ASHRAE-aligned thresholds) —
          not solely from the current 168-hour weather window. The short weather window drives the
          simulation; the annual statistics drive this classification.
        </p>
      </div>

      {/* Primary + secondary strategies */}
      <Card ariaLabel="Primary and secondary strategies">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Thermometer className="w-4 h-4 text-amber-400" aria-hidden="true" /> Core strategy
        </h3>
        {model.primaryStrategy ? (
          <p className="text-base text-slate-100 font-medium">{model.primaryStrategy}</p>
        ) : (
          <p className="text-sm text-slate-500">Not provided by the backend.</p>
        )}
        {model.secondaryStrategies.length > 0 && (
          <>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-4 mb-2">
              Complementary strategies
            </h4>
            <ul className="space-y-1.5">
              {model.secondaryStrategies.map((s) => (
                <li key={s} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="text-amber-400/70 mt-0.5" aria-hidden="true">▪</span>
                  {s}
                </li>
              ))}
            </ul>
          </>
        )}
      </Card>

      {/* Strategy priorities */}
      <Card ariaLabel="Strategy priorities">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-amber-400" aria-hidden="true" /> Strategy priorities
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <PriorityBadge label="Solar capture" value={model.solarCapture} />
          <PriorityBadge label="Thermal mass" value={model.thermalMass} />
          <PriorityBadge label="Insulation" value={model.insulationPriority} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
          <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
            <p className="text-xs text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Wind className="w-3.5 h-3.5" aria-hidden="true" /> Ventilation
            </p>
            <p className="text-xs text-slate-200 mt-1.5 font-mono break-words">
              {model.ventilationStrategy ?? '—'}
            </p>
          </div>
          <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
            <p className="text-xs text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sun className="w-3.5 h-3.5" aria-hidden="true" /> Shading
            </p>
            <p className="text-xs text-slate-200 mt-1.5 font-mono break-words">
              {model.shadingStrategy ?? '—'}
            </p>
          </div>
          <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
            <p className="text-xs text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <DoorOpen className="w-3.5 h-3.5" aria-hidden="true" /> Openings
            </p>
            <p className="text-xs text-slate-200 mt-1.5 font-mono break-words">
              {model.openingStrategy ?? '—'}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 mt-3">
          <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-2">
            <p className="text-xs text-slate-400">
              Entrance airlock:{' '}
              <span className="text-slate-200 font-semibold">
                {model.airlock === null ? '—' : model.airlock ? 'Required' : 'Not required'}
              </span>
            </p>
          </div>
          <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-2">
            <p className="text-xs text-slate-400">
              Thermal buffer zones:{' '}
              <span className="text-slate-200 font-semibold">
                {model.thermalBuffer === null ? '—' : model.thermalBuffer ? 'Recommended' : 'Not required'}
              </span>
            </p>
          </div>
        </div>
      </Card>

      {/* Recommendation vs current selection — explicitly read-only */}
      <Card ariaLabel="Climate recommendation versus current design selection">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-2">
          <Layers className="w-4 h-4 text-amber-400" aria-hidden="true" /> Recommendation vs current design
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Read-only comparison. The climate-derived recommendation is advisory — applying it remains
          a manual, user-controlled decision in the Geometry &amp; Envelope stage.
        </p>
        <div className="space-y-2">
          <div className="hidden sm:grid grid-cols-12 gap-3 text-[11px] uppercase tracking-wider text-slate-500 px-3">
            <span className="col-span-3">Concept</span>
            <span className="col-span-5">Climate-derived recommendation</span>
            <span className="col-span-4">Current design selection</span>
          </div>
          {comparison.map((pair) => (
            <div
              key={pair.concept}
              className="grid grid-cols-1 sm:grid-cols-12 gap-1.5 sm:gap-3 bg-slate-900/50 border border-slate-700/40 rounded-lg px-3 py-2.5"
            >
              <span className="sm:col-span-3 text-sm text-slate-300 font-medium">{pair.concept}</span>
              <span className="sm:col-span-5 text-xs text-amber-200/90">
                {pair.recommendation ?? '—'}
              </span>
              <span
                className={`sm:col-span-4 text-xs ${pair.represented ? 'text-slate-300' : 'text-slate-500 italic'}`}
              >
                {pair.represented ? pair.current : NOT_REPRESENTED}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Physics-grounded explanation */}
      {model.explanation && (
        <Card ariaLabel="Strategy explanation">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Why this strategy
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">{model.explanation}</p>
        </Card>
      )}

      {/* Explainability: triggered rule identifiers */}
      {model.rulesTriggered.length > 0 && (
        <Card ariaLabel="Triggered classification rules">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Classification rules triggered
          </h3>
          <div className="flex flex-wrap gap-2">
            {model.rulesTriggered.map((rule) => {
              const [id, ...rest] = rule.split(':');
              return (
                <span
                  key={rule}
                  title={rest.join(':').trim() || undefined}
                  className="px-2 py-1 rounded-md bg-slate-900/60 border border-slate-700/50 text-[11px] font-mono text-slate-300"
                >
                  {id.trim()}
                </span>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-500 mt-3">
            Deterministic rule identifiers from the climate strategy engine — hover for the full
            rule description. The classification is explainable and reproducible, not an opaque model.
          </p>
        </Card>
      )}
    </div>
  );
}
