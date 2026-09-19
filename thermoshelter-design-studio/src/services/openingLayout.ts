/**
 * THERMOSHELTER — Shared Opening Layout (D4-C1)
 * =============================================
 * THE single deterministic derivation of shelter openings from the canonical
 * ShelterDesign opening inputs. Consumed by BOTH EngineeringBlueprint (2D) and
 * ShelterModel3D, so the two views can never again disagree on opening count
 * or dimensions (D4-C audit finding: Blueprint assumed 2 identical windows
 * while the 3D model rendered 2 south + 1 north with a 70/30 area split).
 *
 * Intended arrangement (preserved from the existing 3D logic):
 *   - Windows: 2 on the solar-facing (South, +Z) facade receiving 70% of the
 *     design windowArea, and 1 on the North (−Z) facade receiving 30%.
 *   - Door: single south-facade entry, aspect ratio ≈ 2.2, bounded to
 *     realistic door dimensions.
 *
 * All functions are pure and deterministic: identical inputs always produce
 * identical outputs. Dimensions are rounded to 2 decimal places (cm precision)
 * and clamped to the same realistic bounds the 3D model has always used.
 */

/** Two-decimal-place rounding (cm precision), shared by every derivation. */
const r2 = (v: number): number => Math.round(v * 100) / 100;

const clamp = (v: number, min: number, max: number): number => Math.max(min, Math.min(max, v));

export interface FacadeWindows {
  /** Number of windows on this facade. */
  count: number;
  /** Area of each window (m²). */
  areaEach: number;
  /** Window width (m). */
  width: number;
  /** Window height (m). */
  height: number;
  /** Total glazing area allocated to this facade (m²). */
  areaTotal: number;
  /** Deterministic placement of each window on the facade, as a horizontal
   *  centre position expressed as a fraction of the facade length (0..1).
   *  Both viewers use these identical centres so plan drawings and the 3D
   *  twin agree not only on count/size but on relative placement. */
  windows: Array<{ /** centre position, fraction of facade width (0..1) */ centerX: number }>;
}

export interface OpeningLayout {
  south: FacadeWindows;
  north: FacadeWindows;
  door: {
    width: number;
    height: number;
    area: number;
    facade: 'south';
  };
  /** Total number of windows across all facades. */
  totalWindowCount: number;
  /** Total window area across all facades (m²). */
  totalWindowArea: number;
}

/** Area share of the design windowArea allocated to the south (solar) facade. */
export const SOUTH_GLAZING_SHARE = 0.7;
/** Area share of the design windowArea allocated to the north facade. */
export const NORTH_GLAZING_SHARE = 0.3;

/**
 * Derive the full deterministic opening layout from the canonical design's
 * total window area (m²) and door area (m²).
 */
export function deriveOpeningLayout(windowArea: number, doorArea: number): OpeningLayout {
  const totalWindowArea = Math.max(0, windowArea || 0);

  const southTotal = totalWindowArea * SOUTH_GLAZING_SHARE;
  const northTotal = totalWindowArea * NORTH_GLAZING_SHARE;

  // South facade: 2 windows splitting 70% of the glazing.
  const southEach = Math.max(0.3, southTotal / 2);
  const southW = clamp(r2(Math.sqrt(southEach * 1.3)), 0.6, 2.4);
  const southH = clamp(r2(southEach / southW), 0.6, 2.0);

  // North facade: 1 window receiving the remaining 30%.
  const northEach = northTotal;
  const northW = clamp(r2(Math.sqrt(northEach * 1.2)), 0.5, 1.8);
  const northH = clamp(r2(northEach / northW), 0.5, 1.6);

  // Door: aspect ratio ~2.2, bounded within realistic door dimensions
  // (formula preserved verbatim from the existing ParametricDoor derivation).
  const doorAreaClamped = clamp(doorArea || 2.0, 0.8, 5.0);
  const doorW = clamp(r2(Math.sqrt(doorAreaClamped / 2.2)), 0.8, 1.8);
  const doorH = clamp(r2(doorAreaClamped / doorW), 1.9, 2.5);

  return {
    south: {
      count: 2,
      areaEach: southEach,
      width: southW,
      height: southH,
      areaTotal: southTotal,
      // Symmetric placement at 1/4 and 3/4 of the facade — deterministic and
      // shared by the Blueprint plan/elevation drawings and the 3D twin.
      windows: [{ centerX: 0.25 }, { centerX: 0.75 }],
    },
    north: {
      count: 1,
      areaEach: northEach,
      width: northW,
      height: northH,
      areaTotal: northTotal,
      windows: [{ centerX: 0.5 }],
    },
    door: { width: doorW, height: doorH, area: doorAreaClamped, facade: 'south' },
    totalWindowCount: 3,
    totalWindowArea,
  };
}
