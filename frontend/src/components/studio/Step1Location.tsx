import React, { useState } from 'react';
import { useDesignStudio } from '../../context';
import { PRESET_LOCATIONS } from '../../lib/api/climate';
import type { LocationOption } from '../../lib/api/climate';
import type { LocationMode } from '../../types';
import { MapPin, Navigation, Compass, WifiOff, CheckCircle2, Search } from 'lucide-react';

export const Step1Location: React.FC = () => {
  const { location, setLocation, errors } = useDesignStudio();
  const activeTab: LocationMode = location.mode || 'preset';
  const [customInput, setCustomInput] = useState<string>(
    location.mode === 'custom' ? location.displayName : ''
  );
  const [gpsStatus, setGpsStatus] = useState<'idle' | 'locating' | 'success' | 'denied'>('idle');

  const handleSelectPreset = (preset: LocationOption) => {
    setLocation({
      mode: 'preset',
      locationId: preset.id,
      displayName: `${preset.name}, ${preset.region}, ${preset.country}`,
      elevationM: preset.elevationM,
      latitude: preset.latitude,
      longitude: preset.longitude,
    });
  };

  const handleUseCurrentLocation = () => {
    setGpsStatus('locating');
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setGpsStatus('success');
          setLocation({
            mode: 'current',
            displayName: `GPS Telemetry: Lat ${pos.coords.latitude.toFixed(4)}°, Lng ${pos.coords.longitude.toFixed(4)}°`,
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            elevationM: undefined,
          });
        },
        () => {
          // Fallback if permission denied or unavailable in dev environment
          setGpsStatus('denied');
          setLocation({
            mode: 'current',
            displayName: 'Simulated GPS: 34.1526° N, 77.5771° E (Leh Field Outpost)',
            latitude: 34.1526,
            longitude: 77.5771,
            elevationM: 3524,
          });
        },
        { timeout: 5000 }
      );
    } else {
      setGpsStatus('denied');
      setLocation({
        mode: 'current',
        displayName: 'Simulated GPS: 34.1526° N, 77.5771° E (Leh Field Outpost)',
        latitude: 34.1526,
        longitude: 77.5771,
        elevationM: 3524,
      });
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customInput.trim()) {
      setLocation({
        mode: 'custom',
        displayName: customInput.trim(),
      });
    }
  };

  const handleSelectOffline = () => {
    setLocation({
      mode: 'offline',
      displayName: 'Offline / Remote Station (Field Estimate Baseline)',
      notes: 'Uncalibrated remote site without network or station pairing',
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[11px] font-mono-data uppercase tracking-widest text-sky-400 mb-1">
          STEP 1 of 5 — GEOGRAPHIC FRAMEWORK
        </div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Select Deployment Location
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Choose a site to link the structural envelope with macroclimatic solar, temperature, and altitude conditions.
        </p>
      </div>

      {/* Mode Selector Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 border-b border-slate-800 pb-3">
        <button
          type="button"
          onClick={() => {
            if (location.mode !== 'preset') {
              handleSelectPreset(PRESET_LOCATIONS[0]);
            }
          }}
          className={`flex items-center justify-center gap-2 py-2 px-3 rounded text-xs font-mono-data transition-all cursor-pointer ${
            activeTab === 'preset'
              ? 'bg-sky-500/20 text-sky-400 border border-sky-500/50 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>SELECT LOCATION</span>
        </button>

        <button
          type="button"
          onClick={handleUseCurrentLocation}
          className={`flex items-center justify-center gap-2 py-2 px-3 rounded text-xs font-mono-data transition-all cursor-pointer ${
            activeTab === 'current'
              ? 'bg-sky-500/20 text-sky-400 border border-sky-500/50 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <Navigation className="w-4 h-4" />
          <span>USE CURRENT GPS</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setLocation({
              mode: 'custom',
              displayName: customInput.trim() || 'Custom Location',
            });
          }}
          className={`flex items-center justify-center gap-2 py-2 px-3 rounded text-xs font-mono-data transition-all cursor-pointer ${
            activeTab === 'custom'
              ? 'bg-sky-500/20 text-sky-400 border border-sky-500/50 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <Search className="w-4 h-4" />
          <span>ENTER PLACE NAME</span>
        </button>

        <button
          type="button"
          onClick={handleSelectOffline}
          className={`flex items-center justify-center gap-2 py-2 px-3 rounded text-xs font-mono-data transition-all cursor-pointer ${
            activeTab === 'offline'
              ? 'bg-sky-500/20 text-sky-400 border border-sky-500/50 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <WifiOff className="w-4 h-4" />
          <span>OFFLINE / UNKNOWN</span>
        </button>
      </div>

      {/* Tab 1: Presets */}
      {activeTab === 'preset' && (
        <div className="space-y-3">
          <label className="block text-xs font-mono-data uppercase text-slate-400">
            Calibrated Meteorological Stations:
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {PRESET_LOCATIONS.map((preset) => {
              const isSelected = location.locationId === preset.id;
              return (
                <div
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-sky-950/40 border-sky-500 ring-1 ring-sky-500/50 shadow-md shadow-sky-950/30'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-1.5 font-bold text-white text-sm">
                        <span>{preset.name}</span>
                        {preset.isHeroTarget && (
                          <span className="text-[9px] bg-sky-500/20 text-sky-400 border border-sky-500/40 px-1.5 py-0.2 rounded font-mono-data font-semibold">
                            HERO TARGET
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5 font-mono-data">
                        {preset.region}, {preset.country}
                      </div>
                    </div>

                    {isSelected && <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0" />}
                  </div>

                  <div className="mt-2.5 pt-2 border-t border-slate-800/70 flex items-center justify-between text-[11px] font-mono-data text-slate-400">
                    <span>{preset.climateType}</span>
                    <span>{preset.elevationM}m alt</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: GPS */}
      {activeTab === 'current' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Navigation className="w-5 h-5 text-sky-400 animate-pulse" />
            <span className="text-sm font-semibold text-white font-mono-data">
              Hardware GPS Integration Boundary
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Acquires device coordinates for local altitude and solar zenith calculation.
            {gpsStatus === 'locating' && ' Inquiring location hardware...'}
            {gpsStatus === 'denied' && ' (Simulated field coordinates applied for desktop preview)'}
          </p>

          <button
            type="button"
            onClick={handleUseCurrentLocation}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-mono-data text-xs font-semibold transition-colors cursor-pointer"
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Re-acquire Device GPS</span>
          </button>
        </div>
      )}

      {/* Tab 3: Custom place name */}
      {activeTab === 'custom' && (
        <form onSubmit={handleCustomSubmit} className="bg-slate-900/60 border border-slate-800 rounded-lg p-5 space-y-4">
          <div>
            <label className="block text-xs font-mono-data uppercase text-slate-300 mb-1">
              Enter Location or Coordinates:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="e.g. Changtang Plateau, Ladakh or 34.22° N, 77.85° E"
                className="flex-1 bg-slate-950 border border-slate-700 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded px-3 py-2 text-sm text-white placeholder-slate-500 outline-none font-mono-data"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-mono-data text-xs font-semibold rounded transition-colors cursor-pointer"
              >
                Set Location
              </button>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Prepared for future geocoding API lookup and dynamic solar irradiance resolution.
          </p>
        </form>
      )}

      {/* Tab 4: Offline / unknown */}
      {activeTab === 'offline' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5 space-y-3">
          <div className="flex items-center gap-2">
            <WifiOff className="w-5 h-5 text-amber-400" />
            <span className="text-sm font-semibold text-white font-mono-data">
              Offline Tactical / Remote Field Operation
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Enables design generation without internet connection or live weather station feeds.
            The system applies a robust conservative high-altitude cold baseline with wide safety margins.
          </p>

          <div className="p-3 bg-amber-950/30 border border-amber-500/30 rounded text-xs text-amber-300 font-mono-data">
            STATUS: Offline baseline selected. Synthesized designs will be marked with ESTIMATED confidence.
          </div>
        </div>
      )}

      {/* Selected Location Confirmation Bar */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-sky-400 shrink-0" />
          <span className="text-xs font-mono-data text-slate-400">Active Site:</span>
          <span className="text-sm font-bold text-white font-mono-data">
            {location.displayName || 'None Selected'}
          </span>
        </div>

        {location.elevationM && (
          <span className="text-xs font-mono-data text-slate-400">
            Altitude: <b className="text-slate-200">{location.elevationM} m</b>
          </span>
        )}
      </div>

      {errors.location && (
        <p className="text-xs text-rose-400 font-mono-data font-semibold">
          ⚠ {errors.location}
        </p>
      )}
    </div>
  );
};
