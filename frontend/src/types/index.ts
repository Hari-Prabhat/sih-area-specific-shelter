// ThermoShelter Engineering Types Definition

export interface City {
  id: string;
  display: string;
  badge: string;
  elevation: string;
  winter_temp: string;
  summer_temp: string;
  solar_ghi: string;
  hdd: number;
  source: string;
  type: string;
  climate_type: string;
  climate_description: string;
}

export interface ClimateData {
  city: string;
  latitude: number;
  longitude: number;
  hourly_temperature: number[];
  hourly_direct_solar: number[];
  hourly_diffuse_solar: number[];
  hourly_wind_speed: number[];
  hourly_humidity: number[];
  metadata?: Record<string, any>;
  climate_type?: string;
  climate_description?: string;
}

export interface Material {
  id: string;
  name: string;
  category: string;
  thermal_conductivity: number;
  density: number;
  specific_heat: number;
  emissivity: number;
  solar_absorptivity: number;
  cost_estimate: number;
  source?: string;
  notes?: string;
}

export interface OrientationCatalogItem {
  id?: string;
  label?: string;
  azimuth?: number;
  solar_factor?: number;
}

export interface ShelterGeometry {
  floor_area_m2: number;
  volume_m3: number;
  solid_wall_area_m2: number;
  roof_area_m2: number;
  window_area_m2: number;
  roof_type: string;
  shelter_model?: string;
  length_m?: number;
  width_m?: number;
  height_m?: number;
}

export interface ComfortMetrics {
  avg: number;
  min_t: number;
  max_t: number;
  mean: number;
  std: number;
  median: number;
}

export interface UValues {
  wall_u: number;
  roof_u: number;
  floor_u: number;
  glass_u: number;
  window_u?: number;
  wall_r_total: number;
  roof_r_total: number;
  floor_r_total: number;
}

export interface ComponentHeatLoss {
  wall_loss_kwh: number;
  roof_loss_kwh: number;
  floor_loss_kwh: number;
  window_loss_kwh: number;
  vent_loss_kwh?: number;
  ventilation_loss_kwh?: number;
  radiation_loss_kwh: number;
  total_heat_loss_kwh: number;
  total_envelope_loss_kwh?: number;
  heating_demand_kwh?: number;
  cooling_demand_kwh?: number;
}

export interface SimulationResult {
  city: string;
  indoor_temperature: number[];
  indoor_temperatures?: number[];
  outdoor_temperature: number[];
  outdoor_temperatures?: number[];
  solar_irradiance: number[];
  solar_power: number[];
  solar_thermal_gain: number[];
  wall_heat_flow: number[];
  roof_heat_flow: number[];
  floor_heat_flow: number[];
  window_heat_flow: number[];
  ventilation_heat_flow: number[];
  radiation_heat_flow: number[];
  net_heat_flow: number[];
  comfort_status: string;
  comfort_hours: number;
  comfort_percentage: number;
  discomfort_degree_hours: number;
  integrated_solar_energy_kwh: number;
  integrated_incident_solar_kwh: number;
  total_heat_loss_kwh: number;
  component_heat_loss_kwh: ComponentHeatLoss;
  comfort_metrics: ComfortMetrics;
  u_values: UValues;
  geometry: ShelterGeometry;
  specs: Record<string, any>;
}

export interface RankedDesign {
  label: string;
  wall_material: string;
  wall_material_name: string;
  insulation_m: number;
  insulation_mm: number;
  window_area_m2: number;
  glazing: string;
  glazing_name: string;
  orientation: string;
  comfort_hours: number;
  comfort_percentage: number;
  discomfort_dh: number;
  total_heat_loss_kwh: number;
  solar_gain_kwh: number;
  overall_score: number;
  sub_scores: {
    comfort: number;
    heat_loss: number;
    solar: number;
  };
}

export interface OptimizationResult {
  city: string;
  climate_type: string;
  climate_name: string;
  home_type: string;
  people: number;
  geometry: {
    floor_area_m2: number;
    length_m: number;
    width_m: number;
    height_m: number;
    volume_m3: number;
  };
  materials: {
    wall_material_id: string;
    wall_material_name: string;
    roof_material: string;
    roof_type: string;
    insulation_type: string;
    glazing_type: string;
    orientation_advice: string;
    shading_advice: string;
    passive_cooling?: string;
  };
  optimal_insulation_m: number;
  optimal_insulation_mm: number;
  optimal_window_area_m2: number;
  optimal_wall_material: string;
  optimal_glazing: string;
  optimal_glazing_name: string;
  optimal_orientation: string;
  discomfort_score: number;
  simulation_result: SimulationResult;
  ranked_designs: RankedDesign[];
  quantitative_evidence: Record<string, any>;
  explanation: string;
}

export interface ComparisonResult {
  baseline: SimulationResult;
  optimized: SimulationResult;
  recommendation: OptimizationResult;
}

export interface MaterialComparisonItem {
  key: string;
  name: string;
  conductivity: number | string;
  density: number | string;
  wall_u: number;
  wall_r: number;
  avg_t: number;
  min_t: number;
  max_t: number;
  comfort_hrs: number;
  comfort_pct: number;
  discomfort_dh: number;
  total_loss_kwh: number;
  indoor_temps: number[];
  outdoor_temps: number[];
}

export interface ArchetypeComparisonItem {
  key: string;
  name: string;
  description: string;
  roof_type: string;
  dimensions: { length: number; width: number; height: number };
  comfort_pct: number;
  discomfort_dh: number;
  heat_loss_kwh: number;
  indoor_temps: number[];
  outdoor_temps: number[];
  geometry: ShelterGeometry;
}

export interface SensitivityData {
  parameter: string;
  unit: string;
  values: number[];
  comfort: number[];
  loss: number[];
}

export interface ValidationBenchmark {
  steady_state: {
    r_total_ref: number;
    r_total_calc: number;
    u_ref: number;
    u_calc: number;
    q_ref_w: number;
    q_calc_w: number;
    mae_w: number;
    rmse_w: number;
    rel_error_pct: number;
    status: string;
  };
  transient: {
    dt_ref_k: number;
    dt_calc_k: number;
    mae_k: number;
    status: string;
  };
}

export interface GlazingCatalogItem {
  name: string;
  u_value: number;
  shgc: number;
  description: string;
}

export interface ShelterModelCatalogItem {
  name: string;
  description: string;
  roof_type: string;
  default_dimensions: {
    length: number;
    width: number;
    height: number;
  };
}

export interface MaterialRecommendation {
  wall_material_id: string;
  wall_material_name: string;
  roof_material: string;
  roof_type: string;
  insulation_type: string;
  glazing_type: string;
  orientation_advice: string;
  shading_advice: string;
  permanence_rationale?: string;
}
