/**
 * Workshop Management Page
 * Overview of workshop orders and progress
 */

import { useEffect, useMemo } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, ProgressBar, Select, SelectItem } from '@tremor/react';
import { Factory, CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { useMaintenanceStore } from '@/stores/maintenanceStore';
import { WorkOrderStatus } from '@/services/maintenanceApi';

export function Workshop() {
  // Get state and actions from store
  const {
    workOrders,
    loading,
    error,
    statusFilter,
    workshopFilter,
    setStatusFilter,
    setWorkshopFilter,
    fetchWorkOrders,
  } = useMaintenanceStore();

  // Load work orders on mount
  useEffect(() => {
    fetchWorkOrders();
  }, [fetchWorkOrders]);

  // Filter orders based on selected filters
  const filteredOrders = useMemo(() => {
    return workOrders.filter((order) => {
      const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
      const matchesWorkshop = workshopFilter === 'all' || order.workshop_id === workshopFilter;
      return matchesStatus && matchesWorkshop;
    });
  }, [workOrders, statusFilter, workshopFilter]);

  // Get unique workshops
  const uniqueWorkshops = useMemo(() => {
    return Array.from(new Set(workOrders.map(o => o.workshop_id).filter(Boolean)));
  }, [workOrders]);

  // Calculate statistics
  const totalOrders = workOrders.length;
  const draftOrders = workOrders.filter(o => o.status === WorkOrderStatus.DRAFT).length;
  const scheduledOrders = workOrders.filter(o => o.status === WorkOrderStatus.SCHEDULED).length;
  const inProgressOrders = workOrders.filter(o => o.status === WorkOrderStatus.IN_PROGRESS).length;
  const completedOrders = workOrders.filter(o => o.status === WorkOrderStatus.COMPLETED).length;

  // Calculate progress for a work order
  const calculateProgress = (order: typeof workOrders[0]): number => {
    if (order.status === WorkOrderStatus.COMPLETED) return 100;
    if (order.status === WorkOrderStatus.DRAFT) return 0;
    if (order.status === WorkOrderStatus.SCHEDULED) return 0;

    // If in progress, calculate based on time
    if (order.actual_start && order.scheduled_end) {
      const start = new Date(order.actual_start).getTime();
      const end = new Date(order.scheduled_end).getTime();
      const now = Date.now();
      const totalDuration = end - start;
      const elapsed = now - start;

      if (totalDuration > 0) {
        return Math.min(Math.max(Math.round((elapsed / totalDuration) * 100), 0), 99);
      }
    }

    return 50; // Default for in_progress without timestamps
  };

  // Loading state
  if (loading && workOrders.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={48} />
          <Text className="text-gray-600">Lade Werkstattaufträge...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Werkstatt-Management</Title>
        <Text>Werkstattaufträge und Reparaturfortschritt</Text>
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
            <div className="p-3 bg-gray-100 rounded-lg">
              <Clock className="text-gray-600" size={20} />
            </div>
            <div>
              <Text>Entwurf</Text>
              <Title className="text-gray-600">{draftOrders}</Title>
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
              <Title className="text-blue-600">{scheduledOrders}</Title>
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
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as WorkOrderStatus | 'all')}>
            <SelectItem value="all">Alle Status</SelectItem>
            <SelectItem value={WorkOrderStatus.DRAFT}>Entwurf</SelectItem>
            <SelectItem value={WorkOrderStatus.SCHEDULED}>Geplant</SelectItem>
            <SelectItem value={WorkOrderStatus.IN_PROGRESS}>In Arbeit</SelectItem>
            <SelectItem value={WorkOrderStatus.COMPLETED}>Abgeschlossen</SelectItem>
            <SelectItem value={WorkOrderStatus.CANCELLED}>Storniert</SelectItem>
          </Select>

          <Select value={workshopFilter} onValueChange={setWorkshopFilter}>
            <SelectItem value="all">Alle Werkstätten</SelectItem>
            {uniqueWorkshops.map((workshop) => (
              <SelectItem key={workshop} value={workshop!}>
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
              <TableHeaderCell>Auftragsnummer</TableHeaderCell>
              <TableHeaderCell>Fahrzeug</TableHeaderCell>
              <TableHeaderCell>Werkstatt</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Aufgaben</TableHeaderCell>
              <TableHeaderCell>Team</TableHeaderCell>
              <TableHeaderCell>Fortschritt</TableHeaderCell>
              <TableHeaderCell>Zeitplan</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredOrders.map((order) => {
              const progress = calculateProgress(order);

              return (
                <TableRow key={order.id}>
                  <TableCell>
                    <span className="font-mono font-medium">{order.order_number}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono">{order.vehicle_id}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{order.workshop_id || '-'}</span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={order.status} />
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {order.tasks && order.tasks.length > 0 ? (
                        order.tasks.map((task, idx) => (
                          <Badge key={idx} size="xs" color="gray">
                            {task}
                          </Badge>
                        ))
                      ) : (
                        <Text className="text-xs text-gray-500">Keine</Text>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {order.assigned_team ? (
                      <Badge color="blue">{order.assigned_team}</Badge>
                    ) : (
                      <Badge color="red">Nicht zugewiesen</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="w-24">
                      <ProgressBar value={progress} color={getProgressColor(progress)} />
                      <Text className="text-xs mt-1">{progress}%</Text>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs">
                      {order.scheduled_start && order.scheduled_end ? (
                        <div>
                          {new Date(order.scheduled_start).toLocaleDateString('de-DE', {
                            day: '2-digit',
                            month: '2-digit',
                          })}
                          {' - '}
                          {new Date(order.scheduled_end).toLocaleDateString('de-DE', {
                            day: '2-digit',
                            month: '2-digit',
                          })}
                        </div>
                      ) : (
                        <Text className="text-gray-500">Nicht geplant</Text>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {filteredOrders.length === 0 && !loading && (
          <div className="text-center py-8">
            <Text className="text-gray-500">
              {workOrders.length === 0
                ? 'Keine Werkstattaufträge vorhanden. Erstellen Sie einen neuen Auftrag.'
                : 'Keine Werkstattaufträge gefunden. Passen Sie die Filter an.'}
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}

// Helper component for status badges
function StatusBadge({ status }: { status: WorkOrderStatus }) {
  const statusConfig: Record<WorkOrderStatus, { label: string; color: 'blue' | 'orange' | 'green' | 'red' | 'gray' }> = {
    [WorkOrderStatus.DRAFT]: { label: 'Entwurf', color: 'gray' },
    [WorkOrderStatus.SCHEDULED]: { label: 'Geplant', color: 'blue' },
    [WorkOrderStatus.IN_PROGRESS]: { label: 'In Arbeit', color: 'orange' },
    [WorkOrderStatus.COMPLETED]: { label: 'Abgeschlossen', color: 'green' },
    [WorkOrderStatus.CANCELLED]: { label: 'Storniert', color: 'red' },
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
