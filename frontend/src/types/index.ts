/**
 * ==============================================================================
 * ThermoShelter Engineering Platform — Shared Frontend Type Contracts
 * ==============================================================================
 * Strict data contracts separating user requirements from backend physics.
 * Adheres strictly to Section 7, 9, 12, 16 of ThermoShelter Design Studio specification.
 */

/**
 * Data status indicators to strictly distinguish source provenance.
 * Never present mock or simulated values as measured real-world conditions.
 */
export type DataStatus = 
  | 'MEASURED'      // Actual sensor / API observation
  | 'HISTORICAL'    // Historical weather / climate data (EPW / IMD / ASHRAE)
  | 'ESTIMATED'     // Derived / interpolated information
  | 'SIMULATED'     // Produced by thermal physics model
  | 'OPTIMIZED'     // Produced by optimization algorithm (e.g. Optuna TPE)
  | 'DEMO_MOCK';    // Development / mock data only

/**
 * Location selection mode for Step 1
 */
export type LocationMode = 'current' | 'preset' | 'custom' | 'offline';

export interface LocationSelection {
  mode: LocationMode;
  locationId?: string;       // e.g. 'leh', 'jaisalmer', 'delhi'
  displayName: string;       // e.g. 'Leh, Ladakh, India'
  latitude?: number;
  longitude?: number;
  elevationM?: number;
  notes?: string;
}

/**
 * Step 2: Mission parameters
 */
export type MissionPurpose =
  | 'Military'
  | 'Disaster Relief'
  | 'Research'
  | 'Residential'
  | 'Medical'
  | 'Storage'
  | 'Command / Operations'
  | 'Temporary Accommodation';

export type DeploymentType = 'Temporary' | 'Seasonal' | 'Permanent';

export type DeploymentDuration = 'Days' | 'Weeks' | 'Months' | 'Years';

export interface MissionRequirements {
  occupants: number;
  purpose: MissionPurpose;
  deploymentType: DeploymentType;
  duration: DeploymentDuration;
}

/**
 * Step 3: Structured engineering priorities
 */
export type DesignPriority =
  | 'Thermal Comfort'
  | 'Energy Independence'
  | 'Low Cost'
  | 'Low Weight'
  | 'Rapid Deployment'
  | 'Durability';

export type PriorityImportance = 'Primary' | 'Secondary' | 'Standard';

export interface PrioritySelection {
  priority: DesignPriority;
  importance: PriorityImportance;
}

/**
 * Step 4: Available Resources (Optional)
 */
export type EnergyResource = 'Solar' | 'Grid' | 'Diesel Generator' | 'None';

export type MaterialResource =
  | 'Local Stone'
  | 'Timber'
  | 'Steel'
  | 'Insulation Panels'
  | 'Other';

export interface AvailableResources {
  energy: EnergyResource[];
  materials: MaterialResource[];
  customMaterialNotes?: string;
}

/**
 * Consolidated User Shelter Requirements
 */
export interface ShelterRequirements {
  location: LocationSelection;
  mission: MissionRequirements;
  priorities: PrioritySelection[];
  resources: AvailableResources;
  isDemoScenario?: boolean;
}

/**
 * Site Profile Contract (Consumes climate info for display in Step 5 / Results)
 */
export interface ClimateProfile {
  id: string;
  name: string;
  region: string;
  elevationM?: number | null;
  climateType: string;
  solarResource: 'Low' | 'Moderate' | 'High' | 'Extreme';
  winterSeverity: 'Mild' | 'Moderate' | 'Severe' | 'Extreme';
  diurnalVariation: 'Low' | 'Moderate' | 'High' | 'Extreme';
  dataConfidence: 'Low' | 'Medium' | 'High';
  status: DataStatus;
  designWinterTempC?: number;
  designSummerTempC?: number;
  annualSolarGhiKwhM2?: number;
  sourceNote?: string;
}

/**
 * Structural Geometry Contract (Output from backend auto-sizing)
 */
export interface ShelterGeometry {
  footprintM2: number;
  lengthM: number;
  widthM: number;
  heightM: number;
  volumeM3: number;
  aspectRatio: number;
  roofType: 'flat' | 'pitched' | 'shed';
  roofSlopeDeg?: number;
  windowAreaM2: number;
  orientation: string;
  status: DataStatus;
}

/**
 * Material Assembly Contract (Recommended envelope envelope configuration)
 */
export interface MaterialAssembly {
  wallMaterial: string;
  roofMaterial: string;
  floorMaterial: string;
  insulationType: string;
  insulationThicknessMm: number;
  glazingType: string;
  thermalMassLevel: 'Low' | 'Medium' | 'High';
  status: DataStatus;
}

/**
 * Design DNA Contract (Exact specifications matching Section 5)
 */
export interface DesignDNAData {
  code: string;               // e.g. 'THERMOCORE-LADAKH-01'
  climate: string;            // e.g. 'Cold / Arid'
  strategy: string;           // e.g. 'Solar Capture + Thermal Retention'
  geometry: string;           // e.g. 'Compact'
  orientation: string;        // e.g. 'South-biased'
  envelope: string;           // e.g. 'High Performance'
  thermalMass: string;        // e.g. 'High'
  ventilation: string;        // e.g. 'Controlled'
}

/**
 * Complete Shelter Design Contract
 */
export interface ShelterDesign {
  designId: string;           // e.g. 'THERMOCORE-LADAKH-01'
  designName: string;
  createdAt: string;
  status: DataStatus;
  isDemo: boolean;
  requirements: ShelterRequirements;
  climateProfile: ClimateProfile;
  dna: DesignDNAData;
  geometry: ShelterGeometry;
  materials: MaterialAssembly;
  passiveStrategy: string;
  ventilationStrategy: string;
  designRationale: string[];
  operationalNotes?: string[];
}

/**
 * Future Simulation Result Contract
 */
export interface SimulationResult {
  simId: string;
  designId: string;
  status: DataStatus;
  isMock: boolean;
  durationHours: number;
  indoorTempProfile: { hour: number; outdoorTempC: number; indoorTempC: number }[];
  metrics: {
    avgIndoorTempC: number;
    minIndoorTempC: number;
    maxIndoorTempC: number;
    comfortHours: number;
    comfortPercentage: number;
    discomfortDegreeHours: number;
    totalHeatLossKwh: number;
    usefulSolarGainKwh: number;
  };
  envelopeUValues: {
    wallU: number;
    roofU: number;
    floorU: number;
    windowU: number;
  };
}

/**
 * Future Optimization Result Contract
 */
export interface OptimizationResult {
  optId: string;
  baselineDesignId: string;
  optimizedDesignId: string;
  status: DataStatus;
  isMock: boolean;
  trialsCount: number;
  parameterAdjustments: {
    parameter: string;
    baseline: string | number;
    optimized: string | number;
    unit?: string;
  }[];
  improvements: {
    metric: string;
    before: number;
    after: number;
    percentageImprovement: number;
    unit: string;
  }[];
}

/**
 * Navigation View Mode
 */
export type AppViewMode =
  | 'design'
  | 'climate'
  | 'simulation'
  | 'compare'
  | 'materials'
  | 'blueprint'
  | 'report';
