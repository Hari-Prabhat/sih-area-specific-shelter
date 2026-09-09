import { useContext } from 'react';
import { DesignStudioContext } from './contextDefinition';
import type { DesignStudioContextType } from './contextDefinition';

export const useDesignStudio = (): DesignStudioContextType => {
  const context = useContext(DesignStudioContext);
  if (!context) {
    throw new Error('useDesignStudio must be used within a DesignStudioProvider');
  }
  return context;
};
