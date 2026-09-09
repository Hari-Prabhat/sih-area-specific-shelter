import React from 'react';
import { AlertTriangle, WifiOff, ServerCrash, HelpCircle, XCircle } from 'lucide-react';

export type ErrorType =
  | 'invalid_location'
  | 'backend_unavailable'
  | 'incomplete_requirements'
  | 'design_generation_failure'
  | 'offline_mode'
  | 'missing_data'
  | 'general';

interface ErrorAlertProps {
  type?: ErrorType;
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

const ERROR_PRESETS: Record<ErrorType, { title: string; icon: React.ElementType }> = {
  invalid_location: {
    title: 'Invalid or Unresolvable Site Location',
    icon: AlertTriangle,
  },
  backend_unavailable: {
    title: 'Engineering Backend Unreachable',
    icon: ServerCrash,
  },
  incomplete_requirements: {
    title: 'Incomplete Mission Parameters',
    icon: HelpCircle,
  },
  design_generation_failure: {
    title: 'Synthesis Pipeline Error',
    icon: XCircle,
  },
  offline_mode: {
    title: 'Operating in Offline Mode',
    icon: WifiOff,
  },
  missing_data: {
    title: 'Climatological Records Unavailable',
    icon: AlertTriangle,
  },
  general: {
    title: 'Engineering System Notice',
    icon: AlertTriangle,
  },
};

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  type = 'general',
  title,
  message,
  actionLabel,
  onAction,
  className = '',
}) => {
  const preset = ERROR_PRESETS[type] || ERROR_PRESETS.general;
  const Icon = preset.icon;

  return (
    <div
      className={`bg-rose-950/40 border border-rose-500/50 rounded-lg p-4 text-slate-200 flex items-start gap-3 shadow-lg ${className}`}
      role="alert"
    >
      <div className="p-1 rounded bg-rose-500/20 text-rose-400 shrink-0 mt-0.5">
        <Icon className="w-5 h-5" />
      </div>

      <div className="flex-1 min-w-0">
        <h5 className="text-sm font-bold text-rose-300 font-mono-data tracking-wide uppercase">
          {title || preset.title}
        </h5>
        <p className="text-xs text-slate-300 mt-1 leading-relaxed">{message}</p>

        {actionLabel && onAction && (
          <div className="mt-3">
            <button
              type="button"
              onClick={onAction}
              className="text-xs font-mono-data font-semibold text-rose-300 hover:text-white bg-rose-900/40 hover:bg-rose-800/60 border border-rose-600/50 px-3 py-1 rounded transition-colors"
            >
              {actionLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
