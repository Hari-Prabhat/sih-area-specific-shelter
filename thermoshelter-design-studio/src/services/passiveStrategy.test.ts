/**
 * Passive-strategy mapper tests (D4-B WP3/WP7) — Vitest
 * =====================================================
 * The backend strategy DTO must map honestly: all 6 canonical climate modes,
 * null/malformed DTOs map to null/empties (never fabricated), comparison
 * pairs reflect real design state, and NOTHING mutates the design.
 */

import { describe, expect, it } from 'vitest';

import {
  CLIMATE_MODES,
  NOT_REPRESENTED,
  buildStrategyComparison,
  mapStrategyDto,
} from './passiveStrategy';
import { ShelterDesign } from '../types';

/** A canonical full DTO as produced by backend/climate/climate_strategy.py. */
const fullDto = {
  version: '1.0.0',
  climate_mode: 'EXTREME COLD',
  primary_strategy: 'Solar heat capture + envelope thermal protection',
  secondary_strategies: ['High thermal mass storage for nocturnal heat release'],
  solar_capture: 'HIGH',
  thermal_mass: 'HIGH',
  insulation_priority: 'HIGH',
  ventilation_strategy: 'CONTROLLED_MINIMAL_PREHEATED',
  shading_strategy: 'MINIMAL_WINTER_EXPOSURE',
  opening_strategy: 'MINIMIZED_HIGH_PERFORMANCE_SOLAR_BIAS',
  airlock: true,
  thermal_buffer: true,
  explanation: 'The climate profile indicates extreme sub-zero conditions…',
  rules_triggered: ['R_EC_01: Winter design sub-zero severe hypothermia mitigation'],
};

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
  insulationType: 'EPS',
  insulationThickness: 5,
  ach: 0.5,
  thermalMassEnabled: true,
  thermalMassThickness: 20,
};

describe('mapStrategyDto — climate modes (WP7: all 6 canonical modes)', () => {
  for (const mode of CLIMATE_MODES) {
    it(`maps ${mode} as the authoritative classification`, () => {
      const m = mapStrategyDto({ ...fullDto, climate_mode: mode });
      expect(m).not.toBeNull();
      expect(m!.climateMode).toBe(mode);
    });
  }

  it('maps an unknown climate mode to null instead of displaying it as fact', () => {
    const m = mapStrategyDto({ ...fullDto, climate_mode: 'TROPICAL PARADISE' });
    expect(m!.climateMode).toBeNull();
  });
});

describe('mapStrategyDto — honest failure modes', () => {
  it('returns null for null strategy (backend derive failure)', () => {
    expect(mapStrategyDto(null)).toBeNull();
  });

  it('returns null for undefined and non-object DTOs', () => {
    expect(mapStrategyDto(undefined)).toBeNull();
    expect(mapStrategyDto('EXTREME COLD')).toBeNull();
    expect(mapStrategyDto(42)).toBeNull();
    expect(mapStrategyDto([fullDto])).toBeNull();
  });

  it('maps an empty object to an all-null model without inventing defaults', () => {
    const m = mapStrategyDto({});
    expect(m).not.toBeNull();
    expect(m!.climateMode).toBeNull();
    expect(m!.primaryStrategy).toBeNull();
    expect(m!.secondaryStrategies).toEqual([]);
    expect(m!.solarCapture).toBeNull();
    expect(m!.thermalMass).toBeNull();
    expect(m!.insulationPriority).toBeNull();
    expect(m!.ventilationStrategy).toBeNull();
    expect(m!.shadingStrategy).toBeNull();
    expect(m!.openingStrategy).toBeNull();
    expect(m!.airlock).toBeNull();
    expect(m!.thermalBuffer).toBeNull();
    expect(m!.explanation).toBeNull();
    expect(m!.rulesTriggered).toEqual([]);
  });

  it('rejects malformed field types (priority/boolean/string)', () => {
    const m = mapStrategyDto({
      solar_capture: 5,
      thermal_mass: null,
      airlock: 'yes',
      rules_triggered: 'R_EC_01',
      secondary_strategies: [1, 'valid strategy', null],
    });
    expect(m!.solarCapture).toBeNull();
    expect(m!.thermalMass).toBeNull();
    expect(m!.airlock).toBeNull();
    expect(m!.rulesTriggered).toEqual([]);
    expect(m!.secondaryStrategies).toEqual(['valid strategy']);
  });

  it('drops empty-string fields to null', () => {
    const m = mapStrategyDto({ ...fullDto, primary_strategy: '   ', version: '' });
    expect(m!.primaryStrategy).toBeNull();
    expect(m!.version).toBeNull();
  });
});

