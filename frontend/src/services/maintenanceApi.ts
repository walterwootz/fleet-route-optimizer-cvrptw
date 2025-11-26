/**
 * Maintenance & Work Order API Service
 * Handles all HTTP communication with the Maintenance backend
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// ============================================================================
// ENUMS
// ============================================================================

export enum MaintenanceType {
  HU = 'HU',
  INSPECTION = 'INSPECTION',
  ECM = 'ECM',
  REPAIR = 'REPAIR',
  PREVENTIVE = 'PREVENTIVE',
}

export enum WorkOrderStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum WorkOrderPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

// ============================================================================
// TYPES
// ============================================================================

export interface MaintenanceTask {
  id: string;
  vehicle_id: string;
  type: MaintenanceType;
  description?: string;
  due_date: string; // ISO timestamp
  due_mileage_km?: number;
  is_overdue: boolean;
  is_completed: boolean;
  completed_at?: string; // ISO timestamp
  created_at: string; // ISO timestamp
}

export interface MaintenanceTaskCreate {
  vehicle_id: string;
  type: MaintenanceType;
  description?: string;
  due_date: string; // ISO timestamp
  due_mileage_km?: number;
}

export interface WorkOrder {
  id: string;
  order_number: string;
  vehicle_id: string;
  workshop_id?: string;
  status: WorkOrderStatus;
  priority: WorkOrderPriority;
  scheduled_start?: string; // ISO timestamp
  scheduled_end?: string; // ISO timestamp
  actual_start?: string; // ISO timestamp
  actual_end?: string; // ISO timestamp
  work_description?: string;
  work_performed?: string;
  findings?: string;
  tasks?: string[];
  estimated_cost?: number;
  actual_cost?: number;
  created_at: string; // ISO timestamp
  updated_at: string; // ISO timestamp
}

export interface WorkOrderCreate {
  vehicle_id: string;
  workshop_id?: string;
  priority?: WorkOrderPriority;
  scheduled_start?: string; // ISO timestamp
  scheduled_end?: string; // ISO timestamp
  work_description?: string;
  tasks?: string[];
}

export interface WorkOrderUpdate {
  status?: WorkOrderStatus;
  priority?: WorkOrderPriority;
  scheduled_start?: string; // ISO timestamp
  scheduled_end?: string; // ISO timestamp
  actual_start?: string; // ISO timestamp
  actual_end?: string; // ISO timestamp
  assigned_track?: string;
  assigned_team?: string;
  work_performed?: string;
  findings?: string;
  actual_cost?: number;
}

export interface ListWorkOrdersParams {
  skip?: number;
  limit?: number;
  status?: WorkOrderStatus;
  vehicle_id?: string;
  workshop_id?: string;
}

export interface ListMaintenanceTasksParams {
  skip?: number;
  limit?: number;
  vehicle_id?: string;
  overdue_only?: boolean;
}

// ============================================================================
// API CLIENT
// ============================================================================

export class MaintenanceAPI {
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

    // Add auth token from localStorage if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  /**
   * Set authentication token
   */
  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // ===== MAINTENANCE TASKS =====

  /**
   * Create a new maintenance task
   */
  async createMaintenanceTask(task: MaintenanceTaskCreate): Promise<MaintenanceTask> {
    const response = await this.client.post<MaintenanceTask>('/maintenance/tasks', task);
    return response.data;
  }

  /**
   * List maintenance tasks with filters
   */
  async listMaintenanceTasks(params?: ListMaintenanceTasksParams): Promise<MaintenanceTask[]> {
    const response = await this.client.get<MaintenanceTask[]>('/maintenance/tasks', {
      params,
    });
    return response.data;
  }

  // ===== WORK ORDERS =====

  /**
   * Create a new work order
   */
  async createWorkOrder(order: WorkOrderCreate): Promise<WorkOrder> {
    const response = await this.client.post<WorkOrder>('/maintenance/orders', order);
    return response.data;
  }

  /**
   * List work orders with filters
   */
  async listWorkOrders(params?: ListWorkOrdersParams): Promise<WorkOrder[]> {
    const response = await this.client.get<WorkOrder[]>('/maintenance/orders', {
      params,
    });
    return response.data;
  }

  /**
   * Update a work order
   */
  async updateWorkOrder(orderId: string, update: WorkOrderUpdate): Promise<WorkOrder> {
    const response = await this.client.patch<WorkOrder>(
      `/maintenance/orders/${orderId}`,
      update
    );
    return response.data;
  }

  /**
   * Get work order by ID or order number
   */
  async getWorkOrder(orderIdOrNumber: string): Promise<WorkOrder> {
    const response = await this.client.get<WorkOrder>(`/maintenance/orders/${orderIdOrNumber}`);
    return response.data;
  }
}

// Export singleton instance
export const maintenanceApi = new MaintenanceAPI();
