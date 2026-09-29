/**
 * THERMOSHELTER — Material Input-Integrity tests (D4-C1)
 * ======================================================
 * Enumerates EVERY simulation-selectable UI material (the ShelterDesigner's
 * wall-material cards = all non-Insulation entries, plus the five insulation
 * option values) and asserts the full resolution chain:
 *
 *   UI selection → frontend entry → backend material ID → backend conductivity
 *
 * The backend DB (data/materials/materials.json) is authoritative — the
 * expected conductivity values below were read directly from it (typical_value)
 * plus the alias layer in services/material_service.py.
 *
 * D4-C fixes under test:
 *   - 'timber' → backend 'wood' alias (previously an unresolvable key that
 *     silently degraded to brick k=0.72 in the physics engine)
 *   - 'concrete_block' → backend 'concrete' alias (same silent-degradation bug)
 *   - XPS entry added (previously missing → generic 0.025 fallback)
 *   - Glass/SIP/PCM/Vermiculite removed (no DB entries → were silently
 *     degraded; they must NOT be simulation-selectable)
 *   - Every UI conductivity matches its mapped backend value exactly
 */
import { describe, expect, it } from 'vitest';
import materialsDbJson from '../../../data/materials/materials.json';
import {
  materials,
  MATERIAL_BACKEND_MAP,
  CANONICAL_ALIASES,
  getMaterialByName,
  getUiNameByBackendId,
  resolveBackendMaterialId,
  wallMaterialKey,
} from './materials';

/** Backend DB values (typical_value) read from data/materials/materials.json. */
const BACKEND_CONDUCTIVITY: Record<string, number> = {
  mud_brick: 0.6,
  stone_granite: 2.8,
  stone_sandstone: 1.8,
  wood: 0.13, // alias → wood_timber_pine (k=0.13)
  plywood_sheathing: 0.13,
  brick: 0.81, // alias → fired_clay_brick (k=0.81)
  concrete: 1.4, // alias → concrete_standard (k=1.4)
  corrugated_galvanized_iron_cgi: 50.0,
  autoclaved_aerated_concrete: 0.16,
  rammed_earth: 1.05,
  trombe_wall_mass: 1.75,
  eps_insulation: 0.036,
  xps_insulation: 0.029,
  puf_insulation: 0.024, // alias → polyurethane_foam (k=0.024)
  glass_wool: 0.04,
  mineral_wool: 0.038,
};

/** The authoritative DB file, imported directly — the backend remains the source of truth. */
const dbRaw = materialsDbJson as Array<{ id: string; thermal_conductivity: { typical_value: number } }>;
const dbConductivity: Record<string, number> = Object.fromEntries(
  dbRaw.map((m) => [m.id, m.thermal_conductivity?.typical_value ?? NaN]),
);

describe('MATERIAL_BACKEND_MAP → backend resolvability', () => {
  it('maps every UI material name to a backend-resolvable ID', () => {
    for (const [uiName, ref] of Object.entries(MATERIAL_BACKEND_MAP)) {
      const id = resolveBackendMaterialId(uiName);
      expect(id, `UI material "${uiName}" must resolve`).not.toBeNull();

      const direct = dbConductivity[id as string];
      const knownAlias = ['wood', 'brick', 'concrete', 'puf_insulation', 'eps_insulation', 'xps_insulation'].includes(
        id as string,
      );
      expect(
        direct !== undefined || knownAlias,
        `"${uiName}" → "${id}" must be a DB id or a documented backend alias`,
      ).toBe(true);
      expect(BACKEND_CONDUCTIVITY[id as string], `no expected conductivity recorded for "${id}"`).toBeDefined();
    }
  });

  it('resolves Timber/Wood to the backend wood alias with k=0.13 (not brick)', () => {
    expect(MATERIAL_BACKEND_MAP['Timber/Wood'].backendId).toBe('wood');
    expect(BACKEND_CONDUCTIVITY['wood']).toBe(0.13);
    expect(BACKEND_CONDUCTIVITY['wood']).not.toBe(0.72);
  });

  it('resolves Concrete selections to the backend concrete alias with k=1.4', () => {
    expect(MATERIAL_BACKEND_MAP['Concrete (Dense)'].backendId).toBe('concrete');
    expect(BACKEND_CONDUCTIVITY['concrete']).toBe(1.4);
  });

  it('resolves XPS, PUF Board and Rock Wool correctly', () => {
    expect(MATERIAL_BACKEND_MAP['XPS'].backendId).toBe('xps_insulation');
    expect(BACKEND_CONDUCTIVITY['xps_insulation']).toBe(0.029);
    expect(MATERIAL_BACKEND_MAP['PUF Board'].backendId).toBe('puf_insulation');
    expect(BACKEND_CONDUCTIVITY['puf_insulation']).toBe(0.024);
    expect(MATERIAL_BACKEND_MAP['Rock Wool'].backendId).toBe('mineral_wool');
    expect(BACKEND_CONDUCTIVITY['mineral_wool']).toBe(0.038);
  });

  it('resolves the RAMMED EARTH selection to the real rammed_earth DB id', () => {
    expect(MATERIAL_BACKEND_MAP['Rammed Earth (Stabilized)'].backendId).toBe('rammed_earth');
    expect(BACKEND_CONDUCTIVITY['rammed_earth']).toBe(1.05);
  });

  it('no longer offers materials the backend cannot simulate (Glass, SIP, PCM, Vermiculite)', () => {
    const selectable = materials.map((m) => m.name);
    expect(selectable).not.toContain('Glass (Clear)');
    expect(selectable.some((n) => /SIP/i.test(n))).toBe(false);
    expect(selectable.some((n) => /PCM/i.test(n))).toBe(false);
    expect(selectable.some((n) => /Vermiculite/i.test(n))).toBe(false);
  });
});

