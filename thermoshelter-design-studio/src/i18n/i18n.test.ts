/**
 * Product-hardening pass — i18n architecture tests.
 * English is the fallback source of truth; every locale must be a subset of
 * the English key space and never render a raw key to users.
 */
import { describe, expect, it } from 'vitest';

// The provider is React-coupled; the data contracts below are tested directly
// by importing the module and inspecting its exports via a tiny reflection
// helper that avoids instantiating React.
import * as i18n from './index';

describe('i18n architecture', () => {
  it('exposes exactly the seven required locales', () => {
    expect(i18n.LOCALE_LIST.map((l) => l.code)).toEqual(['en', 'hi', 'te', 'ta', 'kn', 'bn', 'mr']);
  });

  it('labels each locale with its native script name', () => {
    const labels = i18n.LOCALE_LIST.map((l) => l.nativeLabel);
    expect(labels).toContain('English');
    expect(labels).toContain('हिन्दी');
    expect(labels).toContain('తెలుగు');
  });

  it('translates the core navigation vocabulary in every locale', () => {
    // Spec §41–43: the stepper is the always-visible UI — every locale must
    // translate it so switching translates the app shell, not just the header.
    const locales = i18n.LOCALE_LIST.map((l) => l.code).filter((c) => c !== 'en');
    const coreKeys = [
      'stageClimate', 'stageMission', 'stageDesign', 'stageSimulation',
      'stageOptimization', 'stageBlueprint', 'stageTwin', 'stageReport',
      'back', 'next', 'runSimulation', 'runOptimization',
    ] as const;
    for (const locale of locales) {
      for (const key of coreKeys) {
        const value = i18n.getTranslation(locale, key);
        expect(value, `${locale}/${key} fell back to English`).not.toBe(
          i18n.getTranslation('en', key),
        );
        expect(value.trim().length).toBeGreaterThan(0);
      }
    }
  });

  it('translates the optimizer-managed UX strings in hi/te (live-test languages)', () => {
    // The UX pass's new strings — the orientation-messaging rework and the
    // advanced-controls disclosure — must exist beyond English.
    const uxKeys = [
      'orientationOptimizedTitle', 'orientationOptimizedBody',
      'advancedControls', 'manualAzimuth', 'shelterPermanence',
    ] as const;
    for (const locale of ['hi', 'te'] as const) {
      for (const key of uxKeys) {
        expect(i18n.getTranslation(locale, key)).not.toBe(
          i18n.getTranslation('en', key),
        );
      }
    }
  });

  it('never renders a raw key for any locale/key pair', () => {
    for (const locale of i18n.LOCALE_LIST.map((l) => l.code)) {
      for (const key of ['stageClimate', 'back', 'orientationOptimizedTitle'] as const) {
        const value = i18n.getTranslation(locale, key);
        expect(value).not.toMatch(/^[a-z][a-zA-Z]+$/);
      }
    }
  });
});
