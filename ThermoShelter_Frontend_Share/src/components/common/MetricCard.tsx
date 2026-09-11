import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: string;
  deltaType?: "positive" | "negative" | "neutral";
  icon?: React.ReactNode;
  subtext?: string;
  badge?: string;
  accentColor?: "cyan" | "green" | "orange" | "red" | "gray";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  delta,
  deltaType = "neutral",
  icon,
  subtext,
  badge,
  accentColor = "cyan",
}) => {
  const borderColors = {
    cyan: "border-sky-500/40 hover:border-sky-400",
    green: "border-emerald-500/40 hover:border-emerald-400",
    orange: "border-amber-500/40 hover:border-amber-400",
    red: "border-rose-500/40 hover:border-rose-400",
    gray: "border-slate-700 hover:border-slate-600",
  };

  const deltaColors = {
    positive: "text-emerald-400 bg-emerald-950/40 border-emerald-800/50",
    negative: "text-rose-400 bg-rose-950/40 border-rose-800/50",
    neutral: "text-slate-400 bg-slate-800/50 border-slate-700/50",
  };

  return (
    <div
      className={`bg-slate-900/90 border ${borderColors[accentColor]} rounded-xl p-4 transition-all duration-200 shadow-lg hover:shadow-cyan-950/20 h-full flex flex-col justify-between`}
    >
      <div>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
          <span className="font-medium tracking-wide uppercase">{label}</span>
          {icon && <span className="text-slate-400 text-sm">{icon}</span>}
        </div>

        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-bold font-mono text-white tracking-tight">
            {value}
          </span>
          {unit && <span className="text-xs text-slate-400 font-mono">{unit}</span>}
        </div>
      </div>

      <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs min-h-[28px]">
        {delta ? (
          <span
            className={`px-1.5 py-0.5 rounded border text-[11px] font-mono ${deltaColors[deltaType]}`}
          >
            {delta}
          </span>
        ) : subtext ? (
          <span className="text-slate-400 truncate text-[11px]">{subtext}</span>
        ) : (
          <span className="text-slate-600 text-[11px] font-mono">--</span>
        )}

        {badge && (
          <span className="text-[10px] font-semibold uppercase tracking-wider text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded-full border border-sky-800/50">
            {badge}
          </span>
        )}
      </div>
    </div>
  );
};
