import { DATA_MODE_PROVENANCE, PROVENANCE_DESCRIPTORS, ProvenanceValue } from '../../theme/tokens';

interface ProvenanceChipProps {
  /** Canonical provenance value, or a lowercase Phase B data_mode ('live' | 'forecast' | …). */
  value: ProvenanceValue | string;
  /** When true, the chip explicitly discloses provider fallback — never silent. */
  fallbackUsed?: boolean;
  /** Compact rendering for dense rows (candidate cards, context strip). */
  compact?: boolean;
  className?: string;
}

/**
 * D1 primitive: provenance disclosure. Distinguishes weather-provenance
 * (input data) from result-provenance (SIMULATED / OPTIMIZED) and never
 * presents fallback data as live data. Renders nothing when no value exists —
 * an absent dataset must not be dressed up as a labelled one.
 */
export default function ProvenanceChip({ value, fallbackUsed = false, compact = false, className = '' }: ProvenanceChipProps) {
  const canonical = (Object.prototype.hasOwnProperty.call(PROVENANCE_DESCRIPTORS, value)
    ? value
    : DATA_MODE_PROVENANCE[value]) as ProvenanceValue | undefined;

  if (!canonical) return null;

  const d = PROVENANCE_DESCRIPTORS[canonical];
  const title =
    canonical === 'FALLBACK' || fallbackUsed
      ? 'Explicit fallback dataset served because the live provider was unreachable. NOT live weather.'
      : d.family === 'weather'
        ? `Weather dataset provenance: ${d.label}. Input data for simulation.`
        : `Result provenance: ${d.label}. Computed by the Python backend.`;

  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 border rounded-md font-semibold uppercase tracking-wide ${
        compact ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
      } ${d.tailwind} ${className}`}
    >
      {d.label}
      {fallbackUsed && canonical !== 'FALLBACK' && (
        <span className="text-orange-300">· provider fallback</span>
      )}
    </span>
  );
}
