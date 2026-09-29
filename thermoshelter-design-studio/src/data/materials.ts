/**
 * THERMOSHELTER AI - Material Property Database (Frontend Mirror)
 * ================================================================
 * UI-facing mirror of the authoritative backend material database
 * (data/materials/materials.json, resolved by services/material_service.py).
 *
 * D4-C input-integrity rule: every value below is the BACKEND DB value.
 * The backend DB remains authoritative for all physics; this file exists so
 * the UI displays honest properties and so the frontend sends
 * backend-resolvable material IDs. Tested by materials.test.ts, which
 * enumerates every simulation-selectable UI material and asserts
 * selection -> frontend entry -> backend ID -> backend conductivity.
 *
 * D4-C corrections (audit-verified by executing services/material_service.py):
 *  - All thermalConductivity values now match the backend DB exactly
 *    (previously several diverged: EPS 0.035 vs DB 0.036, brick 0.72 vs 0.81,
 *    rammed earth 0.65 vs 1.05, limestone 1.3 vs sandstone 1.8, ...).
 *  - Added the missing XPS entry (XPS previously fell through to the generic
 *    0.025 fallback in the payload builder).
 *  - Removed Glass (Clear), SIP Panel, PCM Wall and Vermiculite: the backend
 *    DB has NO entries for them, so selecting them silently degraded the
 *    physics to fallback (brick/default) properties. A material the physics
 *    engine cannot resolve must not be simulation-selectable. This removal
 *    is deliberate and documented — not silent.
 *  - MATERIAL_BACKEND_MAP gives the explicit UI-name -> backend-ID mapping;
 *    getMaterialByName resolves the designer's short option values
 *    (EPS / XPS / PUF Board / Rock Wool) via CANONICAL_ALIASES.
 */

import { MaterialProperties } from '../types';

/** Explicit UI selection -> backend material ID (services/material_service.py keys). */
export interface BackendMaterialRef {
  backendId: string;
  /** Documented approximation when no exact DB entry exists. */
  note?: string;
}

export const MATERIAL_BACKEND_MAP: Record<string, BackendMaterialRef> = {
  // ---- Wall / structural ----
  'Mud/Adobe': { backendId: 'mud_brick' },
  'Stone (Granite)': { backendId: 'stone_granite' },
  'Stone (Limestone)': { backendId: 'stone_sandstone', note: 'nearest DB stone (sandstone k=1.8)' },
  'Timber/Wood': { backendId: 'wood' },
  'Bamboo Composite': { backendId: 'plywood_sheathing', note: 'nearest DB timber product (k=0.13)' },
  'Brick (Solid)': { backendId: 'brick' },
  'Concrete (Dense)': { backendId: 'concrete' },
  'Concrete (Lightweight)': { backendId: 'concrete', note: 'single DB concrete entry (k=1.4)' },
  'Steel Sheet': { backendId: 'corrugated_galvanized_iron_cgi', note: 'DB CGI sheet (k=50)' },
  'AAC Block (Autoclaved Aerated Concrete)': { backendId: 'autoclaved_aerated_concrete' },
  'Rammed Earth (Stabilized)': { backendId: 'rammed_earth' },
  'Trombe Wall (Concrete + Glass)': { backendId: 'trombe_wall_mass' },
  // ---- Insulation ----
  EPS: { backendId: 'eps_insulation' },
  XPS: { backendId: 'xps_insulation' },
  'PUF Board': { backendId: 'puf_insulation' },
  'Glass Wool': { backendId: 'glass_wool' },
  'Rock Wool': { backendId: 'mineral_wool', note: 'DB mineral wool (k=0.038)' },
};

/**
 * Resolves a UI material selection to its backend material ID.
 * Returns null when the selection has no backend representation — the caller
 * must not send it to the physics engine (no unknown IDs may be sent).
 */
export function resolveBackendMaterialId(uiName: string | null | undefined): string | null {
  if (!uiName) return null;
  return MATERIAL_BACKEND_MAP[uiName]?.backendId ?? null;
}

/** Designer short option values -> canonical entries in the list below. */
export const CANONICAL_ALIASES: Record<string, string> = {
  EPS: 'Expanded Polystyrene (EPS)',
  XPS: 'Extruded Polystyrene (XPS)',
  'PUF Board': 'Polyurethane Foam (PUF)',
  'Glass Wool': 'Glass Wool',
  'Rock Wool': 'Rock Wool',
};

/**
 * The wall-material key sent in canonical simulation payloads. Derived from
 * MATERIAL_BACKEND_MAP so the payload key and the DB-resolvable ID can never
 * drift apart again (D4-C: 'timber'/'concrete_block' previously did not
 * resolve in the backend and silently became brick, k=0.72).
 */
export function wallMaterialKey(uiName: string | null | undefined): string {
  const id = resolveBackendMaterialId(uiName);
  if (id) return id;
  // Insulation entries are not wall keys; wall default remains brick.
  return 'brick';
}

