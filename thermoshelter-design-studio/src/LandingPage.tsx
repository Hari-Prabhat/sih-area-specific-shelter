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
 * THERMOSHELTER — Landing page (visual polish pass)
 * =====================================================
 * Premium engineering introduction rendered at `/`: animated thermal-field
 * background (pure SVG+CSS, reduced-motion aware), abstract shelter
 * wireframe hero, and focused sections that answer: what is it, how does
 * it work, what does it produce. Honest by construction — no ANSYS/CFD
 * claims, no fabricated metrics. Sections reveal gently on first paint.
 */

/* ---------- Animated engineering field (SVG background) ---------- */
function EngineeringField() {
  return (
    <div className="ts-field" aria-hidden="true">
      <svg preserveAspectRatio="xMidYMid slice" viewBox="0 0 1200 800">
        {/* Thermal contour field — slow-drifting concentric rings */}
        <g className="ts-contour-group">
          <ellipse className="ts-contour" cx="950" cy="620" rx="420" ry="300" />
          <ellipse className="ts-contour" cx="950" cy="620" rx="330" ry="230" />
          <ellipse className="ts-contour ts-contour-warm" cx="950" cy="620" rx="240" ry="160" />
          <ellipse className="ts-contour" cx="950" cy="620" rx="150" ry="95" />
          <ellipse className="ts-contour" cx="160" cy="140" rx="280" ry="200" />
          <ellipse className="ts-contour ts-contour-warm" cx="160" cy="140" rx="190" ry="130" />
          <ellipse className="ts-contour" cx="160" cy="140" rx="110" ry="70" />
        </g>

        {/* Heat-flow lines — dashed paths suggesting convection */}
        <path className="ts-flowline" d="M 0 640 C 200 600, 380 680, 600 640 S 1000 560, 1200 620" />
        <path className="ts-flowline" d="M 0 700 C 220 660, 400 740, 640 700 S 1020 630, 1200 690" style={{ animationDelay: '-5s' }} />
        <path className="ts-flowline" d="M 0 120 C 240 160, 420 90, 660 130 S 1040 190, 1200 140" style={{ animationDelay: '-9s' }} />

        {/* Crosshair ticks — technical-drawing detail */}
        <g className="ts-crosshair">
          <line x1="80" y1="60" x2="80" y2="100" />
          <line x1="60" y1="80" x2="100" y2="80" />
          <line x1="1120" y1="700" x2="1120" y2="740" />
          <line x1="1100" y1="720" x2="1140" y2="720" />
        </g>

        {/* Abstract shelter wireframe — parametric envelope cross-section
            (gabled envelope with solar rays and a heat-flow plume) */}
        <g className="ts-shelter" transform="translate(840, 430)">
          <path d="M -90 60 L 0 -55 L 90 60 Z" />
          <path d="M -60 60 L -60 130 L 60 130 L 60 60" />
          <path d="M -90 60 L -60 60 M 90 60 L 60 60" />
          {/* Envelope resistance arrows */}
          <line x1="0" y1="-20" x2="0" y2="0" />
          <line x1="-45" y1="45" x2="-45" y2="65" />
          <line x1="45" y1="45" x2="45" y2="65" />
        </g>

        {/* Solar rays onto the shelter roof */}
        <g>
          <line className="ts-solar-ray" x1="800" y1="330" x2="840" y2="380" style={{ animationDelay: '0s' }} />
          <line className="ts-solar-ray" x1="850" y1="310" x2="872" y2="372" style={{ animationDelay: '2.5s' }} />
          <line className="ts-solar-ray" x1="905" y1="330" x2="906" y2="378" style={{ animationDelay: '5s' }} />
        </g>

        {/* Thermal-flow particles rising along the field */}
        <g>
          <circle className="ts-particle" cx="240" cy="700" r="2.2" />
          <circle className="ts-particle ts-particle-warm" cx="420" cy="740" r="1.8" style={{ animationDelay: '-6s' }} />
          <circle className="ts-particle" cx="620" cy="720" r="2" style={{ animationDelay: '-11s' }} />
          <circle className="ts-particle ts-particle-warm" cx="760" cy="760" r="1.6" style={{ animationDelay: '-3s' }} />
          <circle className="ts-particle" cx="1020" cy="710" r="2.4" style={{ animationDelay: '-14s' }} />
        </g>
      </svg>
    </div>
  );
}

