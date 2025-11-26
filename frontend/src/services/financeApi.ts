/**
 * Finance API Service
 * Handles invoices, budgets, and cost centers
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// ============================================================================
// ENUMS
// ============================================================================

export enum InvoiceStatus {
  DRAFT = 'draft',
  REVIEWED = 'reviewed',
  APPROVED = 'approved',
  EXPORTED = 'exported',
  REJECTED = 'rejected',
}

// ============================================================================
// TYPES
// ============================================================================

export interface InvoiceLine {
  id?: string;
  invoice_id?: string;
  line_number: number;
  description: string;
  quantity?: number;
  unit_price: number;
  tax_amount: number;
  part_no?: string;
  cost_center_code?: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  supplier_id: string;
  purchase_order_id?: string;
  work_order_id?: string;
  status: InvoiceStatus;
  invoice_date: string;
  due_date: string;
  received_date?: string;
  total_amount: number;
  tax_amount: number;
  currency: string;
  attachment_url?: string;
  notes?: string;
  created_by?: string;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
  lines: InvoiceLine[];
}

export interface InvoiceCreate {
  invoice_number: string;
  supplier_id: string;
  purchase_order_id?: string;
  work_order_id?: string;
  invoice_date: string;
  due_date: string;
  currency?: string;
  attachment_url?: string;
  notes?: string;
  lines: Omit<InvoiceLine, 'id' | 'invoice_id'>[];
}

export interface Budget {
  id: string;
  cost_center_code: string;
  fiscal_year: number;
  quarter?: number;
  month?: number;
  amount_allocated: number;
  amount_spent: number;
  amount_committed: number;
  amount_available: number;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface BudgetOverview {
  total_allocated: number;
  total_spent: number;
  total_committed: number;
  total_available: number;
  currency: string;
  by_cost_center: {
    cost_center_code: string;
    allocated: number;
    spent: number;
    committed: number;
    available: number;
  }[];
}

export interface CostCenter {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListInvoicesParams {
  skip?: number;
  limit?: number;
  status?: InvoiceStatus;
  supplier_id?: string;
}

// ============================================================================
// API CLIENT
// ============================================================================

export class FinanceAPI {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const token = localStorage.getItem('auth_token');
    if (token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // ===== INVOICES =====

  async createInvoice(invoice: InvoiceCreate): Promise<Invoice> {
    const response = await this.client.post<Invoice>('/invoices/inbox', invoice);
    return response.data;
  }

  async listInvoices(params?: ListInvoicesParams): Promise<{ total: number; invoices: Invoice[] }> {
    const response = await this.client.get<{ total: number; invoices: Invoice[] }>('/invoices', {
      params,
    });
    return response.data;
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    const response = await this.client.get<Invoice>(`/invoices/${invoiceId}`);
    return response.data;
  }

  async approveInvoice(invoiceId: string, approvedBy: string): Promise<Invoice> {
    const response = await this.client.post<Invoice>(`/invoices/${invoiceId}/approve`, {
      approved_by: approvedBy,
    });
    return response.data;
  }

  // ===== BUDGETS =====

  async getBudgetOverview(fiscalYear?: number): Promise<BudgetOverview> {
    const response = await this.client.get<BudgetOverview>('/budget/overview', {
      params: fiscalYear ? { fiscal_year: fiscalYear } : undefined,
    });
    return response.data;
  }

  async listBudgets(fiscalYear?: number): Promise<Budget[]> {
    const response = await this.client.get<Budget[]>('/budgets', {
      params: fiscalYear ? { fiscal_year: fiscalYear } : undefined,
    });
    return response.data;
  }

  // ===== COST CENTERS =====

  async listCostCenters(): Promise<{ total: number; cost_centers: CostCenter[] }> {
    const response = await this.client.get<{ total: number; cost_centers: CostCenter[] }>('/cost_centers');
    return response.data;
  }
}

// Export singleton instance
export const financeApi = new FinanceAPI();
