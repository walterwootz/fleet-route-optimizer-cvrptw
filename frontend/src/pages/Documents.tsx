/**
 * Documents Page
 * Certificates and document management
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric } from '@tremor/react';
import { FileText, AlertTriangle, CheckCircle, Clock, Archive } from 'lucide-react';

// Mock data
const mockDocuments = [
  { id: 'DOC-001', locomotive_id: 'BR185-042', type: 'TÜV Zulassung', issued: '2024-01-15', expires: '2026-01-15', status: 'valid', days_until_expiry: 417, responsible: 'MA-135' },
  { id: 'DOC-002', locomotive_id: 'BR185-042', type: 'Betriebserlaubnis', issued: '2023-06-10', expires: '2025-06-10', status: 'valid', days_until_expiry: 197, responsible: 'MA-135' },
  { id: 'DOC-003', locomotive_id: 'BR189-033', type: 'TÜV Zulassung', issued: '2023-08-20', expires: '2025-08-20', status: 'valid', days_until_expiry: 268, responsible: 'MA-135' },
  { id: 'DOC-004', locomotive_id: 'BR189-033', type: 'UIC-Zulassung', issued: '2022-11-01', expires: '2025-11-01', status: 'valid', days_until_expiry: 341, responsible: 'MA-135' },
  { id: 'DOC-005', locomotive_id: 'BR152-123', type: 'TÜV Zulassung', issued: '2024-03-10', expires: '2026-03-10', status: 'valid', days_until_expiry: 471, responsible: 'MA-135' },
  { id: 'DOC-006', locomotive_id: 'BR152-123', type: 'Betriebserlaubnis', issued: '2023-01-15', expires: '2025-01-15', status: 'expiring_soon', days_until_expiry: 51, responsible: 'MA-135' },
  { id: 'DOC-007', locomotive_id: 'BR185-055', type: 'TÜV Zulassung', issued: '2022-10-01', expires: '2024-10-01', status: 'expired', days_until_expiry: -55, responsible: 'MA-135' },
  { id: 'DOC-008', locomotive_id: 'BR189-012', type: 'UIC-Zulassung', issued: '2023-07-20', expires: '2026-07-20', status: 'valid', days_until_expiry: 602, responsible: 'MA-135' },
  { id: 'DOC-009', locomotive_id: 'BR152-087', type: 'Betriebserlaubnis', issued: '2024-02-01', expires: '2026-02-01', status: 'valid', days_until_expiry: 433, responsible: 'MA-135' },
  { id: 'DOC-010', locomotive_id: 'BR185-091', type: 'TÜV Zulassung', issued: '2023-04-15', expires: '2025-04-15', status: 'expiring_soon', days_until_expiry: 141, responsible: 'MA-135' },
  { id: 'DOC-011', locomotive_id: 'BR189-045', type: 'Betriebserlaubnis', issued: '2022-09-10', expires: '2024-09-10', status: 'expired', days_until_expiry: -76, responsible: 'MA-135' },
  { id: 'DOC-012', locomotive_id: 'BR152-156', type: 'UIC-Zulassung', issued: '2024-05-01', expires: '2027-05-01', status: 'valid', days_until_expiry: 887, responsible: 'MA-135' },
];

// Mock maintenance reports
const mockMaintenanceReports = [
  { id: 'REP-001', wo_id: 'WO-12345', locomotive_id: 'BR185-042', date: '2025-11-24', type: 'HU Bericht', uploaded_by: 'MA-123', file_size: '2.4 MB' },
  { id: 'REP-002', wo_id: 'WO-12346', locomotive_id: 'BR189-033', date: '2025-11-22', type: 'Inspektionsbericht', uploaded_by: 'MA-789', file_size: '1.8 MB' },
  { id: 'REP-003', wo_id: 'WO-12347', locomotive_id: 'BR152-123', date: '2025-11-20', type: 'Reparaturbericht', uploaded_by: 'MA-234', file_size: '3.1 MB' },
];

export function Documents() {
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Filter documents
  const filteredDocuments = mockDocuments.filter((doc) => {
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
    const matchesType = typeFilter === 'all' || doc.type === typeFilter;
    return matchesStatus && matchesType;
  });

  // Get unique document types
  const uniqueTypes = Array.from(new Set(mockDocuments.map(d => d.type)));

  // Calculate statistics
  const totalDocuments = mockDocuments.length;
  const validDocuments = mockDocuments.filter(d => d.status === 'valid').length;
  const expiringSoon = mockDocuments.filter(d => d.status === 'expiring_soon').length;
  const expiredDocuments = mockDocuments.filter(d => d.status === 'expired').length;

  // Sort by expiry date (expiring first)
  const sortedDocuments = [...filteredDocuments].sort((a, b) => a.days_until_expiry - b.days_until_expiry);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Dokumente & Zertifikate</Title>
        <Text>Übersicht aller Zulassungen und Berichte</Text>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Gesamt</Text>
              <Metric>{totalDocuments}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Dokumente</Text>
            </div>
            <div className="p-3 bg-gray-100 rounded-lg">
              <FileText className="text-gray-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Gültig</Text>
              <Metric className="text-green-600">{validDocuments}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Aktuelle Docs</Text>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Läuft ab</Text>
              <Metric className="text-orange-600">{expiringSoon}</Metric>
              <Text className="text-xs text-gray-500 mt-1">≤180 Tage</Text>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <Clock className="text-orange-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Abgelaufen</Text>
              <Metric className="text-red-600">{expiredDocuments}</Metric>
              <Text className="text-xs text-gray-500 mt-1">Erneuerung nötig</Text>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertTriangle className="text-red-600" size={20} />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Documents Table */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <Title>Zertifikate & Zulassungen</Title>
                <Text>{filteredDocuments.length} von {totalDocuments}</Text>
              </div>
              <div className="flex gap-2">
                <Select value={statusFilter} onValueChange={setStatusFilter} className="w-40">
                  <SelectItem value="all">Alle Status</SelectItem>
                  <SelectItem value="valid">Gültig</SelectItem>
                  <SelectItem value="expiring_soon">Läuft ab</SelectItem>
                  <SelectItem value="expired">Abgelaufen</SelectItem>
                </Select>
                <Select value={typeFilter} onValueChange={setTypeFilter} className="w-48">
                  <SelectItem value="all">Alle Typen</SelectItem>
                  {uniqueTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </Select>
              </div>
            </div>

            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Dok-Nr</TableHeaderCell>
                  <TableHeaderCell>Lok</TableHeaderCell>
                  <TableHeaderCell>Typ</TableHeaderCell>
                  <TableHeaderCell>Ausgestellt</TableHeaderCell>
                  <TableHeaderCell>Gültig bis</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Verbleibend</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedDocuments.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell>
                      <span className="font-mono text-sm">{doc.id}</span>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono font-medium">{doc.locomotive_id}</span>
                    </TableCell>
                    <TableCell>{doc.type}</TableCell>
                    <TableCell>
                      {new Date(doc.issued).toLocaleDateString('de-DE')}
                    </TableCell>
                    <TableCell>
                      {new Date(doc.expires).toLocaleDateString('de-DE')}
                    </TableCell>
                    <TableCell>
                      <DocumentStatusBadge status={doc.status} />
                    </TableCell>
                    <TableCell>
                      <ExpiryBadge days={doc.days_until_expiry} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {sortedDocuments.length === 0 && (
              <div className="text-center py-8">
                <Text className="text-gray-500">
                  Keine Dokumente gefunden. Passen Sie die Filter an.
                </Text>
              </div>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Document Type Distribution */}
          <Card>
            <Title>Dokumenttypen</Title>
            <Text className="mb-4">Verteilung nach Art</Text>
            <div className="space-y-3">
              {uniqueTypes.map((type) => {
                const count = mockDocuments.filter(d => d.type === type).length;
                return (
                  <div key={type} className="flex items-center justify-between">
                    <Text className="text-sm">{type}</Text>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${(count / totalDocuments) * 100}%` }}
                        />
                      </div>
                      <Text className="text-sm font-medium w-6 text-right">{count}</Text>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Recent Maintenance Reports */}
          <Card>
            <Title>Wartungsberichte</Title>
            <Text className="mb-4">Letzte Uploads</Text>
            <div className="space-y-3">
              {mockMaintenanceReports.map((report) => (
                <div key={report.id} className="border-l-4 border-green-500 pl-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-medium">{report.id}</span>
                    <Badge size="xs" color="gray">{report.file_size}</Badge>
                  </div>
                  <div className="text-sm text-gray-700 mt-1">{report.type}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    <div>Lok: {report.locomotive_id}</div>
                    <div>WO: {report.wo_id}</div>
                    <div className="mt-1">
                      {new Date(report.date).toLocaleDateString('de-DE')} • {report.uploaded_by}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <button className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium">
                Alle Berichte anzeigen →
              </button>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card>
            <Title>Aktionen</Title>
            <div className="mt-4 space-y-2">
              <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
                Dokument hochladen
              </button>
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">
                Ablauf-Erinnerungen
              </button>
              <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">
                Export (PDF)
              </button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper component for document status badges
function DocumentStatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: 'green' | 'orange' | 'red' | 'gray' }> = {
    valid: { label: 'Gültig', color: 'green' },
    expiring_soon: { label: 'Läuft ab', color: 'orange' },
    expired: { label: 'Abgelaufen', color: 'red' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}

// Helper component for expiry badge
function ExpiryBadge({ days }: { days: number }) {
  if (days < 0) {
    return (
      <span className="text-red-600 font-medium text-sm">
        {Math.abs(days)} Tage überfällig
      </span>
    );
  }

  if (days <= 30) {
    return <span className="text-red-600 font-medium text-sm">in {days} Tagen</span>;
  }

  if (days <= 180) {
    return <span className="text-orange-600 font-medium text-sm">in {days} Tagen</span>;
  }

  return <span className="text-gray-600 text-sm">in {days} Tagen</span>;
}
