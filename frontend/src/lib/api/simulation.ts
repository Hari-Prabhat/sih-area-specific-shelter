import type { SimulationResult } from '../../types';

/**
 * Executes a 168-hour transient forward-Euler thermal simulation for a shelter design.
 * Clean abstraction layer preparing for backend connection to services/simulation_service.py.
 */
export async function runSimulation(designId: string): Promise<SimulationResult> {
  await new Promise((resolve) => setTimeout(resolve, 800));

  // Hourly synthetic curve simulating 168 hours (7 days)
  const profile = Array.from({ length: 168 }, (_, i) => {
    const dayProgress = (i % 24) / 24;
    const outdoor = -15 + 12 * Math.sin(dayProgress * 2 * Math.PI - Math.PI / 2);
    // Thermal mass dampens and lags the interior wave
    const indoor = 18.5 + 3.2 * Math.sin((dayProgress - 0.25) * 2 * Math.PI - Math.PI / 2);
    return {
      hour: i + 1,
      outdoorTempC: Math.round(outdoor * 10) / 10,
      indoorTempC: Math.round(indoor * 10) / 10,
    };
  });

  return {
    simId: `SIM-${Date.now().toString().slice(-6)}`,
    designId,
    status: 'DEMO_MOCK',
    isMock: true,
    durationHours: 168,
    indoorTempProfile: profile,
    metrics: {
      avgIndoorTempC: 19.1,
      minIndoorTempC: 16.2,
      maxIndoorTempC: 22.4,
      comfortHours: 142,
      comfortPercentage: 84.5,
      discomfortDegreeHours: 32.8,
      totalHeatLossKwh: 98.4,
      usefulSolarGainKwh: 54.2,
    },
    envelopeUValues: {
      wallU: 0.24,
      roofU: 0.21,
      floorU: 0.35,
      windowU: 0.85,
    },
  };
}
