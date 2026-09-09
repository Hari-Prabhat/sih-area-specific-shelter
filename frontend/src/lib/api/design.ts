import type {
  ShelterRequirements,
  ShelterDesign,
  DesignDNAData,
  ShelterGeometry,
  MaterialAssembly,
} from '../../types';
import { getClimateProfile } from './climate';

/**
 * Generates an area-specific shelter design based on structured user requirements.
 * Prepared for backend coupling with FastAPI / Streamlit backend.
 * Uses structured mock generation with transparent DEMO_MOCK provenance tracking.
 */
export async function generateDesign(requirements: ShelterRequirements): Promise<ShelterDesign> {
  // Simulated processing delay to allow UI to display realistic engineering loading states
  await new Promise((resolve) => setTimeout(resolve, 600));

  const cityKey = (requirements.location.locationId || requirements.location.displayName).toLowerCase();
  const isLeh = cityKey.includes('leh') || cityKey.includes('ladakh');
  const isJaisalmer = cityKey.includes('jaisalmer') || cityKey.includes('desert');
  const isTemp = requirements.mission.deploymentType === 'Temporary';
  const people = Math.max(1, requirements.mission.occupants || 4);

  // Auto-sizing geometry standard (4.5 m2/person SP41 baseline)
  const floorArea = Math.max(12.0, Math.round(people * 4.5 * 10) / 10);
  const length = Math.round(Math.sqrt(floorArea * 1.3) * 10) / 10;
  const width = Math.round((floorArea / length) * 10) / 10;
  const height = isTemp ? 2.6 : 2.8;
  const volume = Math.round(length * width * height * 100) / 100;
  const windowArea = Math.round(floorArea * (isLeh ? 0.22 : 0.15) * 10) / 10;

  const climate = await getClimateProfile(requirements.location.locationId || 'leh');

  if (isLeh || requirements.isDemoScenario) {
    const dna: DesignDNAData = {
      code: 'THERMOCORE-LADAKH-01',
      climate: 'Cold / Arid',
      strategy: 'Solar Capture + Thermal Retention',
      geometry: 'Compact',
      orientation: 'South-biased',
      envelope: 'High Performance',
      thermalMass: 'High',
      ventilation: 'Controlled',
    };

    const geometry: ShelterGeometry = {
      footprintM2: floorArea,
      lengthM: length,
      widthM: width,
      heightM: height,
      volumeM3: volume,
      aspectRatio: 1.3,
      roofType: 'pitched',
      roofSlopeDeg: 40,
      windowAreaM2: windowArea,
      orientation: 'South-biased (180° ± 15°)',
      status: 'DEMO_MOCK',
    };

    const materials: MaterialAssembly = {
      wallMaterial: isTemp
        ? 'PUF Insulated Composite Sandwich Panel (Prefab Modular)'
        : 'Double-Walled Cavity Local Stone / Mud Brick Core',
      roofMaterial: isTemp
        ? 'Insulated Corrugated Metal Sheet with 40° Snow-shedding Pitch'
        : 'Reinforced Insulated Concrete Pitched Slab with Slate Overlayer',
      floorMaterial: 'Soil-gravel floor bed with perimeter thermal break barrier',
      insulationType: 'High-Density Polyurethane Foam (PUF / PIR Core)',
      insulationThicknessMm: isTemp ? 80 : 150,
      glazingType: 'Triple Glazed Low-E Argon-filled (Ug: 0.8 W/m²K, SHGC: 0.58)',
      thermalMassLevel: isTemp ? 'Medium' : 'High',
      status: 'DEMO_MOCK',
    };

    return {
      designId: 'THERMOCORE-LADAKH-01',
      designName: 'High-Altitude Cold Passive Solar Shelter',
      createdAt: new Date().toISOString(),
      status: 'DEMO_MOCK',
      isDemo: true,
      requirements,
      climateProfile: climate,
      dna,
      geometry,
      materials,
      passiveStrategy: 'Direct Gain South Fenestration + Thermal Storage Core + Night Thermal Shutter Insulation',
      ventilationStrategy: 'Controlled low-infiltration mechanical HRV / stack damper with pre-warmed intake',
      designRationale: [
        'South-biased orientation maximizes low-angle winter solar altitude gain during sub-zero months.',
        'Compact geometric envelope minimizes external exposed surface-to-volume ratio (A/V), drastically limiting nocturnal conductive heat leakage.',
        'High internal thermal mass dampens extreme Ladakh diurnal swings of 15°C–20°C, storing midday solar gains for nocturnal radiant release.',
        'Controlled low-leakage ventilation barrier prevents convective cold infiltration while maintaining fresh air exchange.',
      ],
      operationalNotes: [
        'Deploy exterior insulated night shutters over South glazing before sunset.',
        'Ensure snow shedding zone around 40° pitched eaves remains clear.',
      ],
    };
  }

  // Generative mock for other geographic selections
  const designCode = isJaisalmer
    ? 'THERMOCORE-DESERT-02'
    : isTemp
    ? 'THERMOCORE-RAPID-03'
    : 'THERMOCORE-GENERIC-04';

  const dna: DesignDNAData = {
    code: designCode,
    climate: isJaisalmer ? 'Hot / Arid' : 'Moderate / Composite',
    strategy: isJaisalmer ? 'Solar Rejection + Thermal Lag' : 'Balanced Daylighting + Cross Ventilation',
    geometry: isTemp ? 'Elongated Modular' : 'Compact',
    orientation: 'North-South Axis',
    envelope: 'Thermal Inertia Optimized',
    thermalMass: isJaisalmer ? 'High' : 'Medium',
    ventilation: isJaisalmer ? 'Night Flush' : 'Natural Cross-Flow',
  };

  const geometry: ShelterGeometry = {
    footprintM2: floorArea,
    lengthM: length,
    widthM: width,
    heightM: height,
    volumeM3: volume,
    aspectRatio: 1.3,
    roofType: isJaisalmer ? 'flat' : 'shed',
    windowAreaM2: windowArea,
    orientation: 'North-South (Balanced)',
    status: 'DEMO_MOCK',
  };

  const materials: MaterialAssembly = {
    wallMaterial: isJaisalmer
      ? 'High-Albedo Sandstone / Rammed Earth Assembly'
      : 'Modular Aerated Lightweight Concrete / PUF Composite',
    roofMaterial: 'High-Reflectance Cool Roof Coating over Concrete Deck',
    floorMaterial: 'Stabilized Earth / Cast Concrete Slab',
    insulationType: 'Extruded Polystyrene (XPS) Exterior Envelope',
    insulationThicknessMm: 75,
    glazingType: 'Double Glazed Low-E Solar Control Glass',
    thermalMassLevel: 'High',
    status: 'DEMO_MOCK',
  };

  return {
    designId: designCode,
    designName: `${climate.name} Passive Shelter Specification`,
    createdAt: new Date().toISOString(),
    status: 'DEMO_MOCK',
    isDemo: true,
    requirements,
    climateProfile: climate,
    dna,
    geometry,
    materials,
    passiveStrategy: isJaisalmer
      ? 'High-Albedo Solar Shielding + Deep Eaves + Nocturnal Purge Ventilation'
      : 'Natural Cross-Ventilation + Daylight Harvesting + Moderate Insulation',
    ventilationStrategy: isJaisalmer
      ? 'Nocturnal cool-air purge with sealed daytime dampers'
      : 'High-low stack operable louvers with mosquito filtration',
    designRationale: [
      `Sized for ${people} occupants adhering to ${floorArea} m² habitability standard.`,
      `Materials adapted for ${requirements.mission.deploymentType.toLowerCase()} deployment duration (${requirements.mission.duration.toLowerCase()}).`,
      `Engineered passive envelope prioritized for: ${requirements.priorities.map((p) => p.priority).join(', ')}.`,
    ],
  };
}
