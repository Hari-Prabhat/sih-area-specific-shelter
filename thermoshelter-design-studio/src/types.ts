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
  /** D4-A: explicit envelope insulation thickness in cm (0 = uninsulated).
   *  Sent to the backend as insulation_thickness_m; optimizer candidates
   *  restore this value on Apply so applied designs reproduce the
   *  candidate's simulated U-values. */
  insulationThickness: number;
  /** D4-A WP1: air changes per hour — canonical backend design field
   *  (services/contracts.py ShelterDesign.ach, preset DEFAULT_ACH = 0.5). */
  ach: number;
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
  /** D4-A: genuine backend energy metric (heating demand, kWh) — replaces the
   *  former energyEfficiency field that mislabelled comfort percentage as an
   *  independent energy-efficiency metric. */
  heatingDemandKwh: number;
  hourlyTemperatures: number[];
  monthlyTemperatures: number[];
  recommendedImprovements: string[];
}
