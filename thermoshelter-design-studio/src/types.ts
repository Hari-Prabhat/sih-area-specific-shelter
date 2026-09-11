/**
 * THERMOSHELTER AI - Core Frontend UI/Data Types
 * ==============================================
 * Presentation and data contracts for the React Design Studio.
 * NOTE: Thermal physics simulations, forward Euler algorithms,
 * and Bayesian optimizations are performed exclusively by the Python backend.
 * These types represent API responses and UI configuration data only.
 */

export interface ClimateData {
  location: string;
  altitude: number;
  ambientTempMin: number;
  ambientTempMax: number;
  avgAmbientTemp: number;
  solarIrradiance: number;
  avgSunshineHours: number;
  windSpeed: number;
  humidity: number;
  cloudFreeDays: number;
}

export interface ShelterDesign {
  length: number;
  width: number;
  height: number;
  shape: 'rectangular' | 'cylindrical' | 'dome' | 'pyramid';
  orientation: number;
  roofAngle: number;
  wallThickness: number;
  windowArea: number;
  windowGlazing: 'single' | 'double' | 'triple';
  doorArea: number;
  insulationType: string;
  thermalMassEnabled: boolean;
  thermalMassThickness: number;
}

export interface MaterialProperties {
  name: string;
  thermalConductivity: number;
  density: number;
  specificHeat: number;
  emissivity: number;
  solarAbsorptance: number;
  cost: number;
  category: string;
}

export interface SimulationResult {
  avgInsideTemp: number;
  minInsideTemp: number;
  maxInsideTemp: number;
  dailyTempVariation: number;
  solarEnergyGain: number;
  heatLossThroughWalls: number;
  heatLossThroughRoof: number;
  heatLossThroughFloor: number;
  heatLossThroughWindows: number;
  heatLossThroughDoors: number;
  totalHeatLoss: number;
  netHeatBalance: number;
  thermalComfortIndex: number;
  energyEfficiency: number;
  hourlyTemperatures: number[];
  monthlyTemperatures: number[];
  recommendedImprovements: string[];
}
