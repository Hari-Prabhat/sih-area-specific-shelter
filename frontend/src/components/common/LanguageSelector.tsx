import React from "react";
import { Globe } from "lucide-react";
import { useI18n } from "../../i18n/I18nProvider";
import { Language } from "../../i18n/translations";

export const LanguageSelector: React.FC = () => {
  const { language, setLanguage, availableLanguages } = useI18n();

  return (
    <div className="flex items-center gap-1.5">
      <span className="text-slate-400 font-mono hidden md:flex items-center gap-1 text-[11px]">
        <Globe className="w-3.5 h-3.5 text-sky-400" />
        <span>LANG:</span>
      </span>
      <div className="flex items-center gap-0.5 bg-slate-950 p-0.5 rounded-lg border border-slate-800">
        {availableLanguages.map((l) => {
          const isActive = language === l.code;
          return (
            <button
              key={l.code}
              onClick={() => setLanguage(l.code as Language)}
              title={`${l.label} · ${l.nativeLabel}`}
              className={`px-2 py-1 rounded text-[11px] font-semibold transition-all cursor-pointer ${
                isActive
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                  : "text-slate-400 hover:text-white hover:bg-slate-900/60 border border-transparent"
              }`}
            >
              <span className="uppercase tracking-wide">{l.code}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
