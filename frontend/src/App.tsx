import React, { useState } from 'react';
import { BackendStatusProvider } from './context/BackendStatusContext';
import { AuthProvider } from './context/AuthContext';
import { Header } from './components/common/Header';
import { Sidebar, NavView } from './components/common/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { CameraRegistryPage } from './pages/CameraRegistryPage';
import { ANPRVehiclesPage } from './pages/ANPRVehiclesPage';
import { GISMapPage } from './pages/GISMapPage';
import { AlertsIncidentsPage } from './pages/AlertsIncidentsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<NavView>('dashboard');

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardPage />;
      case 'live_monitoring':
        return <LiveMonitoringPage />;
      case 'camera_registry':
        return <CameraRegistryPage />;
      case 'anpr_vehicles':
        return <ANPRVehiclesPage />;
      case 'gis_map':
      case 'vehicle_tracking':
      case 'coverage_gaps':
        return <GISMapPage />;
      case 'alerts':
      case 'incidents':
      case 'investigations':
        return <AlertsIncidentsPage />;
      case 'system_health':
      case 'stream_health':
      case 'audit_logs':
        return <SystemHealthPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <BackendStatusProvider>
      <AuthProvider>
        <div className="command-center-app">
          {/* Top Command Bar */}
          <Header />

          {/* Main Layout Body */}
          <div className="app-main-body">
            {/* Global Multi-Section Sidebar */}
            <Sidebar activeView={activeView} onNavigate={setActiveView} />

            {/* Viewport Canvas */}
            <main className="app-viewport-content" role="main">
              {renderActiveView()}
            </main>
          </div>
        </div>
      </AuthProvider>
    </BackendStatusProvider>
  );
};

export default App;
