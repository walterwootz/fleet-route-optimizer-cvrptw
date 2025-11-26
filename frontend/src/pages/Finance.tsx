/**
 * Finance Page
 * Invoices and budget management
 */

import { useEffect, useMemo } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric, BarList } from '@tremor/react';
import { DollarSign, FileText, TrendingUp, AlertCircle, Loader2 } from 'lucide-react';
import { useFinanceStore } from '@/stores/financeStore';
import { InvoiceStatus } from '@/services/financeApi';

export function Finance() {
  const {
    invoices,
    budgetOverview,
    loading,
    error,
    statusFilter,
    setStatusFilter,
    fetchInvoices,
    fetchBudgetOverview,
  } = useFinanceStore();

  // Load data on mount
  useEffect(() => {
    fetchInvoices();
    fetchBudgetOverview(new Date().getFullYear());
  }, [fetchInvoices, fetchBudgetOverview]);

  // Filter invoices
  const filteredInvoices = useMemo(() => {
    return invoices.filter((inv) => {
      const matchesStatus = statusFilter === 'all' || inv.status === statusFilter;
      return matchesStatus;
    });
  }, [invoices, statusFilter]);

  // Calculate statistics
  const totalInvoices = invoices.length;
  const draftInvoices = invoices.filter(i => i.status === InvoiceStatus.DRAFT).length;
  const reviewedInvoices = invoices.filter(i => i.status === InvoiceStatus.REVIEWED).length;
  const approvedInvoices = invoices.filter(i => i.status === InvoiceStatus.APPROVED).length;
  const exportedInvoices = invoices.filter(i => i.status === InvoiceStatus.EXPORTED).length;

  const totalAmount = invoices.reduce((sum, inv) => sum + inv.total_amount, 0);
  const pendingAmount = invoices.filter(i => i.status === InvoiceStatus.DRAFT || i.status === InvoiceStatus.REVIEWED).reduce((sum, inv) => sum + inv.total_amount, 0);
  const approvedAmount = invoices.filter(i => i.status === InvoiceStatus.APPROVED || i.status === InvoiceStatus.EXPORTED).reduce((sum, inv) => sum + inv.total_amount, 0);

  // Loading state
  if (loading && invoices.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={48} />
          <Text className="text-gray-600">Lade Finanzdaten...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Finanzen</Title>
        <Text>Rechnungen und Budget-Verwaltung</Text>
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
              <Text>Entwurf</Text>
              <Metric className="text-gray-600">{draftInvoices}</Metric>
            </div>
            <div className="p-3 bg-gray-100 rounded-lg">
              <FileText className="text-gray-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Zu prüfen</Text>
              <Metric className="text-yellow-600">{reviewedInvoices}</Metric>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertCircle className="text-yellow-600" size={20} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <Text>Genehmigt</Text>
              <Metric className="text-green-600">{approvedInvoices}</Metric>
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
              <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as InvoiceStatus | 'all')} className="w-48">
                <SelectItem value="all">Alle Status</SelectItem>
                <SelectItem value={InvoiceStatus.DRAFT}>Entwurf</SelectItem>
                <SelectItem value={InvoiceStatus.REVIEWED}>Geprüft</SelectItem>
                <SelectItem value={InvoiceStatus.APPROVED}>Genehmigt</SelectItem>
                <SelectItem value={InvoiceStatus.EXPORTED}>Exportiert</SelectItem>
                <SelectItem value={InvoiceStatus.REJECTED}>Abgelehnt</SelectItem>
              </Select>
            </div>

            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Rechnung</TableHeaderCell>
                  <TableHeaderCell>Lieferant</TableHeaderCell>
                  <TableHeaderCell>Betrag</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Fällig</TableHeaderCell>
                  <TableHeaderCell>Datum</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredInvoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell>
                      <div>
                        <div className="font-mono font-medium text-sm">{inv.invoice_number}</div>
                        <div className="text-xs text-gray-500">{inv.lines.length} Positionen</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Text className="text-sm">{inv.supplier_id.substring(0, 8)}...</Text>
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">
                        €{inv.total_amount.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                      <Text className="text-xs text-gray-500">{inv.currency}</Text>
                    </TableCell>
                    <TableCell>
                      <InvoiceStatusBadge status={inv.status} />
                    </TableCell>
                    <TableCell>
                      <Text className="text-xs">
                        {new Date(inv.due_date).toLocaleDateString('de-DE')}
                      </Text>
                    </TableCell>
                    <TableCell>
                      <Text className="text-xs">
                        {new Date(inv.invoice_date).toLocaleDateString('de-DE')}
                      </Text>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {filteredInvoices.length === 0 && !loading && (
              <div className="text-center py-8">
                <Text className="text-gray-500">
                  {invoices.length === 0
                    ? 'Keine Rechnungen vorhanden.'
                    : 'Keine Rechnungen gefunden. Passen Sie die Filter an.'}
                </Text>
              </div>
            )}
          </Card>
        </div>

        {/* Budget & Stats */}
        <div className="space-y-6">
          {/* Budget Card */}
          {budgetOverview && (
            <Card>
              <Title>Budget-Übersicht {new Date().getFullYear()}</Title>
              <Text className="mb-4">Ausgaben im Überblick</Text>

              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Text>Gesamt Budget</Text>
                    <Text className="font-medium">
                      €{budgetOverview.total_allocated.toLocaleString('de-DE')}
                    </Text>
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <Text>Ausgegeben</Text>
                    <Text className="font-medium text-red-600">
                      €{budgetOverview.total_spent.toLocaleString('de-DE')}
                    </Text>
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <Text>Verfügbar</Text>
                    <Text className="font-medium text-green-600">
                      €{budgetOverview.total_available.toLocaleString('de-DE')}
                    </Text>
                  </div>
                </div>

                <div>
                  {budgetOverview.total_allocated > 0 && (
                    <>
                      <div className="flex items-center justify-between mb-2">
                        <Text className="text-sm">Budgetauslastung</Text>
                        <Text className="text-sm font-medium">
                          {((budgetOverview.total_spent / budgetOverview.total_allocated) * 100).toFixed(1)}%
                        </Text>
                      </div>
                      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            (budgetOverview.total_spent / budgetOverview.total_allocated) * 100 >= 90 ? 'bg-red-500' :
                            (budgetOverview.total_spent / budgetOverview.total_allocated) * 100 >= 75 ? 'bg-orange-500' :
                            'bg-blue-500'
                          }`}
                          style={{
                            width: `${Math.min((budgetOverview.total_spent / budgetOverview.total_allocated) * 100, 100)}%`
                          }}
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Cost Centers */}
          {budgetOverview && budgetOverview.by_cost_center.length > 0 && (
            <Card>
              <Title>Kostenstellen</Title>
              <Text className="mb-4">Top 5 nach Ausgaben</Text>
              <BarList
                data={budgetOverview.by_cost_center
                  .slice(0, 5)
                  .map(cc => ({
                    name: cc.cost_center_code,
                    value: cc.spent,
                  }))}
                valueFormatter={(value) => `€${value.toLocaleString('de-DE')}`}
              />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper component for invoice status badges
function InvoiceStatusBadge({ status }: { status: InvoiceStatus }) {
  const statusConfig: Record<InvoiceStatus, { label: string; color: 'yellow' | 'blue' | 'green' | 'red' | 'gray' }> = {
    [InvoiceStatus.DRAFT]: { label: 'Entwurf', color: 'gray' },
    [InvoiceStatus.REVIEWED]: { label: 'Geprüft', color: 'yellow' },
    [InvoiceStatus.APPROVED]: { label: 'Genehmigt', color: 'green' },
    [InvoiceStatus.EXPORTED]: { label: 'Exportiert', color: 'blue' },
    [InvoiceStatus.REJECTED]: { label: 'Abgelehnt', color: 'red' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
