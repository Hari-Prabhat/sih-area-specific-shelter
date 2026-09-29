/**
 * Product-hardening pass — rich report clipboard export tests.
 * Verifies the document structure Word/Google Docs should receive, the
 * honest-omission rule, and the exact footer/problem-statement wording.
 */
import { describe, expect, it } from 'vitest';
import { reportToHtml, reportToPlainText } from './reportExport';
import type { ReportInput } from './reportModel';

function makeReport(overrides: Partial<ReportInput> = {}): ReportInput {
  return {
    meta: { generatedAt: '2026-01-01T00:00:00Z', engine: 'Python 1D Forward Euler + ISO 6946', tool: 'ThermoShelter Design Studio' },
    site: { location: 'Leh, Ladakh', city: 'leh', latitude: 34.15, longitude: 77.58, elevationLabel: '3500 m', timezone: 'Asia/Kolkata' },
    climate: {
      provenance: { visible: true, provider: 'Open-Meteo', dataMode: 'live', provenance: 'MODEL_ANALYSIS', fallbackUsed: false, hours: 168, periodLabel: '7 days', retrievedLabel: '2026-01-01', coordinatesLabel: '34.15, 77.58', elevationLabel: '3500 m', timezone: 'Asia/Kolkata', locationLabel: 'Leh', notes: null },
      climateMode: 'EXTREME COLD',
      fallbackUsed: false,
      presetOnly: false,
      hours: 168,
    },
    mission: { occupants: 2, ach: 0.5, mobilityRequired: false, priorities: ['thermal_comfort'], comfortBounds: { min: 18, max: 24 } },
    design: {
      length: 6, width: 4, height: 3, shape: 'rectangular', orientationDeg: 180, roofPitchDeg: 0,
      wallThicknessM: 0.23, windowAreaM2: 3, doorAreaM2: 2, glazing: 'Double Glazed',
      insulationType: 'EPS', insulationThicknessCm: 5, thermalMassEnabled: false, thermalMassThicknessCm: 0,
      wallMaterialName: 'Brick', wallMaterialBackendId: 'brick', wallConductivity: 0.72, wallDensity: 1800, wallSpecificHeat: 900,
      openings: { south: { count: 2, areaEach: 1.05, width: 1.2, height: 0.875, areaTotal: 2.1, windows: [{ centerX: 0.3 }, { centerX: 0.7 }] }, north: { count: 1, areaEach: 0.9, width: 1.2, height: 0.75, areaTotal: 0.9, windows: [{ centerX: 0.5 }] }, door: { width: 0.9, height: 2.2, area: 2, facade: 'south' }, totalWindowCount: 3, totalWindowArea: 3 },
    },
    strategy: {
      model: { version: '1', climateMode: 'EXTREME COLD', primaryStrategy: 'Solar capture + high-performance envelope', secondaryStrategies: ['Thermal mass', 'Controlled openings'], solarCapture: 'MAXIMIZE', thermalMass: 'HIGH', insulationPriority: 'CRITICAL', ventilationStrategy: 'Minimal controlled', shadingStrategy: 'None', openingStrategy: 'Sealed', airlock: true, thermalBuffer: true },
      comparison: [],
    },
    simulation: null,
    optimization: null,
    limitations: { statements: ['Reduced-order model.'], geometrySupportedParameters: [], geometrySupportedOptimization: [], geometryNotImplemented: [] },
    ...overrides,
  } as ReportInput;
}

