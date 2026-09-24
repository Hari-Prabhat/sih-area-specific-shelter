import {
  Activity,
  ArrowRight,
  Boxes,
  DraftingCompass,
  Globe2,
  Mountain,
  Sun,
  Thermometer,
} from 'lucide-react';
import ThemeToggle from './theme/ThemeToggle';
import { LanguageSelector, useLocale } from './i18n';

/**
 * THERMOSHELTER — Landing page (product-hardening pass)
 * =====================================================
 * Minimal, premium engineering introduction rendered at `/`. One dominant CTA
 * routes to /studio. Honest by construction: no ANSYS/CFD claims, no
 * fabricated metrics — the technical note states the reduced-order scope.
 */

const WORKFLOW: { key: string; icon: JSX.Element }[] = [
  { key: 'stageClimate', icon: <Globe2 className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageMission', icon: <Mountain className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageDesign', icon: <DraftingCompass className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageSimulation', icon: <Thermometer className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageOptimization', icon: <Activity className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageBlueprint', icon: <DraftingCompass className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageTwin', icon: <Boxes className="w-4 h-4" aria-hidden="true" /> },
  { key: 'stageReport', icon: <Sun className="w-4 h-4" aria-hidden="true" /> },
];

const CAPABILITIES: { titleKey: 'capClimateTitle' | 'capSimTitle' | 'capPassiveTitle' | 'capOptTitle' | 'capBlueprintTitle' | 'capTwinTitle'; bodyKey: 'capClimateBody' | 'capSimBody' | 'capPassiveBody' | 'capOptBody' | 'capBlueprintBody' | 'capTwinBody' }[] = [
  { titleKey: 'capClimateTitle', bodyKey: 'capClimateBody' },
  { titleKey: 'capSimTitle', bodyKey: 'capSimBody' },
  { titleKey: 'capPassiveTitle', bodyKey: 'capPassiveBody' },
  { titleKey: 'capOptTitle', bodyKey: 'capOptBody' },
  { titleKey: 'capBlueprintTitle', bodyKey: 'capBlueprintBody' },
  { titleKey: 'capTwinTitle', bodyKey: 'capTwinBody' },
];

export default function LandingPage({ onEnter }: { onEnter: () => void }) {
  const { t } = useLocale();

  return (
    <div className="min-h-screen engineering-grid-bg flex flex-col" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Top bar */}
      <header className="max-w-6xl w-full mx-auto px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' }}
          >
            <Mountain className="w-4.5 h-4.5 text-white" aria-hidden="true" />
          </div>
          <span className="font-semibold tracking-tight">THERMOSHELTER</span>
        </div>
        <div className="flex items-center gap-2">
          <LanguageSelector />
          <ThemeToggle />
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1">
        <section className="max-w-6xl w-full mx-auto px-6 pt-20 pb-16 text-center">
          <p
            className="text-[11px] font-semibold uppercase tracking-[0.3em] mb-6"
            style={{ color: 'var(--accent-primary)' }}
          >
            SIH 2026 · SIH26051 · DRDO - Problem Statement
          </p>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-4">THERMOSHELTER</h1>
          <p className="text-lg md:text-xl mb-6" style={{ color: 'var(--text-secondary)' }}>
            {t('landingTagline')}
          </p>
          <p className="max-w-2xl mx-auto text-sm md:text-base leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>
            {t('landingIntro')}
          </p>
          <p className="max-w-2xl mx-auto text-sm leading-relaxed mb-10" style={{ color: 'var(--text-muted)' }}>
            {t('landingDetail')}
          </p>
          <button
            type="button"
            onClick={onEnter}
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-white text-sm tracking-wide transition-transform hover:scale-[1.02] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]"
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
              boxShadow: '0 8px 24px rgba(34, 211, 238, 0.25)',
            }}
          >
            {t('enterStudio')}
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </button>
        </section>

        {/* The Challenge */}
        <section className="max-w-6xl w-full mx-auto px-6 py-12">
          <div className="panel p-8 max-w-3xl mx-auto">
            <h2 className="text-xs font-semibold uppercase tracking-[0.25em] mb-4" style={{ color: 'var(--accent-primary)' }}>
              {t('theChallenge')}
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {t('challengeBody')}
            </p>
          </div>
        </section>

        {/* Workflow */}
        <section className="max-w-6xl w-full mx-auto px-6 py-12">
          <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-center mb-8" style={{ color: 'var(--text-muted)' }}>
            {t('workflow')}
          </h2>
          <ol className="flex flex-wrap items-center justify-center gap-2">
            {WORKFLOW.map((step, i) => (
              <WorkflowStep key={step.key} label={t(step.key as never)} icon={step.icon} last={i === WORKFLOW.length - 1} />
            ))}
          </ol>
        </section>

        {/* Capabilities */}
        <section className="max-w-6xl w-full mx-auto px-6 py-12">
          <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-center mb-8" style={{ color: 'var(--text-muted)' }}>
            {t('capabilities')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {CAPABILITIES.map((cap) => (
              <div key={cap.titleKey} className="panel p-6">
                <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                  {t(cap.titleKey)}
                </h3>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {t(cap.bodyKey)}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Engineering honesty note — subtle */}
        <section className="max-w-6xl w-full mx-auto px-6 pt-8 pb-16">
          <p className="text-center text-[11px] max-w-2xl mx-auto leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            {t('honestyNote')}
          </p>
        </section>
      </main>

      <footer className="border-t py-5" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto px-6 text-center text-xs" style={{ color: 'var(--text-muted)' }}>
          {t('footer')}
        </div>
      </footer>
    </div>
  );
}

function WorkflowStep({ label, icon, last }: { label: string; icon: JSX.Element; last: boolean }) {
  return (
    <li className="flex items-center gap-2">
      <span
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
      >
        {icon}
        {label}
      </span>
      {!last && <span aria-hidden="true" style={{ color: 'var(--accent-primary)' }}>→</span>}
    </li>
  );
}
