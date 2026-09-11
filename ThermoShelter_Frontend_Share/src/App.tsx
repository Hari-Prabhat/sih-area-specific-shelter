import React from "react";
import { AppShell } from "./components/layout/AppShell";
import { useDesignStore } from "./store/designStore";
import { OverviewPage } from "./pages/OverviewPage";
import { NewDesignPage } from "./pages/NewDesignPage";
import { ClimatePage } from "./pages/ClimatePage";
import { DesignStudioPage } from "./pages/DesignStudioPage";
import { SimulationPage } from "./pages/SimulationPage";
import { OptimizationPage } from "./pages/OptimizationPage";
import { ComparisonPage } from "./pages/ComparisonPage";
import { MaterialsPage } from "./pages/MaterialsPage";
import { SensitivityPage } from "./pages/SensitivityPage";
import { DigitalTwinPage } from "./pages/DigitalTwinPage";
import { FloorplanPage } from "./pages/FloorplanPage";
import { ValidationPage } from "./pages/ValidationPage";
import { ReportPage } from "./pages/ReportPage";

export const App: React.FC = () => {
  const { activeTab } = useDesignStore();

  const renderActivePage = () => {
    switch (activeTab) {
      case "overview":
        return <OverviewPage />;
      case "new_design":
        return <NewDesignPage />;
      case "climate":
        return <ClimatePage />;
      case "designer":
        return <DesignStudioPage />;
      case "simulation":
        return <SimulationPage />;
      case "optimization":
        return <OptimizationPage />;
      case "compare":
        return <ComparisonPage />;
      case "materials":
        return <MaterialsPage />;
      case "sensitivity":
        return <SensitivityPage />;
      case "twin3d":
        return <DigitalTwinPage />;
      case "floorplan":
        return <FloorplanPage />;
      case "validation":
        return <ValidationPage />;
      case "report":
        return <ReportPage />;
      default:
        return <OverviewPage />;
    }
  };

  return <AppShell>{renderActivePage()}</AppShell>;
};

export default App;
