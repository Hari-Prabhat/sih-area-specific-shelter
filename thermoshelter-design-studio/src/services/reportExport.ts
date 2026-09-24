/**
 * THERMOSHELTER — Rich report clipboard export (product-hardening pass)
 * =====================================================================
 * Converts the canonical ReportInput into document-editor-ready output:
 *  - text/html: headings, tables, bold labels — pastes into Word / Google
 *    Docs / LibreOffice as a structured engineering document.
 *  - text/plain: high-quality fallback with the same structure.
 * Every value comes from the canonical report model (services/reportModel.ts).
 * Nothing is fabricated: sections whose data is absent are omitted entirely.
 * Units stay standardized (°C, kWh, m², m³, W/m²K) and are never translated.
 */
import type { ReportInput } from './reportModel';

const H = {
  h1: (s: string) => `<h1 style="font-family:Arial,sans-serif;font-size:20pt;margin:0 0 4pt 0;">${esc(s)}</h1>`,
  h2: (s: string) => `<h2 style="font-family:Arial,sans-serif;font-size:14pt;margin:14pt 0 4pt 0;border-bottom:1px solid #94a3b8;padding-bottom:2pt;">${esc(s)}</h2>`,
  h3: (s: string) => `<h3 style="font-family:Arial,sans-serif;font-size:11pt;margin:10pt 0 3pt 0;">${esc(s)}</h3>`,
  p: (s: string) => `<p style="font-family:Arial,sans-serif;font-size:10pt;margin:3pt 0;">${s}</p>`,
  table: (rows: string[][]) =>
    `<table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:9.5pt;margin:4pt 0;" cellspace="0">` +
    rows
      .map(
        (r, i) =>
          `<tr>` +
          r.map(
            (c) =>
              `<td style="border:1px solid #cbd5e1;padding:3pt 8pt;${i === 0 ? 'font-weight:bold;background:#eef2f7;' : ''}">${esc(c)}</td>`,
          ).join('') +
          `</tr>`,
      )
      .join('') +
    `</table>`,
  note: (s: string) =>
    `<p style="font-family:Arial,sans-serif;font-size:8.5pt;color:#64748b;margin:4pt 0;">${esc(s)}</p>`,
};

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

interface DocBuilder {
  h1(s: string): void;
  h2(s: string): void;
  h3(s: string): void;
  p(s: string): void;
  table(rows: string[][]): void;
  note(s: string): void;
}

function buildHtml(r: ReportInput): string {
  const b: string[] = [];
  const doc: DocBuilder = {
    h1: (s) => b.push(H.h1(s)),
    h2: (s) => b.push(H.h2(s)),
    h3: (s) => b.push(H.h3(s)),
    p: (s) => b.push(H.p(s)),
    table: (rows) => b.push(H.table(rows)),
    note: (s) => b.push(H.note(s)),
  };
  buildDocument(r, doc, { bold: (s) => `<b>${esc(s)}</b>`, plain: (s) => esc(s) });
  return b.join('\n');
}

function buildPlain(r: ReportInput): string {
  const lines: string[] = [];
  const mkTable = (rows: string[][]) => {
    const w = Math.max(...rows.map((row) => row[0]?.length ?? 0));
    rows.forEach((row, i) => {
      lines.push(i === 0 ? row.join('  |  ') : `${(row[0] ?? '').padEnd(w)}  |  ${row.slice(1).join('  |  ')}`);
    });
  };
  const doc: DocBuilder = {
    h1: (s) => { lines.push('', s.toUpperCase(), '='.repeat(s.length)); },
    h2: (s) => { lines.push('', s, '-'.repeat(s.length)); },
    h3: (s) => { lines.push('', s); },
    p: (s) => lines.push(s),
    table: mkTable,
    note: (s) => lines.push(`(${s})`),
  };
  buildDocument(r, doc, { bold: (s) => s, plain: (s) => s });
  return lines.join('\n');
}

