/**
 * RailFleet Manager - Main Application
 * Fleet Management System with FLEET-ONE AI Agent Integration
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { FleetOverview } from './pages/FleetOverview';
import { Maintenance } from './pages/Maintenance';
import { Workshop } from './pages/Workshop';
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
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/fleet" element={<FleetOverview />} />
          <Route path="/maintenance" element={<Maintenance />} />
          <Route path="/workshop" element={<Workshop />} />
        </Routes>
      </Layout>

      {/* FLEET-ONE Chat Integration */}
      <FleetOneContainer />
    </BrowserRouter>
  );
}

export default App;
