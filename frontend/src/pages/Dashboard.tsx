/**
 * Dashboard Page
 * Main overview with KPIs and fleet status
 */

import { Card, Title, Text, Metric, Grid, BarChart, DonutChart } from '@tremor/react';

export function Dashboard() {
  // Mock data - will be replaced with real API calls
  const fleetData = [
    { name: 'Operational', value: 20, color: 'emerald' },
    { name: 'Maintenance', value: 3, color: 'orange' },
    { name: 'Workshop', value: 2, color: 'purple' },
  ];

  const availabilityData = [
    { month: 'Jan', availability: 92 },
    { month: 'Feb', availability: 89 },
    { month: 'Mar', availability: 94 },
    { month: 'Apr', availability: 91 },
    { month: 'Mai', availability: 93 },
    { month: 'Jun', availability: 90 },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <Title>FLEET-ONE Dashboard</Title>
        <Text>Echtzeit-Übersicht der Flottenmanagement-Systeme</Text>
      </div>

      {/* KPI Cards */}
      <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
        <Card>
          <Text>Gesamtflotte</Text>
          <Metric>25 Loks</Metric>
        </Card>
        <Card>
          <Text>Verfügbarkeit</Text>
          <Metric>92.5%</Metric>
          <Text className="text-emerald-600">↑ 2.3% vs. letzter Monat</Text>
        </Card>
        <Card>
          <Text>Aktive Werkstattaufträge</Text>
          <Metric>12</Metric>
        </Card>
        <Card>
          <Text>Fällige HU-Fristen</Text>
          <Metric>3</Metric>
          <Text className="text-orange-600">In nächsten 14 Tagen</Text>
        </Card>
      </Grid>

      {/* Charts */}
      <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
        <Card>
          <Title>Flottenstatus</Title>
          <DonutChart
            className="mt-6"
            data={fleetData}
            category="value"
            index="name"
            colors={['emerald', 'orange', 'purple']}
          />
        </Card>

        <Card>
          <Title>Verfügbarkeit (letzte 6 Monate)</Title>
          <BarChart
            className="mt-6"
            data={availabilityData}
            index="month"
            categories={['availability']}
            colors={['blue']}
            valueFormatter={(value) => `${value}%`}
            yAxisWidth={40}
          />
        </Card>
      </Grid>

      {/* Recent Activity */}
      <Card>
        <Title>Letzte Aktivitäten</Title>
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between py-2 border-b">
            <div>
              <Text className="font-medium">Werkstattauftrag WO-12345 erstellt</Text>
              <Text className="text-sm text-gray-500">BR185-042 • Werk München</Text>
            </div>
            <Text className="text-sm text-gray-500">vor 2 Stunden</Text>
          </div>
          <div className="flex items-center justify-between py-2 border-b">
            <div>
              <Text className="font-medium">HU-Frist aktualisiert</Text>
              <Text className="text-sm text-gray-500">BR189-033 • Fällig: 10.12.2025</Text>
            </div>
            <Text className="text-sm text-gray-500">vor 4 Stunden</Text>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <Text className="font-medium">Bestellung PR-6789 genehmigt</Text>
              <Text className="text-sm text-gray-500">Bremsscheiben • 50 Stück</Text>
            </div>
            <Text className="text-sm text-gray-500">vor 6 Stunden</Text>
          </div>
        </div>
      </Card>
    </div>
  );
}
