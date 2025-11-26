/**
 * Procurement API Service
 * Handles suppliers and purchase orders
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// ============================================================================
// ENUMS
// ============================================================================

export enum PurchaseOrderStatus {
  DRAFT = 'draft',
  APPROVED = 'approved',
  ORDERED = 'ordered',
  RECEIVED = 'received',
  CLOSED = 'closed',
  CANCELLED = 'cancelled',
}

// ============================================================================
// TYPES
// ============================================================================

export interface Supplier {
  id: string;
  supplier_code: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  payment_terms?: string;
  vat_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  supplier_code: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  payment_terms?: string;
  vat_id?: string;
}

export interface PurchaseOrderLine {
  id?: string;
  purchase_order_id?: string;
  line_number: number;
  part_no: string;
  description: string;
  quantity_ordered: number;
  quantity_received?: number;
  unit_price: number;
  line_total: number;
  notes?: string;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  supplier_id: string;
  work_order_id?: string;
  status: PurchaseOrderStatus;
  order_date?: string;
  expected_delivery_date?: string;
  received_date?: string;
  delivery_location_id?: string;
  total_amount: number;
  currency: string;
  notes?: string;
  created_by?: string;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
  lines: PurchaseOrderLine[];
}

export interface PurchaseOrderCreate {
  po_number: string;
  supplier_id: string;
  work_order_id?: string;
  expected_delivery_date?: string;
  delivery_location_id?: string;
  currency?: string;
  notes?: string;
  lines: Omit<PurchaseOrderLine, 'id' | 'purchase_order_id' | 'line_total'>[];
}

export interface ListSuppliersParams {
  skip?: number;
  limit?: number;
  is_active?: boolean;
  search?: string;
}

export interface ListPurchaseOrdersParams {
  skip?: number;
  limit?: number;
  status?: PurchaseOrderStatus;
  supplier_id?: string;
}

// ============================================================================
// API CLIENT
// ============================================================================

export class ProcurementAPI {
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

  // ===== SUPPLIERS =====

  async createSupplier(supplier: SupplierCreate): Promise<Supplier> {
    const response = await this.client.post<Supplier>('/suppliers', supplier);
    return response.data;
  }

  async listSuppliers(params?: ListSuppliersParams): Promise<{ total: number; suppliers: Supplier[] }> {
    const response = await this.client.get<{ total: number; suppliers: Supplier[] }>('/suppliers', {
      params,
    });
    return response.data;
  }

  async getSupplier(supplierId: string): Promise<Supplier> {
    const response = await this.client.get<Supplier>(`/suppliers/${supplierId}`);
    return response.data;
  }

  // ===== PURCHASE ORDERS =====

  async createPurchaseOrder(po: PurchaseOrderCreate): Promise<PurchaseOrder> {
    const response = await this.client.post<PurchaseOrder>('/purchase_orders', po);
    return response.data;
  }

  async listPurchaseOrders(params?: ListPurchaseOrdersParams): Promise<{ total: number; purchase_orders: PurchaseOrder[] }> {
    const response = await this.client.get<{ total: number; purchase_orders: PurchaseOrder[] }>('/purchase_orders', {
      params,
    });
    return response.data;
  }

  async getPurchaseOrder(poId: string): Promise<PurchaseOrder> {
    const response = await this.client.get<PurchaseOrder>(`/purchase_orders/${poId}`);
    return response.data;
  }

  async approvePurchaseOrder(poId: string, approved_by: string): Promise<PurchaseOrder> {
    const response = await this.client.post<PurchaseOrder>(`/purchase_orders/${poId}/approve`, {
      approved_by,
    });
    return response.data;
  }

  async receivePurchaseOrder(poId: string, lines: { line_id: string; quantity_received: number }[]): Promise<PurchaseOrder> {
    const response = await this.client.post<PurchaseOrder>(`/purchase_orders/${poId}/receive`, {
      lines,
    });
    return response.data;
  }
}

// Export singleton instance
export const procurementApi = new ProcurementAPI();
