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
import { Procurement } from './pages/Procurement';
import { Finance } from './pages/Finance';
import { HR } from './pages/HR';
import { Documents } from './pages/Documents';
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
          <Route path="/procurement" element={<Procurement />} />
          <Route path="/finance" element={<Finance />} />
          <Route path="/hr" element={<HR />} />
          <Route path="/documents" element={<Documents />} />
        </Routes>
      </Layout>

      {/* FLEET-ONE Chat Integration */}
      <FleetOneContainer />
    </BrowserRouter>
  );
}

export default App;
