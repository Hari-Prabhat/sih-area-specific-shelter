import { useState, lazy, Suspense } from 'react';
import {
  BarChart3,
  Thermometer,
  Sun,
  Zap,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Activity,
  Shield,
  Layers,
  ArrowDownRight,
  Flame,
} from 'lucide-react';
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
  ReferenceLine,
} from 'recharts';
import { SimulationResult, ClimateData, ShelterDesign } from '../types';
import { CanonicalSimulationResult, SimulationClimateProfile } from '../services/api';
import {
  HEAT_FLOW_SERIES,
  buildHeatFlowChartData,
  buildSolarChartData,
  buildGainsChartData,
  buildThermalStorageChartData,
} from '../services/heatFlowChart';
import ProvenancePanel from './ProvenancePanel';
import StageSuspense from './ui/StageSuspense';
import { DISPLAY_COMFORT_BOUNDS } from '../theme/tokens';

// D3: lazy three.js digital twin — see ShelterDesigner.
const ShelterModel3D = lazy(() => import('./ShelterModel3D'));

interface SimulationResultsProps {
  result: SimulationResult;
  climateData: ClimateData;
  shelterDesign: ShelterDesign;
  materialName: string;
  /** D4-B: the Phase B/C climate profile — drives the provenance detail panel. */
  climateProfile?: SimulationClimateProfile | null;
  /** D4-C3: dead-gate for the legacy synthetic ambient profile (see below). */
  legacyDemoAmbient?: boolean;
}