/** Shared section assembly — one source of truth for both formats. */
function buildDocument(
  r: ReportInput,
  d: DocBuilder,
  fmt: { bold: (s: string) => string; plain: (s: string) => string },
): void {
  const b = fmt.bold;
  const P = fmt.plain;
  const num = (v: number | null | undefined, unit = '', digits = 1): string =>
    typeof v === 'number' && Number.isFinite(v) ? `${v.toFixed(digits)}${unit}` : '—';

  d.h1('THERMOSHELTER AI');
  d.p(b('AREA-SPECIFIC PASSIVE SHELTER ENGINEERING REPORT'));
  d.p('DRDO - Problem Statement');
  d.p('SIH 2026 | SIH26051');
  d.note(`Generated ${r.meta.generatedAt} · ${r.meta.engine}`);

  // 1. Executive Summary
  d.h2('1. Executive Summary');
  d.p(
    `This report documents the simulated thermal evaluation of a ${r.design.length.toFixed(2)} m × ` +
    `${r.design.width.toFixed(2)} m × ${r.design.height.toFixed(2)} m ${r.design.shape} passive shelter for ` +
    `${r.site.location}. ` +
    (r.simulation
      ? `The authoritative Python thermal simulation predicts an average indoor temperature of ` +
        `${r.simulation.avgIndoorC.toFixed(1)} °C with ${r.simulation.comfortPct.toFixed(0)}% comfort hours ` +
        `over the simulation period.`
      : `No thermal simulation has been run for the current design; simulation sections are omitted.`)
  );

  // 2. Site & Climate
  d.h2('2. Site & Climate');
  d.table([
    ['Field', 'Value'],
    ['Requested location', r.site.location],
    ['Resolved city', r.site.city ?? '—'],
    ['Coordinates', r.site.latitude != null && r.site.longitude != null ? `${r.site.latitude.toFixed(3)}, ${r.site.longitude.toFixed(3)}` : '—'],
    ['Elevation', r.site.elevationLabel ?? '—'],
    ['Timezone', r.site.timezone ?? '—'],
    ['Climate mode', r.climate.climateMode ?? '—'],
    ['Data provenance', r.climate.provenance.provenance ?? r.climate.provenance.dataMode ?? '—'],
    ['Provider', r.climate.provenance.provider ?? '—'],
    ['Retrieved', r.climate.provenance.retrievedLabel ?? '—'],
    ['Simulation data window', r.climate.hours != null ? `${r.climate.hours} h` : '—'],
  ]);
  if (r.climate.fallbackUsed) {
    d.note('Provider fallback data was used. The dataset is not live weather and is labelled FALLBACK throughout.');
  }

  // 3. Shelter Requirements
  d.h2('3. Shelter Requirements');
  d.table([
    ['Field', 'Value'],
    ['Occupants', String(r.mission.occupants)],
    ['Air changes per hour', `${r.mission.ach.toFixed(1)} ACH`],
    ['Deployment type', r.mission.deploymentType ?? '—'],
    ['Duration', r.mission.durationMonths != null ? `${r.mission.durationMonths} months` : '—'],
    ['Mobility required', r.mission.mobilityRequired ? 'Yes' : 'No'],
    ['Priorities', r.mission.priorities.length > 0 ? r.mission.priorities.join(', ') : '—'],
    ['Comfort band', `${r.mission.comfortBounds.min} °C – ${r.mission.comfortBounds.max} °C`],
  ]);

  // 4. Shelter Geometry
  d.h2('4. Shelter Geometry');
  d.table([
    ['Field', 'Value'],
    ['Shape', r.design.shape],
    ['Length', `${r.design.length.toFixed(2)} m`],
    ['Width', `${r.design.width.toFixed(2)} m`],
    ['Clear height', `${r.design.height.toFixed(2)} m`],
    ['Floor area (L × W footprint)', `${(r.design.length * r.design.width).toFixed(1)} m²`],
    ['Orientation', `${r.design.orientationDeg}° azimuth`],
    ['Roof pitch', `${r.design.roofPitchDeg.toFixed(0)}°`],
  ]);

  // 5. Envelope & Materials
  d.h2('5. Envelope & Materials');
  d.table([
    ['Component', 'Specification'],
    ['Wall material', `${r.design.wallMaterialName}${r.design.wallConductivity != null ? ` (k = ${r.design.wallConductivity.toFixed(3)} W/m²K)` : ''}`],
    ['Wall thickness', `${(r.design.wallThicknessM * 100).toFixed(1)} cm`],
    ['Insulation', r.design.insulationType === 'None' ? 'None' : `${r.design.insulationType} — ${r.design.insulationThicknessCm.toFixed(1)} cm`],
    ['Glazing', r.design.glazing],
    ['Window area', `${r.design.windowAreaM2.toFixed(1)} m²`],
    ['Door area', `${r.design.doorAreaM2.toFixed(1)} m²`],
    ['Thermal mass', r.design.thermalMassEnabled ? `Enabled — ${r.design.thermalMassThicknessCm.toFixed(1)} cm` : 'Disabled'],
  ]);
  if (r.design.openings?.south?.count || r.design.openings?.door) {
    d.h3('Openings (deterministic shared layout)');
    const rows: string[][] = [['Type', 'Size / Count', 'Facade']];
    if (r.design.openings.south.count > 0) {
      rows.push([
        'Windows (south)',
        `${r.design.openings.south.count} × ${r.design.openings.south.width.toFixed(2)} × ${r.design.openings.south.height.toFixed(2)} m`,
        'south',
      ]);
    }
    if (r.design.openings.north.count > 0) {
      rows.push([
        'Windows (north)',
        `${r.design.openings.north.count} × ${r.design.openings.north.width.toFixed(2)} × ${r.design.openings.north.height.toFixed(2)} m`,
        'north',
      ]);
    }
    if (r.design.openings.door) {
      rows.push(['Door', `${r.design.openings.door.width.toFixed(2)} × ${r.design.openings.door.height.toFixed(2)} m`, r.design.openings.door.facade]);
    }
    d.table(rows);
  }

  // 6. Passive Design Strategy
  if (r.strategy) {
    d.h2('6. Passive Design Strategy');
    d.p(b(`Climate mode: ${r.strategy.model.climateMode ?? '—'}`));
    d.p(b(`Primary strategy: ${r.strategy.model.primaryStrategy ?? '—'}`));
    if (r.strategy.model.secondaryStrategies.length > 0) {
      d.p(`${b('Supporting strategies:')} ${r.strategy.model.secondaryStrategies.join(', ')}`);
    }
    if (r.strategy.model.ventilationStrategy) {
      d.p(`${b('Ventilation:')} ${r.strategy.model.ventilationStrategy}`);
    }
    if (r.strategy.model.shadingStrategy) {
      d.p(`${b('Shading:')} ${r.strategy.model.shadingStrategy}`);
    }
  }

  // 7. Thermal Simulation
  if (r.simulation) {
    const s = r.simulation;
    d.h2('7. Thermal Simulation');
    d.note('Predicted values from the Python reduced-order thermal model (1D Forward Euler, ISO 6946 U-values). Not measured data.');
    d.table([
      ['Metric', 'Value'],
      ['Average indoor temperature', `${s.avgIndoorC.toFixed(1)} °C`],
      ['Minimum indoor temperature', `${s.minIndoorC.toFixed(1)} °C`],
      ['Maximum indoor temperature', `${s.maxIndoorC.toFixed(1)} °C`],
      ['Comfort hours', `${Math.round(s.comfortHours)} h (${s.comfortPct.toFixed(0)}%)`],
      ['Discomfort degree-hours', `${Math.round(s.discomfortDegreeHours)} °C·h`],
      ['Total heat loss', `${Math.round(s.totalHeatLossKwh)} kWh`],
      ['Incident solar energy', `${Math.round(s.incidentSolarKwh)} kWh`],
      ['Useful solar energy', `${Math.round(s.usefulSolarKwh)} kWh`],
      ['Heating demand', `${Math.round(s.heatingDemandKwh)} kWh`],
      ['Cooling demand', `${Math.round(s.coolingDemandKwh)} kWh`],
    ]);
    d.h3('Envelope U-values');
    d.table([
      ['Assembly', 'U-value (W/m²K)'],
      ['Wall', num(s.uValues.wall_u ?? null, '', 3)],
      ['Roof', num(s.uValues.roof_u ?? null, '', 3)],
      ['Floor', num(s.uValues.floor_u ?? null, '', 3)],
      ['Window', num(s.uValues.window_u ?? null, '', 3)],
      ['Door', num(s.uValues.door_u ?? null, '', 3)],
    ]);
    d.h3('Component heat losses');
    d.table([
      ['Component', 'Loss (kWh)'],
      ['Walls', num(s.componentLossesKwh.wall_loss_kwh, '', 1)],
      ['Roof', num(s.componentLossesKwh.roof_loss_kwh, '', 1)],
      ['Floor', num(s.componentLossesKwh.floor_loss_kwh, '', 1)],
      ['Windows', num(s.componentLossesKwh.window_loss_kwh, '', 1)],
      ['Doors', num(s.componentLossesKwh.door_loss_kwh ?? null, '', 1)],
      ['Ventilation', num(s.componentLossesKwh.ventilation_loss_kwh ?? null, '', 1)],
    ]);
  }

  // 8. Optimization
  if (r.optimization) {
    const o = r.optimization;
    d.h2('8. Optimization');
    d.p(o.objectiveDescription);
    d.note(`Weighted scalar multi-objective score (not Pareto optimization). ${o.nTrials} Optuna TPE trials.`);
    if (o.scenarioProvenance) {
      d.p(`${b('Climate scenario provenance:')} ${o.scenarioProvenance}${o.scenarioFallbackUsed ? ' (fallback dataset)' : ''}`);
    }
    const candTable = (title: string, c: CanonicalCandidate | null): void => {
      if (!c) return;
      d.h3(title);
      d.table([
        ['Parameter', 'Value'],
        ['Comfort hours', `${Math.round(c.comfort_hours)} h (${c.comfort_percentage.toFixed(0)}%)`],
        ['Geometry', c.length_m != null && c.width_m != null && c.height_m != null ? `${c.length_m.toFixed(1)} × ${c.width_m.toFixed(1)} × ${c.height_m.toFixed(1)} m` : 'Base design geometry'],
        ['Orientation', c.orientation],
        ['Insulation', `${c.insulation_mm.toFixed(0)} mm`],
        ['Wall material', c.wall_material_name],
        ['Glazing', c.glazing_name],
        ['Window area', `${c.window_area_m2.toFixed(1)} m²`],
        ['Thermal mass', c.thermal_mass_level ?? '—'],
        ['Heat loss', `${Math.round(c.total_heat_loss_kwh)} kWh`],
        ['Useful solar', `${Math.round(c.solar_gain_kwh)} kWh`],
        ['Objective score', `${c.overall_score.toFixed(1)} / 100`],
      ]);
    };
    d.h3('8.1 Your Design — User-Constrained');
    if (o.rankedDesigns.length > 0) {
      candTable('Best ranked candidate', o.rankedDesigns[0]);
      if (o.rankedDesigns.length > 1) {
        d.p(`${b('Other ranked candidates:')} ${o.rankedDesigns.slice(1).map((c) => `#${c.rank} (${Math.round(c.comfort_percentage)}% comfort)`).join(', ')}`);
      }
    } else {
      d.p('No ranked candidates available.');
    }
    d.h3('8.2 ThermoShelter Recommended Design — Comfort First');
    candTable('Comfort-first recommendation', o.recommended);
    if (!o.recommended) {
      d.p('No comfort-feasible design was found within the current prototype optimization bounds.');
    }
  }

  // 9. Design Comparison
  if (r.optimization?.recommended && r.optimization?.baseline) {
    d.h2('9. Design Comparison');
    const base = r.optimization.baseline;
    d.table([
      ['Metric', 'Baseline (current design)', 'Recommended'],
      ['Comfort %', base.comfortPct != null ? `${base.comfortPct.toFixed(0)}%` : '—', `${r.optimization.recommended.comfort_percentage.toFixed(0)}%`],
      ['Heat loss', base.totalHeatLossKwh != null ? `${Math.round(base.totalHeatLossKwh)} kWh` : '—', `${Math.round(r.optimization.recommended.total_heat_loss_kwh)} kWh`],
    ]);
  }

  // 10. Engineering Recommendations
  d.h2('10. Engineering Recommendations');
  if (r.optimization?.recommended) {
    d.p('The comfort-first recommendation section (8.2) identifies the configuration with the highest simulated comfort found within the prototype search space; parameter-level rationale is derived from the actual differences shown there.');
  } else if (r.simulation) {
    d.p('Run the design optimization to obtain configuration recommendations derived from simulated performance.');
  } else {
    d.p('Run the thermal simulation and optimization stages to generate engineering recommendations.');
  }

  // 11. Limitations & Assumptions
  d.h2('11. Limitations & Assumptions');
  r.limitations.statements.forEach((s) => d.p(`• ${s}`));

  // 12. Data Provenance
  d.h2('12. Data Provenance');
  d.p(`${b('Weather data mode:')} ${r.climate.provenance.dataMode ?? r.climate.provenance.provenance ?? '—'}`);
  if (r.climate.presetOnly) {
    d.p('This report uses bundled design-preset climate data only; no live weather profile was fetched.');
  }
  d.p(`${b('Simulation engine:')} ${r.meta.engine}`);
  d.note(r.climate.fallbackUsed ? 'Fallback status: active — data is not live and is labelled FALLBACK.' : 'Fallback status: not active.');

  // 13. Conclusion
  d.h2('13. Conclusion');
  d.p(
    r.simulation
      ? `The documented ${r.design.shape} shelter configuration achieved ${r.simulation.comfortPct.toFixed(0)}% simulated comfort hours in the evaluated climate window. All values are model-derived predictions from the reduced-order thermal engine and require detailed engineering validation before construction.`
      : 'Thermal simulation has not been run for the current design; conclusions await simulated results.'
  );
  d.note('This report contains simulated/model-derived values only. ANSYS/CFD validation is not currently integrated.');
}

/** Minimal structural type for candidates (avoids importing api.ts here). */
interface CanonicalCandidate {
  rank: number;
  comfort_hours: number;
  comfort_percentage: number;
  insulation_mm: number;
  wall_material_name: string;
  glazing_name: string;
  orientation: string;
  window_area_m2: number;
  thermal_mass_level?: string | null;
  total_heat_loss_kwh: number;
  solar_gain_kwh: number;
  overall_score: number;
  length_m?: number | null;
  width_m?: number | null;
  height_m?: number | null;
}

/** HTML output for the rich clipboard entry. */
export function reportToHtml(r: ReportInput): string {
  return buildHtml(r);
}

/** High-quality plain-text fallback. */
export function reportToPlainText(r: ReportInput): string {
  return buildPlain(r);
}

/** Writes both flavors to the clipboard where supported; falls back to plain text. */
export async function copyReportToClipboard(r: ReportInput): Promise<boolean> {
  const html = reportToHtml(r);
  const text = reportToPlainText(r);
  try {
    if (typeof ClipboardItem !== 'undefined' && navigator.clipboard?.write) {
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/html': new Blob([html], { type: 'text/html' }),
          'text/plain': new Blob([text], { type: 'text/plain' }),
        }),
      ]);
      return true;
    }
  } catch {
    /* fall through to plain text */
  }
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
