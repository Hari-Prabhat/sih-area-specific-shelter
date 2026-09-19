/**
 * THERMOSHELTER — Blueprint Simulation Evidence Overlay (D4-C1, optional)
 * ======================================================================
 * Derives the OPTIONAL Blueprint evidence section from the REAL canonical
 * simulation result. Honesty rules:
 *   - Only genuine engine outputs (U-values, component losses, totals) appear.
 *   - If no canonical result exists, the overlay is simply absent.
 *   - No U-value, loss, or performance value is ever fabricated here.
 *
 * This module stays side-effect free and UI-framework-free so it is directly
 * unit-testable.
 */
import type { CanonicalSimulationResult } from './api';

/** One evidence tile in the Blueprint overlay. */
export interface BlueprintOverlayItem {
  label: string;
  /** Raw numeric value; formatted by formatOverlayValue in the view. */
  value: number;
  unit: string;
}

/** The overlay model consumed by EngineeringBlueprint. */
export interface BlueprintSimulationOverlay {
  items: BlueprintOverlayItem[];
}

/**
 * Builds the overlay from a canonical simulation result, or returns null when
 * no result / no usable evidence exists (the section is then not rendered).
 */
export function buildBlueprintSimulationOverlay(
  result: CanonicalSimulationResult | null | undefined,
): BlueprintSimulationOverlay | null {
  if (!result) return null;

  const items: BlueprintOverlayItem[] = [];

  if (result.u_values && typeof result.u_values.wall_u === 'number' && Number.isFinite(result.u_values.wall_u)) {
    items.push({ label: 'Wall U-value', value: result.u_values.wall_u, unit: 'W/m²·K' });
  }
  if (result.u_values && typeof result.u_values.roof_u === 'number' && Number.isFinite(result.u_values.roof_u)) {
    items.push({ label: 'Roof U-value', value: result.u_values.roof_u, unit: 'W/m²·K' });
  }
  if (result.u_values && typeof result.u_values.floor_u === 'number' && Number.isFinite(result.u_values.floor_u)) {
    items.push({ label: 'Floor U-value', value: result.u_values.floor_u, unit: 'W/m²·K' });
  }
  if (
    result.component_heat_loss_kwh &&
    typeof result.component_heat_loss_kwh.wall_loss_kwh === 'number' &&
    Number.isFinite(result.component_heat_loss_kwh.wall_loss_kwh)
  ) {
    items.push({ label: 'Wall loss', value: result.component_heat_loss_kwh.wall_loss_kwh, unit: 'kWh / 168 h' });
  }
  if (typeof result.total_heat_loss_kwh === 'number' && Number.isFinite(result.total_heat_loss_kwh)) {
    items.push({ label: 'Total heat loss', value: result.total_heat_loss_kwh, unit: 'kWh / 168 h' });
  }
  if (
    result.energy_totals_kwh &&
    typeof result.energy_totals_kwh.heating_demand_kwh === 'number' &&
    Number.isFinite(result.energy_totals_kwh.heating_demand_kwh)
  ) {
    items.push({ label: 'Heating demand', value: result.energy_totals_kwh.heating_demand_kwh, unit: 'kWh' });
  }

  return items.length > 0 ? { items } : null;
}

/** Formats an overlay value for display (1 decimal place, or — for invalid). */
export function formatOverlayValue(value: number): string {
  return Number.isFinite(value) ? (Math.round(value * 10) / 10).toString() : '—';
}
