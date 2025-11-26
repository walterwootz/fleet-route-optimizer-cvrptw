/**
 * HR/Personnel Page
 * Staff management and qualifications
 */

import { useEffect, useMemo, useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric } from '@tremor/react';
import { Users, CheckCircle, Clock, Award, AlertCircle, Loader2 } from 'lucide-react';
import { useHRStore } from '@/stores/hrStore';

export function HR() {
  const {
    staff,
    assignments,
    loading,
    error,
    fetchStaff,
    fetchAssignments,
  } = useHRStore();

  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');

  // Load data on mount
  useEffect(() => {
    fetchStaff({ is_active: true });
    fetchAssignments();
  }, [fetchStaff, fetchAssignments]);

  // Create a map of staff ID to their current assignment
  const staffAssignmentMap = useMemo(() => {
    const map = new Map<string, string>();
    assignments.forEach((assignment) => {
      if (assignment.staff_id && assignment.vehicle_id) {
        map.set(assignment.staff_id, assignment.vehicle_id);
      }
    });
    return map;
  }, [assignments]);

  // Filter staff
  const filteredStaff = useMemo(() => {
    return staff.filter((s) => {
      const matchesRole = roleFilter === 'all' || s.position === roleFilter;
      const isAssigned = staffAssignmentMap.has(s.id);

      // Status filter logic
      let matchesStatus = true;
      if (statusFilter === 'available') {
        matchesStatus = !isAssigned;
      } else if (statusFilter === 'assigned') {
        matchesStatus = isAssigned;
      }
      // 'all' matches everything

      return matchesRole && matchesStatus;
    });
  }, [staff, roleFilter, statusFilter, staffAssignmentMap]);

  // Get unique positions/roles
  const uniqueRoles = useMemo(() => {
    return Array.from(new Set(staff.map(s => s.position)));
  }, [staff]);

  // Calculate statistics
  const totalStaff = staff.filter(s => s.is_active).length;
  const assignedStaff = useMemo(() => {
    return staff.filter(s => staffAssignmentMap.has(s.id)).length;
  }, [staff, staffAssignmentMap]);
  const availableStaff = totalStaff - assignedStaff;

  // Count certifications for issues (staff without certifications)
  const certificateIssues = staff.filter(s => !s.certifications || s.certifications.length === 0).length;

  // Qualification distribution
  const qualificationCounts = useMemo(() => {
    return staff.reduce((acc, s) => {
      (s.qualifications || []).forEach(qual => {
        acc[qual] = (acc[qual] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);
  }, [staff]);

  // Loading state
  if (loading && staff.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={48} />
          <Text className="text-gray-600">Lade Mitarbeiterdaten...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Personal-Management</Title>
        <Text>Mitarbeiter, Qualifikationen und Schulungen</Text>
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

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              <Text>Zertifikate</Text>
              <Metric className="text-red-600">{certificateIssues}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Ohne Zertifikate</Text>
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
                {filteredStaff.map((s) => {
                  const currentAssignment = staffAssignmentMap.get(s.id);
                  const isAssigned = !!currentAssignment;
                  const qualifications = s.qualifications || [];
                  const certifications = s.certifications || [];

                  return (
                    <TableRow key={s.id}>
                      <TableCell>
                        <span className="font-mono text-sm">{s.employee_id}</span>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">{s.first_name} {s.last_name}</span>
                      </TableCell>
                      <TableCell>{s.position}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {qualifications.slice(0, 3).map((qual, idx) => (
                            <Badge key={idx} size="xs" color="blue">
                              {qual}
                            </Badge>
                          ))}
                          {qualifications.length > 3 && (
                            <Badge size="xs" color="gray">
                              +{qualifications.length - 3}
                            </Badge>
                          )}
                          {qualifications.length === 0 && (
                            <Text className="text-xs text-gray-500">Keine</Text>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <StaffStatusBadge isAssigned={isAssigned} />
                      </TableCell>
                      <TableCell>
                        {currentAssignment ? (
                          <span className="font-mono text-sm">{currentAssignment}</span>
                        ) : (
                          <Badge color="gray">Keine</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {certifications.length > 0 ? (
                          <Badge color="green">{certifications.length} Zertifikate</Badge>
                        ) : (
                          <Badge color="red">Keine</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>

            {filteredStaff.length === 0 && !loading && (
              <div className="text-center py-8">
                <Text className="text-gray-500">
                  {staff.length === 0
                    ? 'Keine Mitarbeiter vorhanden.'
                    : 'Keine Mitarbeiter gefunden. Passen Sie die Filter an.'}
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
              {Object.keys(qualificationCounts).length === 0 && (
                <Text className="text-gray-500 text-center py-4">Keine Qualifikationen erfasst.</Text>
              )}
            </div>
          </Card>

          {/* Department Distribution */}
          <Card>
            <Title>Abteilungen</Title>
            <Text className="mb-4">Personal-Übersicht</Text>
            <div className="space-y-2">
              {Array.from(new Set(staff.map(s => s.department)))
                .filter(dept => dept)
                .map((department) => {
                  const count = staff.filter(s => s.department === department).length;
                  return (
                    <div key={department} className="flex items-center justify-between py-2 border-b border-gray-100">
                      <Text className="text-sm font-medium">{department}</Text>
                      <Badge color="blue">{count} Mitarbeiter</Badge>
                    </div>
                  );
                })}
              {Array.from(new Set(staff.map(s => s.department))).filter(d => d).length === 0 && (
                <Text className="text-gray-500 text-center py-4">Keine Abteilungen erfasst.</Text>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper component for staff status badges
function StaffStatusBadge({ isAssigned }: { isAssigned: boolean }) {
  return isAssigned ? (
    <Badge color="blue">Zugewiesen</Badge>
  ) : (
    <Badge color="green">Verfügbar</Badge>
  );
}
