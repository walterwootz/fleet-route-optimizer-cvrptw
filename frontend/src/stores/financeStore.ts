/**
 * Finance Zustand Store
 * Manages invoices, budgets, and cost centers
 */

import { create } from 'zustand';
import { financeApi } from '@/services/financeApi';
import type {
  Invoice,
  InvoiceCreate,
  InvoiceStatus,
  BudgetOverview,
  CostCenter,
} from '@/services/financeApi';

interface FinanceStore {
  // ===== STATE =====
  invoices: Invoice[];
  budgetOverview: BudgetOverview | null;
  costCenters: CostCenter[];
  loading: boolean;
  error: string | null;

  // Filters
  statusFilter: InvoiceStatus | 'all';

  // ===== ACTIONS =====

  // Invoices
  fetchInvoices: (params?: { status?: InvoiceStatus; supplier_id?: string }) => Promise<void>;
  createInvoice: (invoice: InvoiceCreate) => Promise<Invoice | null>;
  approveInvoice: (invoiceId: string, approvedBy: string) => Promise<Invoice | null>;

  // Budgets
  fetchBudgetOverview: (fiscalYear?: number) => Promise<void>;

  // Cost Centers
  fetchCostCenters: () => Promise<void>;

  // Filters
  setStatusFilter: (status: InvoiceStatus | 'all') => void;

  // UI
  clearError: () => void;
}

export const useFinanceStore = create<FinanceStore>((set, get) => ({
  // ===== INITIAL STATE =====
  invoices: [],
  budgetOverview: null,
  costCenters: [],
  loading: false,
  error: null,
  statusFilter: 'all',

  // ===== INVOICES =====

  fetchInvoices: async (params) => {
    set({ loading: true, error: null });

    try {
      const response = await financeApi.listInvoices(params);
      set({ invoices: response.invoices, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch invoices';
      set({ error: errorMsg, loading: false });
    }
  },

  createInvoice: async (invoice: InvoiceCreate) => {
    set({ loading: true, error: null });

    try {
      const newInvoice = await financeApi.createInvoice(invoice);

      set((state) => ({
        invoices: [newInvoice, ...state.invoices],
        loading: false,
      }));

      return newInvoice;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create invoice';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  approveInvoice: async (invoiceId: string, approvedBy: string) => {
    set({ loading: true, error: null });

    try {
      const approvedInvoice = await financeApi.approveInvoice(invoiceId, approvedBy);

      set((state) => ({
        invoices: state.invoices.map((inv) =>
          inv.id === invoiceId ? approvedInvoice : inv
        ),
        loading: false,
      }));

      return approvedInvoice;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to approve invoice';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  // ===== BUDGETS =====

  fetchBudgetOverview: async (fiscalYear) => {
    set({ loading: true, error: null });

    try {
      const overview = await financeApi.getBudgetOverview(fiscalYear);
      set({ budgetOverview: overview, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch budget overview';
      set({ error: errorMsg, loading: false });
    }
  },

  // ===== COST CENTERS =====

  fetchCostCenters: async () => {
    set({ loading: true, error: null });

    try {
      const response = await financeApi.listCostCenters();
      set({ costCenters: response.cost_centers, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch cost centers';
      set({ error: errorMsg, loading: false });
    }
  },

  // ===== FILTERS =====

  setStatusFilter: (status: InvoiceStatus | 'all') => {
    set({ statusFilter: status });
  },

  // ===== UI =====

  clearError: () => {
    set({ error: null });
  },
}));
