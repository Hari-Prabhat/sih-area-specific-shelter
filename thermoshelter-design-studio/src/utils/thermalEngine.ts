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

export function calculateSurfaceAreas(design: ShelterDesign) {
  const { length, width, height, shape } = design;
  switch (shape) {
    case 'rectangular':
      return {
        wallArea: 2 * (length * height) + 2 * (width * height),
        roofArea: length * width,
        floorArea: length * width,
        volume: length * width * height
      };
    case 'cylindrical': {
      const r = Math.sqrt((length * width) / Math.PI);
      return {
        wallArea: 2 * Math.PI * r * height,
        roofArea: Math.PI * r * r,
        floorArea: Math.PI * r * r,
        volume: Math.PI * r * r * height
      };
    }
    case 'dome': {
      const r = Math.sqrt((length * width) / Math.PI);
      return {
        wallArea: Math.PI * r * height,
        roofArea: 2 * Math.PI * r * r,
        floorArea: Math.PI * r * r,
        volume: (2 / 3) * Math.PI * r * r * r
      };
    }
    case 'pyramid': {
      const base = length * width;
      return {
        wallArea: base * 1.5,
        roofArea: base,
        floorArea: base,
        volume: (1 / 3) * base * height
      };
    }
    default:
      return {
        wallArea: 2 * (length * height) + 2 * (width * height),
        roofArea: length * width,
        floorArea: length * width,
        volume: length * width * height
      };
  }
}

export function calculateUValue(
  material: MaterialProperties,
  thickness: number,
  hasInsulation: boolean,
  insulationMaterial?: MaterialProperties
): number {
  const Ri = 0.13;
  const Re = 0.04;
  const Rmaterial = thickness / material.thermalConductivity;
  let totalR = Ri + Re + Rmaterial;
  if (hasInsulation && insulationMaterial) {
    totalR += 0.05 / insulationMaterial.thermalConductivity;
  }
  return 1 / totalR;
}

export function getWindowUValue(glazing: 'single' | 'double' | 'triple'): number {
  return glazing === 'single' ? 5.8 : glazing === 'double' ? 2.8 : 1.5;
}

