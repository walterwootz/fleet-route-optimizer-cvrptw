/**
 * Workshop Management Page
 * Overview of workshop orders and progress
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, ProgressBar, Select, SelectItem } from '@tremor/react';
import { Factory, CheckCircle, Clock, AlertCircle } from 'lucide-react';

// Mock data - will be replaced with API calls
const mockWorkshopOrders = [
  {
    id: 'WO-12345',
    locomotive_id: 'BR185-042',
    workshop_id: 'WERK-MUC',
    workshop_name: 'München',
    status: 'planned',
    planned_start: '2025-12-05T08:00:00',
    planned_end: '2025-12-06T16:00:00',
    tasks: ['HU', 'Bremsprüfung', 'Ölwechsel'],
    assigned_staff: ['MA-123', 'MA-456'],
    progress: 0,
  },
  {
    id: 'WO-12346',
    locomotive_id: 'BR189-033',
    workshop_id: 'WERK-MUC',
    workshop_name: 'München',
    status: 'in_progress',
    planned_start: '2025-11-20T08:00:00',
    planned_end: '2025-11-22T16:00:00',
    actual_start: '2025-11-20T08:15:00',
    tasks: ['HU', 'Klimaanlage'],
    assigned_staff: ['MA-789'],
    progress: 65,
  },
  {
    id: 'WO-12347',
    locomotive_id: 'BR152-123',
    workshop_id: 'WERK-LEI',
    workshop_name: 'Leipzig',
    status: 'in_progress',
    planned_start: '2025-11-22T08:00:00',
    planned_end: '2025-11-23T16:00:00',
    actual_start: '2025-11-22T08:00:00',
    tasks: ['Bremsprüfung'],
    assigned_staff: ['MA-234'],
    progress: 40,
  },
  {
    id: 'WO-12348',
    locomotive_id: 'BR185-091',
    workshop_id: 'WERK-HAM',
    workshop_name: 'Hamburg',
    status: 'completed',
    planned_start: '2025-11-15T08:00:00',
    planned_end: '2025-11-17T16:00:00',
    actual_start: '2025-11-15T08:00:00',
    actual_end: '2025-11-17T15:30:00',
    tasks: ['HU', 'Bremsprüfung', 'Ölwechsel', 'Achslager'],
    assigned_staff: ['MA-345', 'MA-567'],
    progress: 100,
  },
  {
    id: 'WO-12349',
    locomotive_id: 'BR189-012',
    workshop_id: 'WERK-BER',
    workshop_name: 'Berlin',
    status: 'planned',
    planned_start: '2025-12-10T08:00:00',
    planned_end: '2025-12-11T16:00:00',
    tasks: ['Ölwechsel', 'Filter'],
    assigned_staff: [],
    progress: 0,
  },
  {
    id: 'WO-12350',
    locomotive_id: 'BR152-156',
    workshop_id: 'WERK-MUC',
    workshop_name: 'München',
    status: 'delayed',
    planned_start: '2025-11-18T08:00:00',
    planned_end: '2025-11-20T16:00:00',
    actual_start: '2025-11-18T10:30:00',
    tasks: ['HU', 'Getriebe'],
    assigned_staff: ['MA-890'],
    progress: 25,
  },
];

export function Workshop() {
  const [statusFilter, setStatusFilter] = useState('all');
  const [workshopFilter, setWorkshopFilter] = useState('all');

  // Filter orders
  const filteredOrders = mockWorkshopOrders.filter((order) => {
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    const matchesWorkshop = workshopFilter === 'all' || order.workshop_id === workshopFilter;
    return matchesStatus && matchesWorkshop;
  });

  // Get unique workshops
  const uniqueWorkshops = Array.from(new Set(mockWorkshopOrders.map(o => o.workshop_id)));

  // Calculate statistics
  const totalOrders = mockWorkshopOrders.length;
  const plannedOrders = mockWorkshopOrders.filter(o => o.status === 'planned').length;
  const inProgressOrders = mockWorkshopOrders.filter(o => o.status === 'in_progress').length;
  const completedOrders = mockWorkshopOrders.filter(o => o.status === 'completed').length;
  const delayedOrders = mockWorkshopOrders.filter(o => o.status === 'delayed').length;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Werkstatt-Management</Title>
        <Text>Werkstattaufträge und Reparaturfortschritt</Text>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gray-100 rounded-lg">
              <Factory className="text-gray-600" size={20} />
            </div>
            <div>
              <Text>Gesamt</Text>
              <Title>{totalOrders}</Title>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Clock className="text-blue-600" size={20} />
            </div>
            <div>
              <Text>Geplant</Text>
              <Title className="text-blue-600">{plannedOrders}</Title>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-orange-100 rounded-lg">
              <AlertCircle className="text-orange-600" size={20} />
            </div>
            <div>
              <Text>In Arbeit</Text>
              <Title className="text-orange-600">{inProgressOrders}</Title>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={20} />
            </div>
            <div>
              <Text>Abgeschlossen</Text>
              <Title className="text-green-600">{completedOrders}</Title>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="text-red-600" size={20} />
            </div>
            <div>
              <Text>Verzögert</Text>
              <Title className="text-red-600">{delayedOrders}</Title>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectItem value="all">Alle Status</SelectItem>
            <SelectItem value="planned">Geplant</SelectItem>
            <SelectItem value="in_progress">In Arbeit</SelectItem>
            <SelectItem value="completed">Abgeschlossen</SelectItem>
            <SelectItem value="delayed">Verzögert</SelectItem>
          </Select>

          <Select value={workshopFilter} onValueChange={setWorkshopFilter}>
            <SelectItem value="all">Alle Werkstätten</SelectItem>
            {uniqueWorkshops.map((workshop) => (
              <SelectItem key={workshop} value={workshop}>
                {workshop}
              </SelectItem>
            ))}
          </Select>
        </div>
      </Card>

      {/* Orders Table */}
      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Auftrag</TableHeaderCell>
              <TableHeaderCell>Lok</TableHeaderCell>
              <TableHeaderCell>Werkstatt</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Aufgaben</TableHeaderCell>
              <TableHeaderCell>Personal</TableHeaderCell>
              <TableHeaderCell>Fortschritt</TableHeaderCell>
              <TableHeaderCell>Zeitplan</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredOrders.map((order) => (
              <TableRow key={order.id}>
                <TableCell>
                  <span className="font-mono font-medium">{order.id}</span>
                </TableCell>
                <TableCell>
                  <span className="font-mono">{order.locomotive_id}</span>
                </TableCell>
                <TableCell>{order.workshop_name}</TableCell>
                <TableCell>
                  <StatusBadge status={order.status} />
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {order.tasks.map((task, idx) => (
                      <Badge key={idx} size="xs" color="gray">
                        {task}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  {order.assigned_staff.length > 0 ? (
                    <Badge color="blue">{order.assigned_staff.length} MA</Badge>
                  ) : (
                    <Badge color="red">Keine</Badge>
                  )}
                </TableCell>
                <TableCell>
                  <div className="w-24">
                    <ProgressBar value={order.progress} color={getProgressColor(order.progress)} />
                    <Text className="text-xs mt-1">{order.progress}%</Text>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="text-xs">
                    <div>
                      {new Date(order.planned_start).toLocaleDateString('de-DE', {
                        day: '2-digit',
                        month: '2-digit',
                      })}
                      {' - '}
                      {new Date(order.planned_end).toLocaleDateString('de-DE', {
                        day: '2-digit',
                        month: '2-digit',
                      })}
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {filteredOrders.length === 0 && (
          <div className="text-center py-8">
            <Text className="text-gray-500">
              Keine Werkstattaufträge gefunden. Passen Sie die Filter an.
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}

// Helper component for status badges
function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: 'blue' | 'orange' | 'green' | 'red' | 'gray' }> = {
    planned: { label: 'Geplant', color: 'blue' },
    in_progress: { label: 'In Arbeit', color: 'orange' },
    completed: { label: 'Abgeschlossen', color: 'green' },
    delayed: { label: 'Verzögert', color: 'red' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}

// Helper function for progress color
function getProgressColor(progress: number): 'red' | 'orange' | 'yellow' | 'green' {
  if (progress < 25) return 'red';
  if (progress < 50) return 'orange';
  if (progress < 75) return 'yellow';
  return 'green';
}
