/**
 * THERMOSHELTER — Report artifact capture (D4-D3)
 * ===============================================
 * Captures the existing Blueprint and 3D-twin visualizations as report
 * artifacts WITHOUT duplicating any drawing/engineering logic:
 *
 *  - Blueprint: the four views are inline <svg data-blueprint-svg> elements
 *    rendered by EngineeringBlueprint. Capture clones the live DOM node and
 *    serializes it — the drawing logic stays the single source of truth.
 *  - 3D twin: the R3F Canvas runs with preserveDrawingBuffer (the only
 *    permitted config change), enabling gl.domElement.toDataURL('image/png').
 *
 * Honesty: if an artifact cannot be captured, the caller receives null and
 * the report shows the honest "unavailable" state. Nothing is synthesized.
 */

/** Marker attribute placed on the Blueprint's root SVG elements. */
export const BLUEPRINT_SVG_SELECTOR = 'svg[data-blueprint-svg]';

/** Marker attribute placed on the 3D twin's canvas wrapper container. */
export const TWIN_ROOT_SELECTOR = '[data-twin-root]';

/** Blueprint view ids (mirror the component's BlueprintView union). */
export type BlueprintViewId = 'plan' | 'section' | 'elevation' | 'envelope';

export interface BlueprintArtifact {
  view: BlueprintViewId;
  /** Standalone serialized SVG markup (with xmlns for standalone rendering). */
  svg: string;
}

/**
 * Serializes an SVG element to standalone markup. Uses the standard
 * XMLSerializer when available (all browsers); falls back to minimal
 * attribute serialization elsewhere so the capture never crashes.
 */
function serializeSvg(el: Element): string {
  if (typeof XMLSerializer !== 'undefined') {
    return new XMLSerializer().serializeToString(el);
  }
  const attrs = Array.from(el.attributes ?? [])
    .map((a) => `${a.name}="${a.value}"`)
    .join(' ');
  return `<svg ${attrs}>${(el as unknown as { innerHTML?: string }).innerHTML ?? ''}</svg>`;
}

/**
 * Captures every visible Blueprint SVG in the document. The Blueprint shows
 * one view at a time, so this returns the current view; the container exposes
 * the view id via data-blueprint-view when present.
 */
export function captureBlueprintSvgs(root: ParentNode = document): BlueprintArtifact[] {
  const nodes = Array.from(root.querySelectorAll(BLUEPRINT_SVG_SELECTOR)) as unknown as Element[];
  const artifacts: BlueprintArtifact[] = [];
  for (const node of nodes) {
    const view = (node.getAttribute('data-blueprint-view') as BlueprintViewId | null) ?? 'plan';
    const clone = (node.cloneNode(true) ?? node) as Element;
    // Standalone-SVG hygiene: ensure the xmlns namespace so the serialized
    // markup renders outside the React DOM.
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const serialized = serializeSvg(clone);
    if (serialized && serialized.includes('<svg')) {
      artifacts.push({ view, svg: serialized });
    }
  }
  return artifacts;
}

/**
 * Captures the 3D twin canvas as a PNG data URL. The R3F Canvas renders its
 * own <canvas> inside the wrapper marked data-twin-root (see ShelterModel3D);
 * the renderer runs with preserveDrawingBuffer: true (the only permitted
 * config change). Returns null when no canvas exists or the framebuffer is
 * unreadable — the report then shows "3D snapshot unavailable." — never a
 * placeholder image.
 */
export function captureTwinPng(root: ParentNode = document): string | null {
  const container = root.querySelector(TWIN_ROOT_SELECTOR);
  const canvas = (container?.querySelector('canvas') as HTMLCanvasElement | null) ?? null;
  if (!canvas || typeof canvas.toDataURL !== 'function') return null;
  try {
    const url = canvas.toDataURL('image/png');
    // An all-white/blank 1-px frame is not a meaningful artifact; treat
    // zero-size canvases as unavailable.
    if (!url.startsWith('data:image/png') || canvas.width === 0 || canvas.height === 0) {
      return null;
    }
    return url;
  } catch {
    return null;
  }
}
