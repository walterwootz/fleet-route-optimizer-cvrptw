/**
 * Procurement Page
 * Parts inventory and purchase requests
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric, ProgressBar } from '@tremor/react';
import { Package, ShoppingCart, AlertTriangle, CheckCircle } from 'lucide-react';

// Mock data
const mockStock = [
  { part_no: 'P-45678', description: 'Bremsscheibe 330mm', available: 12, reserved: 5, free: 7, reorder_level: 20, status: 'low' },
  { part_no: 'P-99999', description: 'Luftfilter Standard', available: 0, reserved: 0, free: 0, reorder_level: 10, status: 'critical' },
  { part_no: 'P-12345', description: 'Ölfilter Diesel', available: 45, reserved: 8, free: 37, reorder_level: 15, status: 'ok' },
  { part_no: 'P-67890', description: 'Kupplungssatz', available: 8, reserved: 2, free: 6, reorder_level: 5, status: 'ok' },
  { part_no: 'P-11111', description: 'Achslager 200mm', available: 3, reserved: 3, free: 0, reorder_level: 8, status: 'critical' },
  { part_no: 'P-22222', description: 'Bremsbeläge Vorderachse', available: 18, reserved: 4, free: 14, reorder_level: 12, status: 'ok' },
  { part_no: 'P-33333', description: 'Dichtungssatz Motor', available: 25, reserved: 0, free: 25, reorder_level: 10, status: 'ok' },
  { part_no: 'P-44444', description: 'Kühlflüssigkeit 20L', available: 6, reserved: 2, free: 4, reorder_level: 15, status: 'low' },
];

const mockPurchaseRequests = [
  { id: 'PR-6789', part_no: 'P-45678', description: 'Bremsscheibe 330mm', qty: 50, needed_by: '2025-12-15', status: 'pending', related_wo: 'WO-12345' },
  { id: 'PR-6790', part_no: 'P-99999', description: 'Luftfilter Standard', qty: 20, needed_by: '2025-11-30', status: 'approved', related_wo: 'WO-12346' },
  { id: 'PR-6791', part_no: 'P-11111', description: 'Achslager 200mm', qty: 10, needed_by: '2025-12-05', status: 'ordered', related_wo: 'WO-12347' },
  { id: 'PR-6792', part_no: 'P-44444', description: 'Kühlflüssigkeit 20L', qty: 30, needed_by: '2025-12-10', status: 'pending', related_wo: null },
  { id: 'PR-6793', part_no: 'P-12345', description: 'Ölfilter Diesel', qty: 40, needed_by: '2025-12-20', status: 'delivered', related_wo: 'WO-12348' },
];

export function Procurement() {
  const [stockFilter, setStockFilter] = useState('all');
  const [requestFilter, setRequestFilter] = useState('all');

  // Filter stock
  const filteredStock = mockStock.filter((item) => {
    if (stockFilter === 'all') return true;
    return item.status === stockFilter;
  });

  // Filter requests
  const filteredRequests = mockPurchaseRequests.filter((req) => {
    if (requestFilter === 'all') return true;
    return req.status === requestFilter;
  });

  // Calculate statistics
  const totalParts = mockStock.length;
  const criticalParts = mockStock.filter(s => s.status === 'critical').length;
  const lowParts = mockStock.filter(s => s.status === 'low').length;
  const okParts = mockStock.filter(s => s.status === 'ok').length;

  const totalRequests = mockPurchaseRequests.length;
  const pendingRequests = mockPurchaseRequests.filter(r => r.status === 'pending').length;
  const approvedRequests = mockPurchaseRequests.filter(r => r.status === 'approved').length;

  // Calculate total inventory value (mock)
  const totalValue = 125000;
  const monthlySpend = 18500;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Beschaffung</Title>
        <Text>Teile-Lager und Bestellungen</Text>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <Text>Lagerwert</Text>
          <Metric>€{totalValue.toLocaleString('de-DE')}</Metric>
          <Text className="text-gray-500 text-xs mt-1">{totalParts} Teile</Text>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Kritischer Bestand</Text>
              <Metric className="text-red-600">{criticalParts}</Metric>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertTriangle className="text-red-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Niedriger Bestand</Text>
              <Metric className="text-orange-600">{lowParts}</Metric>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <Package className="text-orange-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Monatl. Ausgaben</Text>
              <Metric>€{monthlySpend.toLocaleString('de-DE')}</Metric>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <ShoppingCart className="text-blue-600" size={20} />
            </div>
          </div>
        </Card>
      </div>

      {/* Stock Table */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <Title>Lagerbestand</Title>
            <Text>{filteredStock.length} von {totalParts} Teilen</Text>
          </div>
          <Select value={stockFilter} onValueChange={setStockFilter} className="w-48">
            <SelectItem value="all">Alle Teile</SelectItem>
            <SelectItem value="critical">Kritisch</SelectItem>
            <SelectItem value="low">Niedrig</SelectItem>
            <SelectItem value="ok">OK</SelectItem>
          </Select>
        </div>

        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Teil-Nr.</TableHeaderCell>
              <TableHeaderCell>Beschreibung</TableHeaderCell>
              <TableHeaderCell>Verfügbar</TableHeaderCell>
              <TableHeaderCell>Reserviert</TableHeaderCell>
              <TableHeaderCell>Frei</TableHeaderCell>
              <TableHeaderCell>Mindestbestand</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredStock.map((item) => (
              <TableRow key={item.part_no}>
                <TableCell>
                  <span className="font-mono font-medium">{item.part_no}</span>
                </TableCell>
                <TableCell>{item.description}</TableCell>
                <TableCell>{item.available}</TableCell>
                <TableCell>{item.reserved}</TableCell>
                <TableCell>
                  <span className={item.free === 0 ? 'text-red-600 font-medium' : ''}>
                    {item.free}
                  </span>
                </TableCell>
                <TableCell>{item.reorder_level}</TableCell>
                <TableCell>
                  <StockStatusBadge status={item.status} free={item.free} reorder={item.reorder_level} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Purchase Requests */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <Title>Bestellanforderungen</Title>
            <Text>{filteredRequests.length} Anfragen</Text>
          </div>
          <Select value={requestFilter} onValueChange={setRequestFilter} className="w-48">
            <SelectItem value="all">Alle Status</SelectItem>
            <SelectItem value="pending">Ausstehend</SelectItem>
            <SelectItem value="approved">Genehmigt</SelectItem>
            <SelectItem value="ordered">Bestellt</SelectItem>
            <SelectItem value="delivered">Geliefert</SelectItem>
          </Select>
        </div>

        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>PR-Nummer</TableHeaderCell>
              <TableHeaderCell>Teil</TableHeaderCell>
              <TableHeaderCell>Menge</TableHeaderCell>
              <TableHeaderCell>Benötigt bis</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Zugeordnet</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRequests.map((req) => (
              <TableRow key={req.id}>
                <TableCell>
                  <span className="font-mono font-medium">{req.id}</span>
                </TableCell>
                <TableCell>
                  <div>
                    <div className="font-mono text-xs text-gray-500">{req.part_no}</div>
                    <div className="text-sm">{req.description}</div>
                  </div>
                </TableCell>
                <TableCell>{req.qty} Stück</TableCell>
                <TableCell>
                  {new Date(req.needed_by).toLocaleDateString('de-DE')}
                </TableCell>
                <TableCell>
                  <RequestStatusBadge status={req.status} />
                </TableCell>
                <TableCell>
                  {req.related_wo ? (
                    <span className="font-mono text-sm">{req.related_wo}</span>
                  ) : (
                    <Badge color="gray">Kein WO</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

// Helper component for stock status badges
function StockStatusBadge({ status, free, reorder }: { status: string; free: number; reorder: number }) {
  if (free === 0) {
    return <Badge color="red">Leer</Badge>;
  }

  const statusConfig: Record<string, { label: string; color: 'red' | 'orange' | 'green' | 'gray' }> = {
    critical: { label: 'Kritisch', color: 'red' },
    low: { label: 'Niedrig', color: 'orange' },
    ok: { label: 'OK', color: 'green' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}

// Helper component for request status badges
function RequestStatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: 'yellow' | 'blue' | 'purple' | 'green' | 'gray' }> = {
    pending: { label: 'Ausstehend', color: 'yellow' },
    approved: { label: 'Genehmigt', color: 'blue' },
    ordered: { label: 'Bestellt', color: 'purple' },
    delivered: { label: 'Geliefert', color: 'green' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
