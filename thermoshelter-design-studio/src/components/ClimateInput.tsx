import { Thermometer, Sun, Wind, Droplets, Mountain, MapPin } from 'lucide-react';
import { ClimateData } from '../utils/thermalEngine';
import { climatePresets } from '../data/climatePresets';

interface ClimateInputProps {
  climateData: ClimateData;
  setClimateData: (data: ClimateData) => void;
}

export default function ClimateInput({ climateData, setClimateData }: ClimateInputProps) {
  const updateField = (field: keyof ClimateData, value: number | string) => {
    setClimateData({ ...climateData, [field]: value });
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
              onClick={() => setClimateData({ ...preset })}
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
                className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500/50"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
