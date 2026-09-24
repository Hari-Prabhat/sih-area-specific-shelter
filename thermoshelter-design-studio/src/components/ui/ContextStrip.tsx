import { MapPin, Mountain, Ruler, Thermometer } from 'lucide-react';
import ProvenanceChip from './ProvenanceChip';
import { ProvenanceValue } from '../../theme/tokens';

export interface ContextStripData {
  location?: string | null;
  /** Authoritative site classification (strategy.climate_mode) — the primary climate label. */
  climateZone?: string | null;
  /** Provenance-only coarse zone of the current weather window (climate dict climate_zone).
   *  Rendered with an explicit scope label so it can never be confused with the
 *  authoritative classification above. */
  windowZoneLabel?: string | null;
  provenance?: ProvenanceValue | string | null;
  fallbackUsed?: boolean;
  windowHours?: number | null;
  materialName?: string | null;
  insulationLabel?: string | null;
  orientationDeg?: number | null;
  geometryLabel?: string | null;
  /** Authoritative canonical shelter form (rectangular/cylindrical/dome/pyramid). */
  shapeLabel?: string | null;
}

interface ContextStripProps {
  data: ContextStripData;
}

/**
 * D1 primitive: the persistent CURRENT DESIGN context strip. Every value is
 * derived from the canonical ShelterDesign / ClimateProfile by the caller;
 * anything unavailable is omitted — never fabricated. Backend health is
 * deliberately NOT displayed here (available via /api/health for monitoring).
 */
export default function ContextStrip({ data }: ContextStripProps) {
  const zone = data.climateZone ? data.climateZone.replace(/_/g, ' ').toUpperCase() : null;
  const windowZone = data.windowZoneLabel ? data.windowZoneLabel.replace(/_/g, ' ').toUpperCase() : null;
  const hasDesign = Boolean(data.materialName || data.geometryLabel);

  return (
    <div
      role="status"
      aria-label="Current design context"
      className="border rounded-xl px-4 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      <span
        className="text-[10px] font-semibold uppercase tracking-widest"
        style={{ color: 'var(--text-muted)' }}
      >
        {hasDesign ? 'Current Design' : 'No design configured yet'}
      </span>

      {data.location && (
        <span className="inline-flex items-center gap-1.5 font-semibold" style={{ color: 'var(--text-primary)' }}>
          <MapPin className="w-3.5 h-3.5" style={{ color: 'var(--thermal)' }} aria-hidden="true" />
          {data.location}
        </span>
      )}
      {zone && (
        <span
          className="font-medium"
          style={{ color: 'var(--accent-primary)' }}
          title="Authoritative site climate classification (annual climatological profile)"
        >
          {zone}
        </span>
      )}
      {windowZone && (
        <span
          style={{ color: 'var(--text-muted)' }}
          title="Coarse zone of the current weather window only — provenance context, NOT the site classification"
        >
          ({windowZone} window)
        </span>
      )}
      {data.provenance && (
        <ProvenanceChip value={data.provenance} fallbackUsed={data.fallbackUsed} compact />
      )}
      {data.windowHours != null && (
        <span className="inline-flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
          <Thermometer className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
          {data.windowHours} h window
        </span>
      )}

      <span className="w-px h-4" style={{ background: 'var(--border-strong)' }} aria-hidden="true" />

      {data.geometryLabel && (
        <span className="inline-flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
          <Ruler className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
          {data.geometryLabel}
        </span>
      )}
      {data.shapeLabel && (
        <span className="capitalize" style={{ color: 'var(--text-secondary)' }}>
          {data.shapeLabel}
        </span>
      )}
      {data.materialName && <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{data.materialName}</span>}
      {data.insulationLabel && <span style={{ color: 'var(--text-secondary)' }}>{data.insulationLabel}</span>}
      {data.orientationDeg != null && (
        <span style={{ color: 'var(--text-secondary)' }}>
          {data.orientationDeg}° {data.orientationDeg >= 315 || data.orientationDeg < 45 ? 'N' : data.orientationDeg < 135 ? 'E' : data.orientationDeg < 225 ? 'S' : 'W'}-facing
        </span>
      )}

      {!data.location && (
        <Mountain className="w-3.5 h-3.5 ml-auto" style={{ color: 'var(--text-muted)' }} aria-hidden="true" />
      )}
    </div>
  );
}
