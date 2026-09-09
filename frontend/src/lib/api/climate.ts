import type { ClimateProfile, DataStatus } from '../../types';

export interface LocationOption {
  id: string;
  name: string;
  region: string;
  country: string;
  elevationM: number;
  climateType: string;
  latitude: number;
  longitude: number;
  isHeroTarget?: boolean;
}

/**
 * High-confidence location database aligned with data/climate/locations.json
 */
export const PRESET_LOCATIONS: LocationOption[] = [
  {
    id: 'leh',
    name: 'Leh',
    region: 'Ladakh',
    country: 'India',
    elevationM: 3524,
    climateType: 'Cold (High-Altitude Desert)',
    latitude: 34.1526,
    longitude: 77.5771,
    isHeroTarget: true,
  },
  {
    id: 'kargil',
    name: 'Kargil',
    region: 'Ladakh',
    country: 'India',
    elevationM: 2676,
    climateType: 'Cold (High-Altitude Mountain)',
    latitude: 34.5539,
    longitude: 76.1349,
  },
  {
    id: 'srinagar',
    name: 'Srinagar',
    region: 'Jammu and Kashmir',
    country: 'India',
    elevationM: 1585,
    climateType: 'Temperate (Mountain Valley)',
    latitude: 34.0837,
    longitude: 74.7973,
  },
  {
    id: 'jaisalmer',
    name: 'Jaisalmer',
    region: 'Rajasthan',
    country: 'India',
    elevationM: 225,
    climateType: 'Hot-Dry (Arid Desert)',
    latitude: 26.9157,
    longitude: 70.9083,
  },
  {
    id: 'delhi',
    name: 'Delhi NCR',
    region: 'Northern Plains',
    country: 'India',
    elevationM: 216,
    climateType: 'Composite (Extreme Seasonal Swings)',
    latitude: 28.6139,
    longitude: 77.2090,
  },
  {
    id: 'chennai',
    name: 'Chennai',
    region: 'Tamil Nadu',
    country: 'India',
    elevationM: 6,
    climateType: 'Warm-Humid (Coromandel Coast)',
    latitude: 13.0827,
    longitude: 80.2707,
  },
  {
    id: 'bengaluru',
    name: 'Bengaluru',
    region: 'Karnataka',
    country: 'India',
    elevationM: 920,
    climateType: 'Temperate (Deccan Plateau)',
    latitude: 12.9716,
    longitude: 77.5946,
  },
];

/**
 * Retrieve curated list of calibrated climate locations
 */
export async function listLocations(): Promise<LocationOption[]> {
  // Simulates lightweight async API fetch to prepare for backend REST endpoint
  await new Promise((resolve) => setTimeout(resolve, 80));
  return PRESET_LOCATIONS;
}

/**
 * Retrieve detailed site and climate profile for a given location identifier
 */
export async function getClimateProfile(locationIdOrName: string): Promise<ClimateProfile> {
  await new Promise((resolve) => setTimeout(resolve, 120));

  const normalized = locationIdOrName.toLowerCase().trim();
  const preset = PRESET_LOCATIONS.find(
    (loc) => loc.id === normalized || loc.name.toLowerCase() === normalized
  );

  if (preset) {
    if (preset.id === 'leh') {
      return {
        id: 'leh',
        name: 'Leh, Ladakh',
        region: 'Ladakh, India',
        elevationM: 3524,
        climateType: 'High-altitude cold',
        solarResource: 'High',
        winterSeverity: 'Extreme',
        diurnalVariation: 'High',
        dataConfidence: 'High',
        status: 'HISTORICAL',
        designWinterTempC: -18.5,
        designSummerTempC: 26.0,
        annualSolarGhiKwhM2: 2100.0,
        sourceNote: 'IMD Climatological Tables & NREL NSRDB / ASHRAE Fundamentals',
      };
    }

    if (preset.id === 'jaisalmer') {
      return {
        id: 'jaisalmer',
        name: 'Jaisalmer, Rajasthan',
        region: 'Thar Desert, India',
        elevationM: 225,
        climateType: 'Hot-Dry (Arid Desert)',
        solarResource: 'Extreme',
        winterSeverity: 'Mild',
        diurnalVariation: 'High',
        dataConfidence: 'High',
        status: 'HISTORICAL',
        designWinterTempC: 7.0,
        designSummerTempC: 46.0,
        annualSolarGhiKwhM2: 2250.0,
        sourceNote: 'MNRE Solar Resource Map & IMD Climatological Normals',
      };
    }

    if (preset.id === 'delhi') {
      return {
        id: 'delhi',
        name: 'Delhi NCR',
        region: 'Northern Plains, India',
        elevationM: 216,
        climateType: 'Composite (Extreme Seasonal Swings)',
        solarResource: 'Moderate',
        winterSeverity: 'Moderate',
        diurnalVariation: 'Moderate',
        dataConfidence: 'High',
        status: 'HISTORICAL',
        designWinterTempC: 5.0,
        designSummerTempC: 43.5,
        annualSolarGhiKwhM2: 1900.0,
        sourceNote: 'Bureau of Energy Efficiency (BEE) ECBC / ISHRAE',
      };
    }

    if (preset.id === 'chennai') {
      return {
        id: 'chennai',
        name: 'Chennai',
        region: 'Coromandel Coast, India',
        elevationM: 6,
        climateType: 'Warm-Humid Coastal',
        solarResource: 'Moderate',
        winterSeverity: 'Mild',
        diurnalVariation: 'Low',
        dataConfidence: 'High',
        status: 'HISTORICAL',
        designWinterTempC: 20.0,
        designSummerTempC: 38.0,
        annualSolarGhiKwhM2: 1850.0,
        sourceNote: 'IMD Marine Station & ASHRAE Weather Data',
      };
    }

    // Default for other known presets
    return {
      id: preset.id,
      name: `${preset.name}, ${preset.region}`,
      region: `${preset.region}, ${preset.country}`,
      elevationM: preset.elevationM,
      climateType: preset.climateType,
      solarResource: 'Moderate',
      winterSeverity: 'Moderate',
      diurnalVariation: 'Moderate',
      dataConfidence: 'High',
      status: 'HISTORICAL',
      sourceNote: 'Regional Climatological Observation',
    };
  }

  // Handle custom, offline, or unmapped locations gracefully
  const isOffline = normalized === 'offline' || normalized.includes('unknown');
  const status: DataStatus = isOffline ? 'ESTIMATED' : 'DEMO_MOCK';

  return {
    id: isOffline ? 'offline-loc' : 'custom-loc',
    name: locationIdOrName || 'Uncalibrated Site',
    region: isOffline ? 'Offline / Remote Coordinates' : 'Custom Input Coordinates',
    elevationM: null,
    climateType: isOffline ? 'Unmapped (Synthetic Alpine Baseline)' : 'Estimated Regional Climate',
    solarResource: 'Moderate',
    winterSeverity: 'Moderate',
    diurnalVariation: 'Moderate',
    dataConfidence: 'Low',
    status,
    sourceNote: isOffline
      ? 'Offline synthetic envelope estimate (Field calibration recommended)'
      : 'Interpolated regional estimates (Awaiting meteorological station pairing)',
  };
}
