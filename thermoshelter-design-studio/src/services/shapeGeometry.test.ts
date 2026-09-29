/**
 * Product-hardening pass — display-only shape geometry mirror tests.
 * The backend (services/geometry.py) is authoritative; this verifies the UI
 * mirror matches the same closed-form analytics so displayed values never
 * contradict what the engine will compute.
 */
import { describe, expect, it } from 'vitest';
import { calculateShapeGeometryDisplay } from './shapeGeometry';

describe('calculateShapeGeometryDisplay', () => {
  it('rectangular: L × W × H (canonical baseline)', () => {
    const g = calculateShapeGeometryDisplay('rectangular', 6, 4, 3);
    expect(g.floorArea).toBeCloseTo(24, 3);
    expect(g.volume).toBeCloseTo(72, 3);
  });

  it('cylindrical: L = diameter, π r² floor, π r² H volume', () => {
    const g = calculateShapeGeometryDisplay('cylindrical', 6, 6, 3);
    expect(g.floorArea).toBeCloseTo(Math.PI * 9, 3);
    expect(g.volume).toBeCloseTo(Math.PI * 9 * 3, 3);
  });

  it('dome pure hemisphere (H = r): 2/3 π r³ volume, no drum', () => {
    const g = calculateShapeGeometryDisplay('dome', 6, 6, 3);
    expect(g.floorArea).toBeCloseTo(Math.PI * 9, 3);
    expect(g.volume).toBeCloseTo((2 / 3) * Math.PI * 27, 3);
  });

  it('dome with drum (H > r): drum + spherical cap volume', () => {
    // r = 3, H = 4 → drum 1 m, cap 3 m (mirror of the backend formula
    // V = π r² h_drum + (π h_cap² / 3)(3r − h_cap))
    const g = calculateShapeGeometryDisplay('dome', 6, 6, 4);
    const expected = Math.PI * 9 * 1 + (Math.PI * 9 / 3) * (9 - 3);
    expect(g.volume).toBeCloseTo(expected, 3);
  });

  it('pyramid: base area, V = A·h/3', () => {
    const g = calculateShapeGeometryDisplay('pyramid', 6, 4, 3);
    expect(g.floorArea).toBeCloseTo(24, 3);
    expect(g.volume).toBeCloseTo(24, 3);
  });
});
