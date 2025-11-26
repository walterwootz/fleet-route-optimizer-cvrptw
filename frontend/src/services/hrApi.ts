/**
 * HR API Service
 * Handles staff and assignments
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// ============================================================================
// TYPES
// ============================================================================

export interface Staff {
  id: string;
  employee_id: string;
  first_name: string;
  last_name: string;
  position: string;
  department: string;
  qualifications?: string[];
  certifications?: string[];
  email?: string;
  phone?: string;
  is_active: boolean;
  hired_date?: string;
  created_at: string;
  updated_at: string;
}

export interface StaffCreate {
  employee_id: string;
  first_name: string;
  last_name: string;
  position: string;
  department: string;
  qualifications?: string[];
  certifications?: string[];
  email?: string;
  phone?: string;
  hired_date?: string;
}

export interface StaffAssignment {
  id: string;
  staff_id: string;
  work_order_id?: string;
  workshop_id?: string;
  assigned_date: string;
  start_time?: string;
  end_time?: string;
  role: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface StaffAssignmentCreate {
  staff_id: string;
  work_order_id?: string;
  workshop_id?: string;
  assigned_date: string;
  start_time?: string;
  end_time?: string;
  role: string;
  notes?: string;
}

export interface ListStaffParams {
  skip?: number;
  limit?: number;
  department?: string;
  position?: string;
  is_active?: boolean;
}

export interface ListAssignmentsParams {
  skip?: number;
  limit?: number;
  staff_id?: string;
  work_order_id?: string;
  workshop_id?: string;
}

// ============================================================================
// API CLIENT
// ============================================================================

export class HRAPI {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1/hr') {
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

  // ===== STAFF =====

  async createStaff(staff: StaffCreate): Promise<Staff> {
    const response = await this.client.post<Staff>('/staff', staff);
    return response.data;
  }

  async listStaff(params?: ListStaffParams): Promise<{ total: number; staff: Staff[] }> {
    const response = await this.client.get<{ total: number; staff: Staff[] }>('/staff', {
      params,
    });
    return response.data;
  }

  async getStaff(staffId: string): Promise<Staff> {
    const response = await this.client.get<Staff>(`/staff/${staffId}`);
    return response.data;
  }

  // ===== ASSIGNMENTS =====

  async createAssignment(assignment: StaffAssignmentCreate): Promise<StaffAssignment> {
    const response = await this.client.post<StaffAssignment>('/assignments', assignment);
    return response.data;
  }

  async listAssignments(params?: ListAssignmentsParams): Promise<{ total: number; assignments: StaffAssignment[] }> {
    const response = await this.client.get<{ total: number; assignments: StaffAssignment[] }>('/assignments', {
      params,
    });
    return response.data;
  }
}

// Export singleton instance
export const hrApi = new HRAPI();
