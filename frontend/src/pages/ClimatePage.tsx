import React, { useState } from "react";
import { useDesignStore } from "../store/designStore";
import { SectionHeader } from "../components/common/SectionHeader";
import { MetricCard } from "../components/common/MetricCard";
import {
  Thermometer,
  Sun,
  MapPin,
  CheckCircle,
  Lightbulb,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

export const ClimatePage: React.FC = () => {
  const { selectedCity, setCity, cities, climateData } = useDesignStore();
  const [viewHours, setViewHours] = useState<24 | 168>(24);

  const meta = climateData?.metadata || {};
  const temps = climateData?.hourly_temperature || [];
  const solar = climateData?.hourly_direct_solar || [];
  const humidity = climateData?.hourly_humidity || [];

  // Build chart dataset
  const chartData = [];
  const count = Math.min(viewHours, temps.length);
  for (let i = 0; i < count; i++) {
    chartData.push({
      hour: `H${i + 1}`,
      temperature: temps[i] !== undefined ? parseFloat(temps[i].toFixed(1)) : 0,
      solar: solar[i] !== undefined ? parseFloat(solar[i].toFixed(1)) : 0,
      humidity: humidity[i] !== undefined ? parseFloat(humidity[i].toFixed(1)) : 0,
    });
  }

  const avgTemp = temps.length > 0 ? (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1) : "-";
  const minTemp = temps.length > 0 ? Math.min(...temps).toFixed(1) : "-";
  const maxTemp = temps.length > 0 ? Math.max(...temps).toFixed(1) : "-";

  // Climate specific architectural implications from engineering physics
  const getEngineeringImplications = () => {
    const ct = climateData?.climate_type || "cold";
    if (ct === "cold") {
      return {
        title: "Alpine Severe Cold (Leh / Ladakh)",
        points: [
          "Nighttime sub-zero temperatures (down to -18.5°C) require heavy envelope insulation (R ≥ 3.0 m²K/W) to prevent catastrophic nocturnal heat loss.",
          "High solar irradiance (GHI > 2,100 kWh/m²) makes direct passive solar gain via South-facing double/triple glazing the primary natural heat source.",
          "Steep pitched roofs (≥ 30°) are essential for snow runoff and establishing an attic buffer space.",
          "Low ambient moisture necessitates airtight building envelopes with controlled ventilation to minimize infiltration enthalpy loss.",
        ],
      };
    } else if (ct === "hot_dry") {
      return {
        title: "Hot & Arid Desert (Jaisalmer / Thar)",
        points: [
          "Extreme diurnal temperature swings (up to 20°C swing) mandate high thermal mass walls (stone/mud) to delay peak heat penetration until cool night hours.",
          "Solar irradiance exceeds 2,250 kWh/m²; fenestration must be restricted (< 15% WWR) and shaded with deep overhangs or jali screens.",
          "Night sky radiative cooling and ventilated courtyards provide passive thermal relief.",
          "Roof surface must employ high-albedo cool coatings or thermal buffer layers.",
        ],
      };
    } else {
      return {
        title: "Warm & Humid / Coastal (Chennai / Coastal)",
        points: [
          "Sustained high relative humidity (> 75%) requires cross-ventilation apertures and elevated ceiling heights to maximize indoor air velocity.",
          "Minimal diurnal temperature swing means thermal mass provides little benefit; lightweight ventilated envelopes perform better.",
          "Continuous solar shading and radiant roof barriers prevent internal heat accumulation.",
        ],
      };
    }
  };

  const implications = getEngineeringImplications();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        title="Climate Engine & Environmental Boundary Conditions"
        subtitle="Authoritative meteorological weather datasets derived from IMD, NREL NSRDB, and ASHRAE EPW reference files."
        badge={climateData?.climate_type ? climateData.climate_type.toUpperCase() : "AWAITING LOCATION"}
        action={
          <div className="flex items-center gap-2">
            <select
              value={selectedCity}
              onChange={(e) => setCity(e.target.value)}
              className={`font-mono font-semibold text-xs rounded-lg px-3 py-2 cursor-pointer transition-all ${
                !selectedCity
                  ? "bg-amber-950/60 border-2 border-amber-400 text-amber-300"
                  : "bg-slate-900 border border-slate-700 text-sky-400"
              }`}
            >
              <option value="" className="bg-slate-950 text-amber-400 font-bold">
                📍 Choose the location
              </option>
              {cities.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-950 text-white">
                  {c.display}
                </option>
              ))}
            </select>
          </div>
        }
      />

      {/* If no location chosen yet */}
      {!selectedCity && (
        <div className="eng-panel p-8 text-center border-2 border-amber-400/60 bg-amber-950/10 space-y-3">
          <MapPin className="w-10 h-10 text-amber-400 mx-auto animate-bounce" />
          <h3 className="text-base font-bold text-white">Please Choose a Deployment Location</h3>
          <p className="text-xs text-slate-300 max-w-md mx-auto">
            Select a location from the dropdown in the top bar or above to load authentic hourly EPW weather curves, solar flux, and engineering guidelines.
          </p>
          <div className="flex justify-center gap-2 pt-2">
            {cities.map((c) => (
              <button
                key={c.id}
                onClick={() => setCity(c.id)}
                className="px-3 py-1.5 bg-slate-900 border border-slate-700 hover:border-sky-400 text-slate-200 text-xs font-mono rounded-lg transition-all cursor-pointer"
              >
                {c.display.split("(")[0].trim()}
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedCity && (
        <>
          {/* Hero Environmental Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <MetricCard
              label="Design Elevation"
              value={meta.elevation || "3,524 m"}
              icon={<MapPin className="w-4 h-4 text-sky-400" />}
              accentColor="cyan"
              subtext={meta.type || "Observed Reference"}
            />
            <MetricCard
              label="Winter Design Temp"
              value={minTemp}
              unit="°C"
              icon={<Thermometer className="w-4 h-4 text-sky-400" />}
              accentColor="cyan"
              subtext={`Mean: ${avgTemp}°C`}
            />
            <MetricCard
              label="Summer Peak Temp"
              value={maxTemp}
              unit="°C"
              icon={<Sun className="w-4 h-4 text-amber-400" />}
              accentColor="orange"
              subtext={`Diurnal: ${(parseFloat(maxTemp) - parseFloat(minTemp)).toFixed(1)}°C`}
            />
            <MetricCard
              label="Solar Resource (GHI)"
              value={meta.solar_ghi || "2,100"}
              icon={<Sun className="w-4 h-4 text-amber-400" />}
              accentColor="orange"
              subtext="Annual Irradiation"
            />
            <MetricCard
              label="Heating Degree Days"
              value={meta.hdd !== undefined ? meta.hdd : 4850}
              unit="HDD"
              icon={<Thermometer className="w-4 h-4 text-rose-400" />}
              accentColor="red"
              subtext="Base 18°C Standard"
            />
          </div>

          {/* Hourly Meteorological Profile Chart */}
          <div className="eng-panel p-6 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Thermometer className="w-4 h-4 text-sky-400" />
                  <span>Hourly Meteorological Dynamics ({selectedCity.toUpperCase()})</span>
                </h2>
                <p className="text-xs text-slate-400">
                  Transient ambient temperature (°C) and direct solar irradiance (W/m²)
                </p>
              </div>

              {/* Time range selector */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
                <button
                  onClick={() => setViewHours(24)}
                  className={`px-3 py-1 rounded font-medium transition-all ${
                    viewHours === 24
                      ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  24-Hour Cycle
                </button>
                <button
                  onClick={() => setViewHours(168)}
                  className={`px-3 py-1 rounded font-medium transition-all ${
                    viewHours === 168
                      ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  168-Hour Week
                </button>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="temp" stroke="#38bdf8" tick={{ fontSize: 11 }} unit="°C" />
                  <YAxis yAxisId="solar" orientation="right" stroke="#f59e0b" tick={{ fontSize: 11 }} unit="W" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                  <Line
                    yAxisId="temp"
                    type="monotone"
                    dataKey="temperature"
                    name="Ambient Temp (°C)"
                    stroke="#38bdf8"
                    strokeWidth={2.5}
                    dot={false}
                  />
                  <Line
                    yAxisId="solar"
                    type="monotone"
                    dataKey="solar"
                    name="Solar Irradiance (W/m²)"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* WHAT THIS MEANS FOR YOUR SHELTER: Engineering Physical Interpretation */}
          <div className="eng-panel p-6 border-sky-500/30 space-y-4">
            <div className="flex items-center gap-2 text-sky-400">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-white tracking-tight">
                WHAT THIS MEANS FOR YOUR SHELTER · {implications.title}
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {implications.points.map((pt, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start gap-3"
                >
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300 leading-relaxed">{pt}</span>
                </div>
              ))}
            </div>

            {/* Provenance Footer */}
            <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex flex-wrap items-center justify-between gap-2">
              <span>
                <b>Data Provenance:</b> {meta.source || "IMD Station & NREL NSRDB / ASHRAE EPW Reference"}
              </span>
              <span className="font-mono">
                Lat: {climateData?.latitude ?? 0}°, Lon: {climateData?.longitude ?? 0}°
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
