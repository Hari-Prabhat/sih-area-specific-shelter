export type Language = "en" | "te" | "hi";

export const LANGUAGE_STORAGE_KEY = "language";
export const DEFAULT_LANGUAGE: Language = "en";

export const AVAILABLE_LANGUAGES: { code: Language; label: string; nativeLabel: string }[] = [
  { code: "en", label: "English", nativeLabel: "English" },
  { code: "te", label: "Telugu", nativeLabel: "తెలుగు" },
  { code: "hi", label: "Hindi", nativeLabel: "हिन्दी" },
];

export interface TranslationKeys {
  temperature: string;
  humidity: string;
  wind: string;
  rain: string;
  weather: string;
  search: string;
  loading: string;
  error: string;
  sunny: string;
  cloudy: string;
  partlyCloudy: string;
  rainy: string;
  foggy: string;
  drizzle: string;
  snowy: string;
  rainShowers: string;
  thunderstorm: string;
  unknown: string;
  searchPlaceholder: string;
  searchButton: string;
  location: string;
  noResults: string;
  selectLocation: string;
  precipitationMm: string;
  windKmh: string;
  humidityPct: string;
  errorFetchingWeather: string;
  errorSearchingLocation: string;
}

const en: TranslationKeys = {
  temperature: "Temperature",
  humidity: "Humidity",
  wind: "Wind",
  rain: "Rain",
  weather: "Weather",
  search: "Search",
  loading: "Loading",
  error: "Error",
  sunny: "Sunny",
  cloudy: "Cloudy",
  partlyCloudy: "Partly Cloudy",
  rainy: "Rainy",
  foggy: "Foggy",
  drizzle: "Drizzle",
  snowy: "Snowy",
  rainShowers: "Rain Showers",
  thunderstorm: "Thunderstorm",
  unknown: "Unknown",
  searchPlaceholder: "Search city or location...",
  searchButton: "Search",
  location: "Location",
  noResults: "No locations found",
  selectLocation: "Select a location",
  precipitationMm: "mm",
  windKmh: "km/h",
  humidityPct: "%",
  errorFetchingWeather: "Failed to fetch weather data",
  errorSearchingLocation: "Failed to search location",
};

const te: TranslationKeys = {
  temperature: "ఉష్ణోగ్రత",
  humidity: "తేమ",
  wind: "గాలి",
  rain: "వర్షం",
  weather: "వాతావరణం",
  search: "వెతుకు",
  loading: "లోడ్ అవుతోంది",
  error: "లోపం",
  sunny: "ఎండగా ఉంది",
  cloudy: "మేఘావృతం",
  partlyCloudy: "పాక్షికంగా మేఘావృతం",
  rainy: "వర్షం",
  foggy: "పొగమంచు",
  drizzle: "చల్లగా వర్షం",
  snowy: "మంచు",
  rainShowers: "వర్షాలు",
  thunderstorm: "పుదగలు తీగలు",
  unknown: "తెలియదు",
  searchPlaceholder: "నగరం లేదా ప్రదేశాన్ని వెతకండి...",
  searchButton: "వెతకండి",
  location: "ప్రదేశం",
  noResults: "ప్రదేశాలు కనుగొనబడలేదు",
  selectLocation: "ప్రదేశం ఎంచుకోండి",
  precipitationMm: "మిమీ",
  windKmh: "కిమీ/గం",
  humidityPct: "%",
  errorFetchingWeather: "వాతావరణ డేటాను పొందడం విఫలమైంది",
  errorSearchingLocation: "ప్రదేశాన్ని వెతకడం విఫలమైంది",
};

const hi: TranslationKeys = {
  temperature: "तापमान",
  humidity: "नमी",
  wind: "हवा",
  rain: "बारिश",
  weather: "मौसम",
  search: "खोजें",
  loading: "लोड हो रहा है",
  error: "त्रुटि",
  sunny: "धूप",
  cloudy: "बादल",
  partlyCloudy: "आंशिक रूप से बादल",
  rainy: "बारिश",
  foggy: "कोहरा",
  drizzle: "बूंदाबांदी",
  snowy: "बर्फ",
  rainShowers: "बारिश की बौछारें",
  thunderstorm: "आंधी तूफान",
  unknown: "अज्ञात",
  searchPlaceholder: "शहर या स्थान खोजें...",
  searchButton: "खोजें",
  location: "स्थान",
  noResults: "कोई स्थान नहीं मिला",
  selectLocation: "एक स्थान चुनें",
  precipitationMm: "मिमी",
  windKmh: "किमी/घंटा",
  humidityPct: "%",
  errorFetchingWeather: "मौसम डेटा प्राप्त करने में विफल",
  errorSearchingLocation: "स्थान खोजने में विफल",
};

export const translations: Record<Language, TranslationKeys> = {
  en,
  te,
  hi,
};

export function getInitialLanguage(): Language {
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

export function setStoredLanguage(lang: Language): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  } catch {
    // ignore storage errors
  }
}
