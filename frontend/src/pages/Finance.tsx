/**
 * Finance Page
 * Invoices and budget management
 */

import { useState } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric, BarList } from '@tremor/react';
import { DollarSign, FileText, TrendingUp, AlertCircle } from 'lucide-react';

// Mock data
const mockInvoices = [
  { id: 'INV-987', invoice_number: 'RE-2025-001', supplier: 'Siemens Mobility', amount: 15000, currency: 'EUR', status: 'pending_approval', related_wo: 'WO-12345', created_at: '2025-11-24' },
  { id: 'INV-988', invoice_number: 'RE-2025-002', supplier: 'Bombardier', amount: 8500, currency: 'EUR', status: 'approved', related_wo: 'WO-12346', created_at: '2025-11-22' },
  { id: 'INV-989', invoice_number: 'RE-2025-003', supplier: 'Knorr-Bremse', amount: 3200, currency: 'EUR', status: 'paid', related_wo: 'WO-12347', created_at: '2025-11-20' },
  { id: 'INV-990', invoice_number: 'RE-2025-004', supplier: 'SKF Lager', amount: 1850, currency: 'EUR', status: 'paid', related_wo: 'WO-12348', created_at: '2025-11-18' },
  { id: 'INV-991', invoice_number: 'RE-2025-005', supplier: 'Vossloh', amount: 12000, currency: 'EUR', status: 'overdue', related_wo: null, created_at: '2025-10-15' },
  { id: 'INV-992', invoice_number: 'RE-2025-006', supplier: 'Faiveley Transport', amount: 4500, currency: 'EUR', status: 'approved', related_wo: 'WO-12349', created_at: '2025-11-23' },
];

export function Finance() {
  const [statusFilter, setStatusFilter] = useState('all');

  // Filter invoices
  const filteredInvoices = mockInvoices.filter((inv) => {
    if (statusFilter === 'all') return true;
    return inv.status === statusFilter;
  });

  // Calculate statistics
  const totalInvoices = mockInvoices.length;
  const pendingInvoices = mockInvoices.filter(i => i.status === 'pending_approval').length;
  const overdueInvoices = mockInvoices.filter(i => i.status === 'overdue').length;
  const paidInvoices = mockInvoices.filter(i => i.status === 'paid').length;

  const totalAmount = mockInvoices.reduce((sum, inv) => sum + inv.amount, 0);
  const pendingAmount = mockInvoices.filter(i => i.status === 'pending_approval' || i.status === 'approved').reduce((sum, inv) => sum + inv.amount, 0);
  const paidAmount = mockInvoices.filter(i => i.status === 'paid').reduce((sum, inv) => sum + inv.amount, 0);
  const overdueAmount = mockInvoices.filter(i => i.status === 'overdue').reduce((sum, inv) => sum + inv.amount, 0);

  // Spending by supplier
  const supplierSpending = Object.entries(
    mockInvoices.reduce((acc, inv) => {
      acc[inv.supplier] = (acc[inv.supplier] || 0) + inv.amount;
      return acc;
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  // Budget data (mock)
  const budget = {
    total: 500000,
    spent: totalAmount,
    remaining: 500000 - totalAmount,
    percentage: (totalAmount / 500000) * 100
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Finanzen</Title>
        <Text>Rechnungen und Budget-Verwaltung</Text>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Gesamt Rechnungen</Text>
              <Metric>€{totalAmount.toLocaleString('de-DE')}</Metric>
              <Text className="text-xs text-gray-500 mt-1">{totalInvoices} Rechnungen</Text>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="text-blue-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Ausstehend</Text>
              <Metric className="text-yellow-600">€{pendingAmount.toLocaleString('de-DE')}</Metric>
              <Text className="text-xs text-gray-500 mt-1">{pendingInvoices} Rechnungen</Text>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertCircle className="text-yellow-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Überfällig</Text>
              <Metric className="text-red-600">€{overdueAmount.toLocaleString('de-DE')}</Metric>
              <Text className="text-xs text-gray-500 mt-1">{overdueInvoices} Rechnungen</Text>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="text-red-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Bezahlt</Text>
              <Metric className="text-green-600">€{paidAmount.toLocaleString('de-DE')}</Metric>
              <Text className="text-xs text-gray-500 mt-1">{paidInvoices} Rechnungen</Text>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <DollarSign className="text-green-600" size={20} />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Invoices Table */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <Title>Rechnungen</Title>
                <Text>{filteredInvoices.length} von {totalInvoices}</Text>
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter} className="w-48">
                <SelectItem value="all">Alle Status</SelectItem>
                <SelectItem value="pending_approval">Ausstehend</SelectItem>
                <SelectItem value="approved">Genehmigt</SelectItem>
                <SelectItem value="paid">Bezahlt</SelectItem>
                <SelectItem value="overdue">Überfällig</SelectItem>
              </Select>
            </div>

            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Rechnung</TableHeaderCell>
                  <TableHeaderCell>Lieferant</TableHeaderCell>
                  <TableHeaderCell>Betrag</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>WO</TableHeaderCell>
                  <TableHeaderCell>Datum</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredInvoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell>
                      <div>
                        <div className="font-mono font-medium text-sm">{inv.invoice_number}</div>
                        <div className="font-mono text-xs text-gray-500">{inv.id}</div>
                      </div>
                    </TableCell>
                    <TableCell>{inv.supplier}</TableCell>
                    <TableCell>
                      <span className="font-medium">
                        €{inv.amount.toLocaleString('de-DE')}
                      </span>
                    </TableCell>
                    <TableCell>
                      <InvoiceStatusBadge status={inv.status} />
                    </TableCell>
                    <TableCell>
                      {inv.related_wo ? (
                        <span className="font-mono text-sm">{inv.related_wo}</span>
                      ) : (
                        <Badge color="gray">Kein WO</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {new Date(inv.created_at).toLocaleDateString('de-DE')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </div>

        {/* Budget & Supplier Stats */}
        <div className="space-y-6">
          {/* Budget Card */}
          <Card>
            <Title>Jahresbudget 2025</Title>
            <Text className="mb-4">Ausgaben im Überblick</Text>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Text>Gesamtbudget</Text>
                  <Text className="font-medium">€{budget.total.toLocaleString('de-DE')}</Text>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <Text>Ausgegeben</Text>
                  <Text className="font-medium text-red-600">
                    €{budget.spent.toLocaleString('de-DE')}
                  </Text>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <Text>Verfügbar</Text>
                  <Text className="font-medium text-green-600">
                    €{budget.remaining.toLocaleString('de-DE')}
                  </Text>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-sm">Budgetauslastung</Text>
                  <Text className="text-sm font-medium">{budget.percentage.toFixed(1)}%</Text>
                </div>
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      budget.percentage >= 90 ? 'bg-red-500' :
                      budget.percentage >= 75 ? 'bg-orange-500' :
                      'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(budget.percentage, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Top Suppliers */}
          <Card>
            <Title>Top Lieferanten</Title>
            <Text className="mb-4">Nach Ausgaben</Text>
            <BarList data={supplierSpending} valueFormatter={(value) => `€${value.toLocaleString('de-DE')}`} />
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper component for invoice status badges
function InvoiceStatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: 'yellow' | 'blue' | 'green' | 'red' | 'gray' }> = {
    pending_approval: { label: 'Ausstehend', color: 'yellow' },
    approved: { label: 'Genehmigt', color: 'blue' },
    paid: { label: 'Bezahlt', color: 'green' },
    overdue: { label: 'Überfällig', color: 'red' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
