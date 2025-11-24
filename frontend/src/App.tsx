/**
 * RailFleet Manager - Main Application
 * Fleet Management System with FLEET-ONE AI Agent Integration
 */

import { useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { FleetOneContainer } from './components/FleetOne/FleetOneContainer';
import { useFleetOneStore } from './stores/fleetOneStore';

function App() {
  const { initSession } = useFleetOneStore();

  useEffect(() => {
    // Initialize FLEET-ONE session
    // TODO: Get user from auth context
    const userId = 'demo_dispatcher';
    const userRole = 'dispatcher';

    initSession(userId, userRole as any);
  }, [initSession]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">RF</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  RailFleet Manager
                </h1>
                <p className="text-sm text-gray-500">
                  Powered by FLEET-ONE AI
                </p>
              </div>
            </div>

            {/* User info */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  Demo Dispatcher
                </p>
                <p className="text-xs text-gray-500">Disponent</p>
              </div>
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium">DD</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main>
        <Dashboard />
      </main>

      {/* FLEET-ONE Chat Integration */}
      <FleetOneContainer />

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="px-6 py-4">
          <p className="text-center text-sm text-gray-500">
            RailFleet Manager © 2025 | Phase 3 (WP15-WP25) | FLEET-ONE Agent v1.0.0
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
