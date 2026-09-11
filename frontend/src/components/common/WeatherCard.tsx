import React, { useEffect, useMemo, useState } from "react";
import {
  Search,
  Sun,
  Cloud,
  CloudSun,
  CloudRain,
  CloudFog,
  CloudDrizzle,
  Snowflake,
  CloudLightning,
  MapPin,
  Thermometer,
  Droplets,
  Wind,
  Loader2,
  AlertCircle,
  X,
} from "lucide-react";
import { useI18n } from "../../i18n/I18nProvider";
import {
  CurrentWeatherResponse,
  GeocodingResult,
  getCurrentWeather,
  searchLocation,
  weatherCodeToCondition,
  WeatherConditionKey,
} from "../../api/weather";

interface WeatherCardProps {
  defaultLatitude?: number;
  defaultLongitude?: number;
  defaultLocationName?: string;
  fallbackCity?: string;
}

const DEFAULT_FALLBACK_CITY = "Delhi";

function ConditionIcon({
  condition,
  className,
}: {
  condition: WeatherConditionKey;
  className?: string;
}) {
  const cls = className ?? "w-10 h-10";
  switch (condition) {
    case "sunny":
      return <Sun className={`${cls} text-amber-400`} />;
    case "partlyCloudy":
      return <CloudSun className={`${cls} text-sky-300`} />;
    case "cloudy":
      return <Cloud className={`${cls} text-slate-400`} />;
    case "foggy":
      return <CloudFog className={`${cls} text-slate-400`} />;
    case "drizzle":
      return <CloudDrizzle className={`${cls} text-sky-400`} />;
    case "rainy":
    case "rainShowers":
      return <CloudRain className={`${cls} text-sky-400`} />;
    case "snowy":
      return <Snowflake className={`${cls} text-sky-200`} />;
    case "thunderstorm":
      return <CloudLightning className={`${cls} text-violet-400`} />;
    case "unknown":
    default:
      return <Cloud className={`${cls} text-slate-400`} />;
  }
}

