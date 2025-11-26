/**
 * Fleet Overview Page
 * Table view of all locomotives with filters
 */

import { useEffect, useMemo, useState } from 'react';
import { Card, Title, Text, Badge, TextInput, Select, SelectItem, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell } from '@tremor/react';
import { Search, Filter, Loader2, AlertCircle } from 'lucide-react';
import { useVehiclesStore } from '@/stores/vehiclesStore';
import { VehicleStatus } from '@/services/vehiclesApi';

export function FleetOverview() {
  const {
    vehicles,
    loading,
    error,
    fetchVehicles,
  } = useVehiclesStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [seriesFilter, setSeriesFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');

  // Load vehicles on mount
  useEffect(() => {
    fetchVehicles();
  }, [fetchVehicles]);

  // Filter locomotives
  const filteredLocomotives = useMemo(() => {
    return vehicles.filter((vehicle) => {
      const matchesSearch =
        vehicle.asset_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        vehicle.model.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || vehicle.status === statusFilter;
      const matchesSeries = seriesFilter === 'all' || vehicle.model === seriesFilter;
      const matchesLocation = locationFilter === 'all' || vehicle.current_location === locationFilter;

      return matchesSearch && matchesStatus && matchesSeries && matchesLocation;
    });
  }, [vehicles, searchTerm, statusFilter, seriesFilter, locationFilter]);

  // Get unique values for filters
  const uniqueSeries = useMemo(() => {
    return Array.from(new Set(vehicles.map(v => v.model)));
  }, [vehicles]);

  const uniqueLocations = useMemo(() => {
    return Array.from(new Set(vehicles.map(v => v.current_location).filter(Boolean)));
  }, [vehicles]);

  // Loading state
  if (loading && vehicles.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={48} />
          <Text className="text-gray-600">Lade Flottendaten...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Flottenübersicht</Title>
        <Text>Alle Lokomotiven im Überblick</Text>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-l-4 border-red-500 bg-red-50">
          <div className="flex items-start space-x-3">
            <AlertCircle className="text-red-600 mt-1" size={20} />
            <div>
              <Title className="text-red-900">Fehler beim Laden</Title>
              <Text className="text-red-700">{error}</Text>
            </div>
          </div>
        </Card>
      )}

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
              <SelectItem value={VehicleStatus.AVAILABLE}>Verfügbar</SelectItem>
              <SelectItem value={VehicleStatus.IN_SERVICE}>Im Einsatz</SelectItem>
              <SelectItem value={VehicleStatus.MAINTENANCE_DUE}>Wartung fällig</SelectItem>
              <SelectItem value={VehicleStatus.WORKSHOP_PLANNED}>Werkstatt geplant</SelectItem>
              <SelectItem value={VehicleStatus.IN_WORKSHOP}>In Werkstatt</SelectItem>
              <SelectItem value={VehicleStatus.OUT_OF_SERVICE}>Außer Betrieb</SelectItem>
              <SelectItem value={VehicleStatus.RETIRED}>Stillgelegt</SelectItem>
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
              {filteredLocomotives.length} von {vehicles.length} Lokomotiven
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
            {filteredLocomotives.map((vehicle) => (
              <TableRow key={vehicle.id}>
                <TableCell>
                  <span className="font-mono font-medium">{vehicle.asset_id}</span>
                </TableCell>
                <TableCell>{vehicle.model}</TableCell>
                <TableCell>
                  <StatusBadge status={vehicle.status} />
                </TableCell>
                <TableCell>{vehicle.current_location || '-'}</TableCell>
                <TableCell>
                  {vehicle.last_service_date
                    ? new Date(vehicle.last_service_date).toLocaleDateString('de-DE')
                    : '-'}
                </TableCell>
                <TableCell>
                  {vehicle.status === VehicleStatus.WORKSHOP_PLANNED || vehicle.status === VehicleStatus.IN_WORKSHOP ? (
                    <Badge color="blue">Ja</Badge>
                  ) : (
                    <Badge color="gray">Nein</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {filteredLocomotives.length === 0 && !loading && (
          <div className="text-center py-8">
            <Text className="text-gray-500">
              {vehicles.length === 0
                ? 'Keine Fahrzeuge vorhanden.'
                : 'Keine Fahrzeuge gefunden. Passen Sie die Filter an.'}
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}

// Helper component for status badges
function StatusBadge({ status }: { status: VehicleStatus }) {
  const statusConfig: Record<VehicleStatus, { label: string; color: 'green' | 'red' | 'purple' | 'yellow' | 'orange' | 'gray' }> = {
    [VehicleStatus.AVAILABLE]: { label: 'Verfügbar', color: 'green' },
    [VehicleStatus.IN_SERVICE]: { label: 'Im Einsatz', color: 'green' },
    [VehicleStatus.MAINTENANCE_DUE]: { label: 'Wartung fällig', color: 'orange' },
    [VehicleStatus.WORKSHOP_PLANNED]: { label: 'Werkstatt geplant', color: 'yellow' },
    [VehicleStatus.IN_WORKSHOP]: { label: 'In Werkstatt', color: 'purple' },
    [VehicleStatus.OUT_OF_SERVICE]: { label: 'Außer Betrieb', color: 'red' },
    [VehicleStatus.RETIRED]: { label: 'Stillgelegt', color: 'gray' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
