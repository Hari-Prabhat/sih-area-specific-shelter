/**
 * THERMOSHELTER — Provenance Panel (D4-B WP5)
 * ===========================================
 * Progressive-disclosure detail panel for the Simulation stage. Shows the
 * real metadata of the weather dataset the simulation consumed, plus the
 * SIMULATED result indicator. Never calls model-derived weather "measured";
 * optional fields absent from the contract are shown as "—" or omitted,
 * never invented. ContextStrip remains the compact at-a-glance indicator;
 * this panel is the detail layer. Field derivation lives in
 * services/provenanceView.ts (unit-tested honesty contract).
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, Database } from 'lucide-react';
import { SimulationClimateProfile } from '../services/api';
import { ProvenanceView, formatProvenanceView } from '../services/provenanceView';
import ProvenanceChip from './ui/ProvenanceChip';

interface ProvenancePanelProps {
  climateProfile: SimulationClimateProfile | null;
  /** True when the displayed results come from the Python simulation (not preset fallbacks). */
  simulated: boolean;
}

function FieldRow({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5 border-b border-slate-700/30 last:border-b-0">
      <span className="text-xs text-slate-400 flex-shrink-0">{label}</span>
      <span className="text-xs text-slate-200 text-right font-mono break-all">
        {value ?? '—'}
      </span>
    </div>
  );
}

export default function ProvenancePanel({ climateProfile, simulated }: ProvenancePanelProps) {
  const [open, setOpen] = useState(false);

  // No profile → no provenance to disclose. Never render a misleading panel.
  const view: ProvenanceView = formatProvenanceView(climateProfile, simulated);
  if (!view.visible) return null;

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700/30">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="provenance-detail"
        className="w-full flex items-center justify-between gap-3 px-5 py-3.5 text-left"
      >
        <span className="flex items-center gap-2.5 min-w-0 flex-wrap">
          <Database className="w-4 h-4 text-slate-400 flex-shrink-0" aria-hidden="true" />
          <span className="text-sm font-semibold text-slate-300">Simulation Data Provenance</span>
          {view.provenance && (
            <ProvenanceChip value={view.provenance} fallbackUsed={view.fallbackUsed} compact />
          )}
          {simulated && <ProvenanceChip value="SIMULATED" compact />}
        </span>
        <span className="text-slate-500 flex-shrink-0">
          {open ? (
            <ChevronDown className="w-4 h-4" aria-hidden="true" />
          ) : (
            <ChevronRight className="w-4 h-4" aria-hidden="true" />
          )}
        </span>
      </button>

      {open && (
        <div id="provenance-detail" className="px-5 pb-4 pt-1 border-t border-slate-700/30">
          {/* Fallback disclosure — explicit, never silent */}
          {view.fallbackUsed && (
            <div
              className="mb-3 px-3 py-2 bg-orange-500/10 border border-orange-500/30 rounded-lg text-xs text-orange-300"
              role="note"
            >
              FALLBACK DATASET in use — the live provider was unreachable and an explicitly
              labelled bundled/design fallback was served. These are NOT live observations.
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8">
            <div>
              <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mt-2 mb-1">
                Weather dataset
              </h4>
              <FieldRow label="Provider" value={view.provider} />
              <FieldRow label="Data mode" value={view.dataMode} />
              <FieldRow
                label="Provenance"
                value={view.provenance ? view.provenance.replace(/_/g, ' ').toLowerCase() : null}
              />
              <FieldRow
                label="Fallback used"
                value={view.fallbackUsed ? 'Yes — explicit fallback' : 'No'}
              />
              <FieldRow label="Hours in window" value={view.hours !== null ? String(view.hours) : null} />
              <FieldRow label="Period" value={view.periodLabel} />
              <FieldRow label="Retrieved" value={view.retrievedLabel} />
              <FieldRow label="Provider notes" value={view.notes} />
            </div>
            <div>
              <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mt-2 mb-1">
                Site &amp; result
              </h4>
              <FieldRow label="Coordinates" value={view.coordinatesLabel} />
              <FieldRow label="Elevation (model-derived)" value={view.elevationLabel} />
              <FieldRow label="Timezone" value={view.timezone} />
              <FieldRow label="Location label" value={view.locationLabel} />
              <FieldRow
                label="Result provenance"
                value={simulated ? 'SIMULATED — Python thermal engine output' : null}
              />
              <FieldRow
                label="Result basis"
                value={simulated ? 'Computed from the weather dataset above — not a measurement' : null}
              />
            </div>
          </div>

          <p className="text-[11px] text-slate-500 mt-3 leading-relaxed">
            Weather values are provider model/forecast data for the requested coordinates — gridded
            model-derived estimates, not on-site measurements. Simulation outputs are calculated by
            the Python thermal engine from that dataset.
          </p>
        </div>
      )}
    </div>
  );
}
