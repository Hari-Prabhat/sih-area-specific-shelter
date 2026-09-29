/**
 * THERMOSHELTER — Display-only shape geometry mirror (product-hardening pass)
 * ===========================================================================
 * Mirrors services/geometry.py `calculate_shape_geometry` exactly so the
 * Design stage can show shape-aware floor area / volume while the user edits.
 * The BACKEND remains the single authority: these values are never sent to the
 * simulation (the engine recomputes them from the canonical design), never
 * persisted, and exist only for immediate UI feedback.
 */

export type ShelterShape = 'rectangular' | 'cylindrical' | 'dome' | 'pyramid';

export function calculateShapeGeometryDisplay(
  shape: ShelterShape,
  length: number,
  width: number,
  height: number,
): { floorArea: number; volume: number } {
  if (shape === 'cylindrical') {
    const r = length / 2;
    return { floorArea: Math.PI * r * r, volume: Math.PI * r * r * height };
  }
  if (shape === 'dome') {
    const r = length / 2;
    const drumH = Math.max(0, Math.min(height - r, height));
    const capH = Math.max(0, height - drumH);
    const capVol = (Math.PI * capH * capH / 3) * (3 * r - capH);
    return { floorArea: Math.PI * r * r, volume: Math.PI * r * r * drumH + capVol };
  }
  if (shape === 'pyramid') {
    return { floorArea: length * width, volume: (length * width * height) / 3 };
  }
  return { floorArea: length * width, volume: length * width * height };
}
