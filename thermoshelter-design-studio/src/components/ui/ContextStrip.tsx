import { MapPin, Mountain, Ruler, Thermometer } from 'lucide-react';
import ProvenanceChip from './ProvenanceChip';
import { ProvenanceValue } from '../../theme/tokens';

export interface ContextStripData {
  location?: string | null;
  climateZone?: string | null;
  provenance?: ProvenanceValue | string | null;
  fallbackUsed?: boolean;
  windowHours?: number | null;
  materialName?: string | null;
  insulationLabel?: string | null;
  orientationDeg?: number | null;
  geometryLabel?: string | null;
  backendHealth?: 'connecting' | 'connected' | 'unavailable';
}

interface ContextStripProps {
  data: ContextStripData;
}

const HEALTH_STYLES: Record<NonNullable<ContextStripData['backendHealth']>, { dot: string; label: string; title: string }> = {
  connected: { dot: 'bg-emerald-400', label: 'Backend', title: 'FastAPI backend reachable' },
  connecting: { dot: 'bg-slate-400 animate-pulse', label: 'Connecting', title: 'Checking FastAPI backend…' },
  unavailable: { dot: 'bg-red-400 animate-pulse', label: 'Backend offline', title: 'FastAPI backend not reachable — start it to run simulations' },
};

/**
 * D1 primitive: the persistent engineering-context strip. Every value is
 * derived from actual application state by the caller; anything unavailable
 * is omitted — never fabricated. This is the single glanceable answer to
 * "what am I designing, where, and on what data?".
 */
export default function ContextStrip({ data }: ContextStripProps) {
  const health = data.backendHealth ? HEALTH_STYLES[data.backendHealth] : null;
  const zone = data.climateZone ? data.climateZone.replace(/_/g, ' ').toUpperCase() : null;

  return (
    <div
      role="status"
      aria-label="Current engineering context"
      className="bg-slate-900/70 border border-slate-700/40 rounded-xl px-4 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs"
    >
      {data.location && (
        <span className="inline-flex items-center gap-1.5 text-slate-100 font-semibold">
          <MapPin className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
          {data.location}
        </span>
      )}
      {zone && <span className="text-sky-300 font-medium">{zone}</span>}
      {data.provenance && (
        <ProvenanceChip value={data.provenance} fallbackUsed={data.fallbackUsed} compact />
      )}
      {data.windowHours != null && (
        <span className="inline-flex items-center gap-1 text-slate-400">
          <Thermometer className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
          {data.windowHours} h window
        </span>
      )}

      <span className="w-px h-4 bg-slate-700/60" aria-hidden="true" />

      {data.materialName && <span className="text-slate-200 font-medium">{data.materialName}</span>}
      {data.insulationLabel && <span className="text-slate-400">{data.insulationLabel}</span>}
      {data.orientationDeg != null && (
        <span className="text-slate-400">
          {data.orientationDeg}° {data.orientationDeg >= 315 || data.orientationDeg < 45 ? 'N' : data.orientationDeg < 135 ? 'E' : data.orientationDeg < 225 ? 'S' : 'W'}-facing
        </span>
      )}
      {data.geometryLabel && (
        <span className="inline-flex items-center gap-1 text-slate-400">
          <Ruler className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
          {data.geometryLabel}
        </span>
      )}

      {health && (
        <span className="ml-auto inline-flex items-center gap-1.5 text-slate-400" title={health.title}>
          <span className={`w-2 h-2 rounded-full ${health.dot}`} aria-hidden="true" />
          {health.label}
        </span>
      )}
      {!data.location && (
        <Mountain className="w-3.5 h-3.5 text-slate-600 ml-auto" aria-hidden="true" />
      )}
    </div>
  );
}
