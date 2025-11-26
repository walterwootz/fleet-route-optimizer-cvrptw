/**
 * Procurement Zustand Store
 * Manages suppliers, purchase orders, and procurement state
 */

import { create } from 'zustand';
import { procurementApi } from '@/services/procurementApi';
import type {
  Supplier,
  SupplierCreate,
  PurchaseOrder,
  PurchaseOrderCreate,
  PurchaseOrderStatus,
} from '@/services/procurementApi';

interface ProcurementStore {
  // ===== STATE =====
  suppliers: Supplier[];
  purchaseOrders: PurchaseOrder[];
  loading: boolean;
  error: string | null;

  // Filters
  statusFilter: PurchaseOrderStatus | 'all';
  supplierFilter: string | 'all';

  // ===== ACTIONS =====

  // Suppliers
  fetchSuppliers: (params?: { is_active?: boolean; search?: string }) => Promise<void>;
  createSupplier: (supplier: SupplierCreate) => Promise<Supplier | null>;

  // Purchase Orders
  fetchPurchaseOrders: (params?: {
    status?: PurchaseOrderStatus;
    supplier_id?: string;
  }) => Promise<void>;
  createPurchaseOrder: (po: PurchaseOrderCreate) => Promise<PurchaseOrder | null>;
  approvePurchaseOrder: (poId: string, approvedBy: string) => Promise<PurchaseOrder | null>;

  // Filters
  setStatusFilter: (status: PurchaseOrderStatus | 'all') => void;
  setSupplierFilter: (supplier: string | 'all') => void;

  // UI
  clearError: () => void;
}

export const useProcurementStore = create<ProcurementStore>((set, get) => ({
  // ===== INITIAL STATE =====
  suppliers: [],
  purchaseOrders: [],
  loading: false,
  error: null,
  statusFilter: 'all',
  supplierFilter: 'all',

  // ===== SUPPLIERS =====

  fetchSuppliers: async (params) => {
    set({ loading: true, error: null });

    try {
      const response = await procurementApi.listSuppliers(params);
      set({ suppliers: response.suppliers, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch suppliers';
      set({ error: errorMsg, loading: false });
    }
  },

  createSupplier: async (supplier: SupplierCreate) => {
    set({ loading: true, error: null });

    try {
      const newSupplier = await procurementApi.createSupplier(supplier);

      set((state) => ({
        suppliers: [newSupplier, ...state.suppliers],
        loading: false,
      }));

      return newSupplier;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create supplier';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  // ===== PURCHASE ORDERS =====

  fetchPurchaseOrders: async (params) => {
    set({ loading: true, error: null });

    try {
      const response = await procurementApi.listPurchaseOrders(params);
      set({ purchaseOrders: response.purchase_orders, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch purchase orders';
      set({ error: errorMsg, loading: false });
    }
  },

  createPurchaseOrder: async (po: PurchaseOrderCreate) => {
    set({ loading: true, error: null });

    try {
      const newPO = await procurementApi.createPurchaseOrder(po);

      set((state) => ({
        purchaseOrders: [newPO, ...state.purchaseOrders],
        loading: false,
      }));

      return newPO;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create purchase order';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  approvePurchaseOrder: async (poId: string, approvedBy: string) => {
    set({ loading: true, error: null });

    try {
      const approvedPO = await procurementApi.approvePurchaseOrder(poId, approvedBy);

      set((state) => ({
        purchaseOrders: state.purchaseOrders.map((po) =>
          po.id === poId ? approvedPO : po
        ),
        loading: false,
      }));

      return approvedPO;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to approve purchase order';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  // ===== FILTERS =====

  setStatusFilter: (status: PurchaseOrderStatus | 'all') => {
    set({ statusFilter: status });
  },

  setSupplierFilter: (supplier: string | 'all') => {
    set({ supplierFilter: supplier });
  },

  // ===== UI =====

  clearError: () => {
    set({ error: null });
  },
}));