describe('buildStrategyComparison — recommendation vs current design', () => {
  it('builds pairs from real design state', () => {
    const m = mapStrategyDto(fullDto)!;
    const pairs = buildStrategyComparison(m, baseDesign);
    const byConcept = Object.fromEntries(pairs.map((p) => [p.concept, p]));

    expect(byConcept['Thermal mass']).toMatchObject({
      recommendation: 'Prioritize thermal mass storage (HIGH)',
      current: 'Enabled — 20 cm floor-core mass',
      represented: true,
    });
    expect(byConcept['Envelope insulation']).toMatchObject({
      current: 'EPS — 5 cm',
      represented: true,
    });
    expect(byConcept['Solar capture']).toMatchObject({
      current: 'Orientation 180° · double glazing · 3 m² glazing',
      represented: true,
    });
    expect(byConcept['Ventilation']).toMatchObject({
      recommendation: 'CONTROLLED_MINIMAL_PREHEATED',
      current: '0.5 air changes per hour',
      represented: true,
    });
    expect(byConcept['Entrance airlock']).toMatchObject({
      recommendation: 'Required',
      represented: false,
    });
    expect(byConcept['Solar shading']).toMatchObject({
      current: NOT_REPRESENTED,
      represented: false,
    });
  });

  it('reflects a changed design (disabled mass, uninsulated, single glazing, high ACH)', () => {
    const m = mapStrategyDto(fullDto)!;
    const design: ShelterDesign = {
      ...baseDesign,
      thermalMassEnabled: false,
      thermalMassThickness: 0,
      insulationType: 'None',
      insulationThickness: 0,
      windowGlazing: 'single',
      ach: 3,
    };
    const byConcept = Object.fromEntries(
      buildStrategyComparison(m, design).map((p) => [p.concept, p]),
    );
    expect(byConcept['Thermal mass'].current).toBe('Disabled');
    expect(byConcept['Envelope insulation'].current).toBe('None');
    expect(byConcept['Solar capture'].current).toContain('single glazing');
    expect(byConcept['Ventilation'].current).toBe('3 air changes per hour');
  });

  it('renders MINIMIZED and MODERATE recommendations distinctly', () => {
    const m = mapStrategyDto({ ...fullDto, solar_capture: 'MINIMIZED', insulation_priority: 'MODERATE' })!;
    const pairs = buildStrategyComparison(m, baseDesign);
    const byConcept = Object.fromEntries(pairs.map((p) => [p.concept, p]));
    expect(byConcept['Solar capture'].recommendation).toBe('Minimize solar heat capture (MINIMIZED)');
    expect(byConcept['Envelope insulation'].recommendation).toBe('Moderate envelope insulation (MODERATE)');
  });

  it('shows "—" (null recommendation) when the backend omitted a field', () => {
    const m = mapStrategyDto({ ...fullDto, ventilation_strategy: undefined, airlock: undefined })!;
    const byConcept = Object.fromEntries(
      buildStrategyComparison(m, baseDesign).map((p) => [p.concept, p]),
    );
    expect(byConcept['Ventilation'].recommendation).toBeNull();
    expect(byConcept['Entrance airlock'].recommendation).toBeNull();
  });
});

describe('no mutation guarantees (WP7: strategy never mutates design)', () => {
  it('mapStrategyDto and buildStrategyComparison never mutate their inputs', () => {
    const dto = { ...fullDto, secondary_strategies: ['keep me'] };
    const dtoSnapshot = JSON.parse(JSON.stringify(dto));
    const designSnapshot = JSON.parse(JSON.stringify(baseDesign));

    const m = mapStrategyDto(dto)!;
    buildStrategyComparison(m, baseDesign);

    expect(dto).toEqual(dtoSnapshot);
    expect(baseDesign).toEqual(designSnapshot);
  });
});
