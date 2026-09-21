/**
 * Studio store unit tests (D2) — Vitest
 * =====================================
 * Verifies the shared-state architecture's engineering-critical behavior
 * WITHOUT thermal math: the candidate → ShelterDesign thermal-mass
 * preservation contract (mirroring services/optimize.py THERMAL_MASS_LEVELS)
 * and the provenance selector mapping.
 */

import { describe, expect, it } from 'vitest';

import {
  massLevelToDesignMass,
  orientationToDegrees,
  glazingToUi,
  candidateDesignPatch,
  PROTOTYPE_GEOMETRY_BOUNDS,
} from './useStudioState';
import { activeWeatherProvenance } from './useStudioState';
import type { CanonicalOptimizationCandidate, SimulationClimateProfile } from '../services/api';
import type { ShelterDesign } from '../types';

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

describe('D4-A WP2: candidate → design insulation-thickness restoration', () => {
  const baseDesign: ShelterDesign = {
    length: 6,
    width: 4,
    height: 3,
    shape: 'rectangular',
    orientation: 180,
    roofAngle: 30,
    wallThickness: 0.3,
    windowArea: 3,
    windowGlazing: 'double',
    doorArea: 2,
    insulationType: 'XPS',
    insulationThickness: 4,
    ach: 0.5,
    thermalMassEnabled: true,
    thermalMassThickness: 10,
  };

  const candidate = (overrides: Partial<CanonicalOptimizationCandidate>): CanonicalOptimizationCandidate =>
    ({
      rank: 1,
      label: 'Test Candidate',
      rationale: 'test',
      overall_score: 0.8,
      sub_scores: { comfort: 0.8, efficiency: 0.7, solar: 0.6 },
      insulation_mm: 120,
      insulation_thickness_m: 0.12,
      window_area_m2: 5.5,
      wall_material: 'mud',
      wall_material_name: 'Rammed Earth (Stabilized)',
      glazing: 'triple_low_e',
      glazing_name: 'Triple Glazed Low-E',
      orientation: 'south',
      comfort_hours: 100,
      comfort_percentage: 80,
      discomfort_dh: 20,
      total_heat_loss_kwh: 100,
      solar_gain_kwh: 50,
      u_values: { wall_u: 0.2, roof_u: 0.3, floor_u: 0.4, window_u: 0.8 },
      heating_demand_kwh: 40,
      cooling_demand_kwh: 0,
      total_conditioning_demand_kwh: 40,
      effective_thermal_capacity_j_k: 2.5e7,
      thermal_mass_level: 'high',
      ...overrides,
    }) as CanonicalOptimizationCandidate;

  it('restores the candidate insulation thickness (mm → cm) on apply', () => {
    const patch = candidateDesignPatch(baseDesign, candidate({}));
    expect(patch.insulationThickness).toBe(12);
  });

  it('keeps an uninsulated candidate uninsulated and zeroes the thickness', () => {
    const patch = candidateDesignPatch(baseDesign, candidate({ insulation_thickness_m: 0, insulation_mm: 0 }));
    expect(patch.insulationType).toBe('None');
    expect(patch.insulationThickness).toBe(0);
  });

  it('selects a real insulation product when the previous design had none', () => {
    const patch = candidateDesignPatch(
      { ...baseDesign, insulationType: 'None' },
      candidate({}),
    );
    expect(patch.insulationType).toBe('EPS');
  });

  it('round-trips the applied design back into the canonical SI payload', () => {
    // Applied design must reproduce the candidate's envelope semantics —
    // the same 0.12 m thickness the optimizer evaluated.
    const patch = candidateDesignPatch(baseDesign, candidate({}));
    const applied: ShelterDesign = { ...baseDesign, ...patch };
    const thicknessM =
      applied.insulationType !== 'None' && applied.insulationThickness > 0
        ? applied.insulationThickness / 100.0
        : 0.0;
    expect(thicknessM).toBeCloseTo(0.12, 10);
    expect(applied.windowArea).toBeCloseTo(5.5, 10);
    expect(applied.orientation).toBe(180);
  });

  it('preserves thermal-mass restoration through the shared patch', () => {
    const patch = candidateDesignPatch(baseDesign, candidate({ thermal_mass_level: 'medium' }));
    expect(patch.thermalMassEnabled).toBe(true);
    expect(patch.thermalMassThickness).toBe(10);
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

describe('D5-A: candidate geometry carry-through', () => {
  const baseDesign: ShelterDesign = {
    length: 6,
    width: 4,
    height: 3,
    shape: 'rectangular',
    orientation: 180,
    roofAngle: 30,
    wallThickness: 0.3,
    windowArea: 3,
    windowGlazing: 'double',
    doorArea: 2,
    insulationType: 'XPS',
    insulationThickness: 8,
    ach: 0.5,
    thermalMassEnabled: false,
    thermalMassThickness: 0,
  };

  const candidate = (overrides: Partial<CanonicalOptimizationCandidate>): CanonicalOptimizationCandidate =>
    ({
      rank: 1,
      label: 'Geometry Candidate',
      rationale: 'test',
      overall_score: 0.8,
      sub_scores: { comfort: 0.8, efficiency: 0.7, solar: 0.6 },
      insulation_mm: 80,
      insulation_thickness_m: 0.08,
      window_area_m2: 4.0,
      wall_material: 'brick',
      wall_material_name: 'Brick',
      glazing: 'double_clear',
      glazing_name: 'Double Glazed',
      orientation: 'south',
      comfort_hours: 90,
      comfort_percentage: 53.6,
      discomfort_dh: 700,
      total_heat_loss_kwh: 80,
      solar_gain_kwh: 30,
      u_values: { wall_u: 0.35, roof_u: 0.3, floor_u: 0.4, window_u: 2.8 },
      heating_demand_kwh: 40,
      cooling_demand_kwh: 0,
      total_conditioning_demand_kwh: 40,
      effective_thermal_capacity_j_k: 1.5e7,
      thermal_mass_level: 'medium',
      ...overrides,
    }) as CanonicalOptimizationCandidate;

  it('carries candidate geometry into the design patch when present', () => {
    const patch = candidateDesignPatch(
      baseDesign,
      candidate({ length_m: 5.2, width_m: 3.4, height_m: 2.6 })
    );
    expect(patch.length).toBe(5.2);
    expect(patch.width).toBe(3.4);
    expect(patch.height).toBe(2.6);
  });

  it('does NOT touch design dimensions for legacy candidates without geometry', () => {
    const patch = candidateDesignPatch(baseDesign, candidate({ length_m: null }));
    expect(patch.length).toBeUndefined();
    expect(patch.width).toBeUndefined();
    expect(patch.height).toBeUndefined();
  });

  it('preserves all existing candidate fields alongside geometry carry', () => {
    const patch = candidateDesignPatch(
      baseDesign,
      candidate({ length_m: 5.0, width_m: 3.0, height_m: 2.5, insulation_thickness_m: 0.1 })
    );
    expect(patch.windowArea).toBe(4.0);
    expect(patch.insulationThickness).toBe(10);
    expect(patch.thermalMassEnabled).toBe(true);
    expect(patch.thermalMassThickness).toBe(10);
  });

  it('D5-B: applied design equals the candidate geometry end-to-end', () => {
    // The D5-B fidelity contract, mirrored frontend-side: composing the
    // candidate patch onto the design yields the candidate's exact geometry
    // (what the next simulation payload, Blueprint, 3D and Report will show).
    const geom = { length_m: 8.3, width_m: 3.0, height_m: 4.0 };
    const patch = candidateDesignPatch(baseDesign, candidate(geom));
    const applied: ShelterDesign = { ...baseDesign, ...patch };
    expect(applied.length).toBe(8.3);
    expect(applied.width).toBe(3.0);
    expect(applied.height).toBe(4.0);
  });
});

describe('prototype geometry bounds (Batch 1-A)', () => {
  it('exposes exactly the approved D5-B prototype bounds', () => {
    // These are the approved PROPOSED PROTOTYPE OPTIMIZATION BOUNDS — the UI
    // presents them read-only and the store sends them only when geometry
    // search is explicitly enabled. Changing them requires re-approval.
    expect(PROTOTYPE_GEOMETRY_BOUNDS).toEqual({
      min_length_m: 4.0,
      max_length_m: 10.0,
      min_width_m: 3.0,
      max_width_m: 6.0,
      min_height_m: 2.4,
      max_height_m: 4.0,
      max_aspect_ratio: 3.0,
    });
    // Every bound is finite and positive; min <= max per dimension.
    for (const [k, v] of Object.entries(PROTOTYPE_GEOMETRY_BOUNDS)) {
      expect(Number.isFinite(v), k).toBe(true);
      expect(v).toBeGreaterThan(0);
    }
    expect(PROTOTYPE_GEOMETRY_BOUNDS.min_length_m).toBeLessThanOrEqual(PROTOTYPE_GEOMETRY_BOUNDS.max_length_m);
    expect(PROTOTYPE_GEOMETRY_BOUNDS.min_width_m).toBeLessThanOrEqual(PROTOTYPE_GEOMETRY_BOUNDS.max_width_m);
    expect(PROTOTYPE_GEOMETRY_BOUNDS.min_height_m).toBeLessThanOrEqual(PROTOTYPE_GEOMETRY_BOUNDS.max_height_m);
  });
});
