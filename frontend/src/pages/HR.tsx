/**
 * HR/Personnel Page
 * Staff management and qualifications
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric } from '@tremor/react';
import { Users, CheckCircle, Clock, Award, AlertCircle } from 'lucide-react';

// Mock data
const mockStaff = [
  { id: 'MA-123', name: 'Hans Müller', role: 'Mechaniker', qualifications: ['Schweißen', 'Hydraulik', 'Elektrik'], status: 'available', current_assignment: null, certificates_valid: true, next_training: '2025-03-15' },
  { id: 'MA-456', name: 'Anna Schmidt', role: 'Mechaniker', qualifications: ['HU-Prüfer', 'Bremsen', 'Achsen'], status: 'available', current_assignment: null, certificates_valid: true, next_training: '2025-04-20' },
  { id: 'MA-789', name: 'Peter Wagner', role: 'Elektriker', qualifications: ['Elektrik', 'Steuerung', 'Diagnose'], status: 'assigned', current_assignment: 'WO-12346', certificates_valid: true, next_training: '2025-02-10' },
  { id: 'MA-234', name: 'Maria Fischer', role: 'Mechaniker', qualifications: ['Bremsen', 'Fahrwerk'], status: 'assigned', current_assignment: 'WO-12347', certificates_valid: true, next_training: '2025-05-01' },
  { id: 'MA-345', name: 'Thomas Weber', role: 'Teamleiter', qualifications: ['HU-Prüfer', 'Schweißen', 'Hydraulik', 'Management'], status: 'available', current_assignment: null, certificates_valid: true, next_training: '2025-03-30' },
  { id: 'MA-567', name: 'Julia Becker', role: 'Mechaniker', qualifications: ['Achslager', 'Getriebe'], status: 'available', current_assignment: null, certificates_valid: false, next_training: '2025-01-15' },
  { id: 'MA-890', name: 'Michael Klein', role: 'Elektriker', qualifications: ['Elektrik', 'Klimaanlage'], status: 'assigned', current_assignment: 'WO-12350', certificates_valid: true, next_training: '2025-06-12' },
  { id: 'MA-678', name: 'Sarah Hoffmann', role: 'Mechaniker', qualifications: ['Bremsen', 'Hydraulik', 'Ölwechsel'], status: 'training', current_assignment: null, certificates_valid: true, next_training: null },
  { id: 'MA-901', name: 'Klaus Schneider', role: 'Teamleiter', qualifications: ['HU-Prüfer', 'Bremsen', 'Elektrik', 'Management'], status: 'available', current_assignment: null, certificates_valid: true, next_training: '2025-04-15' },
  { id: 'MA-135', name: 'Claudia Zimmermann', role: 'Administrativ', qualifications: ['Planung', 'Dokumentation'], status: 'available', current_assignment: null, certificates_valid: true, next_training: '2025-07-01' },
];

// Mock training sessions
const mockTrainingSessions = [
  { id: 'TR-001', type: 'HU-Prüfer Auffrischung', date: '2025-01-15', participants: ['MA-567'], status: 'scheduled' },
  { id: 'TR-002', type: 'Schweißtechnik Fortgeschritten', date: '2025-02-10', participants: ['MA-789'], status: 'scheduled' },
  { id: 'TR-003', type: 'Neue Bremssysteme Schulung', date: '2025-03-05', participants: ['MA-234', 'MA-456', 'MA-678'], status: 'scheduled' },
];

export function HR() {
  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');

  // Filter staff
  const filteredStaff = mockStaff.filter((staff) => {
    const matchesStatus = statusFilter === 'all' || staff.status === statusFilter;
    const matchesRole = roleFilter === 'all' || staff.role === roleFilter;
    return matchesStatus && matchesRole;
  });

  // Get unique roles
  const uniqueRoles = Array.from(new Set(mockStaff.map(s => s.role)));

  // Calculate statistics
  const totalStaff = mockStaff.length;
  const availableStaff = mockStaff.filter(s => s.status === 'available').length;
  const assignedStaff = mockStaff.filter(s => s.status === 'assigned').length;
  const inTraining = mockStaff.filter(s => s.status === 'training').length;
  const certificateIssues = mockStaff.filter(s => !s.certificates_valid).length;

  // Qualification distribution
  const qualificationCounts = mockStaff.reduce((acc, staff) => {
    staff.qualifications.forEach(qual => {
      acc[qual] = (acc[qual] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Personal-Management</Title>
        <Text>Mitarbeiter, Qualifikationen und Schulungen</Text>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Gesamt</Text>
              <Metric>{totalStaff}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Mitarbeiter</Text>
            </div>
            <div className="p-3 bg-gray-100 rounded-lg">
              <Users className="text-gray-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Verfügbar</Text>
              <Metric className="text-green-600">{availableStaff}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Einsatzbereit</Text>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Zugewiesen</Text>
              <Metric className="text-blue-600">{assignedStaff}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Im Einsatz</Text>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Clock className="text-blue-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>In Schulung</Text>
              <Metric className="text-orange-600">{inTraining}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Weiterbildung</Text>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <Award className="text-orange-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Zertifikate</Text>
              <Metric className="text-red-600">{certificateIssues}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Probleme</Text>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="text-red-600" size={20} />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Staff Table */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <Title>Mitarbeiter</Title>
                <Text>{filteredStaff.length} von {totalStaff}</Text>
              </div>
              <div className="flex gap-2">
                <Select value={statusFilter} onValueChange={setStatusFilter} className="w-40">
                  <SelectItem value="all">Alle Status</SelectItem>
                  <SelectItem value="available">Verfügbar</SelectItem>
                  <SelectItem value="assigned">Zugewiesen</SelectItem>
                  <SelectItem value="training">In Schulung</SelectItem>
                </Select>
                <Select value={roleFilter} onValueChange={setRoleFilter} className="w-40">
                  <SelectItem value="all">Alle Rollen</SelectItem>
                  {uniqueRoles.map((role) => (
                    <SelectItem key={role} value={role}>
                      {role}
                    </SelectItem>
                  ))}
                </Select>
              </div>
            </div>

            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>ID</TableHeaderCell>
                  <TableHeaderCell>Name</TableHeaderCell>
                  <TableHeaderCell>Rolle</TableHeaderCell>
                  <TableHeaderCell>Qualifikationen</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Zuordnung</TableHeaderCell>
                  <TableHeaderCell>Zertifikate</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredStaff.map((staff) => (
                  <TableRow key={staff.id}>
                    <TableCell>
                      <span className="font-mono text-sm">{staff.id}</span>
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">{staff.name}</span>
                    </TableCell>
                    <TableCell>{staff.role}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {staff.qualifications.slice(0, 3).map((qual, idx) => (
                          <Badge key={idx} size="xs" color="blue">
                            {qual}
                          </Badge>
                        ))}
                        {staff.qualifications.length > 3 && (
                          <Badge size="xs" color="gray">
                            +{staff.qualifications.length - 3}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <StaffStatusBadge status={staff.status} />
                    </TableCell>
                    <TableCell>
                      {staff.current_assignment ? (
                        <span className="font-mono text-sm">{staff.current_assignment}</span>
                      ) : (
                        <Badge color="gray">Keine</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {staff.certificates_valid ? (
                        <Badge color="green">Gültig</Badge>
                      ) : (
                        <Badge color="red">Abgelaufen</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {filteredStaff.length === 0 && (
              <div className="text-center py-8">
                <Text className="text-gray-500">
                  Keine Mitarbeiter gefunden. Passen Sie die Filter an.
                </Text>
              </div>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Top Qualifications */}
          <Card>
            <Title>Qualifikationen</Title>
            <Text className="mb-4">Verteilung im Team</Text>
            <div className="space-y-3">
              {Object.entries(qualificationCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
                .map(([qual, count]) => (
                  <div key={qual} className="flex items-center justify-between">
                    <Text className="text-sm">{qual}</Text>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${(count / totalStaff) * 100}%` }}
                        />
                      </div>
                      <Text className="text-sm font-medium w-8 text-right">{count}</Text>
                    </div>
                  </div>
                ))}
            </div>
          </Card>

          {/* Upcoming Training */}
          <Card>
            <Title>Geplante Schulungen</Title>
            <Text className="mb-4">{mockTrainingSessions.length} Termine</Text>
            <div className="space-y-3">
              {mockTrainingSessions.map((session) => (
                <div key={session.id} className="border-l-4 border-blue-500 pl-3 py-2">
                  <div className="font-medium text-sm">{session.type}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(session.date).toLocaleDateString('de-DE', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </div>
                  <div className="mt-2">
                    <Badge size="xs" color="blue">
                      {session.participants.length} Teilnehmer
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper component for staff status badges
function StaffStatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: 'green' | 'blue' | 'orange' | 'gray' }> = {
    available: { label: 'Verfügbar', color: 'green' },
    assigned: { label: 'Zugewiesen', color: 'blue' },
    training: { label: 'In Schulung', color: 'orange' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