describe('reportToPlainText', () => {
  it('uses the exact required header and problem-statement wording', () => {
    const text = reportToPlainText(makeReport());
    expect(text).toContain('THERMOSHELTER AI');
    expect(text).toContain('AREA-SPECIFIC PASSIVE SHELTER ENGINEERING REPORT');
    expect(text).toContain('DRDO - Problem Statement');
    expect(text).toContain('SIH 2026 | SIH26051');
  });

  it('contains the always-present numbered sections', () => {
    const text = reportToPlainText(makeReport());
    for (const s of ['1. Executive Summary', '2. Site & Climate', '3. Shelter Requirements', '4. Shelter Geometry', '5. Envelope & Materials', '6. Passive Design Strategy', '10. Engineering Recommendations', '11. Limitations & Assumptions', '12. Data Provenance', '13. Conclusion']) {
      expect(text).toContain(s);
    }
  });

  it('contains data-dependent sections when their data exists', () => {
    const r = makeReport({
      simulation: {
        avgIndoorC: 20, minIndoorC: 18, maxIndoorC: 22, comfortPct: 90, comfortHours: 151,
        discomfortDegreeHours: 10, uValues: { wall_u: 0.4, roof_u: 0.5, floor_u: 0.8, window_u: 2.8, door_u: 1.8 }, componentLossesKwh: { wall_loss_kwh: 1, roof_loss_kwh: 1, floor_loss_kwh: 1, window_loss_kwh: 1, ventilation_loss_kwh: 1, radiation_loss_kwh: 0 },
        totalHeatLossKwh: 5, heatingDemandKwh: 5, coolingDemandKwh: 0, incidentSolarKwh: 10, usefulSolarKwh: 5,
        heatFlow: { data: [] } as never, solar: { data: [] } as never,
        hasThermalStorage: false, hasInternalGain: true, hasHourlyDemand: true,
      },
      optimization: {
        nTrials: 20, homeType: 'Permanent', objectiveDescription: 'Weighted scalar objective.',
        rankedDesigns: [], recommended: null, baseline: { hasBaseline: false, comfortPct: null, heatingDemandKwh: null, totalHeatLossKwh: null, solarGainKwh: null },
        scenarioProvenance: 'MODEL_ANALYSIS', scenarioFallbackUsed: false,
      },
    } as Partial<ReportInput> as ReportInput);
    const text = reportToPlainText(r);
    expect(text).toContain('7. Thermal Simulation');
    expect(text).toContain('8. Optimization');
  });

  it('omits the simulation section entirely when no simulation exists (honest omission)', () => {
    const text = reportToPlainText(makeReport());
    expect(text).not.toContain('Average indoor temperature');
    expect(text).toContain('No thermal simulation has been run');
  });

  it('renders real simulated values when a simulation exists', () => {
    const r = makeReport({
      simulation: {
        avgIndoorC: -5.9, minIndoorC: -9, maxIndoorC: -2, comfortPct: 4.2, comfortHours: 7,
        discomfortDegreeHours: 120, uValues: { wall_u: 0.4, roof_u: 0.5, floor_u: 0.8, window_u: 2.8, door_u: 1.8 },
        componentLossesKwh: { wall_loss_kwh: 100, roof_loss_kwh: 60, floor_loss_kwh: 40, window_loss_kwh: 30, door_loss_kwh: 10, ventilation_loss_kwh: 20, radiation_loss_kwh: 5 },
        totalHeatLossKwh: 265, heatingDemandKwh: 300, coolingDemandKwh: 0, incidentSolarKwh: 400, usefulSolarKwh: 132,
        heatFlow: { data: [] } as never, solar: { data: [] } as never,
        hasThermalStorage: false, hasInternalGain: true, hasHourlyDemand: true,
      },
    });
    const text = reportToPlainText(r);
    expect(text).toContain('-5.9 °C');
    expect(text).toContain('4%');
    expect(text).toContain('265 kWh');
  });

  it('labels fallback data explicitly and never as live', () => {
    const r = makeReport();
    r.climate.fallbackUsed = true;
    r.climate.provenance.fallbackUsed = true;
    const text = reportToPlainText(r);
    expect(text).toContain('FALLBACK');
    expect(text).toContain('not live');
  });
});

describe('reportToHtml', () => {
  it('produces document-editor structure (headings + tables), not JSON', () => {
    const html = reportToHtml(makeReport());
    expect(html).toContain('<h1');
    expect(html).toContain('<h2');
    expect(html).toContain('<table');
    expect(html).not.toContain('{');
  });

  it('escapes user-influenced location text', () => {
    const r = makeReport();
    r.site.location = 'Leh <b>&</b> Ladakh';
    const html = reportToHtml(r);
    expect(html).toContain('&lt;b&gt;');
  });
});
