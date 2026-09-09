import type { OptimizationResult, DesignPriority } from '../../types';

/**
 * Invokes Bayesian multi-objective optimization (Optuna TPE) to refine envelope parameters.
 * Clean abstraction layer preparing for backend connection to services/optimize.py.
 */
export async function optimizeDesign(
  designId: string,
  _priorities: DesignPriority[] = ['Thermal Comfort', 'Energy Independence']
): Promise<OptimizationResult> {
  await new Promise((resolve) => setTimeout(resolve, 950));

  return {
    optId: `OPT-${Date.now().toString().slice(-6)}`,
    baselineDesignId: designId,
    optimizedDesignId: `${designId}-OPT`,
    status: 'DEMO_MOCK',
    isMock: true,
    trialsCount: 50,
    parameterAdjustments: [
      {
        parameter: 'Wall Insulation Thickness',
        baseline: '100 mm',
        optimized: '140 mm',
        unit: 'mm',
      },
      {
        parameter: 'South Glazing Area',
        baseline: '3.2 m²',
        optimized: '4.1 m²',
        unit: 'm²',
      },
      {
        parameter: 'Roof Pitch Angle',
        baseline: '35°',
        optimized: '42°',
        unit: 'deg',
      },
      {
        parameter: 'Night Shutter Thermal Resistance (R)',
        baseline: '0.8 m²K/W',
        optimized: '1.6 m²K/W',
        unit: 'm²K/W',
      },
    ],
    improvements: [
      {
        metric: 'Discomfort Degree Hours',
        before: 64.2,
        after: 24.8,
        percentageImprovement: 61.4,
        unit: '°C·h',
      },
      {
        metric: 'Weekly Heating Deficiency',
        before: 112.5,
        after: 46.1,
        percentageImprovement: 59.0,
        unit: 'kWh',
      },
      {
        metric: 'Comfort Hours Ratio',
        before: 68.0,
        after: 89.3,
        percentageImprovement: 31.3,
        unit: '%',
      },
    ],
  };
}
