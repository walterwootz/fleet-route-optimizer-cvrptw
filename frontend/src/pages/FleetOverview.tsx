/**
 * Fleet Overview Page
 * Table view of all locomotives with filters
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, TextInput, Select, SelectItem, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell } from '@tremor/react';
import { Search, Filter } from 'lucide-react';

// Mock data - will be replaced with API calls
const mockLocomotives = [
  { id: 'BR185-042', series: 'BR 185', status: 'operational', location: 'Berlin', last_maintenance: '2024-06-15', planned_workshop_flag: false },
  { id: 'BR189-033', series: 'BR 189', status: 'maintenance_due', location: 'Hamburg', last_maintenance: '2024-07-20', planned_workshop_flag: true },
  { id: 'BR152-123', series: 'BR 152', status: 'maintenance_due', location: 'München', last_maintenance: '2024-05-10', planned_workshop_flag: false },
  { id: 'BR185-055', series: 'BR 185', status: 'in_workshop', location: 'Leipzig', last_maintenance: '2024-08-01', planned_workshop_flag: true },
  { id: 'BR189-012', series: 'BR 189', status: 'operational', location: 'Berlin', last_maintenance: '2024-09-15', planned_workshop_flag: false },
  { id: 'BR152-087', series: 'BR 152', status: 'operational', location: 'München', last_maintenance: '2024-08-22', planned_workshop_flag: false },
  { id: 'BR185-091', series: 'BR 185', status: 'planned_for_workshop', location: 'Hamburg', last_maintenance: '2024-04-30', planned_workshop_flag: true },
  { id: 'BR189-045', series: 'BR 189', status: 'operational', location: 'Leipzig', last_maintenance: '2024-10-01', planned_workshop_flag: false },
  { id: 'BR152-156', series: 'BR 152', status: 'maintenance_due', location: 'Berlin', last_maintenance: '2024-03-15', planned_workshop_flag: false },
  { id: 'BR185-103', series: 'BR 185', status: 'operational', location: 'München', last_maintenance: '2024-09-05', planned_workshop_flag: false },
];

export function FleetOverview() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [seriesFilter, setSeriesFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');

  // Filter locomotives
  const filteredLocomotives = mockLocomotives.filter((loco) => {
    const matchesSearch = loco.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || loco.status === statusFilter;
    const matchesSeries = seriesFilter === 'all' || loco.series === seriesFilter;
    const matchesLocation = locationFilter === 'all' || loco.location === locationFilter;

    return matchesSearch && matchesStatus && matchesSeries && matchesLocation;
  });

  // Get unique values for filters
  const uniqueSeries = Array.from(new Set(mockLocomotives.map(l => l.series)));
  const uniqueLocations = Array.from(new Set(mockLocomotives.map(l => l.location)));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Flottenübersicht</Title>
        <Text>Alle Lokomotiven im Überblick</Text>
      </div>

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Filter size={20} className="text-gray-500" />
            <Text className="font-medium">Filter</Text>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <TextInput
              icon={Search}
              placeholder="Suche nach ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectItem value="all">Alle Status</SelectItem>
              <SelectItem value="operational">Operational</SelectItem>
              <SelectItem value="maintenance_due">Maintenance Due</SelectItem>
              <SelectItem value="in_workshop">In Workshop</SelectItem>
              <SelectItem value="planned_for_workshop">Planned for Workshop</SelectItem>
            </Select>

            {/* Series Filter */}
            <Select value={seriesFilter} onValueChange={setSeriesFilter}>
              <SelectItem value="all">Alle Baureihen</SelectItem>
              {uniqueSeries.map((series) => (
                <SelectItem key={series} value={series}>
                  {series}
                </SelectItem>
              ))}
            </Select>

            {/* Location Filter */}
            <Select value={locationFilter} onValueChange={setLocationFilter}>
              <SelectItem value="all">Alle Standorte</SelectItem>
              {uniqueLocations.map((location) => (
                <SelectItem key={location} value={location}>
                  {location}
                </SelectItem>
              ))}
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Text className="text-sm text-gray-600">
              {filteredLocomotives.length} von {mockLocomotives.length} Lokomotiven
            </Text>
            {(searchTerm || statusFilter !== 'all' || seriesFilter !== 'all' || locationFilter !== 'all') && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('all');
                  setSeriesFilter('all');
                  setLocationFilter('all');
                }}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Filter zurücksetzen
              </button>
            )}
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>ID</TableHeaderCell>
              <TableHeaderCell>Baureihe</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Standort</TableHeaderCell>
              <TableHeaderCell>Letzte Wartung</TableHeaderCell>
              <TableHeaderCell>Werkstatt geplant</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredLocomotives.map((loco) => (
              <TableRow key={loco.id}>
                <TableCell>
                  <span className="font-mono font-medium">{loco.id}</span>
                </TableCell>
                <TableCell>{loco.series}</TableCell>
                <TableCell>
                  <StatusBadge status={loco.status} />
                </TableCell>
                <TableCell>{loco.location}</TableCell>
                <TableCell>
                  {new Date(loco.last_maintenance).toLocaleDateString('de-DE')}
                </TableCell>
                <TableCell>
                  {loco.planned_workshop_flag ? (
                    <Badge color="blue">Ja</Badge>
                  ) : (
                    <Badge color="gray">Nein</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {filteredLocomotives.length === 0 && (
          <div className="text-center py-8">
            <Text className="text-gray-500">
              Keine Lokomotiven gefunden. Passen Sie die Filter an.
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}

// Helper component for status badges
function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: 'green' | 'red' | 'purple' | 'yellow' | 'gray' }> = {
    operational: { label: 'Operational', color: 'green' },
    maintenance_due: { label: 'Wartung fällig', color: 'red' },
    in_workshop: { label: 'In Werkstatt', color: 'purple' },
    planned_for_workshop: { label: 'Werkstatt geplant', color: 'yellow' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