/* ---------- Landing content data ---------- */

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

const PIPELINE_STEPS = [
  { num: '01', titleKey: 'stageClimate', bodyKey: 'howClimate' },
  { num: '02', titleKey: 'stageMission', bodyKey: 'howMission' },
  { num: '03', titleKey: 'stageDesign', bodyKey: 'howDesign' },
  { num: '04', titleKey: 'stageSimulation', bodyKey: 'howSimulation' },
  { num: '05', titleKey: 'stageOptimization', bodyKey: 'howOptimization' },
  { num: '06', titleKey: 'stageBlueprint', bodyKey: 'howBlueprint' },
  { num: '07', titleKey: 'stageReport', bodyKey: 'howReport' },
] as const;

const OUTPUTS = [
  { titleKey: 'outThermalTitle', bodyKey: 'outThermalBody' },
  { titleKey: 'outOptimizedTitle', bodyKey: 'outOptimizedBody' },
  { titleKey: 'outBlueprintTitle', bodyKey: 'outBlueprintBody' },
  { titleKey: 'outTwinTitle', bodyKey: 'outTwinBody' },
] as const;

const CLIMATES = [
  { titleKey: 'climColdTitle', bodyKey: 'climColdBody' },
  { titleKey: 'climHotDryTitle', bodyKey: 'climHotDryBody' },
  { titleKey: 'climHumidTitle', bodyKey: 'climHumidBody' },
  { titleKey: 'climCompositeTitle', bodyKey: 'climCompositeBody' },
] as const;

