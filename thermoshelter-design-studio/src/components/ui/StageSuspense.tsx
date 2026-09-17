import { Loader2 } from 'lucide-react';

interface StageSuspenseProps {
  /** Which heavyweight view is being prepared, shown honestly to the user. */
  label?: string;
}

/**
 * D3: Suspense fallback for lazily-loaded stage views (3D twin, Blueprint,
 * charts). Indeterminate by design — the application never fabricates
 * progress percentages. Matches the D1 surface language (slate/amber).
 */
export default function StageSuspense({ label = 'stage view' }: StageSuspenseProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center gap-3 py-24 text-slate-400"
    >
      <Loader2 className="w-8 h-8 animate-spin text-amber-400/80" aria-hidden="true" />
      <p className="text-sm font-medium">Preparing {label}…</p>
      <p className="text-xs text-slate-500">Loaded on demand to keep the studio fast.</p>
    </div>
  );
}