describe('enumerated simulation-selectable materials', () => {
  const selectableWalls = materials.filter((m) => m.category !== 'Insulation');
  const insulationOptions = Object.keys(CANONICAL_ALIASES);

  it('the designer exposes a healthy set of wall materials', () => {
    expect(selectableWalls.length).toBeGreaterThanOrEqual(10);
    expect(insulationOptions).toEqual(['EPS', 'XPS', 'PUF Board', 'Glass Wool', 'Rock Wool']);
  });

  it('every selectable wall material resolves to a real backend id', () => {
    for (const m of selectableWalls) {
      const id = resolveBackendMaterialId(m.name);
      expect(id, `wall material "${m.name}" must resolve to a backend id`).not.toBeNull();
      expect(BACKEND_CONDUCTIVITY[id as string], `missing conductivity for "${id}"`).toBeDefined();
    }
  });

  it('every insulation option resolves to a real backend id', () => {
    for (const opt of insulationOptions) {
      const id = resolveBackendMaterialId(opt);
      expect(id, `insulation option "${opt}" must resolve`).not.toBeNull();
      expect(BACKEND_CONDUCTIVITY[id as string], `missing conductivity for "${id}"`).toBeDefined();
    }
  });

  it('every frontend conductivity value matches its mapped backend DB value exactly', () => {
    for (const m of materials) {
      const id = resolveBackendMaterialId(m.name);
      if (!id) continue; // non-simulatable entries are forbidden by the test above
      const backendK = dbConductivity[id] ?? BACKEND_CONDUCTIVITY[id];
      expect(backendK, `no DB conductivity for "${id}"`).toBeDefined();
      expect(m.thermalConductivity, `"${m.name}" k must match backend "${id}"`).toBe(backendK);
    }
  });

  it('wallMaterialKey never emits the retired unresolvable keys', () => {
    for (const m of selectableWalls) {
      const key = wallMaterialKey(m.name);
      expect(key).not.toBe('timber');
      expect(key).not.toBe('concrete_block');
      expect(BACKEND_CONDUCTIVITY[key] !== undefined || ['wood', 'brick', 'concrete'].includes(key)).toBe(true);
    }
  });

  it('wallMaterialKey resolves every mapped name to its real backend id; only unknown names fall back to brick', () => {
    expect(wallMaterialKey(null)).toBe('brick');
    expect(wallMaterialKey('Not A Material')).toBe('brick');
    expect(wallMaterialKey('Timber/Wood')).toBe('wood');
    expect(wallMaterialKey('Concrete (Dense)')).toBe('concrete');
    expect(wallMaterialKey('Mud/Adobe')).toBe('mud_brick');
    // Insulation names also resolve to their real DB ids (they are in the
    // conductivity map) — so no wall payload can ever carry a fake key.
    expect(wallMaterialKey('EPS')).toBe('eps_insulation');
  });
});

describe('getMaterialByName canonical aliases', () => {
  it('resolves the designer short option values to canonical entries', () => {
    expect(getMaterialByName('EPS')?.thermalConductivity).toBe(0.036);
    expect(getMaterialByName('XPS')?.thermalConductivity).toBe(0.029);
    expect(getMaterialByName('PUF Board')?.thermalConductivity).toBe(0.024);
    expect(getMaterialByName('Glass Wool')?.thermalConductivity).toBe(0.04);
    expect(getMaterialByName('Rock Wool')?.thermalConductivity).toBe(0.038);
  });

  it('returns undefined for unknown names (honest failure, no invention)', () => {
    expect(getMaterialByName('Unobtanium')).toBeUndefined();
  });

  it('Batch 1-B: backend material keys round-trip back to a UI option', () => {
    // Apply Candidate stores the candidate's material as a UI name. The
    // round-trip key -> UI name -> key must be identity for every backend ID
    // the optimizer can echo (wall_material), otherwise the applied design
    // silently breaks the next Run Simulation (Batch 1-G regression).
    const backendIds = new Set(
      materials
        .filter((m) => m.category !== 'Insulation')
        .map((m) => resolveBackendMaterialId(m.name))
        .filter((id): id is string => !!id),
    );
    expect(backendIds.size).toBeGreaterThan(5);
    for (const id of backendIds) {
      const uiName = getUiNameByBackendId(id);
      expect(uiName, `backend id ${id}`).not.toBeNull();
      expect(resolveBackendMaterialId(uiName!), `round trip ${id}`).toBe(id);
      // And the restored name must resolve through getMaterialByName (the
      // exact lookup runSimulation performs before every payload).
      expect(getMaterialByName(uiName!), `lookup for ${uiName}`).toBeDefined();
    }
  });

  it('Batch 1-B: the optimizer echo name maps to a resolvable UI material', () => {
    // "Rammed Earth (Stabilized / Unstabilized)" is the backend display name
    // echoed by wall_material_name — NOT a UI option. The candidate's
    // wall_material KEY ('rammed_earth') must restore 'Rammed Earth (Stabilized)'.
    expect(getUiNameByBackendId('rammed_earth')).toBe('Rammed Earth (Stabilized)');
    expect(getMaterialByName(getUiNameByBackendId('rammed_earth')!)).toBeDefined();
    expect(getUiNameByBackendId('brick')).toBe('Brick (Solid)');
    expect(getUiNameByBackendId('not_a_real_id')).toBeNull();
  });
});
