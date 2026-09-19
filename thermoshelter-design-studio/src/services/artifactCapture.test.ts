/**
 * THERMOSHELTER — Artifact capture tests (D4-D3)
 * ==============================================
 * Verifies Blueprint SVG serialization and 3D canvas null-safety against a
 * synthetic DOM, plus the protected 3D Canvas configuration
 * (preserveDrawingBuffer) and the D4-C capture hooks via source contracts.
 */
import { describe, expect, it } from 'vitest';
// Node fs is available in the Vitest runtime; the browser bundle never imports
// this test file. The frontend tsconfig has no node types, hence the suppress.
// @ts-expect-error -- node:fs is not typed in the frontend tsconfig
import { readFileSync } from 'node:fs';
import {
  BLUEPRINT_SVG_SELECTOR,
  TWIN_ROOT_SELECTOR,
  captureBlueprintSvgs,
  captureTwinPng,
} from './artifactCapture';

// ---------------------------------------------------------------------------
// Minimal synthetic DOM — no jsdom dependency needed for these code paths.
// ---------------------------------------------------------------------------

function makeSvgEl(view: string, inner: string): unknown {
  // Attribute list mirroring the minimal DOM Attribute interface — the
  // non-browser serializer fallback reads el.attributes.
  const attributes: Array<{ name: string; value: string }> = [
    { name: 'data-blueprint-svg', value: '' },
    { name: 'data-blueprint-view', value: view },
  ];
  const el = {
    getAttribute: (name: string) => attributes.find((a) => a.name === name)?.value ?? null,
    setAttribute: (name: string, value: string) => {
      const existing = attributes.find((a) => a.name === name);
      if (existing) existing.value = value;
      else attributes.push({ name, value });
    },
    get attributes() {
      return attributes;
    },
    innerHTML: inner,
    cloneNode: () => makeSvgEl(view, inner),
  };
  return el;
}

function makeRootWithSvg(view: string, inner: string) {
  const svg = makeSvgEl(view, inner);
  return {
    querySelectorAll: (sel: string) => (sel === BLUEPRINT_SVG_SELECTOR ? [svg] : []),
    querySelector: (sel: string) => (sel === TWIN_ROOT_SELECTOR ? null : null),
  };
}

describe('captureBlueprintSvgs', () => {
  it('serializes a marked Blueprint SVG with xmlns added', () => {
    const root = makeRootWithSvg('plan', '<g><rect width="10" height="10"/></g>');
    const artifacts = captureBlueprintSvgs(root as unknown as ParentNode);
    expect(artifacts).toHaveLength(1);
    expect(artifacts[0].view).toBe('plan');
    expect(artifacts[0].svg).toContain('<svg');
    expect(artifacts[0].svg).toContain('xmlns="http://www.w3.org/2000/svg"');
    expect(artifacts[0].svg).toContain('data-blueprint-view="plan"');
    expect(artifacts[0].svg).toContain('<g><rect width="10" height="10"/></g>');
  });

  it('reads the view id from the capture hook', () => {
    const root = makeRootWithSvg('elevation', '<g/>');
    const artifacts = captureBlueprintSvgs(root as unknown as ParentNode);
    expect(artifacts[0].view).toBe('elevation');
  });

  it('returns an empty list when no Blueprint SVG exists (honest absence)', () => {
    const empty = { querySelectorAll: () => [], querySelector: () => null };
    expect(captureBlueprintSvgs(empty as unknown as ParentNode)).toEqual([]);
  });
});

describe('captureTwinPng', () => {
  it('returns null when no twin root exists', () => {
    const empty = { querySelectorAll: () => [], querySelector: () => null };
    expect(captureTwinPng(empty as unknown as ParentNode)).toBeNull();
  });

  it('returns null when the container has no canvas', () => {
    const root = {
      querySelectorAll: () => [],
      querySelector: (sel: string) =>
        sel === TWIN_ROOT_SELECTOR ? { querySelector: () => null } : null,
    };
    expect(captureTwinPng(root as unknown as ParentNode)).toBeNull();
  });

  it('returns null when toDataURL throws (framebuffer unavailable)', () => {
    const root = {
      querySelectorAll: () => [],
      querySelector: (sel: string) =>
        sel === TWIN_ROOT_SELECTOR
          ? {
              querySelector: () => ({
                width: 800,
                height: 600,
                toDataURL: () => {
                  throw new Error('readback blocked');
                },
              }),
            }
          : null,
    };
    expect(captureTwinPng(root as unknown as ParentNode)).toBeNull();
  });

  it('returns null for a zero-size canvas (no meaningful frame)', () => {
    const root = {
      querySelectorAll: () => [],
      querySelector: (sel: string) =>
        sel === TWIN_ROOT_SELECTOR
          ? {
              querySelector: () => ({
                width: 0,
                height: 0,
                toDataURL: () => 'data:image/png;base64,AAAA',
              }),
            }
          : null,
    };
    expect(captureTwinPng(root as unknown as ParentNode)).toBeNull();
  });

  it('returns the PNG data URL when capture succeeds', () => {
    const root = {
      querySelectorAll: () => [],
      querySelector: (sel: string) =>
        sel === TWIN_ROOT_SELECTOR
          ? {
              querySelector: () => ({
                width: 800,
                height: 600,
                toDataURL: () => 'data:image/png;base64,AAAA',
              }),
            }
          : null,
    };
    expect(captureTwinPng(root as unknown as ParentNode)).toBe('data:image/png;base64,AAAA');
  });
});

// ---------------------------------------------------------------------------
// Source contracts — protected components keep their capture hooks/config.
// ---------------------------------------------------------------------------

describe('source contracts', () => {
  it('ShelterModel3D keeps preserveDrawingBuffer and the twin-root hook', async () => {
    const src = (await import('../components/ShelterModel3D.tsx?raw')).default;
    expect(src).toContain('preserveDrawingBuffer: true');
    expect(src).toContain('data-twin-root');
  });

  it('EngineeringBlueprint keeps the three drawing-view capture hooks', async () => {
    const src = (await import('../components/EngineeringBlueprint.tsx?raw')).default;
    expect(src.match(/data-blueprint-svg/g)?.length).toBe(3);
    expect(src).toContain('data-blueprint-view="plan"');
    expect(src).toContain('data-blueprint-view="section"');
    expect(src).toContain('data-blueprint-view="elevation"');
  });

  it('ReportStage uses window.print and honest unavailable notes', async () => {
    const src = (await import('../components/ReportStage.tsx?raw')).default;
    expect(src).toContain('window.print()');
    expect(src).toContain('Blueprint artifact unavailable.');
    expect(src).toContain('3D snapshot unavailable.');
    expect(src).toContain('Illustrative parameter-driven digital twin snapshot');
    expect(src.toLowerCase()).not.toContain('pareto');
    expect(src.toLowerCase()).not.toMatch(/\bmeasured\b/);
  });

  it('reportPrint.css hides the app shell and targets A4', () => {
    const css = readFileSync(new URL('../report/reportPrint.css', import.meta.url), 'utf-8');
    expect(css).toContain('@media print');
    expect(css).toContain('@page');
    expect(css).toContain('size: A4');
    expect(css).toContain('.no-print');
    expect(css).toContain('.report-document');
  });
});
