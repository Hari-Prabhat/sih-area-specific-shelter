import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

/**
 * THERMOSHELTER — Theme system (product-hardening pass)
 * =====================================================
 * Semantic design tokens are defined in index.css on `:root[data-theme='dark']`
 * and `:root[data-theme='light']`; every component consumes the variables —
 * no hard-coded theme colors. First visit respects system preference; an
 * explicit selection persists to localStorage. index.html applies the stored
 * theme BEFORE first paint (no wrong-theme flash).
 */
const STORAGE_KEY = 'thermoshelter.theme';

export type Theme = 'dark' | 'light';

function readStoredTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'light') return stored;
  } catch {
    /* storage unavailable */
  }
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export function useTheme(): { theme: Theme; toggleTheme: () => void } {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* persistence unavailable */
    }
  }, [theme]);

  return { theme, toggleTheme: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')) };
}

/** Compact accessible toggle: ☀ / ☾ with a screen-reader label. */
export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={isDark ? 'Light theme' : 'Dark theme'}
      className="p-2 rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)] text-[var(--text-secondary)] hover:text-[var(--accent-primary)] hover:border-[var(--accent-primary)]/50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]"
    >
      {isDark ? <Sun className="w-4 h-4" aria-hidden="true" /> : <Moon className="w-4 h-4" aria-hidden="true" />}
    </button>
  );
}
