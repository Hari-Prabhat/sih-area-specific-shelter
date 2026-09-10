import React from "react";

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  badge?: string;
  action?: React.ReactNode;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  badge,
  action,
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-6 border-b border-slate-800 gap-3">
      <div>
        <div className="flex items-center gap-2.5">
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            {title}
          </h1>
          {badge && (
            <span className="text-[11px] font-semibold text-sky-400 bg-sky-950/80 px-2.5 py-0.5 rounded-full border border-sky-800/60 font-mono">
              {badge}
            </span>
          )}
        </div>
        {subtitle && (
          <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="flex items-center gap-3">{action}</div>}
    </div>
  );
};
