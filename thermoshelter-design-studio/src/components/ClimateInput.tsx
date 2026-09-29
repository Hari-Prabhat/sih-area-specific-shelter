import { Thermometer, Sun, Wind, Droplets, Mountain, MapPin, Search, Loader2, X } from 'lucide-react';
import { useState } from 'react';
import { ClimateData } from '../types';
import { climatePresets } from '../data/climatePresets';
import {
  ClimateLocationCandidate,
  SimulationClimateProfile,
  WeatherDatasetMode,
  describeClimateError,
  fetchSimulationClimateProfile,
  geocodeLocations,
} from '../services/api';

interface ClimateInputProps {
  climateData: ClimateData;
  setClimateData: (data: ClimateData) => void;
  climateProfile?: SimulationClimateProfile | null;
  onProfileChange?: (profile: SimulationClimateProfile | null) => void;
}

const CLIMATE_MODES: { value: WeatherDatasetMode; label: string }[] = [
  { value: 'live', label: 'Live' },
  { value: 'forecast', label: 'Forecast' },
  { value: 'design', label: 'Design' },
];

const MODE_BADGE: Record<string, string> = {
  live: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  forecast: 'bg-sky-500/20 text-sky-400 border-sky-500/30',
  historical: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
  design: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  fallback: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
};

