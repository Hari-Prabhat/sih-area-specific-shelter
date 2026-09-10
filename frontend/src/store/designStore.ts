import { create } from "zustand";
import { api } from "../api/client";
import {
  City,
  ClimateData,
  Material,
  SimulationResult,
  OptimizationResult,
  ComparisonResult,
  GlazingCatalogItem,
  OrientationCatalogItem,
  ShelterModelCatalogItem,
} from "../types";

export interface DesignState {
  length: number;
  width: number;
  height: number;
  roofType: string;
  wallMaterial: string;
  roofMaterial: string;
  insulationThicknessMm: number;
  windowArea: number;
  glazing: string;
  orientation: string;
}

interface AppStore {
  // Navigation
  activeTab: string;
  setActiveTab: (tab: string) => void;

  // Global project state
  selectedCity: string;
  cities: City[];
  climateData: ClimateData | null;
  people: number;
  homeType: "Permanent" | "Temporary";

  // Catalogs loaded from backend API
  materialsCatalog: Record<string, Material>;
  glazingCatalog: Record<string, GlazingCatalogItem>;
  orientationsCatalog: Record<string, number | OrientationCatalogItem>;
  shelterModelsCatalog: Record<string, ShelterModelCatalogItem>;

  // Design parameters
  design: DesignState;

  // Stale tracking for simulation
  isSimulationStale: boolean;
  lastSimulatedDesign: (DesignState & {
    city: string;
    occupants: number;
  }) | null;

  // Simulation & Optimization cache
  simulationResult: SimulationResult | null;
  optimizationResult: OptimizationResult | null;
  comparisonResult: ComparisonResult | null;

  // UI state
  loading: {
    init: boolean;
    climate: boolean;
    simulation: boolean;
    optimization: boolean;
    comparison: boolean;
  };
  error: string | null;

  // Actions
  setCity: (city: string) => Promise<void>;
  setPeople: (people: number) => void;
  setHomeType: (type: "Permanent" | "Temporary") => void;
  updateDesign: (patch: Partial<DesignState>) => void;
  autoSizeDesign: () => Promise<void>;
  fetchInitialData: () => Promise<void>;
  runSimulation: () => Promise<void>;
  runOptimization: (trials?: number) => Promise<void>;
  runComparison: () => Promise<void>;
  applyOptimizationRecommendation: () => void;
  resetToNewDesign: (params?: {
    city?: string;
    people?: number;
    homeType?: "Permanent" | "Temporary";
    archetype?: "recommended" | "standard" | "compact" | "solar";
  }) => Promise<void>;
}

