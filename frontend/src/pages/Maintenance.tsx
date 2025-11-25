/**
 * Maintenance Page
 * Overview of maintenance tasks and HU deadlines
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, BarList } from '@tremor/react';
import { Calendar, AlertTriangle, Clock, Wrench } from 'lucide-react';

// Mock data - will be replaced with API calls
const mockMaintenanceTasks = [
  { id: 'TASK-001', locomotive_id: 'BR185-042', type: 'HU', due_date: '2025-12-05', status: 'pending', priority: 'high', days_until: 11 },
  { id: 'TASK-002', locomotive_id: 'BR189-033', type: 'HU', due_date: '2025-12-10', status: 'pending', priority: 'high', days_until: 16 },
  { id: 'TASK-003', locomotive_id: 'BR152-123', type: 'Bremsprüfung', due_date: '2025-12-07', status: 'pending', priority: 'medium', days_until: 13 },
  { id: 'TASK-004', locomotive_id: 'BR185-091', type: 'HU', due_date: '2025-11-28', status: 'overdue', priority: 'critical', days_until: -4 },
  { id: 'TASK-005', locomotive_id: 'BR189-012', type: 'Ölwechsel', due_date: '2025-12-15', status: 'pending', priority: 'low', days_until: 21 },
  { id: 'TASK-006', locomotive_id: 'BR152-156', type: 'HU', due_date: '2025-12-01', status: 'pending', priority: 'high', days_until: 7 },
  { id: 'TASK-007', locomotive_id: 'BR185-055', type: 'Klimaanlage', due_date: '2025-12-20', status: 'pending', priority: 'low', days_until: 26 },
  { id: 'TASK-008', locomotive_id: 'BR189-045', type: 'HU', due_date: '2026-01-10', status: 'pending', priority: 'medium', days_until: 47 },
];

export function Maintenance() {
  const [filter, setFilter] = useState<'all' | 'overdue' | 'urgent' | 'upcoming'>('all');

  // Filter tasks
  const filteredTasks = mockMaintenanceTasks.filter((task) => {
    if (filter === 'all') return true;
    if (filter === 'overdue') return task.status === 'overdue';
    if (filter === 'urgent') return task.days_until <= 7 && task.days_until >= 0;
    if (filter === 'upcoming') return task.days_until > 7;
    return true;
  });

  // Sort by due date (overdue first)
  const sortedTasks = [...filteredTasks].sort((a, b) => a.days_until - b.days_until);

  // Calculate statistics
  const overdueTasks = mockMaintenanceTasks.filter(t => t.status === 'overdue').length;
  const urgentTasks = mockMaintenanceTasks.filter(t => t.days_until <= 7 && t.days_until >= 0).length;
  const upcomingTasks = mockMaintenanceTasks.filter(t => t.days_until > 7).length;

  // Task types distribution
  const taskTypeData = Object.entries(
    mockMaintenanceTasks.reduce((acc, task) => {
      acc[task.type] = (acc[task.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Wartungsplanung</Title>
        <Text>HU-Fristen und Instandhaltungsaufgaben</Text>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card
          className={`cursor-pointer transition ${filter === 'overdue' ? 'ring-2 ring-red-500' : ''}`}
          onClick={() => setFilter(filter === 'overdue' ? 'all' : 'overdue')}
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertTriangle className="text-red-600" size={24} />
            </div>
            <div>
              <Text>Überfällig</Text>
              <Title className="text-red-600">{overdueTasks}</Title>
            </div>
          </div>
        </Card>

        <Card
          className={`cursor-pointer transition ${filter === 'urgent' ? 'ring-2 ring-orange-500' : ''}`}
          onClick={() => setFilter(filter === 'urgent' ? 'all' : 'urgent')}
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-orange-100 rounded-lg">
              <Clock className="text-orange-600" size={24} />
            </div>
            <div>
              <Text>Dringend (≤7 Tage)</Text>
              <Title className="text-orange-600">{urgentTasks}</Title>
            </div>
          </div>
        </Card>

        <Card
          className={`cursor-pointer transition ${filter === 'upcoming' ? 'ring-2 ring-blue-500' : ''}`}
          onClick={() => setFilter(filter === 'upcoming' ? 'all' : 'upcoming')}
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Calendar className="text-blue-600" size={24} />
            </div>
            <div>
              <Text>Geplant (>7 Tage)</Text>
              <Title className="text-blue-600">{upcomingTasks}</Title>
            </div>
          </div>
        </Card>

        <Card
          className={`cursor-pointer transition ${filter === 'all' ? 'ring-2 ring-gray-500' : ''}`}
          onClick={() => setFilter('all')}
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gray-100 rounded-lg">
              <Wrench className="text-gray-600" size={24} />
            </div>
            <div>
              <Text>Gesamt</Text>
              <Title>{mockMaintenanceTasks.length}</Title>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task List */}
        <div className="lg:col-span-2">
          <Card>
            <Title>Wartungsaufgaben</Title>
            <Text className="mb-4">
              {filter === 'all' && 'Alle Aufgaben'}
              {filter === 'overdue' && 'Überfällige Aufgaben'}
              {filter === 'urgent' && 'Dringende Aufgaben (≤7 Tage)'}
              {filter === 'upcoming' && 'Geplante Aufgaben (>7 Tage)'}
            </Text>

            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Lok</TableHeaderCell>
                  <TableHeaderCell>Typ</TableHeaderCell>
                  <TableHeaderCell>Fällig</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Tage</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedTasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell>
                      <span className="font-mono font-medium">{task.locomotive_id}</span>
                    </TableCell>
                    <TableCell>{task.type}</TableCell>
                    <TableCell>
                      {new Date(task.due_date).toLocaleDateString('de-DE')}
                    </TableCell>
                    <TableCell>
                      <PriorityBadge priority={task.priority} status={task.status} />
                    </TableCell>
                    <TableCell>
                      <DaysUntilBadge days={task.days_until} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {sortedTasks.length === 0 && (
              <div className="text-center py-8">
                <Text className="text-gray-500">
                  Keine Aufgaben in dieser Kategorie.
                </Text>
              </div>
            )}
          </Card>
        </div>

        {/* Task Type Distribution */}
        <div>
          <Card>
            <Title>Aufgaben nach Typ</Title>
            <Text className="mb-4">Verteilung der Wartungsarten</Text>
            <BarList data={taskTypeData} className="mt-4" />
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper component for priority badges
function PriorityBadge({ priority, status }: { priority: string; status: string }) {
  if (status === 'overdue') {
    return <Badge color="red">Überfällig</Badge>;
  }

  const priorityConfig: Record<string, { label: string; color: 'red' | 'orange' | 'yellow' | 'blue' | 'gray' }> = {
    critical: { label: 'Kritisch', color: 'red' },
    high: { label: 'Hoch', color: 'orange' },
    medium: { label: 'Mittel', color: 'yellow' },
    low: { label: 'Niedrig', color: 'blue' },
  };

  const config = priorityConfig[priority] || { label: priority, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}

// Helper component for days until badge
function DaysUntilBadge({ days }: { days: number }) {
  if (days < 0) {
    return (
      <span className="text-red-600 font-medium">
        {Math.abs(days)} Tage überfällig
      </span>
    );
  }

  if (days === 0) {
    return <span className="text-orange-600 font-medium">Heute fällig</span>;
  }

  if (days <= 7) {
    return <span className="text-orange-600 font-medium">in {days} Tagen</span>;
  }

  return <span className="text-gray-600">in {days} Tagen</span>;
}
