import { BarChart3, Thermometer, Sun, Zap, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { SimulationResult, ClimateData, ShelterDesign } from '../utils/thermalEngine';
import ShelterModel3D from './ShelterModel3D';

interface SimulationResultsProps {
  result: SimulationResult;
  climateData: ClimateData;
  shelterDesign: ShelterDesign;
  materialName: string;
}

export default function SimulationResults({
  result,
  climateData,
  shelterDesign,
  materialName,
}: SimulationResultsProps) {
  const hourlyData = result.hourlyTemperatures.map((temp, hour) => ({
    hour: `${hour}:00`,
    inside: temp,
    ambient:
      climateData.avgAmbientTemp +
      ((climateData.ambientTempMax - climateData.ambientTempMin) / 2) * Math.sin(((hour - 9) * Math.PI) / 12),
  }));

  const monthlyData = result.monthlyTemperatures.map((temp, month) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return {
      month: months[month],
      inside: temp,
      ambient:
        Math.round((climateData.avgAmbientTemp + [-8, -5, -1, 4, 8, 12, 14, 13, 9, 4, -2, -6][month]) * 10) / 10,
    };
  });

  const heatLossData = [
    { name: 'Walls', value: result.heatLossThroughWalls, color: '#f59e0b' },
    { name: 'Roof', value: result.heatLossThroughRoof, color: '#ef4444' },
    { name: 'Floor', value: result.heatLossThroughFloor, color: '#3b82f6' },
    { name: 'Windows', value: result.heatLossThroughWindows, color: '#8b5cf6' },
    { name: 'Doors', value: result.heatLossThroughDoors, color: '#10b981' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-green-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Simulation Results</h2>
          <p className="text-sm text-slate-400">
            {climateData.location} | {materialName} | {shelterDesign.shape}
          </p>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border border-orange-500/20 rounded-xl p-4">
          <Thermometer className="w-5 h-5 text-orange-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase">Avg Inside Temp</p>
          <p className="text-lg font-bold text-white mt-1">{result.avgInsideTemp}°C</p>
          <p className="text-[10px] text-slate-500">
            {result.minInsideTemp}° to {result.maxInsideTemp}°C
          </p>
        </div>
        <div className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border border-yellow-500/20 rounded-xl p-4">
          <Sun className="w-5 h-5 text-yellow-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase">Solar Gain</p>
          <p className="text-lg font-bold text-white mt-1">{result.solarEnergyGain} kWh/day</p>
        </div>
        <div className="bg-gradient-to-br from-red-500/20 to-red-600/5 border border-red-500/20 rounded-xl p-4">
          <Zap className="w-5 h-5 text-red-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase">Total Heat Loss</p>
          <p className="text-lg font-bold text-white mt-1">{result.totalHeatLoss} W</p>
        </div>
        <div className="bg-gradient-to-br from-green-500/20 to-green-600/5 border border-green-500/20 rounded-xl p-4">
          <TrendingUp className="w-5 h-5 text-green-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase">Efficiency</p>
          <p className="text-lg font-bold text-white mt-1">{result.energyEfficiency}%</p>
        </div>
      </div>
      {/* 3D Shelter Visualization */}
      <ShelterModel3D
        design={shelterDesign}
        materialName={materialName}
        comfortIndex={result.thermalComfortIndex}
        avgTemp={result.avgInsideTemp}
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">24-Hour Temperature Profile</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="hour" stroke="#64748b" fontSize={10} interval={3} />
              <YAxis stroke="#64748b" fontSize={10} unit="°C" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Area type="monotone" dataKey="inside" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} name="Inside" />
              <Area type="monotone" dataKey="ambient" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} name="Ambient" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Heat Loss Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={heatLossData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {heatLossData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value: number) => [`${value} W`, '']}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Monthly Temperature</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={10} unit="°C" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
            />
            <Bar dataKey="inside" fill="#f59e0b" name="Inside" radius={[4, 4, 0, 0]} />
            <Bar dataKey="ambient" fill="#3b82f6" name="Ambient" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" /> Recommendations
        </h3>
        <div className="space-y-3">
          {result.recommendedImprovements.map((rec, i) => (
            <div key={i} className="flex items-start gap-3 bg-slate-700/30 rounded-lg p-3">
              <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-slate-300">{rec}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
