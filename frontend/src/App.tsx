import React, { useState } from 'react';
import type { AppViewMode } from './types';
import { DesignStudioProvider } from './context/DesignStudioContext';
import { Header } from './components/common/Header';
import { Navigation } from './components/common/Navigation';
import { DesignStudio } from './components/studio/DesignStudio';
import { PlaceholderPage } from './components/placeholders/PlaceholderPage';
import { ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppViewMode>('design');

  return (
    <DesignStudioProvider>
      <div className="min-h-screen bg-[#0a0f1d] text-slate-100 flex flex-col selection:bg-sky-500/30 selection:text-sky-200">
        {/* Engineering Top Bar */}
        <Header />

        {/* Primary View Navigation */}
        <Navigation currentView={currentView} onViewChange={setCurrentView} />

        {/* Main Work Area */}
        <main className="flex-1">
          {currentView === 'design' ? (
            <DesignStudio />
          ) : (
            <PlaceholderPage
              view={currentView}
              onNavigateToDesign={() => setCurrentView('design')}
            />
          )}
        </main>

        {/* Engineering Platform Footer */}
        <footer className="border-t border-slate-800/80 bg-slate-950/80 text-slate-500 text-xs py-6 mt-12 font-mono-data">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>
                ThermoShelter AI • Passive Building Physics Digital Twin & Design Optimizer
              </span>
            </div>

            <div className="flex items-center gap-4 text-[11px]">
              <span>SP 41 & NBC 2016 Compliant</span>
              <span>•</span>
              <span>ISO 6946 Envelope Engine</span>
              <span>•</span>
              <span className="text-amber-400/80">Stage-1 Design Studio UI</span>
            </div>
          </div>
        </footer>
      </div>
    </DesignStudioProvider>
  );
};

export default App;
