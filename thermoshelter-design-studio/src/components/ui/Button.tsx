import { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
  loadingText?: string;
  icon?: ReactNode;
  /** Full-width button (useful in card grids). */
  block?: boolean;
}

/**
 * D1 primitive: the single action language for the whole studio.
 * One primary style (cyan technical identity; amber is reserved for
 * thermal/solar data values, not actions) — no per-tab CTA colors.
 * Enforces visible keyboard focus, honest disabled states and loading feedback.
 */
export default function Button({
  variant = 'primary',
  loading = false,
  loadingText,
  icon,
  block = false,
  className = '',
  children,
  disabled,
  type = 'button',
  ...rest
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center gap-2 font-semibold rounded-lg transition-all ' +
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ' +
    'disabled:opacity-50 disabled:cursor-not-allowed';

  const sizes = 'px-5 py-2.5 text-sm';

  const variants: Record<ButtonVariant, string> = {
    primary:
      'bg-gradient-to-r from-cyan-500 to-sky-600 text-slate-950 shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-sky-500',
    secondary:
      'bg-slate-700/70 text-slate-100 border border-slate-600/60 hover:bg-slate-600/70',
    ghost: 'text-slate-300 hover:text-slate-100 hover:bg-slate-700/50',
    danger: 'bg-red-600/90 text-white hover:bg-red-500',
  };

  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      className={`${base} ${sizes} ${variants[variant]} ${block ? 'w-full' : ''} ${className}`}
      {...rest}
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : icon}
      <span>{loading ? loadingText ?? 'Working…' : children}</span>
    </button>
  );
}
