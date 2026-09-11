import { MaterialProperties } from '../utils/thermalEngine';

export const materials: MaterialProperties[] = [
  { name: "Mud/Adobe", thermalConductivity: 0.55, density: 1700, specificHeat: 920, emissivity: 0.91, solarAbsorptance: 0.65, cost: 200, category: "Traditional" },
  { name: "Stone (Granite)", thermalConductivity: 2.5, density: 2700, specificHeat: 790, emissivity: 0.90, solarAbsorptance: 0.60, cost: 800, category: "Traditional" },
  { name: "Stone (Limestone)", thermalConductivity: 1.3, density: 2400, specificHeat: 900, emissivity: 0.88, solarAbsorptance: 0.55, cost: 600, category: "Traditional" },
  { name: "Timber/Wood", thermalConductivity: 0.15, density: 600, specificHeat: 1700, emissivity: 0.90, solarAbsorptance: 0.50, cost: 500, category: "Traditional" },
  { name: "Bamboo Composite", thermalConductivity: 0.12, density: 400, specificHeat: 1500, emissivity: 0.85, solarAbsorptance: 0.45, cost: 300, category: "Traditional" },
  { name: "Brick (Solid)", thermalConductivity: 0.72, density: 1920, specificHeat: 835, emissivity: 0.93, solarAbsorptance: 0.70, cost: 450, category: "Modern" },
  { name: "Concrete (Dense)", thermalConductivity: 1.7, density: 2300, specificHeat: 880, emissivity: 0.92, solarAbsorptance: 0.65, cost: 550, category: "Modern" },
  { name: "Concrete (Lightweight)", thermalConductivity: 0.38, density: 1400, specificHeat: 1000, emissivity: 0.90, solarAbsorptance: 0.55, cost: 650, category: "Modern" },
  { name: "Steel Sheet", thermalConductivity: 50.0, density: 7800, specificHeat: 500, emissivity: 0.25, solarAbsorptance: 0.35, cost: 900, category: "Modern" },
  { name: "Glass (Clear)", thermalConductivity: 1.0, density: 2500, specificHeat: 840, emissivity: 0.90, solarAbsorptance: 0.15, cost: 1200, category: "Modern" },
  { name: "Expanded Polystyrene (EPS)", thermalConductivity: 0.035, density: 25, specificHeat: 1400, emissivity: 0.90, solarAbsorptance: 0.30, cost: 250, category: "Insulation" },
  { name: "Polyurethane Foam (PUF)", thermalConductivity: 0.025, density: 35, specificHeat: 1400, emissivity: 0.90, solarAbsorptance: 0.25, cost: 400, category: "Insulation" },
  { name: "Glass Wool", thermalConductivity: 0.040, density: 30, specificHeat: 800, emissivity: 0.90, solarAbsorptance: 0.20, cost: 300, category: "Insulation" },
  { name: "Rock Wool", thermalConductivity: 0.045, density: 80, specificHeat: 1000, emissivity: 0.90, solarAbsorptance: 0.30, cost: 350, category: "Insulation" },
  { name: "Vermiculite", thermalConductivity: 0.065, density: 120, specificHeat: 1200, emissivity: 0.90, solarAbsorptance: 0.40, cost: 200, category: "Insulation" },
  { name: "AAC Block (Autoclaved Aerated Concrete)", thermalConductivity: 0.16, density: 600, specificHeat: 1000, emissivity: 0.90, solarAbsorptance: 0.50, cost: 700, category: "Composite" },
  { name: "SIP Panel (Structural Insulated Panel)", thermalConductivity: 0.035, density: 150, specificHeat: 1300, emissivity: 0.90, solarAbsorptance: 0.35, cost: 1500, category: "Composite" },
  { name: "Rammed Earth (Stabilized)", thermalConductivity: 0.65, density: 2000, specificHeat: 920, emissivity: 0.92, solarAbsorptance: 0.60, cost: 350, category: "Composite" },
  { name: "Phase Change Material (PCM) Wall", thermalConductivity: 0.20, density: 800, specificHeat: 3500, emissivity: 0.90, solarAbsorptance: 0.40, cost: 2500, category: "Composite" },
  { name: "Trombe Wall (Concrete + Glass)", thermalConductivity: 1.2, density: 2200, specificHeat: 900, emissivity: 0.95, solarAbsorptance: 0.90, cost: 1000, category: "Composite" },
];

export function getMaterialByName(name: string): MaterialProperties | undefined {
  return materials.find(m => m.name === name || m.name.includes(`(${name})`) || m.name.toLowerCase().includes(name.toLowerCase()));
}
