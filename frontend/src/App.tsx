import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { BackendStatusProvider } from './context/BackendStatusContext';
import { AuthProvider } from './context/AuthContext';
import { RealtimeEventProvider } from './context/RealtimeEventContext';
import { Header } from './components/common/Header';
import { Sidebar, NavView } from './components/common/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { CameraRegistryPage } from './pages/CameraRegistryPage';
import { ANPRVehiclesPage } from './pages/ANPRVehiclesPage';
import { GISMapPage } from './pages/GISMapPage';
import { AlertsIncidentsPage } from './pages/AlertsIncidentsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { VehicleIntelligencePage } from './pages/VehicleIntelligencePage';

export const AppContent: React.FC = () => {
  const [activeView, setActiveView] = useState<NavView>('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  const handleNavigate = (view: NavView) => {
    setActiveView(view);
    setIsMobileMenuOpen(false); // Close mobile drawer upon selection
  };

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
      case 'coverage_gaps':
        return <GISMapPage />;
      case 'vehicle_tracking':
      case 'investigations':
        return <VehicleIntelligencePage />;
      case 'alerts':
      case 'incidents':
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
    <div className="command-center-app">
      {/* Top Command Bar */}
      <Header
        isMobileMenuOpen={isMobileMenuOpen}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      />

      {/* Main Layout Body */}
      <div className="app-main-body">
        {/* Mobile Backdrop Overlay */}
        {isMobileMenuOpen && (
          <div
            className="mobile-sidebar-backdrop"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Global Multi-Section Sidebar */}
        <Sidebar
          activeView={activeView}
          onNavigate={handleNavigate}
          isMobileOpen={isMobileMenuOpen}
          onCloseMobile={() => setIsMobileMenuOpen(false)}
        />

        {/* Viewport Canvas */}
        <main className="app-viewport-content" role="main">
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BackendStatusProvider>
        <AuthProvider>
          <RealtimeEventProvider>
            <AppContent />
          </RealtimeEventProvider>
        </AuthProvider>
      </BackendStatusProvider>
    </ThemeProvider>
  );
};

export default App;
