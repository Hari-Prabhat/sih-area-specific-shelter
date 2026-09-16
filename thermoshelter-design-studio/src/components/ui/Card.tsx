import { ReactNode } from 'react';

type CardVariant = 'default' | 'highlighted' | 'panel';

interface CardProps {
  children: ReactNode;
  variant?: CardVariant;
  className?: string;
  /** Accessible name when the card groups interactive content. */
  ariaLabel?: string;
}

const VARIANTS: Record<CardVariant, string> = {
  default: 'bg-slate-800/50 border-slate-700/30',
  highlighted: 'bg-slate-800/70 border-amber-500/30',
  panel: 'bg-slate-900/60 border-slate-700/40',
};

/**
 * D1 primitive: the studio surface. Replaces the repeated
 * `bg-slate-800/50 rounded-xl border border-slate-700/30 p-6` block.
 */
export default function Card({ children, variant = 'default', className = '', ariaLabel }: CardProps) {
  return (
    <section
      aria-label={ariaLabel}
      className={`rounded-xl border p-6 ${VARIANTS[variant]} ${className}`}
    >
      {children}
    </section>
  );
}