export const WeatherCard: React.FC<WeatherCardProps> = ({
  defaultLatitude,
  defaultLongitude,
  defaultLocationName,
  fallbackCity = DEFAULT_FALLBACK_CITY,
}) => {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searching, setSearching] = useState(false);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [weather, setWeather] = useState<CurrentWeatherResponse | null>(null);
  const [locationName, setLocationName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const condition: WeatherConditionKey = useMemo(() => {
    if (!weather) return "unknown";
    return weatherCodeToCondition(weather.current.weather_code);
  }, [weather]);

  const conditionLabel: string = useMemo(() => {
    const key = condition as keyof typeof t;
    return (t[key] as string) || t.unknown;
  }, [condition, t]);

  const fetchWeatherFor = async (
    lat: number,
    lon: number,
    name: string
  ) => {
    setError(null);
    setLoadingWeather(true);
    try {
      const data = await getCurrentWeather(lat, lon);
      setWeather(data);
      setLocationName(name);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.errorFetchingWeather;
      setError(msg);
      setWeather(null);
    } finally {
      setLoadingWeather(false);
    }
  };

  const loadInitial = async () => {
    if (
      typeof defaultLatitude === "number" &&
      typeof defaultLongitude === "number"
    ) {
      await fetchWeatherFor(
        defaultLatitude,
        defaultLongitude,
        defaultLocationName || fallbackCity
      );
      return;
    }
    setError(null);
    setSearching(true);
    try {
      const results = await searchLocation(fallbackCity, 1);
      if (results.length > 0) {
        const r = results[0];
        await fetchWeatherFor(
          r.latitude,
          r.longitude,
          buildLocationLabel(r)
        );
      } else {
        setError(t.noResults);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.errorSearchingLocation;
      setError(msg);
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    void loadInitial();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultLatitude, defaultLongitude, defaultLocationName, fallbackCity]);

  const buildLocationLabel = (r: GeocodingResult): string => {
    const parts: string[] = [];
    if (r.name) parts.push(r.name);
    if (r.admin2 && r.admin2 !== r.name) parts.push(r.admin2);
    if (r.admin1 && r.admin1 !== r.admin2) parts.push(r.admin1);
    if (r.country) parts.push(r.country);
    return parts.length > 0 ? parts.join(", ") : String(r.id);
  };

  const handleSearch = async () => {
    const q = query.trim();
    if (!q) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    setError(null);
    setSearching(true);
    setShowDropdown(false);
    try {
      const results = await searchLocation(q, 5);
      setSearchResults(results);
      setShowDropdown(true);
      if (results.length === 0) {
        setError(t.noResults);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.errorSearchingLocation;
      setError(msg);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectLocation = (r: GeocodingResult) => {
    setQuery("");
    setSearchResults([]);
    setShowDropdown(false);
    void fetchWeatherFor(r.latitude, r.longitude, buildLocationLabel(r));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      void handleSearch();
    }
  };

  return (
    <div className="bg-slate-900/90 border border-sky-500/30 rounded-2xl p-5 shadow-lg shadow-sky-950/20 space-y-4 w-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sun className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            {t.weather}
          </h3>
        </div>
      </div>

      <div className="relative w-full">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (showDropdown) setShowDropdown(false);
              }}
              onKeyDown={handleKeyDown}
              onFocus={() => {
                if (searchResults.length > 0) setShowDropdown(true);
              }}
              onBlur={() => {
                setTimeout(() => setShowDropdown(false), 150);
              }}
              placeholder={t.searchPlaceholder}
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 transition-colors"
            />
          </div>
          <button
            onClick={() => void handleSearch()}
            disabled={searching || !query.trim()}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-slate-950 rounded-lg text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0"
          >
            {searching ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Search className="w-3.5 h-3.5" />
            )}
            <span>{t.searchButton}</span>
          </button>
        </div>

        {showDropdown && searchResults.length > 0 && (
          <div className="absolute z-30 mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg shadow-xl overflow-hidden max-h-60 overflow-y-auto">
            {searchResults.map((r) => (
              <button
                key={r.id}
                onClick={() => handleSelectLocation(r)}
                className="w-full text-left px-3 py-2 hover:bg-sky-500/10 border-b border-slate-800/60 last:border-0 transition-colors cursor-pointer"
              >
                <div className="flex items-start gap-2">
                  <MapPin className="w-3.5 h-3.5 text-sky-400 mt-0.5 shrink-0" />
                  <div className="text-xs">
                    <div className="text-white font-medium">
                      {buildLocationLabel(r)}
                    </div>
                    <div className="text-slate-500 font-mono text-[10px]">
                      {r.latitude.toFixed(3)}°, {r.longitude.toFixed(3)}°
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-2 px-3 py-2 bg-rose-950/60 border border-rose-800/60 rounded-lg">
          <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <div className="text-xs text-rose-200 flex-1">{error}</div>
          <button
            onClick={() => setError(null)}
            className="text-rose-400 hover:text-rose-200 cursor-pointer shrink-0"
            aria-label="Dismiss error"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {(loadingWeather || searching) && !weather && !error && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-sky-400 animate-spin" />
          <span className="ml-2 text-xs text-slate-400">{t.loading}...</span>
        </div>
      )}

      {weather && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <MapPin className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-xs font-semibold text-sky-300 truncate">
              {locationName}
            </span>
          </div>

          <div className="flex items-center justify-between gap-4 bg-slate-950/60 rounded-xl p-4 border border-slate-800/60">
            <div className="space-y-1">
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black font-mono text-white leading-none">
                  {weather.current.temperature_2m.toFixed(0)}
                </span>
                <span className="text-lg font-bold text-slate-400">°C</span>
              </div>
              <div className="text-sm font-semibold text-slate-300">
                {conditionLabel}
              </div>
            </div>
            <div className="p-2 rounded-xl bg-slate-900 border border-slate-800">
              <ConditionIcon condition={condition} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            <div className="bg-slate-950/60 border border-slate-800/60 rounded-xl p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase tracking-wider font-semibold">
                <Droplets className="w-3 h-3" />
                <span>{t.humidity}</span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-bold font-mono text-white">
                  {weather.current.relative_humidity_2m.toFixed(0)}
                </span>
                <span className="text-[11px] text-slate-500">{t.humidityPct}</span>
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/60 rounded-xl p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase tracking-wider font-semibold">
                <Wind className="w-3 h-3" />
                <span>{t.wind}</span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-bold font-mono text-white">
                  {weather.current.wind_speed_10m.toFixed(0)}
                </span>
                <span className="text-[11px] text-slate-500">{t.windKmh}</span>
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/60 rounded-xl p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-500 text-[10px] uppercase tracking-wider font-semibold">
                <CloudRain className="w-3 h-3" />
                <span>{t.rain}</span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-bold font-mono text-white">
                  {weather.current.precipitation.toFixed(1)}
                </span>
                <span className="text-[11px] text-slate-500">{t.precipitationMm}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!weather && !loadingWeather && !searching && !error && (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <Thermometer className="w-8 h-8 text-slate-600 mb-2" />
          <span className="text-xs text-slate-500">{t.selectLocation}</span>
        </div>
      )}
    </div>
  );
};
