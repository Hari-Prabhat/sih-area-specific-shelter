import { create } from "zustand";
import { api } from "../api/client";
import {
  City,
  ClimateData,
  SimulationResult,
  OptimizationResult,
  ComparisonResult,
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

  // Design parameters
  design: DesignState;

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
      set({ selectedCity: "", climateData: null, simulationResult: null, optimizationResult: null, comparisonResult: null });
      return;
    }
    set((s) => ({
      selectedCity: city,
      simulationResult: null,
      optimizationResult: null,
      comparisonResult: null,
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
    set({ people });
    get().autoSizeDesign();
  },

  setHomeType: (homeType: "Permanent" | "Temporary") => {
    set({ homeType });
    get().autoSizeDesign();
  },

  updateDesign: (patch: Partial<DesignState>) => {
    set((s) => ({
      design: { ...s.design, ...patch },
    }));
  },

  autoSizeDesign: async () => {
    const { people, homeType, design } = get();
    try {
      const geo = await api.autoSize(people, homeType);
      set({
        design: {
          ...design,
          length: geo.length_m,
          width: geo.width_m,
          height: geo.height_m,
        },
      });
    } catch (e) {
      // fallback local calculation
      const floorArea = Math.max(12.0, people * 4.5);
      const length = Math.round(Math.sqrt(floorArea * 1.3) * 10) / 10;
      const width = Math.round((floorArea / length) * 10) / 10;
      set({
        design: {
          ...design,
          length,
          width,
          height: homeType === "Temporary" ? 2.6 : 2.8,
        },
      });
    }
  },

  fetchInitialData: async () => {
    set((s) => ({ loading: { ...s.loading, init: true }, error: null }));
    try {
      const citiesRes = await api.getCities();
      set({
        cities: citiesRes.cities,
        loading: { ...get().loading, init: false },
      });

      // If user had a city selected, fetch its climate and simulate; otherwise wait for user to choose location
      const currentCity = get().selectedCity;
      if (currentCity) {
        const climate = await api.getClimate(currentCity);
        set({ climateData: climate });
        await get().runSimulation();
      }
    } catch (e: any) {
      // Graceful fallback to standard city metadata so UI remains interactive even before backend is ready
      set({
        cities: [
          { id: "leh", display: "🏔️ Leh, Ladakh (Cold)", badge: "Cold", elevation: "3,524 m", winter_temp: "-18.5°C", summer_temp: "25.0°C", solar_ghi: "2,100 kWh/m²", hdd: 4850, source: "IMD Leh", type: "Alpine High Altitude", climate_type: "cold", climate_description: "Alpine Severe Cold" },
          { id: "jaisalmer", display: "🏜️ Jaisalmer (Hot-Dry)", badge: "Hot-Dry", elevation: "225 m", winter_temp: "7.0°C", summer_temp: "46.0°C", solar_ghi: "2,250 kWh/m²", hdd: 850, source: "IMD Jaisalmer", type: "Desert Arid", climate_type: "hot_dry", climate_description: "Hot & Arid Desert" },
          { id: "chennai", display: "🌊 Chennai (Humid)", badge: "Warm-Humid", elevation: "6 m", winter_temp: "20.0°C", summer_temp: "38.0°C", solar_ghi: "1,950 kWh/m²", hdd: 120, source: "IMD Chennai", type: "Coastal Tropical", climate_type: "hot_humid", climate_description: "Warm & Humid Coastal" },
          { id: "delhi", display: "🏙️ Delhi (Composite)", badge: "Composite", elevation: "216 m", winter_temp: "5.0°C", summer_temp: "44.0°C", solar_ghi: "1,900 kWh/m²", hdd: 1200, source: "IMD Delhi", type: "Subtropical Composite", climate_type: "composite", climate_description: "Composite Extreme" },
          { id: "bengaluru", display: "🌳 Bengaluru (Moderate)", badge: "Moderate", elevation: "920 m", winter_temp: "15.0°C", summer_temp: "34.0°C", solar_ghi: "1,850 kWh/m²", hdd: 450, source: "IMD Bengaluru", type: "Plateau Temperate", climate_type: "moderate", climate_description: "Temperate Moderate" },
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

    set((s) => ({
      design: {
        ...s.design,
        wallMaterial: optimizationResult.optimal_wall_material,
        insulationThicknessMm: Math.round(
          optimizationResult.optimal_insulation_mm
        ),
        windowArea:
          Math.round(optimizationResult.optimal_window_area_m2 * 10) / 10,
        glazing: optimizationResult.optimal_glazing,
        orientation: optimizationResult.optimal_orientation,
      },
      simulationResult: optimizationResult.simulation_result,
    }));
  },
}));