export default function SimulationResults({
  result,
  climateData,
  shelterDesign,
  materialName,
  climateProfile = null,

  /**
   * D4-C3 legacy/demo dead-gate: set true ONLY by explicit legacy/demo callers.
   * When false (all canonical production paths), the synthetic 24-hour ambient
   * sine fallback is disabled and the ambient series is honestly omitted for
   * non-canonical results instead of fabricating outdoor temperatures.
   */
  legacyDemoAmbient = false,
}: SimulationResultsProps) {
  // Module-scope-style flag for the timeseries builder closure.
  const LEGACY_DEMO = legacyDemoAmbient;
  const [timeframeView, setTimeframeView] = useState<'7days' | '48h'>('7days');
  const canonical = (result as any).canonical as CanonicalSimulationResult | undefined;

  // D4-B WP4: hourly component heat flows — REAL backend arrays only. The
  // builder validates, aligns to the shortest common length, and reports
  // honest absence; series visibility is user-toggleable.
  const heatFlow = (() => {
    if (!canonical) return null;
    return buildHeatFlowChartData(canonical);
  })();
  const [hiddenFlows, setHiddenFlows] = useState<Record<string, boolean>>({});
  const visibleFlows = heatFlow?.availableSeries.filter((s) => !hiddenFlows[s.key]) ?? [];

  // D4-B WP4: solar chart — incident vs useful thermal gain from real arrays.
  const solarChart = canonical ? buildSolarChartData(canonical) : null;
  const [showSolarOverlay, setShowSolarOverlay] = useState(false);

  // Optional thermal-storage flow, clearly labelled as storage (not loss).
  const storageChart =
    canonical && heatFlow?.hasData ? buildThermalStorageChartData(canonical, heatFlow.hourCount) : null;
  const [showStorage, setShowStorage] = useState(false);

  // D4-C3: Internal Gains & Auxiliary Energy — REAL backend arrays only.
  const gainsChart = canonical ? buildGainsChartData(canonical) : null;

  // Multi-day timeseries when canonical data is available
  const timeseriesData = (() => {
    if (canonical && canonical.indoor_temperatures && canonical.indoor_temperatures.length > 0) {
      const hoursCount = timeframeView === '48h' ? 48 : canonical.indoor_temperatures.length;
      const step = timeframeView === '48h' ? 1 : Math.max(1, Math.floor(canonical.indoor_temperatures.length / 84));
      const points = [];
      for (let i = 0; i < hoursCount; i += step) {
        const day = Math.floor(i / 24) + 1;
        const hr = i % 24;
        points.push({
          time: `D${day} ${hr.toString().padStart(2, '0')}:00`,
          inside: Math.round(canonical.indoor_temperatures[i] * 10) / 10,
          ambient: Math.round(canonical.outdoor_temperatures[i] * 10) / 10,
          solar: Math.round((canonical.solar_thermal_gain?.[i] || 0) / 10) / 100, // kW
        });
      }
      return points;
    }
    // D4-C3: the legacy synthetic 24-hour sine profile is DEAD-GATED — it can
    // no longer appear in the normal canonical flow. It renders only behind an
    // explicit legacy/demo result flag, and is labelled as synthetic so it can
    // never be mistaken for real weather or a real simulation.
    return result.hourlyTemperatures.map((temp, hour) => ({
      time: `${hour}:00`,
      inside: temp,
      ambient: LEGACY_DEMO ?
        Math.round(
          (climateData.avgAmbientTemp +
            ((climateData.ambientTempMax - climateData.ambientTempMin) / 2) * Math.sin(((hour - 9) * Math.PI) / 12)) *
            10
        ) / 10 : null,
      solar: 0,
      synthetic: !LEGACY_DEMO || undefined,
    }));
  })();

  // Component heat loss distribution (7 components for canonical, 5 for fallback)
  const heatLossData = (() => {
    if (canonical && canonical.component_heat_loss_kwh) {
      const c = canonical.component_heat_loss_kwh;
      return [
        { name: 'Walls', value: Math.round(c.wall_loss_kwh), color: '#f59e0b' },
        { name: 'Roof', value: Math.round(c.roof_loss_kwh), color: '#ef4444' },
        { name: 'Floor', value: Math.round(c.floor_loss_kwh), color: '#3b82f6' },
        { name: 'Windows', value: Math.round(c.window_loss_kwh), color: '#06b6d4' },
        { name: 'Doors', value: Math.round(c.door_loss_kwh || 0), color: '#10b981' },
        { name: 'Ventilation', value: Math.round(c.ventilation_loss_kwh), color: '#8b5cf6' },
        { name: 'Radiation', value: Math.round(c.radiation_loss_kwh), color: '#ec4899' },
      ].filter((item) => item.value > 0);
    }
    return [
      { name: 'Walls', value: result.heatLossThroughWalls, color: '#f59e0b' },
      { name: 'Roof', value: result.heatLossThroughRoof, color: '#ef4444' },
      { name: 'Floor', value: result.heatLossThroughFloor, color: '#3b82f6' },
      { name: 'Windows', value: result.heatLossThroughWindows, color: '#06b6d4' },
      { name: 'Doors', value: result.heatLossThroughDoors, color: '#10b981' },
    ];
  })();

  const monthlyData = (result.monthlyTemperatures || []).map((temp, month) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return {
      month: months[month] || `M${month + 1}`,
      inside: temp,
      ambient: climateData.avgAmbientTemp,
    };
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">Thermal Simulation Dashboard</h2>
              {canonical && (
                <span className="text-[10px] px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded font-mono">
                  Python Forward Euler (Authoritative)
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400">
              {/* Batch 2B/Session 2: when a resolved climate profile is active,
                  its canonical location is authoritative over the preset label. */}
              {climateProfile?.climate?.city ?? climateData.location} | {materialName} | {shelterDesign.shape} ({shelterDesign.length}×{shelterDesign.width}×{shelterDesign.height}m)
            </p>
          </div>
        </div>
      </div>

      {/* D4-B WP5: collapsible provenance detail (weather + result provenance) */}
      <ProvenancePanel climateProfile={climateProfile} simulated={!!canonical} />

      {/* Row 1: Key Performance Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Inside Temp */}
        <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border border-orange-500/20 rounded-xl p-4">
          <Thermometer className="w-5 h-5 text-orange-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Avg Indoor Temp</p>
          <p className="text-2xl font-bold text-white mt-1">{result.avgInsideTemp}°C</p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Min: <span className="text-blue-400 font-semibold">{result.minInsideTemp}°C</span> | Max: <span className="text-amber-400 font-semibold">{result.maxInsideTemp}°C</span>
          </p>
        </div>

        {/* Solar Gain (Distinguishing Incident Solar vs Useful Thermal Gain) */}
        <div className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border border-yellow-500/20 rounded-xl p-4">
          <Sun className="w-5 h-5 text-yellow-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Solar Thermal Gain</p>
          <p className="text-2xl font-bold text-white mt-1">
            {canonical ? `${Math.round(canonical.integrated_solar_energy_kwh)} kWh` : `${result.solarEnergyGain} kWh/day`}
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5 truncate">
            {canonical ? `Incident: ${Math.round(canonical.integrated_incident_solar_kwh)} kWh` : 'Passive Solar Harvesting'}
          </p>
        </div>

        {/* Total Heat Loss & Heating Demand */}
        <div className="bg-gradient-to-br from-red-500/20 to-red-600/5 border border-red-500/20 rounded-xl p-4">
          <Zap className="w-5 h-5 text-red-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Total Heat Loss</p>
          <p className="text-2xl font-bold text-white mt-1">
            {canonical ? `${Math.round(canonical.total_heat_loss_kwh)} kWh` : `${result.totalHeatLoss} W`}
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {canonical ? `Heating Demand: ${Math.round(canonical.energy_totals_kwh?.heating_demand_kwh || 0)} kWh` : 'Envelope Conduction'}
          </p>
        </div>

        {/* Comfort Index & DDH */}
        <div className="bg-gradient-to-br from-green-500/20 to-green-600/5 border border-green-500/20 rounded-xl p-4">
          <TrendingUp className="w-5 h-5 text-green-400 mb-2" />
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Thermal Comfort</p>
          <p className="text-2xl font-bold text-white mt-1">{result.thermalComfortIndex}%</p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {canonical ? `DDH: ${Math.round(canonical.discomfort_degree_hours)} °C·h` : 'Predicted Comfort Index'}
          </p>
        </div>
      </div>

      {/* ISO 6946 Thermal U-Values & Envelope Physics (When Canonical Data Exists) */}
      {canonical && canonical.u_values && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              ISO 6946 Envelope Thermal Transmittance (U-Values)
            </h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase">Solid Wall U</span>
              <span className="text-sm font-mono font-bold text-amber-400 block mt-1">
                {canonical.u_values.wall_u.toFixed(2)} W/m²·K
              </span>
              <span className="text-[9px] text-slate-500">R ≈ {(1 / canonical.u_values.wall_u).toFixed(2)} m²·K/W</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase">Roof U</span>
              <span className="text-sm font-mono font-bold text-red-400 block mt-1">
                {canonical.u_values.roof_u.toFixed(2)} W/m²·K
              </span>
              <span className="text-[9px] text-slate-500">R ≈ {(1 / canonical.u_values.roof_u).toFixed(2)} m²·K/W</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase">Ground Floor U</span>
              <span className="text-sm font-mono font-bold text-blue-400 block mt-1">
                {canonical.u_values.floor_u.toFixed(2)} W/m²·K
              </span>
              <span className="text-[9px] text-slate-500">R ≈ {(1 / canonical.u_values.floor_u).toFixed(2)} m²·K/W</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase">Fenestration U</span>
              <span className="text-sm font-mono font-bold text-cyan-400 block mt-1">
                {canonical.u_values.window_u.toFixed(2)} W/m²·K
              </span>
              <span className="text-[9px] text-slate-500">Glazing Assembly</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
              <span className="text-[10px] text-slate-400 block uppercase">Door U</span>
              <span className="text-sm font-mono font-bold text-emerald-400 block mt-1">
                {(canonical.u_values.door_u ?? 1.80).toFixed(2)} W/m²·K
              </span>
              <span className="text-[9px] text-slate-500">Insulated Core</span>
            </div>
          </div>
        </div>
      )}

      {/* 3D Shelter Visualization (lazy three.js twin) */}
      <Suspense fallback={<StageSuspense label="3D visualization" />}>
        <ShelterModel3D
          design={shelterDesign}
          materialName={materialName}
          comfortIndex={result.thermalComfortIndex}
          avgTemp={result.avgInsideTemp}
        />
      </Suspense>

      {/* Row 2: Multi-Day Temperature Profile & Heat Loss Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeseries Temperature Profile */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-400" />
              {canonical ? 'Multi-Day Temperature Dynamics' : '24-Hour Temperature Profile'}
              {!canonical && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-700/50 font-mono uppercase">
                  Synthetic legacy profile — not real weather
                </span>
              )}
            </h3>
            {canonical && (
              <div className="flex gap-1 bg-slate-900/60 p-0.5 rounded border border-slate-700 text-[10px]">
                <button
                  onClick={() => setTimeframeView('48h')}
                  className={`px-2 py-0.5 rounded ${timeframeView === '48h' ? 'bg-amber-500 text-black font-bold' : 'text-slate-400'}`}
                >
                  48h
                </button>
                <button
                  onClick={() => setTimeframeView('7days')}
                  className={`px-2 py-0.5 rounded ${timeframeView === '7days' ? 'bg-amber-500 text-black font-bold' : 'text-slate-400'}`}
                >
                  7 Days
                </button>
              </div>
            )}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={timeseriesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval={timeframeView === '48h' ? 5 : 11} />
              <YAxis stroke="#64748b" fontSize={10} unit="°C" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <ReferenceLine y={DISPLAY_COMFORT_BOUNDS.min} stroke="#22c55e" strokeDasharray="3 3" label={{ value: `${DISPLAY_COMFORT_BOUNDS.min}°C Comfort Min`, fill: '#22c55e', fontSize: 10 }} />
              <ReferenceLine y={DISPLAY_COMFORT_BOUNDS.max} stroke="#10b981" strokeDasharray="3 3" label={{ value: `${DISPLAY_COMFORT_BOUNDS.max}°C Comfort Max`, fill: '#10b981', fontSize: 10 }} />
              <Area type="monotone" dataKey="inside" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.25} name="Indoor Temp (°C)" />
              <Area type="monotone" dataKey="ambient" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} name="Ambient Temp (°C)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Heat Loss Distribution */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <ArrowDownRight className="w-4 h-4 text-red-400" />
              Component Heat Loss Breakdown
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              {canonical ? 'Units: kWh Total' : 'Units: Watts Steady-State'}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={heatLossData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={85}
                paddingAngle={3}
                dataKey="value"
              >
                {heatLossData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value: number) => [`${value} ${canonical ? 'kWh' : 'W'}`, 'Loss']}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* D4-B WP4: Hourly Component Heat Flows (REAL backend arrays, W) */}
      {heatFlow && heatFlow.hasData && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-400" />
              Hourly Component Heat Flows
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              Units: W (hourly average power) · {heatFlow.hourCount} h · actual simulation output
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3">
            Real per-component conduction/ventilation/radiation flows returned by the Python engine —
            no interpolated or synthetic points.
          </p>
          {/* Series visibility toggles (do not rely on color alone) */}
          <div className="flex flex-wrap gap-1.5 mb-3">
            {heatFlow.availableSeries.map((s) => (
              <button
                key={s.key}
                type="button"
                onClick={() => setHiddenFlows((prev) => ({ ...prev, [s.key]: !prev[s.key] }))}
                aria-pressed={!hiddenFlows[s.key]}
                className={`px-2 py-1 rounded-md text-[11px] font-medium border transition-colors ${
                  hiddenFlows[s.key]
                    ? 'bg-slate-900/60 text-slate-500 border-slate-700/50 line-through'
                    : 'bg-slate-700/50 text-slate-200 border-slate-600/50 hover:bg-slate-700'
                }`}
              >
                <span
                  className="inline-block w-2 h-2 rounded-full mr-1.5 align-middle"
                  style={{ backgroundColor: s.color }}
                  aria-hidden="true"
                />
                {s.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setShowStorage((v) => !v)}
              aria-pressed={showStorage}
              className={`px-2 py-1 rounded-md text-[11px] font-medium border transition-colors ${
                showStorage
                  ? 'bg-slate-700/50 text-slate-200 border-slate-600/50'
                  : 'bg-slate-900/60 text-slate-500 border-slate-700/50'
              } ${storageChart?.hasData ? '' : 'hidden'}`}
            >
              Thermal storage flow
            </button>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={heatFlow.points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval={11} />
              <YAxis stroke="#64748b" fontSize={10} unit=" W" width={52} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [`${Math.round(value * 10) / 10} W`, name]}
                labelFormatter={(label: string) => `Hour: ${label}`}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {visibleFlows.map((s) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label}
                  stroke={s.color}
                  fill={s.color}
                  fillOpacity={0.08}
                  strokeWidth={1.5}
                  stackId="components"
                  connectNulls={false}
                />
              ))}
              {showStorage && storageChart?.hasData && (
                <Area
                  type="monotone"
                  dataKey="storage"
                  name="Thermal storage flow (+ stored / − released)"
                  stroke="#94a3b8"
                  fill="#94a3b8"
                  fillOpacity={0.06}
                  strokeWidth={1.5}
                  strokeDasharray="4 3"
                  connectNulls={false}
                />
              )}
              <Area
                type="monotone"
                dataKey="net_heat_flow"
                name="Net heat flow"
                stroke="#ffffff"
                fill="none"
                strokeWidth={2}
                dot={false}
                connectNulls={false}
              />
            </AreaChart>
          </ResponsiveContainer>
          {showStorage && (
            <p className="text-[10px] text-slate-500 mt-2">
              Thermal storage flow shows energy absorbed/released by the thermal mass
              (positive = energy stored in the mass as indoor temperature rises; negative =
              energy released from the mass as temperature falls). It is internal energy
              redistribution, not a heat loss.
            </p>
          )}
        </div>
      )}
      {heatFlow && !heatFlow.hasData && canonical && (
        <div className="bg-slate-800/50 rounded-xl border border-dashed border-slate-700/60 p-8 text-center">
          <p className="text-sm font-medium text-slate-300 mb-1">Hourly heat-flow series unavailable</p>
          <p className="text-xs text-slate-500">
            The backend did not return component heat-flow arrays for this result, so no flow chart is
            shown — values are never synthesized.
          </p>
        </div>
      )}

      {/* D4-B WP4: Hourly solar profile — incident vs useful thermal gain (REAL arrays) */}
      {solarChart?.hasData && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Sun className="w-4 h-4 text-yellow-400" />
              Hourly Solar Profile
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">Units: W · actual simulation output</span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3">
            Incident solar power on the glazing versus the useful SHGC-filtered thermal gain — real
            hourly values from the same simulation run.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={solarChart.points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval={11} />
              <YAxis stroke="#64748b" fontSize={10} unit=" W" width={52} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [`${Math.round(value * 10) / 10} W`, name]}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {solarChart.hasIncident && (
                <Area
                  type="monotone"
                  dataKey="incident"
                  name="Incident solar on glazing"
                  stroke="#facc15"
                  fill="#facc15"
                  fillOpacity={0.15}
                  strokeWidth={1.5}
                  connectNulls={false}
                />
              )}
              {solarChart.hasThermalGain && (
                <Area
                  type="monotone"
                  dataKey="thermalGain"
                  name="Useful solar thermal gain (SHGC-filtered)"
                  stroke="#f97316"
                  fill="#f97316"
                  fillOpacity={0.25}
                  strokeWidth={1.5}
                  connectNulls={false}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* D4-C3: Internal Gains & Auxiliary Energy (REAL backend arrays, W) */}
      {gainsChart?.hasData && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Flame className="w-4 h-4 text-orange-400" />
              Internal Gains & Auxiliary Energy
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">Units: W · actual simulation output</span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3">
            Sensible internal gains (occupants × per-person heat) and the auxiliary heating/cooling power the
            engine computed per hour — real arrays, never synthesized.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={gainsChart.points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval={11} />
              <YAxis stroke="#64748b" fontSize={10} unit=" W" width={52} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [`${Math.round(value * 10) / 10} W`, name]}
                labelFormatter={(label: string) => `Hour: ${label}`}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {gainsChart.hasInternalGain && (
                <Area type="monotone" dataKey="internalGain" name="Internal gains" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} strokeWidth={1.5} connectNulls={false} />
              )}
              {gainsChart.hasHeatingDemand && (
                <Area type="monotone" dataKey="heatingDemand" name="Auxiliary heating" stroke="#f97316" fill="#f97316" fillOpacity={0.15} strokeWidth={1.5} connectNulls={false} />
              )}
              {gainsChart.hasCoolingDemand && (
                <Area type="monotone" dataKey="coolingDemand" name="Auxiliary cooling" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.15} strokeWidth={1.5} connectNulls={false} />
              )}
              {gainsChart.hasNetLoad && (
                <Area type="monotone" dataKey="netLoad" name="Net load (heat − cool)" stroke="#94a3b8" fill="none" strokeWidth={1.5} strokeDasharray="4 3" dot={false} connectNulls={false} />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
      {canonical && gainsChart && !gainsChart.hasData && (
        <div className="bg-slate-800/50 rounded-xl border border-dashed border-slate-700/60 p-6 text-center">
          <p className="text-sm font-medium text-slate-300 mb-1">Internal gains / auxiliary-energy series unavailable</p>
          <p className="text-xs text-slate-500">
            The backend did not return hourly gain/demand arrays for this result — values are never synthesized.
          </p>
        </div>
      )}

      {/* Row 3: Solar & Energy Balance (When Canonical is Available) */}
      {canonical && canonical.energy_totals_kwh && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Solar Energy Harvesting Ratio */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Sun className="w-4 h-4 text-yellow-400" /> Solar Aperture Energy Conversion
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Total Incident Solar Irradiation on Glazing</span>
                  <span className="text-white font-mono font-bold">
                    {Math.round(canonical.integrated_incident_solar_kwh)} kWh
                  </span>
                </div>
                <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                  <div className="bg-yellow-500 h-full rounded-full w-full" />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Useful Transmitted Solar Thermal Gain (SHGC Filtered)</span>
                  <span className="text-amber-400 font-mono font-bold">
                    {Math.round(canonical.integrated_solar_energy_kwh)} kWh
                  </span>
                </div>
                <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-400 h-full rounded-full"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.round(
                          (canonical.integrated_solar_energy_kwh /
                            Math.max(1, canonical.integrated_incident_solar_kwh)) *
                            100
                        )
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <p className="text-[11px] text-slate-400 pt-2 leading-relaxed">
                Useful solar thermal gain is absorbed into interior mass slabs and air nodes via orientation-dependent irradiance algorithms.
              </p>
            </div>
          </div>

          {/* Heating / Cooling Auxiliary Demand */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Flame className="w-4 h-4 text-orange-400" /> Auxiliary Thermal Energy Demands
            </h3>
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/50">
                <span className="text-xs text-slate-400 block mb-1">Auxiliary Heating Required</span>
                <span className="text-xl font-bold font-mono text-orange-400">
                  {Math.round(canonical.energy_totals_kwh.heating_demand_kwh)} kWh
                </span>
                <span className="text-[10px] text-slate-500 block mt-1">To sustain {DISPLAY_COMFORT_BOUNDS.min}°C setpoint</span>
              </div>
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/50">
                <span className="text-xs text-slate-400 block mb-1">Cooling Energy Required</span>
                <span className="text-xl font-bold font-mono text-sky-400">
                  {Math.round(canonical.energy_totals_kwh.cooling_demand_kwh)} kWh
                </span>
                <span className="text-[10px] text-slate-500 block mt-1">Overheating prevention</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Row 4: Monthly Projection */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Annual Diurnal Monthly Projection</h3>
        {monthlyData && monthlyData.length >= 12 ? (
          <ResponsiveContainer width="100%" height={220}>
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
        ) : (
          <div className="py-8 text-center text-slate-400 text-sm border border-dashed border-slate-700/60 rounded-lg">
            <p className="font-medium text-slate-300 mb-1">Annual Monthly Projection Unavailable</p>
            <p className="text-xs text-slate-500 font-mono">
              Simulation executed for 168-hour (7-day) transient horizon. Annual diurnal projection requires a full 8760-hour annual simulation.
            </p>
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" /> Engineering Recommendations
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