export function runSimulation(
  climate: ClimateData,
  design: ShelterDesign,
  material: MaterialProperties,
  insulationMaterial?: MaterialProperties
): SimulationResult {
  const surfaces = calculateSurfaceAreas(design);
  const dailyIrradiance = climate.solarIrradiance / 365;

  // Solar gain
  const windowSHGC = design.windowGlazing === 'single' ? 0.85 : design.windowGlazing === 'double' ? 0.70 : 0.55;
  const windowSolarGain = design.windowArea * dailyIrradiance * windowSHGC;
  const orientationFactor = Math.cos((design.orientation * Math.PI) / 180) * 0.5 + 0.5;
  const wallSolarGain = surfaces.wallArea * dailyIrradiance * 0.6 * orientationFactor * 0.1;
  const roofSolarGain = surfaces.roofArea * dailyIrradiance * 0.7 * 0.15;
  const thermalMassFactor = design.thermalMassEnabled ? 1.15 : 1.0;
  const solarGain = (windowSolarGain + wallSolarGain + roofSolarGain) * thermalMassFactor;

  // Heat loss
  const tempDiff = climate.avgAmbientTemp - 18;
  const wallU = calculateUValue(material, design.wallThickness, true, insulationMaterial);
  const roofU = calculateUValue(material, design.wallThickness * 0.8, true, insulationMaterial);
  const floorU = calculateUValue(material, 0.15, true, insulationMaterial);
  const windowU = getWindowUValue(design.windowGlazing);
  const windFactor = 1 + (climate.windSpeed * 0.02);

  const wallLoss = surfaces.wallArea * wallU * Math.abs(tempDiff) * windFactor;
  const roofLoss = surfaces.roofArea * roofU * Math.abs(tempDiff) * windFactor * 1.2;
  const floorLoss = surfaces.floorArea * floorU * Math.abs(tempDiff) * 0.5;
  const windowLoss = design.windowArea * windowU * Math.abs(tempDiff);
  const doorLoss = design.doorArea * 3.5 * Math.abs(tempDiff);
  const totalLoss = wallLoss + roofLoss + floorLoss + windowLoss + doorLoss;

  const solarGainW = (solarGain * 1000) / 24;
  const netBalance = solarGainW - totalLoss;
  const shelterEffect = netBalance > 0 ? Math.min(12, netBalance / 500) : Math.max(-5, netBalance / 300);

  const avgInsideTemp = Math.round((climate.avgAmbientTemp + shelterEffect + 5) * 10) / 10;
  const minInsideTemp = Math.round((avgInsideTemp - 3 - (design.thermalMassEnabled ? 1 : 2)) * 10) / 10;
  const maxInsideTemp = Math.round((avgInsideTemp + 4 + (design.thermalMassEnabled ? 1 : 2)) * 10) / 10;

  // Hourly temperatures
  const hourlyTemperatures: number[] = [];
  for (let hour = 0; hour < 24; hour++) {
    const tempRange = climate.ambientTempMax - climate.ambientTempMin;
    const ambientTemp = climate.avgAmbientTemp + (tempRange / 2) * Math.sin(((hour - 9) * Math.PI) / 12);
    let solarAtHour = 0;
    if (hour >= 6 && hour <= 18) {
      solarAtHour = dailyIrradiance * 1.5 * Math.max(0, Math.cos(((hour - 12) * Math.PI) / 12));
    }
    const solarGainHour = (design.windowArea * solarAtHour * windowSHGC + surfaces.roofArea * solarAtHour * 0.7 * 0.15) * 1000;
    const heatLossHour = (surfaces.wallArea * wallU + surfaces.roofArea * roofU + design.windowArea * windowU) * (18 - ambientTemp) * 10;
    const thermalMass = design.thermalMassEnabled
      ? (design.thermalMassThickness / 100) * material.density * material.specificHeat * surfaces.wallArea
      : 100000;
    const tempChange = (solarGainHour - Math.max(0, heatLossHour)) / thermalMass;
    hourlyTemperatures.push(Math.round((ambientTemp + 5 + tempChange * 2) * 10) / 10);
  }

  // Monthly temperatures
  const monthlyOffsets = [-8, -5, -1, 4, 8, 12, 14, 13, 9, 4, -2, -6];
  const monthlyTemperatures = monthlyOffsets.map((offset) => {
    const ambientMonth = climate.avgAmbientTemp + offset;
    const shelterEffect = ambientMonth < 15 ? 8 : ambientMonth > 30 ? -5 : 3;
    return Math.round((ambientMonth + shelterEffect) * 10) / 10;
  });

  // Comfort index
  const optimalTemp = 22;
  const tempDeviation = Math.abs(avgInsideTemp - optimalTemp);
  const tempScore = Math.max(0, 50 - tempDeviation * 5);
  const humidityScore = Math.max(
    0,
    25 - (climate.humidity < 30 ? (30 - climate.humidity) * 0.5 : climate.humidity > 60 ? (climate.humidity - 60) * 0.5 : 0)
  );
  const airScore = Math.max(0, 25 - (climate.windSpeed > 2 ? (climate.windSpeed - 2) * 5 : 0));
  const comfortIndex = Math.round(tempScore + humidityScore + airScore);
  const energyEfficiency = Math.round(
    Math.min(100, Math.max(0, 50 + (solarGainW / (totalLoss + 1)) * 30 + (design.thermalMassEnabled ? 10 : 0)))
  );

  // Recommendations
  const recommendations: string[] = [];
  if (roofLoss > wallLoss * 0.5) {
    recommendations.push("Increase roof insulation thickness to reduce heat loss through the roof.");
  }
  if (design.windowArea > surfaces.wallArea * 0.2) {
    recommendations.push("Reduce window-to-wall ratio or upgrade to triple glazing.");
  }
  if (!design.thermalMassEnabled) {
    recommendations.push("Add thermal mass material to store solar heat during day and release at night.");
  }
  if (climate.windSpeed > 5) {
    recommendations.push("Consider windbreak walls or vegetation barriers.");
  }
  if (design.orientation > 45 && design.orientation < 315) {
    recommendations.push("Reorient shelter to face south (180°) for maximum solar gain.");
  }
  if (comfortIndex < 60) {
    recommendations.push("Thermal comfort is below optimal. Consider improved insulation and passive solar design.");
  }
  if (recommendations.length === 0) {
    recommendations.push("Design is well-optimized for the given climate conditions.");
  }

  return {
    avgInsideTemp,
    minInsideTemp,
    maxInsideTemp,
    dailyTempVariation: Math.round((maxInsideTemp - minInsideTemp) * 10) / 10,
    solarEnergyGain: Math.round(solarGain * 100) / 100,
    heatLossThroughWalls: Math.round(wallLoss),
    heatLossThroughRoof: Math.round(roofLoss),
    heatLossThroughFloor: Math.round(floorLoss),
    heatLossThroughWindows: Math.round(windowLoss),
    heatLossThroughDoors: Math.round(doorLoss),
    totalHeatLoss: Math.round(totalLoss),
    netHeatBalance: Math.round(netBalance),
    thermalComfortIndex: comfortIndex,
    energyEfficiency,
    hourlyTemperatures,
    monthlyTemperatures,
    recommendedImprovements: recommendations,
  };
}
