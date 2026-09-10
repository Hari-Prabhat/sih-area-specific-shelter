// ThermoShelter API Client - Connected directly to FastAPI Backend

import {
  City,
  ClimateData,
  Material,
  SimulationResult,
  OptimizationResult,
  ComparisonResult,
  MaterialComparisonItem,
  ArchetypeComparisonItem,
  SensitivityData,
  ValidationBenchmark,
  GlazingCatalogItem,
  OrientationCatalogItem,
  ShelterModelCatalogItem,
} from "../types";

// When on Vite dev/preview (port 5173 or relative), use relative path to leverage Vite reverse proxy.
// Otherwise fallback to http://127.0.0.1:8000
const API_BASE =
  import.meta.env.VITE_API_BASE_URL !== undefined
    ? import.meta.env.VITE_API_BASE_URL
    : typeof window !== "undefined" && window.location.port === "5173"
    ? ""
    : "http://127.0.0.1:8000";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      ...options,
    });

    if (!res.ok) {
      let errorDetail = `API Error: ${res.status} ${res.statusText}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errorDetail = errJson.detail;
      } catch {
        // fallback
      }
      throw new Error(errorDetail);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    if (
      err.message === "Failed to fetch" ||
      err.name === "TypeError" ||
      err.message?.includes("NetworkError")
    ) {
      throw new Error(
        "FastAPI backend is unreachable on port 8000. Please start the backend in a terminal: python -m uvicorn api:app --port 8000"
      );
    }
    throw err;
  }
}

export const api = {
  getHealth: () => request<{ status: string; service: string }>("/api/health"),

  getCities: () => request<{ cities: City[] }>("/api/climate/cities"),

  getClimate: (city: string) => request<ClimateData>(`/api/climate/${city}`),

  getMaterials: () =>
    request<{ materials: Record<string, Material> }>("/api/materials"),

  getMaterial: (id: string) => request<Material>(`/api/materials/${id}`),

  getShelterModels: () =>
    request<{ models: Record<string, ShelterModelCatalogItem> }>("/api/shelter-models"),

  getGlazing: () =>
    request<{ glazing: Record<string, GlazingCatalogItem> }>("/api/glazing"),

  getOrientations: () =>
    request<{ orientations: Record<string, number | OrientationCatalogItem> }>("/api/orientations"),

  autoSize: (people: number, homeType: string) =>
    request<{
      floor_area_m2: number;
      length_m: number;
      width_m: number;
      height_m: number;
      volume_m3: number;
    }>("/api/auto-size", {
      method: "POST",
      body: JSON.stringify({ people, home_type: homeType }),
    }),

  recommendMaterials: (climateType: string, homeType: string) =>
    request<any>("/api/recommend-materials", {
      method: "POST",
      body: JSON.stringify({ climate_type: climateType, home_type: homeType }),
    }),

  runSimulation: (params: {
    city: string;
    length: number;
    width: number;
    height: number;
    wall_material: string;
    insulation_thickness_m: number;
    window_area: number;
    glazing: string;
    orientation: string;
    roof_type: string;
    occupants: number;
    hours_to_simulate?: number;
    shelter_model?: string;
  }) =>
    request<SimulationResult>("/api/simulation", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  runOptimization: (params: {
    city: string;
    people: number;
    home_type: string;
    n_trials?: number;
    max_insulation_mm?: number;
    max_window_area?: number;
  }) =>
    request<OptimizationResult>("/api/optimization", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  runComparison: (params: {
    city: string;
    people: number;
    home_type: string;
  }) =>
    request<ComparisonResult>("/api/comparison", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  runMaterialComparison: (params: {
    city: string;
    insulation_mm: number;
    window_area: number;
    occupants: number;
  }) =>
    request<{ materials: MaterialComparisonItem[] }>(
      "/api/material-comparison",
      {
        method: "POST",
        body: JSON.stringify(params),
      }
    ),

  runArchetypeComparison: (params: {
    city: string;
    occupants: number;
    height?: number;
  }) =>
    request<{ archetypes: ArchetypeComparisonItem[] }>(
      "/api/archetype-comparison",
      {
        method: "POST",
        body: JSON.stringify(params),
      }
    ),

  runSensitivity: (params: {
    city: string;
    parameter: "insulation" | "window_area";
    occupants: number;
  }) =>
    request<SensitivityData>("/api/sensitivity", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  getValidation: () => request<ValidationBenchmark>("/api/validation"),

  exportMarkdown: (params: {
    city: string;
    people: number;
    home_type: string;
    n_trials?: number;
    max_insulation_mm?: number;
    max_window_area?: number;
  }) =>
    request<{ markdown: string }>("/api/export/markdown", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  exportJson: (params: {
    city: string;
    people: number;
    home_type: string;
    n_trials?: number;
    max_insulation_mm?: number;
    max_window_area?: number;
  }) =>
    request<any>("/api/export/json", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};
