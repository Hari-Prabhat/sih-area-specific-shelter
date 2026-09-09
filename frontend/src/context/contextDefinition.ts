import { createContext } from 'react';
import type {
  ShelterDesign,
  LocationSelection,
  MissionRequirements,
  PrioritySelection,
  AvailableResources,
  DesignPriority,
  PriorityImportance,
} from '../types';
import type { ErrorType } from '../components/common/ErrorAlert';

export interface ValidationErrors {
  location?: string;
  occupants?: string;
  purpose?: string;
  deploymentType?: string;
  duration?: string;
  priorities?: string;
}

export interface DesignStudioContextType {
  // Navigation & View
  step: number;
  viewMode: 'studio' | 'result';
  maxAccessibleStep: number;
  goToStep: (targetStep: number) => void;
  nextStep: () => boolean;
  prevStep: () => void;
  resetStudio: () => void;

  // Form State
  location: LocationSelection;
  mission: MissionRequirements;
  priorities: PrioritySelection[];
  resources: AvailableResources;
  isDemoScenario: boolean;

  // Setters
  setLocation: (loc: LocationSelection) => void;
  setMissionField: <K extends keyof MissionRequirements>(field: K, value: MissionRequirements[K]) => void;
  togglePriority: (priority: DesignPriority) => void;
  setPriorityImportance: (priority: DesignPriority, importance: PriorityImportance) => void;
  toggleEnergyResource: (resource: AvailableResources['energy'][number]) => void;
  toggleMaterialResource: (resource: AvailableResources['materials'][number]) => void;
  setCustomMaterialNotes: (notes: string) => void;

  // Golden Demo
  loadGoldenDemo: () => void;

  // Processing & Generation
  generatedDesign: ShelterDesign | null;
  isLoading: boolean;
  loadingStage: string;
  error: { type: ErrorType; message: string } | null;
  clearError: () => void;
  handleGenerateDesign: () => Promise<void>;

  // Validation
  errors: ValidationErrors;
  validateCurrentStep: () => boolean;
}

export const DesignStudioContext = createContext<DesignStudioContextType | undefined>(undefined);
