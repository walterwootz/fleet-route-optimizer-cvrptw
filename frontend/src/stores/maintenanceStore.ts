/**
 * Maintenance & Work Order Zustand Store
 * Manages work orders, maintenance tasks, loading states
 */

import { create } from 'zustand';
import { maintenanceApi } from '@/services/maintenanceApi';
import type {
  WorkOrder,
  WorkOrderCreate,
  WorkOrderUpdate,
  WorkOrderStatus,
  MaintenanceTask,
  MaintenanceTaskCreate,
} from '@/services/maintenanceApi';

interface MaintenanceStore {
  // ===== STATE =====
  workOrders: WorkOrder[];
  maintenanceTasks: MaintenanceTask[];
  selectedWorkOrder: WorkOrder | null;
  loading: boolean;
  error: string | null;

  // Filters
  statusFilter: WorkOrderStatus | 'all';
  workshopFilter: string | 'all';

  // ===== ACTIONS =====

  // Work Orders
  fetchWorkOrders: (params?: {
    status?: WorkOrderStatus;
    vehicle_id?: string;
    workshop_id?: string;
  }) => Promise<void>;
  createWorkOrder: (order: WorkOrderCreate) => Promise<WorkOrder | null>;
  updateWorkOrder: (orderId: string, update: WorkOrderUpdate) => Promise<WorkOrder | null>;
  getWorkOrder: (orderIdOrNumber: string) => Promise<WorkOrder | null>;

  // Maintenance Tasks
  fetchMaintenanceTasks: (params?: {
    vehicle_id?: string;
    overdue_only?: boolean;
  }) => Promise<void>;
  createMaintenanceTask: (task: MaintenanceTaskCreate) => Promise<MaintenanceTask | null>;

  // Filters
  setStatusFilter: (status: WorkOrderStatus | 'all') => void;
  setWorkshopFilter: (workshop: string | 'all') => void;

  // UI
  setSelectedWorkOrder: (order: WorkOrder | null) => void;
  clearError: () => void;
}

export const useMaintenanceStore = create<MaintenanceStore>((set, get) => ({
  // ===== INITIAL STATE =====
  workOrders: [],
  maintenanceTasks: [],
  selectedWorkOrder: null,
  loading: false,
  error: null,
  statusFilter: 'all',
  workshopFilter: 'all',

  // ===== WORK ORDERS =====

  /**
   * Fetch work orders from API
   */
  fetchWorkOrders: async (params) => {
    set({ loading: true, error: null });

    try {
      const workOrders = await maintenanceApi.listWorkOrders(params);
      set({ workOrders, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch work orders';
      set({
        error: errorMsg,
        loading: false,
      });
    }
  },

  /**
   * Create a new work order
   */
  createWorkOrder: async (order: WorkOrderCreate) => {
    set({ loading: true, error: null });

    try {
      const newOrder = await maintenanceApi.createWorkOrder(order);

      // Add to state
      set((state) => ({
        workOrders: [newOrder, ...state.workOrders],
        loading: false,
      }));

      return newOrder;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create work order';
      set({
        error: errorMsg,
        loading: false,
      });
      return null;
    }
  },

  /**
   * Update an existing work order
   */
  updateWorkOrder: async (orderId: string, update: WorkOrderUpdate) => {
    set({ loading: true, error: null });

    try {
      const updatedOrder = await maintenanceApi.updateWorkOrder(orderId, update);

      // Update in state
      set((state) => ({
        workOrders: state.workOrders.map((wo) =>
          wo.id === orderId ? updatedOrder : wo
        ),
        selectedWorkOrder:
          state.selectedWorkOrder?.id === orderId ? updatedOrder : state.selectedWorkOrder,
        loading: false,
      }));

      return updatedOrder;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to update work order';
      set({
        error: errorMsg,
        loading: false,
      });
      return null;
    }
  },

  /**
   * Get a single work order by ID or order number
   */
  getWorkOrder: async (orderIdOrNumber: string) => {
    set({ loading: true, error: null });

    try {
      const workOrder = await maintenanceApi.getWorkOrder(orderIdOrNumber);
      set({
        selectedWorkOrder: workOrder,
        loading: false,
      });
      return workOrder;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch work order';
      set({
        error: errorMsg,
        loading: false,
      });
      return null;
    }
  },

  // ===== MAINTENANCE TASKS =====

  /**
   * Fetch maintenance tasks from API
   */
  fetchMaintenanceTasks: async (params) => {
    set({ loading: true, error: null });

    try {
      const tasks = await maintenanceApi.listMaintenanceTasks(params);
      set({ maintenanceTasks: tasks, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch maintenance tasks';
      set({
        error: errorMsg,
        loading: false,
      });
    }
  },

  /**
   * Create a new maintenance task
   */
  createMaintenanceTask: async (task: MaintenanceTaskCreate) => {
    set({ loading: true, error: null });

    try {
      const newTask = await maintenanceApi.createMaintenanceTask(task);

      // Add to state
      set((state) => ({
        maintenanceTasks: [newTask, ...state.maintenanceTasks],
        loading: false,
      }));

      return newTask;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create maintenance task';
      set({
        error: errorMsg,
        loading: false,
      });
      return null;
    }
  },

  // ===== FILTERS =====

  /**
   * Set status filter
   */
  setStatusFilter: (status: WorkOrderStatus | 'all') => {
    set({ statusFilter: status });
  },

  /**
   * Set workshop filter
   */
  setWorkshopFilter: (workshop: string | 'all') => {
    set({ workshopFilter: workshop });
  },

  // ===== UI =====

  /**
   * Set selected work order for details view
   */
  setSelectedWorkOrder: (order: WorkOrder | null) => {
    set({ selectedWorkOrder: order });
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
