import React from 'react';
import { useDesignStudio } from '../../context';
import { StepProgress } from '../common/StepProgress';
import { Step1Location } from './Step1Location';
import { Step2Mission } from './Step2Mission';
import { Step3Priorities } from './Step3Priorities';
import { Step4Resources } from './Step4Resources';
import { Step5Review } from './Step5Review';
import { GeneratedDesignView } from './GeneratedDesignView';
import { LoadingOverlay } from '../common/LoadingOverlay';
import { ErrorAlert } from '../common/ErrorAlert';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const DesignStudio: React.FC = () => {
  const {
    step,
    viewMode,
    maxAccessibleStep,
    goToStep,
    nextStep,
    prevStep,
    isLoading,
    loadingStage,
    error,
    clearError,
  } = useDesignStudio();

  if (viewMode === 'result') {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <GeneratedDesignView />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Loading Overlay */}
      {isLoading && <LoadingOverlay stageText={loadingStage} isMockMode={true} />}

      {/* Multi-step progress tracker */}
      <StepProgress
        currentStep={step}
        onStepClick={goToStep}
        maxAccessibleStep={maxAccessibleStep}
      />

      {/* Global Error Banner */}
      {error && (
        <ErrorAlert
          type={error.type}
          message={error.message}
          actionLabel="Dismiss"
          onAction={clearError}
        />
      )}

      {/* Active Step Content Container */}
      <div className="bg-slate-900/70 border border-slate-700/70 rounded-xl p-6 sm:p-8 shadow-xl">
        {step === 1 && <Step1Location />}
        {step === 2 && <Step2Mission />}
        {step === 3 && <Step3Priorities />}
        {step === 4 && <Step4Resources />}
        {step === 5 && <Step5Review />}

        {/* Step Navigation Controls (Steps 1-4) */}
        {step < 5 && (
          <div className="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={prevStep}
              disabled={step === 1}
              className={`flex items-center gap-1.5 px-4 py-2 rounded text-xs font-mono-data font-semibold uppercase transition-colors ${
                step === 1
                  ? 'text-slate-600 bg-slate-950/40 border border-slate-800/40 cursor-not-allowed'
                  : 'text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 cursor-pointer'
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
              <span>PREVIOUS</span>
            </button>

            <button
              type="button"
              onClick={nextStep}
              className="flex items-center gap-1.5 px-6 py-2.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-mono-data text-xs font-bold uppercase tracking-wider transition-all shadow-md shadow-sky-600/20 cursor-pointer hover:translate-x-0.5"
            >
              <span>CONTINUE</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