export default function ClimateInput({ climateData, setClimateData, climateProfile, onProfileChange }: ClimateInputProps) {
  const updateField = (field: keyof ClimateData, value: number | string) => {
    setClimateData({ ...climateData, [field]: value });
  };

  // ---- Phase B: live/location-driven climate retrieval (minimal UI) ----
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<WeatherDatasetMode>('live');
  const [candidates, setCandidates] = useState<ClimateLocationCandidate[]>([]);
  const [searching, setSearching] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [climateError, setClimateError] = useState<string | null>(null);

  const candidateKey = (c: ClimateLocationCandidate) =>
    `${c.latitude.toFixed(4)},${c.longitude.toFixed(4)}`;

  const handleSearch = async () => {
    if (!query.trim() || searching) return;
    setSearching(true);
    setClimateError(null);
    setCandidates([]);
    try {
      const results = await geocodeLocations(query.trim(), 4);
      setCandidates(results);
      if (results.length === 0) setClimateError(`No location found for "${query.trim()}".`);
    } catch (err) {
      setClimateError(describeClimateError(err));
    } finally {
      setSearching(false);
    }
  };

  const handleSelect = async (candidate: ClimateLocationCandidate) => {
    if (fetching || !onProfileChange) return;
    setFetching(true);
    setClimateError(null);
    try {
      const profile = await fetchSimulationClimateProfile(candidateKey(candidate), mode, 168);
      onProfileChange(profile);
    } catch (err) {
      setClimateError(describeClimateError(err));
    } finally {
      setFetching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
          <Thermometer className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Climate Data Input</h2>
          <p className="text-sm text-slate-400">Select a region or input custom atmospheric conditions</p>
        </div>
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-amber-400" /> Select Region
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {climatePresets.map((preset) => (
            <button
              key={preset.location}
              onClick={() => {
                // Session 2: switching to a design preset invalidates any live
                // climate profile AND the results computed from it — the
                // preset path must stay honestly labelled as preset-only.
                if (climateProfile) onProfileChange?.(null);
                setClimateData({ ...preset });
              }}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-all text-left ${
                climateData.location === preset.location
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
              }`}
            >
              <span className="block truncate">{preset.location}</span>
              <span className="text-[10px] text-slate-500">
                {preset.altitude}m | {preset.avgAmbientTemp}°C
              </span>
            </button>
          ))}
        </div>
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <Search className="w-4 h-4 text-emerald-400" /> Live Weather / Location Climate
        </h3>
        <p className="text-xs text-slate-500 mb-3">
          Search any Indian city, district, state, 6-digit PIN code, or "lat, lon" coordinates.
          Modes are never mixed: Live ends now, Forecast looks ahead, Design uses bundled benchmark climate.
        </p>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
placeholder="City, district, state, PIN code, or 'lat, lon'"
            className="flex-1 min-w-[220px] px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-emerald-500/50"
          />
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as WeatherDatasetMode)}
            className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-100 focus:outline-none"
          >
            {CLIMATE_MODES.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
          <button
            onClick={handleSearch}
            disabled={searching || !query.trim()}
            className="px-4 py-2 bg-emerald-600/80 hover:bg-emerald-600 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-all"
          >
            {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
          </button>
        </div>
        {climateError && (
          <div className="mb-3 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400 flex items-start justify-between gap-2">
            <span>{climateError}</span>
            <button onClick={() => setClimateError(null)} aria-label="Dismiss">
              <X className="w-3.5 h-3.5 text-red-400/70 hover:text-red-300" />
            </button>
          </div>
        )}
        {candidates.length > 0 && (
          <div className="mb-3 space-y-1.5">
            {candidates.map((c, idx) => (
              <button
                key={`${candidateKey(c)}-${idx}`}
                onClick={() => handleSelect(c)}
                disabled={fetching}
                className="w-full px-3 py-2 bg-slate-700/30 hover:bg-slate-700/50 border border-slate-600/30 rounded-lg text-left transition-all disabled:opacity-50"
              >
                <span className="block text-sm text-slate-200">{c.place_name}</span>
                <span className="text-[10px] text-slate-500">
                  {c.latitude.toFixed(3)}, {c.longitude.toFixed(3)}
                  {c.elevation != null ? ` | ${Math.round(c.elevation)}m` : ''}
                  {c.region ? ` | ${c.region}` : ''}
                </span>
              </button>
            ))}
          </div>
        )}
        {fetching && (
          <div className="mb-3 flex items-center gap-2 text-xs text-slate-400">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Fetching {mode} climate from provider…
          </div>
        )}
        {climateProfile && !fetching && (
          <div className="flex flex-wrap items-center gap-2">
            <span className={`px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wide border ${MODE_BADGE[climateProfile.series.data_mode] ?? 'bg-slate-500/20 text-slate-300 border-slate-500/30'}`}>
              {climateProfile.series.data_mode}{climateProfile.series.fallback_used ? ' (provider down)' : ''}
            </span>
            <span className="text-xs text-slate-300">{climateProfile.climate.city}</span>
            <span className="text-[10px] text-slate-500">
              {climateProfile.series.provider}
              {climateProfile.climate.elevation_m != null ? ` | ${Math.round(climateProfile.climate.elevation_m)}m` : ''}
              {` | ${climateProfile.series.air_temperature_C.length}h`}
            </span>
            <button
              onClick={() => onProfileChange?.(null)}
              className="ml-auto text-[10px] text-slate-500 hover:text-slate-300 underline"
            >
              Use presets only
            </button>
          </div>
        )}
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Custom Climate Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { icon: <MapPin className="w-4 h-4 text-blue-400" />, label: "Location Name", field: 'location', type: 'text' },
            { icon: <Mountain className="w-4 h-4 text-green-400" />, label: "Altitude (m)", field: 'altitude', type: 'number' },
            { icon: <Thermometer className="w-4 h-4 text-blue-400" />, label: "Min Temp (°C)", field: 'ambientTempMin', type: 'number' },
            { icon: <Thermometer className="w-4 h-4 text-red-400" />, label: "Max Temp (°C)", field: 'ambientTempMax', type: 'number' },
            { icon: <Thermometer className="w-4 h-4 text-amber-400" />, label: "Avg Temp (°C)", field: 'avgAmbientTemp', type: 'number' },
            { icon: <Sun className="w-4 h-4 text-yellow-400" />, label: "Solar Irradiance (kWh/m²/yr)", field: 'solarIrradiance', type: 'number' },
            { icon: <Sun className="w-4 h-4 text-orange-400" />, label: "Sunshine Hours/Day", field: 'avgSunshineHours', type: 'number' },
            { icon: <Wind className="w-4 h-4 text-cyan-400" />, label: "Wind Speed (m/s)", field: 'windSpeed', type: 'number' },
            { icon: <Droplets className="w-4 h-4 text-blue-400" />, label: "Humidity (%)", field: 'humidity', type: 'number' },
          ].map((input) => (
            <div key={input.field} className="space-y-1.5">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-400">
                {input.icon}
                {input.label}
              </label>
              <input
                type={input.type}
                value={climateData[input.field as keyof ClimateData] as string | number}
                onChange={(e) =>
                  updateField(
                    input.field as keyof ClimateData,
                    input.type === 'number' ? Number(e.target.value) : e.target.value
                  )
                }
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-amber-500/50"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
