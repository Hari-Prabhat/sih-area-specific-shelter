import React, { useState, useCallback } from 'react';
import type {
  ShelterRequirements,
  ShelterDesign,
  LocationSelection,
  MissionRequirements,
  PrioritySelection,
  AvailableResources,
  DesignPriority,
  PriorityImportance,
} from '../types';
import { generateDesign } from '../lib/api/design';
import { PRESET_LOCATIONS } from '../lib/api/climate';
import type { ErrorType } from '../components/common/ErrorAlert';
import { DesignStudioContext } from './contextDefinition';
import type { ValidationErrors } from './contextDefinition';

const INITIAL_LOCATION: LocationSelection = {
  mode: 'preset',
  locationId: 'leh',
  displayName: 'Leh, Ladakh, India',
  elevationM: 3524,
  latitude: 34.1526,
  longitude: 77.5771,
};

const INITIAL_MISSION: MissionRequirements = {
  occupants: 4,
  purpose: 'Residential',
  deploymentType: 'Permanent',
  duration: 'Years',
};

const INITIAL_PRIORITIES: PrioritySelection[] = [
  { priority: 'Thermal Comfort', importance: 'Primary' },
  { priority: 'Energy Independence', importance: 'Primary' },
];

const INITIAL_RESOURCES: AvailableResources = {
  energy: ['Solar'],
  materials: ['Local Stone', 'Insulation Panels'],
};

