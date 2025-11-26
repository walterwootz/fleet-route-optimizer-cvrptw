/**
 * HR Zustand Store
 * Manages staff and assignments
 */

import { create } from 'zustand';
import { hrApi } from '@/services/hrApi';
import type {
  Staff,
  StaffCreate,
  StaffAssignment,
  StaffAssignmentCreate,
} from '@/services/hrApi';

interface HRStore {
  // ===== STATE =====
  staff: Staff[];
  assignments: StaffAssignment[];
  loading: boolean;
  error: string | null;

  // Filters
  departmentFilter: string | 'all';

  // ===== ACTIONS =====

  // Staff
  fetchStaff: (params?: { department?: string; position?: string; is_active?: boolean }) => Promise<void>;
  createStaff: (staff: StaffCreate) => Promise<Staff | null>;

  // Assignments
  fetchAssignments: (params?: { staff_id?: string; work_order_id?: string }) => Promise<void>;
  createAssignment: (assignment: StaffAssignmentCreate) => Promise<StaffAssignment | null>;

  // Filters
  setDepartmentFilter: (department: string | 'all') => void;

  // UI
  clearError: () => void;
}

export const useHRStore = create<HRStore>((set, get) => ({
  // ===== INITIAL STATE =====
  staff: [],
  assignments: [],
  loading: false,
  error: null,
  departmentFilter: 'all',

  // ===== STAFF =====

  fetchStaff: async (params) => {
    set({ loading: true, error: null });

    try {
      const response = await hrApi.listStaff(params);
      set({ staff: response.staff, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch staff';
      set({ error: errorMsg, loading: false });
    }
  },

  createStaff: async (staff: StaffCreate) => {
    set({ loading: true, error: null });

    try {
      const newStaff = await hrApi.createStaff(staff);

      set((state) => ({
        staff: [newStaff, ...state.staff],
        loading: false,
      }));

      return newStaff;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create staff';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  // ===== ASSIGNMENTS =====

  fetchAssignments: async (params) => {
    set({ loading: true, error: null });

    try {
      const response = await hrApi.listAssignments(params);
      set({ assignments: response.assignments, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to fetch assignments';
      set({ error: errorMsg, loading: false });
    }
  },

  createAssignment: async (assignment: StaffAssignmentCreate) => {
    set({ loading: true, error: null });

    try {
      const newAssignment = await hrApi.createAssignment(assignment);

      set((state) => ({
        assignments: [newAssignment, ...state.assignments],
        loading: false,
      }));

      return newAssignment;
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to create assignment';
      set({ error: errorMsg, loading: false });
      return null;
    }
  },

  // ===== FILTERS =====

  setDepartmentFilter: (department: string | 'all') => {
    set({ departmentFilter: department });
  },

  // ===== UI =====

  clearError: () => {
    set({ error: null });
  },
}));
