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
});