export const materials: MaterialProperties[] = [
  // Backend: mud_brick k=0.6 rho=1600 sh=1000
  { name: 'Mud/Adobe', thermalConductivity: 0.6, density: 1600, specificHeat: 1000, emissivity: 0.9, solarAbsorptance: 0.7, cost: 200, category: 'Traditional' },
  // Backend: stone_granite k=2.8 rho=2600 sh=820
  { name: 'Stone (Granite)', thermalConductivity: 2.8, density: 2600, specificHeat: 820, emissivity: 0.9, solarAbsorptance: 0.65, cost: 800, category: 'Traditional' },
  // Backend: stone_sandstone k=1.8 rho=2200 sh=920 (nearest DB stone to limestone)
  { name: 'Stone (Limestone)', thermalConductivity: 1.8, density: 2200, specificHeat: 920, emissivity: 0.9, solarAbsorptance: 0.68, cost: 600, category: 'Traditional' },
  // Backend: wood_timber_pine k=0.13 rho=500 sh=1600 (D4-C: was 0.15, sent as unresolvable 'timber')
  { name: 'Timber/Wood', thermalConductivity: 0.13, density: 500, specificHeat: 1600, emissivity: 0.9, solarAbsorptance: 0.6, cost: 500, category: 'Traditional' },
  // Backend: plywood_sheathing k=0.13 rho=600 sh=1700 (nearest DB timber product)
  { name: 'Bamboo Composite', thermalConductivity: 0.13, density: 600, specificHeat: 1700, emissivity: 0.9, solarAbsorptance: 0.6, cost: 300, category: 'Traditional' },
  // Backend: fired_clay_brick k=0.81 rho=1800 sh=880 (D4-C: was 0.72)
  { name: 'Brick (Solid)', thermalConductivity: 0.81, density: 1800, specificHeat: 880, emissivity: 0.9, solarAbsorptance: 0.7, cost: 450, category: 'Modern' },
  // Backend: concrete_standard k=1.4 rho=2300 sh=880 (D4-C: was 1.7, sent as unresolvable 'concrete_block')
  { name: 'Concrete (Dense)', thermalConductivity: 1.4, density: 2300, specificHeat: 880, emissivity: 0.9, solarAbsorptance: 0.65, cost: 550, category: 'Modern' },
  // Backend: concrete (single concrete entry) k=1.4
  { name: 'Concrete (Lightweight)', thermalConductivity: 1.4, density: 1400, specificHeat: 1000, emissivity: 0.9, solarAbsorptance: 0.55, cost: 650, category: 'Modern' },
  // Backend: corrugated_galvanized_iron_cgi k=50 rho=7850 sh=480
  { name: 'Steel Sheet', thermalConductivity: 50.0, density: 7850, specificHeat: 480, emissivity: 0.28, solarAbsorptance: 0.65, cost: 900, category: 'Modern' },
  // Backend: autoclaved_aerated_concrete k=0.16 rho=550 sh=1000 (D4-C: density was 600)
  { name: 'AAC Block (Autoclaved Aerated Concrete)', thermalConductivity: 0.16, density: 550, specificHeat: 1000, emissivity: 0.9, solarAbsorptance: 0.45, cost: 700, category: 'Composite' },
  // Backend: rammed_earth k=1.05 rho=2000 sh=1050 (D4-C: was 0.65)
  { name: 'Rammed Earth (Stabilized)', thermalConductivity: 1.05, density: 2000, specificHeat: 1050, emissivity: 0.9, solarAbsorptance: 0.72, cost: 350, category: 'Composite' },
  // Backend: trombe_wall_mass k=1.75 rho=2400 sh=1000 (D4-C: was 1.2)
  { name: 'Trombe Wall (Concrete + Glass)', thermalConductivity: 1.75, density: 2400, specificHeat: 1000, emissivity: 0.92, solarAbsorptance: 0.95, cost: 1000, category: 'Composite' },
  // ---- Insulation (backend DB values) ----
  // Backend: eps_insulation k=0.036 rho=25 sh=1450 (D4-C: was 0.035)
  { name: 'Expanded Polystyrene (EPS)', thermalConductivity: 0.036, density: 25, specificHeat: 1450, emissivity: 0.9, solarAbsorptance: 0.3, cost: 250, category: 'Insulation' },
  // Backend: xps_insulation k=0.029 rho=35 sh=1500 (D4-C: previously missing entirely)
  { name: 'Extruded Polystyrene (XPS)', thermalConductivity: 0.029, density: 35, specificHeat: 1500, emissivity: 0.9, solarAbsorptance: 0.35, cost: 320, category: 'Insulation' },
  // Backend: puf_insulation k=0.024 rho=32 sh=1400
  { name: 'Polyurethane Foam (PUF)', thermalConductivity: 0.024, density: 32, specificHeat: 1400, emissivity: 0.9, solarAbsorptance: 0.35, cost: 400, category: 'Insulation' },
  // Backend: glass_wool k=0.04 rho=24 sh=840
  { name: 'Glass Wool', thermalConductivity: 0.04, density: 24, specificHeat: 840, emissivity: 0.9, solarAbsorptance: 0.4, cost: 300, category: 'Insulation' },
  // Backend: mineral_wool k=0.038 rho=60 sh=1030 (DB mineral wool; no separate rock-wool entry)
  { name: 'Rock Wool', thermalConductivity: 0.038, density: 60, specificHeat: 1030, emissivity: 0.9, solarAbsorptance: 0.5, cost: 350, category: 'Insulation' },
];

/**
 * Batch 1-B: inverse mapping from a backend material ID (e.g. the optimizer's
 * `wall_material` key, echoed in `wall_material_name`) back to the designer's
 * UI selection. Apply Candidate must restore the canonical UI material the
 * payload will re-send; a backend display name that is not a UI option
 * (e.g. "Rammed Earth (Stabilized / Unstabilized)") previously left the store
 * holding an unresolvable name, silently breaking the next Run Simulation.
 */
export function getUiNameByBackendId(backendId: string | null | undefined): string | null {
  if (!backendId) return null;
  for (const [uiName, entry] of Object.entries(MATERIAL_BACKEND_MAP)) {
    if (entry.backendId === backendId) return uiName;
  }
  return null;
}

export function getMaterialByName(name: string): MaterialProperties | undefined {
  if (!name) return undefined;
  const canonical = CANONICAL_ALIASES[name] ?? name;
  return (
    materials.find((m) => m.name === canonical) ??
    materials.find((m) => m.name.toLowerCase().includes(canonical.toLowerCase()))
  );
}
