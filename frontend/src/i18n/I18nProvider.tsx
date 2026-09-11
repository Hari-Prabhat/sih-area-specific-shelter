import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  AVAILABLE_LANGUAGES,
  DEFAULT_LANGUAGE,
  Language,
  LANGUAGE_STORAGE_KEY,
  TranslationKeys,
  translations,
} from "./translations";

interface I18nContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: TranslationKeys;
  availableLanguages: typeof AVAILABLE_LANGUAGES;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function getInitialLanguage(): Language {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY) as Language | null;
    if (stored && (stored === "en" || stored === "te" || stored === "hi")) {
      return stored;
    }
  } catch {
    // ignore storage errors
  }
  return DEFAULT_LANGUAGE;
}

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => getInitialLanguage());

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
      } catch {
        // ignore storage errors
      }
    }
  }, []);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === LANGUAGE_STORAGE_KEY && e.newValue) {
        const newLang = e.newValue as Language;
        if (newLang === "en" || newLang === "te" || newLang === "hi") {
          setLanguageState(newLang);
        }
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const value = useMemo<I18nContextValue>(
    () => ({
      language,
      setLanguage,
      t: translations[language],
      availableLanguages: AVAILABLE_LANGUAGES,
    }),
    [language, setLanguage]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

// oxlint-disable-next-line react/only-export-components
export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return ctx;
}