export const useDesignStore = create<AppStore>((set, get) => ({
  activeTab: "overview",
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Default option is unselected so user is prompted to "Choose the location"
  selectedCity: "",
  cities: [],
  climateData: null,
  people: 4,
  homeType: "Permanent",

  // Catalogs initialized with resilient defaults
  materialsCatalog: {},
  glazingCatalog: {},
  orientationsCatalog: {},
  shelterModelsCatalog: {},

  design: {
    length: 4.5,
    width: 3.2,
    height: 2.8,
    roofType: "pitched",
    wallMaterial: "brick",
    roofMaterial: "insulated_metal",
    insulationThicknessMm: 60,
    windowArea: 2.5,
    glazing: "double_clear",
    orientation: "south",
  },

  isSimulationStale: false,
  lastSimulatedDesign: null,

  simulationResult: null,
  optimizationResult: null,
  comparisonResult: null,

  loading: {
    init: false,
    climate: false,
    simulation: false,
    optimization: false,
    comparison: false,
  },
  error: null,

  setCity: async (city: string) => {
    if (!city) {
      set({
        selectedCity: "",
        climateData: null,
        simulationResult: null,
        optimizationResult: null,
        comparisonResult: null,
        isSimulationStale: false,
        lastSimulatedDesign: null,
      });
      return;
    }
    set((s) => ({
      selectedCity: city,
      simulationResult: null,
      optimizationResult: null,
      comparisonResult: null,
      isSimulationStale: false,
      lastSimulatedDesign: null,
      loading: { ...s.loading, climate: true },
      error: null,
    }));
    try {
      const climate = await api.getClimate(city);
      const isCold = climate.climate_type === "cold";
      set((s) => ({
        climateData: climate,
        design: {
          ...s.design,
          roofType: isCold ? "pitched" : "flat",
        },
        loading: { ...s.loading, climate: false },
      }));
    } catch (e: any) {
      set((s) => ({
        error: e.message || "Failed to load climate data",
        loading: { ...s.loading, climate: false },
      }));
    }
  },

  setPeople: (people: number) => {
    const hasSim = get().simulationResult !== null;
    set({ people, isSimulationStale: hasSim });
    get().autoSizeDesign();
  },

  setHomeType: (homeType: "Permanent" | "Temporary") => {
    const hasSim = get().simulationResult !== null;
    set({ homeType, isSimulationStale: hasSim });
    get().autoSizeDesign();
  },

  updateDesign: (patch: Partial<DesignState>) => {
    const prev = get().design;
    const next = { ...prev, ...patch };
    const lastSim = get().lastSimulatedDesign;
    let isStale = get().isSimulationStale;

    if (get().simulationResult && lastSim) {
      const keys = Object.keys(next) as (keyof DesignState)[];
      const hasChanged = keys.some((k) => next[k] !== lastSim[k]);
      if (hasChanged) isStale = true;
    } else if (get().simulationResult) {
      isStale = true;
    }

    set({ design: next, isSimulationStale: isStale });
  },

  autoSizeDesign: async () => {
    const { people, homeType, simulationResult } = get();
    try {
      const geo = await api.autoSize(people, homeType);
      const current = get();
      set({
        design: {
          ...current.design,
          length: geo.length_m,
          width: geo.width_m,
          height: geo.height_m,
        },
        isSimulationStale: simulationResult !== null,
      });
    } catch (e: any) {
      set({
        error: e.message || "Auto-sizing failed. Please check the backend connection.",
        isSimulationStale: simulationResult !== null,
      });
    }
  },

  fetchInitialData: async () => {
    set((s) => ({ loading: { ...s.loading, init: true }, error: null }));
    try {
      // Parallel fetch of cities and backend engineering catalogs
      const [citiesRes, matsRes, glazingRes, orientRes, modelsRes] =
        await Promise.allSettled([
          api.getCities(),
          api.getMaterials(),
          api.getGlazing(),
          api.getOrientations(),
          api.getShelterModels(),
        ]);

      const cities =
        citiesRes.status === "fulfilled" ? citiesRes.value.cities : [];
      const materials =
        matsRes.status === "fulfilled" ? matsRes.value.materials : {};
      const glazing =
        glazingRes.status === "fulfilled" ? glazingRes.value.glazing : {};
      const orientations =
        orientRes.status === "fulfilled" ? orientRes.value.orientations : {};
      const shelterModels =
        modelsRes.status === "fulfilled" ? modelsRes.value.models : {};

      set({
        cities: cities.length > 0 ? cities : get().cities,
        materialsCatalog: materials,
        glazingCatalog: glazing,
        orientationsCatalog: orientations,
        shelterModelsCatalog: shelterModels,
        loading: { ...get().loading, init: false },
      });

      // If user had a city selected, fetch its climate
      const currentCity = get().selectedCity;
      if (currentCity) {
        const climate = await api.getClimate(currentCity);
        set({ climateData: climate });
        await get().runSimulation();
      }
    } catch (e: any) {
      // Graceful fallback to standard city metadata so UI remains interactive
      set({
        cities: [
          {
            id: "leh",
            display: "🏔️ Leh, Ladakh (Cold)",
            badge: "Cold",
            elevation: "3,524 m",
            winter_temp: "-18.5°C",
            summer_temp: "25.0°C",
            solar_ghi: "2,100 kWh/m²",
            hdd: 4850,
            source: "IMD Leh",
            type: "Alpine High Altitude",
            climate_type: "cold",
            climate_description: "Alpine Severe Cold",
          },
          {
            id: "jaisalmer",
            display: "🏜️ Jaisalmer (Hot-Dry)",
            badge: "Hot-Dry",
            elevation: "225 m",
            winter_temp: "7.0°C",
            summer_temp: "46.0°C",
            solar_ghi: "2,250 kWh/m²",
            hdd: 850,
            source: "IMD Jaisalmer",
            type: "Desert Arid",
            climate_type: "hot_dry",
            climate_description: "Hot & Arid Desert",
          },
          {
            id: "chennai",
            display: "🌊 Chennai (Humid)",
            badge: "Warm-Humid",
            elevation: "6 m",
            winter_temp: "20.0°C",
            summer_temp: "38.0°C",
            solar_ghi: "1,950 kWh/m²",
            hdd: 120,
            source: "IMD Chennai",
            type: "Coastal Tropical",
            climate_type: "hot_humid",
            climate_description: "Warm & Humid Coastal",
          },
          {
            id: "delhi",
            display: "🏙️ Delhi (Composite)",
            badge: "Composite",
            elevation: "216 m",
            winter_temp: "5.0°C",
            summer_temp: "44.0°C",
            solar_ghi: "1,900 kWh/m²",
            hdd: 1200,
            source: "IMD Delhi",
            type: "Subtropical Composite",
            climate_type: "composite",
            climate_description: "Composite Extreme",
          },
          {
            id: "bengaluru",
            display: "🌳 Bengaluru (Moderate)",
            badge: "Moderate",
            elevation: "920 m",
            winter_temp: "15.0°C",
            summer_temp: "34.0°C",
            solar_ghi: "1,850 kWh/m²",
            hdd: 450,
            source: "IMD Bengaluru",
            type: "Plateau Temperate",
            climate_type: "moderate",
            climate_description: "Temperate Moderate",
          },
        ],
        error: e.message || "Cannot connect to backend",
        loading: { ...get().loading, init: false },
      });
    }
  },

  runSimulation: async () => {
    const { selectedCity, design, people } = get();
    if (!selectedCity) {
      return;
    }
    set((s) => ({
      loading: { ...s.loading, simulation: true },
      error: null,
    }));
    try {
      const result = await api.runSimulation({
        city: selectedCity,
        length: design.length,
        width: design.width,
        height: design.height,
        wall_material: design.wallMaterial,
        insulation_thickness_m: design.insulationThicknessMm / 1000.0,
        window_area: design.windowArea,
        glazing: design.glazing,
        orientation: design.orientation,
        roof_type: design.roofType,
        occupants: people,
      });
      set((s) => ({
        simulationResult: result,
        lastSimulatedDesign: {
          ...design,
          city: selectedCity,
          occupants: people,
        },
        isSimulationStale: false,
        loading: { ...s.loading, simulation: false },
      }));
    } catch (e: any) {
      set((s) => ({
        error: e.message || "Simulation failed",
        loading: { ...s.loading, simulation: false },
      }));
    }
  },

  runOptimization: async (trials: number = 35) => {
    const { selectedCity, people, homeType } = get();
    if (!selectedCity) {
      set({ error: "Please choose a location to run Bayesian optimization." });
      return;
    }
    set((s) => ({
      loading: { ...s.loading, optimization: true },
      error: null,
    }));
    try {
      const rec = await api.runOptimization({
        city: selectedCity,
        people,
        home_type: homeType,
        n_trials: trials,
      });
      set((s) => ({
        optimizationResult: rec,
        loading: { ...s.loading, optimization: false },
      }));
    } catch (e: any) {
      set((s) => ({
        error: e.message || "Optimization failed",
        loading: { ...s.loading, optimization: false },
      }));
    }
  },

  runComparison: async () => {
    const { selectedCity, people, homeType } = get();
    if (!selectedCity) {
      return;
    }
    set((s) => ({
      loading: { ...s.loading, comparison: true },
      error: null,
    }));
    try {
      const comp = await api.runComparison({
        city: selectedCity,
        people,
        home_type: homeType,
      });
      set((s) => ({
        comparisonResult: comp,
        loading: { ...s.loading, comparison: false },
      }));
    } catch (e: any) {
      set((s) => ({
        error: e.message || "Comparison failed",
        loading: { ...s.loading, comparison: false },
      }));
    }
  },

  applyOptimizationRecommendation: () => {
    const { optimizationResult } = get();
    if (!optimizationResult) return;

    const newDesign: DesignState = {
      ...get().design,
      wallMaterial: optimizationResult.optimal_wall_material,
      insulationThicknessMm: Math.round(
        optimizationResult.optimal_insulation_mm
      ),
      windowArea:
        Math.round(optimizationResult.optimal_window_area_m2 * 10) / 10,
      glazing: optimizationResult.optimal_glazing,
      orientation: optimizationResult.optimal_orientation,
    };

    set({
      design: newDesign,
      simulationResult: optimizationResult.simulation_result,
      lastSimulatedDesign: {
        ...newDesign,
        city: get().selectedCity,
        occupants: get().people,
      },
      isSimulationStale: false,
    });
  },

  resetToNewDesign: async (params) => {
    const city = params?.city ?? get().selectedCity ?? "leh";
    const people = params?.people ?? 4;
    const homeType = params?.homeType ?? "Permanent";
    const archetype = params?.archetype ?? "recommended";

    // Set location and typology
    set({
      selectedCity: city,
      people,
      homeType,
      simulationResult: null,
      optimizationResult: null,
      comparisonResult: null,
      isSimulationStale: false,
      lastSimulatedDesign: null,
      activeTab: "designer",
    });

    // Auto-size and fetch climate if needed
    try {
      const [climate, geo] = await Promise.all([
        api.getClimate(city),
        api.autoSize(people, homeType),
      ]);
      const isCold = climate.climate_type === "cold";
      const modelKey =
        archetype === "compact"
          ? "compact_shelter"
          : archetype === "solar"
          ? "elongated_shelter"
          : isCold
          ? "rectangular_pitched"
          : "rectangular_flat";
      const catalogModel = get().shelterModelsCatalog[modelKey];
      const modelDimensions = catalogModel?.default_dimensions;
      set({
        climateData: climate,
        design: {
          length: modelDimensions?.length ?? geo.length_m,
          width: modelDimensions?.width ?? geo.width_m,
          height: modelDimensions?.height ?? geo.height_m,
          roofType: catalogModel?.roof_type ?? (isCold ? "pitched" : "flat"),
          wallMaterial: isCold ? "brick" : "stone",
          roofMaterial: "insulated_metal",
          insulationThicknessMm: archetype === "standard" ? 60 : isCold ? 80 : 40,
          windowArea: archetype === "solar" ? 4.5 : isCold ? 2.5 : 1.8,
          glazing: isCold ? "double_low_e" : "double_clear",
          orientation: "south",
        },
      });
    } catch {
      await get().autoSizeDesign();
    }
  },
}));
