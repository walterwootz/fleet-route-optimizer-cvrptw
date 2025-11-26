/**
 * Procurement Page
 * Purchase orders and supplier management
 */

import { useEffect, useMemo } from 'react';
import { Card, Title, Text, Badge, Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, Select, SelectItem, Metric } from '@tremor/react';
import { Package, ShoppingCart, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { useProcurementStore } from '@/stores/procurementStore';
import { PurchaseOrderStatus } from '@/services/procurementApi';

export function Procurement() {
  const {
    purchaseOrders,
    suppliers,
    loading,
    error,
    statusFilter,
    setStatusFilter,
    fetchPurchaseOrders,
    fetchSuppliers,
  } = useProcurementStore();

  // Load data on mount
  useEffect(() => {
    fetchPurchaseOrders();
    fetchSuppliers({ is_active: true });
  }, [fetchPurchaseOrders, fetchSuppliers]);

  // Filter purchase orders
  const filteredOrders = useMemo(() => {
    return purchaseOrders.filter((po) => {
      const matchesStatus = statusFilter === 'all' || po.status === statusFilter;
      return matchesStatus;
    });
  }, [purchaseOrders, statusFilter]);

  // Get supplier name by ID
  const getSupplierName = (supplierId: string): string => {
    const supplier = suppliers.find(s => s.id === supplierId);
    return supplier ? supplier.name : supplierId;
  };

  // Calculate statistics
  const totalOrders = purchaseOrders.length;
  const draftOrders = purchaseOrders.filter(po => po.status === PurchaseOrderStatus.DRAFT).length;
  const approvedOrders = purchaseOrders.filter(po => po.status === PurchaseOrderStatus.APPROVED).length;
  const orderedOrders = purchaseOrders.filter(po => po.status === PurchaseOrderStatus.ORDERED).length;
  const receivedOrders = purchaseOrders.filter(po => po.status === PurchaseOrderStatus.RECEIVED).length;

  // Calculate total value
  const totalValue = purchaseOrders.reduce((sum, po) => sum + po.total_amount, 0);

  // Loading state
  if (loading && purchaseOrders.length === 0) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={48} />
          <Text className="text-gray-600">Lade Bestellungen...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Title>Beschaffung</Title>
        <Text>Bestellungen und Lieferanten</Text>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-l-4 border-red-500 bg-red-50">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="text-red-600 mt-1" size={20} />
            <div>
              <Title className="text-red-900">Fehler beim Laden</Title>
              <Text className="text-red-700">{error}</Text>
            </div>
          </div>
        </Card>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <Text>Gesamtwert</Text>
          <Metric>€{totalValue.toLocaleString('de-DE')}</Metric>
          <Text className="text-gray-500 text-xs mt-1">{totalOrders} Bestellungen</Text>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gray-100 rounded-lg">
              <Package className="text-gray-600" size={20} />
            </div>
            <div>
              <Text>Entwurf</Text>
              <Metric className="text-gray-600">{draftOrders}</Metric>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={20} />
            </div>
            <div>
              <Text>Genehmigt</Text>
              <Metric className="text-green-600">{approvedOrders}</Metric>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <ShoppingCart className="text-blue-600" size={20} />
            </div>
            <div>
              <Text>Bestellt</Text>
              <Metric className="text-blue-600">{orderedOrders}</Metric>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Package className="text-purple-600" size={20} />
            </div>
            <div>
              <Text>Erhalten</Text>
              <Metric className="text-purple-600">{receivedOrders}</Metric>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as PurchaseOrderStatus | 'all')}>
          <SelectItem value="all">Alle Status</SelectItem>
          <SelectItem value={PurchaseOrderStatus.DRAFT}>Entwurf</SelectItem>
          <SelectItem value={PurchaseOrderStatus.APPROVED}>Genehmigt</SelectItem>
          <SelectItem value={PurchaseOrderStatus.ORDERED}>Bestellt</SelectItem>
          <SelectItem value={PurchaseOrderStatus.RECEIVED}>Erhalten</SelectItem>
          <SelectItem value={PurchaseOrderStatus.CLOSED}>Abgeschlossen</SelectItem>
          <SelectItem value={PurchaseOrderStatus.CANCELLED}>Storniert</SelectItem>
        </Select>
      </Card>

      {/* Purchase Orders Table */}
      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Bestellnummer</TableHeaderCell>
              <TableHeaderCell>Lieferant</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Bestelldatum</TableHeaderCell>
              <TableHeaderCell>Lieferdatum</TableHeaderCell>
              <TableHeaderCell>Positionen</TableHeaderCell>
              <TableHeaderCell>Gesamtbetrag</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredOrders.map((po) => (
              <TableRow key={po.id}>
                <TableCell>
                  <span className="font-mono font-medium">{po.po_number}</span>
                </TableCell>
                <TableCell>
                  <Text>{getSupplierName(po.supplier_id)}</Text>
                </TableCell>
                <TableCell>
                  <StatusBadge status={po.status} />
                </TableCell>
                <TableCell>
                  {po.order_date ? (
                    <Text className="text-xs">
                      {new Date(po.order_date).toLocaleDateString('de-DE')}
                    </Text>
                  ) : (
                    <Text className="text-xs text-gray-500">-</Text>
                  )}
                </TableCell>
                <TableCell>
                  {po.expected_delivery_date ? (
                    <Text className="text-xs">
                      {new Date(po.expected_delivery_date).toLocaleDateString('de-DE')}
                    </Text>
                  ) : (
                    <Text className="text-xs text-gray-500">-</Text>
                  )}
                </TableCell>
                <TableCell>
                  <Badge color="blue">{po.lines.length} Positionen</Badge>
                </TableCell>
                <TableCell>
                  <Text className="font-medium">
                    €{po.total_amount.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Text>
                  <Text className="text-xs text-gray-500">{po.currency}</Text>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {filteredOrders.length === 0 && !loading && (
          <div className="text-center py-8">
            <Text className="text-gray-500">
              {purchaseOrders.length === 0
                ? 'Keine Bestellungen vorhanden. Erstellen Sie eine neue Bestellung.'
                : 'Keine Bestellungen gefunden. Passen Sie die Filter an.'}
            </Text>
          </div>
        )}
      </Card>

      {/* Suppliers Overview */}
      <Card>
        <Title>Aktive Lieferanten</Title>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          {suppliers.slice(0, 6).map((supplier) => (
            <div key={supplier.id} className="p-4 bg-gray-50 rounded-lg">
              <Text className="font-medium">{supplier.name}</Text>
              <Text className="text-xs text-gray-500">{supplier.supplier_code}</Text>
              {supplier.payment_terms && (
                <Badge size="xs" color="gray" className="mt-2">
                  {supplier.payment_terms}
                </Badge>
              )}
            </div>
          ))}
        </div>
        {suppliers.length === 0 && !loading && (
          <Text className="text-gray-500 text-center py-4">Keine Lieferanten vorhanden.</Text>
        )}
      </Card>
    </div>
  );
}

// Helper component for status badges
function StatusBadge({ status }: { status: PurchaseOrderStatus }) {
  const statusConfig: Record<PurchaseOrderStatus, { label: string; color: 'blue' | 'orange' | 'green' | 'red' | 'gray' | 'purple' }> = {
    [PurchaseOrderStatus.DRAFT]: { label: 'Entwurf', color: 'gray' },
    [PurchaseOrderStatus.APPROVED]: { label: 'Genehmigt', color: 'green' },
    [PurchaseOrderStatus.ORDERED]: { label: 'Bestellt', color: 'blue' },
    [PurchaseOrderStatus.RECEIVED]: { label: 'Erhalten', color: 'purple' },
    [PurchaseOrderStatus.CLOSED]: { label: 'Abgeschlossen', color: 'gray' },
    [PurchaseOrderStatus.CANCELLED]: { label: 'Storniert', color: 'red' },
  };

  const config = statusConfig[status] || { label: status, color: 'gray' };

  return <Badge color={config.color}>{config.label}</Badge>;
}
