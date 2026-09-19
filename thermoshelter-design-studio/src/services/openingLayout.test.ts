/**
 * THERMOSHELTER — Shared Opening Layout tests (D4-C1)
 * ===================================================
 * Proves the single deterministic derivation consumed by BOTH the 2D
 * Engineering Blueprint and the 3D Digital Twin: identical inputs must always
 * produce identical opening counts/dimensions on both facades and the door.
 */
import { describe, it, expect } from 'vitest';
import { deriveOpeningLayout, SOUTH_GLAZING_SHARE, NORTH_GLAZING_SHARE } from './openingLayout';

describe('deriveOpeningLayout', () => {
  it('allocates 70% of glazing to 2 south windows and 30% to 1 north window', () => {
    const layout = deriveOpeningLayout(3.0, 2.0);

    expect(layout.south.count).toBe(2);
    expect(layout.north.count).toBe(1);
    expect(layout.totalWindowCount).toBe(3);
    expect(layout.south.areaTotal).toBeCloseTo(3.0 * SOUTH_GLAZING_SHARE, 10);
    expect(layout.north.areaTotal).toBeCloseTo(3.0 * NORTH_GLAZING_SHARE, 10);
    expect(layout.south.areaEach).toBeCloseTo(layout.south.areaTotal / 2, 10);
    expect(layout.north.areaEach).toBeCloseTo(layout.north.areaTotal, 10);
  });

  it('derives window dimensions within realistic bounds and matching area', () => {
    const layout = deriveOpeningLayout(3.0, 2.0);

    expect(layout.south.width).toBeGreaterThanOrEqual(0.6);
    expect(layout.south.width).toBeLessThanOrEqual(2.4);
    expect(layout.south.height).toBeGreaterThanOrEqual(0.6);
    expect(layout.south.height).toBeLessThanOrEqual(2.0);
    expect(layout.north.width).toBeGreaterThanOrEqual(0.5);
    expect(layout.north.width).toBeLessThanOrEqual(1.8);
    expect(layout.north.height).toBeGreaterThanOrEqual(0.5);
    expect(layout.north.height).toBeLessThanOrEqual(1.6);

    // width * height must reproduce the per-window area within rounding.
    expect(layout.south.width * layout.south.height).toBeCloseTo(layout.south.areaEach, 1);
    expect(layout.north.width * layout.north.height).toBeCloseTo(layout.north.areaEach, 1);
  });

  it('derives the door deterministically with aspect-ratio 2.2 and realistic bounds', () => {
    const layout = deriveOpeningLayout(3.0, 2.0);

    expect(layout.door.facade).toBe('south');
    expect(layout.door.width).toBeGreaterThanOrEqual(0.8);
    expect(layout.door.width).toBeLessThanOrEqual(1.8);
    expect(layout.door.height).toBeGreaterThanOrEqual(1.9);
    expect(layout.door.height).toBeLessThanOrEqual(2.5);
    expect(layout.door.width * layout.door.height).toBeCloseTo(layout.door.area, 1);
  });

  it('is deterministic — identical inputs always produce identical outputs', () => {
    const a = deriveOpeningLayout(4.2, 2.4);
    const b = deriveOpeningLayout(4.2, 2.4);

    expect(a).toEqual(b);
  });

  it('handles zero window area without fabricating dimensions', () => {
    const layout = deriveOpeningLayout(0, 2.0);

    expect(layout.south.areaEach).toBe(0.3); // per-window floor (existing 3D rule)
    expect(layout.north.areaEach).toBe(0);
  });

  it('scales window dimensions monotonically with total glazing area', () => {
    const small = deriveOpeningLayout(1.0, 2.0);
    const large = deriveOpeningLayout(6.0, 2.0);

    expect(large.south.areaEach).toBeGreaterThan(small.south.areaEach);
    expect(large.north.areaEach).toBeGreaterThan(small.north.areaEach);
  });
});

describe('shared consumption contract', () => {
  it('EngineeringBlueprint consumes the shared layout (no local window derivation)', async () => {
    const src = (await import('../components/EngineeringBlueprint.tsx?raw')).default;
    expect(src).toContain("from '../services/openingLayout'");
    expect(src).not.toMatch(/const numWindows\s*=\s*\d/);
  });

  it('ShelterModel3D consumes the shared layout (no local window derivation)', async () => {
    const src = (await import('../components/ShelterModel3D.tsx?raw')).default;
    expect(src).toContain("from '../services/openingLayout'");
    expect(src).not.toMatch(/frontGlazingTotal\s*=\s*windowArea\s*\*\s*0\.7/);
  });
});
