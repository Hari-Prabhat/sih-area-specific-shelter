/**
 * Studio store unit tests (D2) — Vitest
 * =====================================
 * Verifies the shared-state architecture's engineering-critical behavior
 * WITHOUT thermal math: the candidate → ShelterDesign thermal-mass
 * preservation contract (mirroring services/optimize.py THERMAL_MASS_LEVELS)
 * and the provenance selector mapping.
 */

import { describe, expect, it } from 'vitest';

import { massLevelToDesignMass, orientationToDegrees, glazingToUi } from './useStudioState';
import { activeWeatherProvenance } from './useStudioState';
import type { SimulationClimateProfile } from '../services/api';

describe('candidate thermal-mass preservation (D2 bug fix)', () => {
  it('maps optimizer mass levels onto canonical ShelterDesign semantics', () => {
    // services/optimize.py THERMAL_MASS_LEVELS: none/low/medium/high → 0/50/100/200 mm
    expect(massLevelToDesignMass('none')).toEqual({ thermalMassEnabled: false, thermalMassThickness: 0 });
    expect(massLevelToDesignMass('low')).toEqual({ thermalMassEnabled: true, thermalMassThickness: 5 });
    expect(massLevelToDesignMass('medium')).toEqual({ thermalMassEnabled: true, thermalMassThickness: 10 });
    expect(massLevelToDesignMass('high')).toEqual({ thermalMassEnabled: true, thermalMassThickness: 20 });
  });

  it('treats missing or unknown levels as disabled mass (no invented values)', () => {
    expect(massLevelToDesignMass(undefined)).toEqual({ thermalMassEnabled: false, thermalMassThickness: 0 });
    expect(massLevelToDesignMass(null)).toEqual({ thermalMassEnabled: false, thermalMassThickness: 0 });
    expect(massLevelToDesignMass('extreme')).toEqual({ thermalMassEnabled: false, thermalMassThickness: 0 });
  });

  it('produces canonical SI payload values when applied design is simulated', () => {
    // Applying a "high" candidate must send the exact canonical thickness (0.20 m)
    // the optimizer evaluated — buildCanonicalSimulationPayload divides cm by 100.
    const applied = massLevelToDesignMass('high');
    const thicknessM = applied.thermalMassEnabled ? applied.thermalMassThickness / 100.0 : 0.0;
    expect(thicknessM).toBeCloseTo(0.2, 10);
    expect(applied.thermalMassEnabled).toBe(true);
  });
});

describe('candidate field mapping helpers', () => {
  it('maps optimizer orientation strings to canonical azimuth degrees', () => {
    expect(orientationToDegrees('north')).toBe(0);
    expect(orientationToDegrees('east')).toBe(90);
    expect(orientationToDegrees('south')).toBe(180);
    expect(orientationToDegrees('west')).toBe(270);
    expect(orientationToDegrees('south-facing')).toBe(180);
  });

  it('maps optimizer glazing keys to UI glazing options', () => {
    expect(glazingToUi('single_clear')).toBe('single');
    expect(glazingToUi('double_clear')).toBe('double');
    expect(glazingToUi('double_low_e')).toBe('double');
    expect(glazingToUi('triple_low_e')).toBe('triple');
  });
});

describe('weather provenance selector', () => {
  const profile = (
    overrides: Record<string, unknown>,
    climateOverrides: Record<string, unknown> = {},
  ): SimulationClimateProfile =>
    ({
      climate: { city: 'Test', data_provenance: 'model_analysis', ...climateOverrides },
      series: {
        latitude: 26.9,
        longitude: 70.9,
        timestamps: [],
        air_temperature_C: [30],
        solar_direct_W_m2: [0],
        solar_diffuse_W_m2: [0],
        data_mode: 'live',
        provenance: 'MODEL_ANALYSIS',
        provider: 'Test',
        retrieval_timestamp: '',
        period_start: '',
        period_end: '',
        fallback_used: false,
        ...overrides,
      },
      strategy: null,
    }) as unknown as SimulationClimateProfile;

  it('maps canonical provenance values through unchanged', () => {
    expect(activeWeatherProvenance(profile({}))).toBe('MODEL_ANALYSIS');
    expect(
      activeWeatherProvenance(
        profile({ data_mode: 'forecast', provenance: 'FORECAST' }, { data_provenance: 'forecast' })
      )
    ).toBe('FORECAST');
  });

  it('maps lowercase data_mode strings onto canonical provenance', () => {
    expect(
      activeWeatherProvenance(
        profile({ provenance: undefined, data_mode: 'historical' }, { data_provenance: undefined })
      )
    ).toBe('HISTORICAL_REANALYSIS');
    expect(
      activeWeatherProvenance(
        profile({ provenance: undefined, data_mode: 'fallback' }, { data_provenance: undefined })
      )
    ).toBe('FALLBACK');
    expect(
      activeWeatherProvenance(
        profile({ provenance: undefined, data_mode: 'design' }, { data_provenance: undefined })
      )
    ).toBe('DESIGN');
  });

  it('returns null when no profile exists (honest absence)', () => {
    expect(activeWeatherProvenance(null)).toBeNull();
  });
});