export const DesignStudioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [step, setStep] = useState<number>(1);
  const [viewMode, setViewMode] = useState<'studio' | 'result'>('studio');
  const [maxAccessibleStep, setMaxAccessibleStep] = useState<number>(1);

  const [location, setLocation] = useState<LocationSelection>(INITIAL_LOCATION);
  const [mission, setMission] = useState<MissionRequirements>(INITIAL_MISSION);
  const [priorities, setPriorities] = useState<PrioritySelection[]>(INITIAL_PRIORITIES);
  const [resources, setResources] = useState<AvailableResources>(INITIAL_RESOURCES);
  const [isDemoScenario, setIsDemoScenario] = useState<boolean>(false);

  const [generatedDesign, setGeneratedDesign] = useState<ShelterDesign | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingStage, setLoadingStage] = useState<string>('');
  const [error, setError] = useState<{ type: ErrorType; message: string } | null>(null);
  const [errors, setErrors] = useState<ValidationErrors>({});

  const clearError = () => setError(null);

  // Validation rules per step
  const validateStep = useCallback(
    (stepToValidate: number): { isValid: boolean; newErrors: ValidationErrors } => {
      const errs: ValidationErrors = {};

      if (stepToValidate === 1) {
        if (!location.displayName || location.displayName.trim() === '') {
          errs.location = 'Please select a preset location or enter valid coordinates/place name.';
        }
      }

      if (stepToValidate === 2) {
        if (!mission.occupants || mission.occupants <= 0 || !Number.isInteger(mission.occupants)) {
          errs.occupants = 'Occupants must be a strictly positive integer (1 or more).';
        }
        if (!mission.purpose) {
          errs.purpose = 'Shelter purpose specification is required.';
        }
        if (!mission.deploymentType) {
          errs.deploymentType = 'Deployment type (Temporary, Seasonal, Permanent) is required.';
        }
        if (!mission.duration) {
          errs.duration = 'Deployment duration selection is required.';
        }
      }

      if (stepToValidate === 3) {
        if (!priorities || priorities.length === 0) {
          errs.priorities = 'Select at least one engineering design priority.';
        }
      }

      // Step 4 resources are optional by definition in specification

      setErrors(errs);
      return { isValid: Object.keys(errs).length === 0, newErrors: errs };
    },
    [location, mission, priorities]
  );

  const validateCurrentStep = useCallback(() => {
    return validateStep(step).isValid;
  }, [validateStep, step]);

  const goToStep = (targetStep: number) => {
    if (targetStep < step || targetStep <= maxAccessibleStep) {
      setStep(targetStep);
      setViewMode('studio');
      setErrors({});
      setError(null);
    }
  };

  const nextStep = (): boolean => {
    const { isValid } = validateStep(step);
    if (!isValid) return false;

    if (step < 5) {
      const next = step + 1;
      setStep(next);
      setMaxAccessibleStep((currentMax) => Math.max(currentMax, next));
      return true;
    }
    return true;
  };

  const prevStep = () => {
    if (step > 1) {
      setStep((s) => s - 1);
      setErrors({});
    }
  };

  const resetStudio = () => {
    setStep(1);
    setViewMode('studio');
    setMaxAccessibleStep(1);
    setLocation(INITIAL_LOCATION);
    setMission(INITIAL_MISSION);
    setPriorities(INITIAL_PRIORITIES);
    setResources({ energy: [], materials: [] });
    setIsDemoScenario(false);
    setGeneratedDesign(null);
    setError(null);
    setErrors({});
  };

  const loadGoldenDemo = () => {
    const lehPreset = PRESET_LOCATIONS.find((l) => l.id === 'leh') || {
      id: 'leh',
      name: 'Leh',
      region: 'Ladakh',
      elevationM: 3524,
      latitude: 34.1526,
      longitude: 77.5771,
    };

    setLocation({
      mode: 'preset',
      locationId: 'leh',
      displayName: 'Leh, Ladakh, India',
      elevationM: lehPreset.elevationM,
      latitude: lehPreset.latitude,
      longitude: lehPreset.longitude,
    });

    setMission({
      occupants: 4,
      purpose: 'Residential',
      deploymentType: 'Permanent',
      duration: 'Years',
    });

    setPriorities([
      { priority: 'Thermal Comfort', importance: 'Primary' },
      { priority: 'Energy Independence', importance: 'Primary' },
    ]);

    setResources({
      energy: ['Solar'],
      materials: ['Local Stone', 'Timber', 'Insulation Panels'],
      customMaterialNotes: 'Locally quarried granite & sun-dried mud bricks',
    });

    setIsDemoScenario(true);
    setMaxAccessibleStep(5);
    setStep(5); // Jump straight to review for rapid demo inspection
    setViewMode('studio');
    setErrors({});
    setError(null);
  };

  const setMissionField = <K extends keyof MissionRequirements>(
    field: K,
    value: MissionRequirements[K]
  ) => {
    setMission((prev) => ({ ...prev, [field]: value }));
    setIsDemoScenario(false);
  };

  const togglePriority = (p: DesignPriority) => {
    setIsDemoScenario(false);
    setPriorities((prev) => {
      const exists = prev.find((item) => item.priority === p);
      if (exists) {
        return prev.filter((item) => item.priority !== p);
      } else {
        return [...prev, { priority: p, importance: 'Primary' }];
      }
    });
  };

  const setPriorityImportance = (p: DesignPriority, importance: PriorityImportance) => {
    setIsDemoScenario(false);
    setPriorities((prev) =>
      prev.map((item) => (item.priority === p ? { ...item, importance } : item))
    );
  };

  const toggleEnergyResource = (res: AvailableResources['energy'][number]) => {
    setIsDemoScenario(false);
    setResources((prev) => {
      const has = prev.energy.includes(res);
      return {
        ...prev,
        energy: has ? prev.energy.filter((r) => r !== res) : [...prev.energy, res],
      };
    });
  };

  const toggleMaterialResource = (mat: AvailableResources['materials'][number]) => {
    setIsDemoScenario(false);
    setResources((prev) => {
      const has = prev.materials.includes(mat);
      return {
        ...prev,
        materials: has ? prev.materials.filter((m) => m !== mat) : [...prev.materials, mat],
      };
    });
  };

  const setCustomMaterialNotes = (notes: string) => {
    setResources((prev) => ({ ...prev, customMaterialNotes: notes }));
  };

  const handleGenerateDesign = async () => {
    // Validate entire requirements contract before submission
    for (let s = 1; s <= 3; s++) {
      const { isValid, newErrors } = validateStep(s);
      if (!isValid) {
        setStep(s);
        setError({
          type: 'incomplete_requirements',
          message: Object.values(newErrors)[0] || 'Please complete all required fields.',
        });
        return;
      }
    }

    try {
      setIsLoading(true);
      setError(null);

      // Distinct engineering synthesis processing stages
      setLoadingStage('Preparing site profile & boundary conditions...');
      await new Promise((r) => setTimeout(r, 400));

      setLoadingStage('Analyzing microclimate & solar exposure...');
      await new Promise((r) => setTimeout(r, 450));

      setLoadingStage('Generating shelter configuration & envelope assembly...');

      const reqs: ShelterRequirements = {
        location,
        mission,
        priorities,
        resources,
        isDemoScenario,
      };

      const result = await generateDesign(reqs);
      setGeneratedDesign(result);
      setViewMode('result');
    } catch (err: unknown) {
      setError({
        type: 'design_generation_failure',
        message: err instanceof Error ? err.message : 'Unexpected synthesis pipeline error occurred.',
      });
    } finally {
      setIsLoading(false);
      setLoadingStage('');
    }
  };

  return (
    <DesignStudioContext.Provider
      value={{
        step,
        viewMode,
        maxAccessibleStep,
        goToStep,
        nextStep,
        prevStep,
        resetStudio,
        location,
        mission,
        priorities,
        resources,
        isDemoScenario,
        setLocation,
        setMissionField,
        togglePriority,
        setPriorityImportance,
        toggleEnergyResource,
        toggleMaterialResource,
        setCustomMaterialNotes,
        loadGoldenDemo,
        generatedDesign,
        isLoading,
        loadingStage,
        error,
        clearError,
        handleGenerateDesign,
        errors,
        validateCurrentStep,
      }}
    >
      {children}
    </DesignStudioContext.Provider>
  );
};