export default function LandingPage({ onEnter }: { onEnter: () => void }) {
  const { t } = useLocale();

  return (
    <div className="relative min-h-screen engineering-grid-bg flex flex-col overflow-hidden" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <EngineeringField />

      {/* Top bar */}
      <header className="relative z-10 max-w-6xl w-full mx-auto px-6 py-5 flex items-center justify-between">
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
      <main className="relative z-10 flex-1">
        <section className="max-w-6xl w-full mx-auto px-6 pt-16 pb-16 text-center">
          <p
            className="ts-reveal ts-reveal-1 text-[11px] font-semibold uppercase tracking-[0.3em] mb-6"
            style={{ color: 'var(--accent-primary)' }}
          >
            SIH 2026 · SIH26051 · DRDO - Problem Statement
          </p>
          <h1 className="ts-reveal ts-reveal-1 text-5xl md:text-6xl font-bold tracking-tight mb-4">THERMOSHELTER</h1>
          <p className="ts-reveal ts-reveal-2 text-lg md:text-xl mb-6" style={{ color: 'var(--text-secondary)' }}>
            {t('landingTagline')}
          </p>
          <p className="ts-reveal ts-reveal-2 max-w-2xl mx-auto text-sm md:text-base leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>
            {t('landingIntro')}
          </p>
          <p className="ts-reveal ts-reveal-2 max-w-2xl mx-auto text-sm leading-relaxed mb-10" style={{ color: 'var(--text-muted)' }}>
            {t('landingDetail')}
          </p>
          <button
            type="button"
            onClick={onEnter}
            className="ts-reveal ts-reveal-3 inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-white text-sm tracking-wide transition-transform hover:scale-[1.02] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]"
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
              boxShadow: '0 8px 24px rgba(34, 211, 238, 0.25)',
            }}
          >
            {t('enterStudio')}
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </button>
        </section>

        {/* How It Works — numbered pipeline */}
        <section className="max-w-6xl w-full mx-auto px-6 py-14">
          <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-center mb-10" style={{ color: 'var(--text-muted)' }}>
            {t('howItWorks')}
          </h2>
          <ol className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PIPELINE_STEPS.map((step) => (
              <li key={step.num} className="panel p-5 flex gap-3">
                <span className="text-lg font-bold font-mono leading-none pt-0.5" style={{ color: 'var(--accent-primary)' }}>
                  {step.num}
                </span>
                <div>
                  <h3 className="text-sm font-semibold mb-1">{t(step.titleKey as never)}</h3>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                    {t(step.bodyKey as never)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        {/* The Challenge */}
        <section className="max-w-6xl w-full mx-auto px-6 py-10">
          <div className="panel p-8 max-w-3xl mx-auto">
            <h2 className="text-xs font-semibold uppercase tracking-[0.25em] mb-4" style={{ color: 'var(--accent-primary)' }}>
              {t('theChallenge')}
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {t('challengeBody')}
            </p>
          </div>
        </section>

        {/* Design → Analysis → Decision — core value flow */}
        <section className="max-w-6xl w-full mx-auto px-6 py-14">
          <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-center mb-10" style={{ color: 'var(--text-muted)' }}>
            {t('designDecisionTitle')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ValueStage
              label={t('designStage')}
              detail={t('designStageBody')}
              icon={<DraftingCompass className="w-5 h-5" aria-hidden="true" />}
            />
            <ValueStage
              label={t('analysisStage')}
              detail={t('analysisStageBody')}
              icon={<Thermometer className="w-5 h-5" aria-hidden="true" />}
              thermal
            />
            <ValueStage
              label={t('decisionStage')}
              detail={t('decisionStageBody')}
              icon={<Activity className="w-5 h-5" aria-hidden="true" />}
            />
          </div>
        </section>

        {/* Workflow chips */}
        <section className="max-w-6xl w-full mx-auto px-6 py-10">
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
        <section className="max-w-6xl w-full mx-auto px-6 py-14">
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

        {/* Built for extreme climates */}
        <section className="max-w-6xl w-full mx-auto px-6 py-14">
          <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-center mb-8" style={{ color: 'var(--text-muted)' }}>
            {t('extremeClimatesTitle')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {CLIMATES.map((c) => (
              <div key={c.titleKey} className="panel p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Mountain className="w-4 h-4" aria-hidden="true" style={{ color: 'var(--accent-primary)' }} />
                  <h3 className="text-sm font-semibold">{t(c.titleKey as never)}</h3>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {t(c.bodyKey as never)}
                </p>
              </div>
            ))}
          </div>
          <p className="text-center text-[11px] mt-4" style={{ color: 'var(--text-muted)' }}>
            {t('climatesDisclaimer')}
          </p>
        </section>

        {/* What ThermoShelter generates */}
        <section className="max-w-6xl w-full mx-auto px-6 py-14">
          <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-center mb-8" style={{ color: 'var(--text-muted)' }}>
            {t('outputsTitle')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {OUTPUTS.map((o) => (
              <div key={o.titleKey} className="panel p-5">
                <h3 className="text-sm font-semibold mb-2">{t(o.titleKey as never)}</h3>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {t(o.bodyKey as never)}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Engineering honesty note — subtle */}
        <section className="max-w-6xl w-full mx-auto px-6 pt-8 pb-14">
          <p className="text-center text-[11px] max-w-2xl mx-auto leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            {t('honestyNote')}
          </p>
        </section>

        {/* Final CTA */}
        <section className="max-w-6xl w-full mx-auto px-6 pb-20 text-center">
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
      </main>

      <footer className="relative z-10 border-t py-5" style={{ borderColor: 'var(--border)' }}>
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

function ValueStage({ label, detail, icon, thermal }: { label: string; detail: string; icon: JSX.Element; thermal?: boolean }) {
  return (
    <div className="panel p-6 text-center">
      <div
        className="w-10 h-10 mx-auto mb-3 rounded-lg flex items-center justify-center"
        style={{ background: thermal ? 'color-mix(in srgb, var(--thermal) 12%, transparent)' : 'color-mix(in srgb, var(--accent-primary) 12%, transparent)', color: thermal ? 'var(--thermal)' : 'var(--accent-primary)' }}
      >
        {icon}
      </div>
      <h3 className="text-sm font-semibold uppercase tracking-wider mb-1.5">{label}</h3>
      <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
        {detail}
      </p>
    </div>
  );
}
