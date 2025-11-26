/**
 * Vehicles API Client
 *
 * Provides TypeScript interfaces and API methods for vehicle/fleet management.
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

const API_BASE_URL = '/api/v1';

// ============================================================================
// ENUMS
// ============================================================================

export enum VehicleStatus {
  AVAILABLE = 'available',
  IN_SERVICE = 'in_service',
  WORKSHOP_PLANNED = 'workshop_planned',
  IN_WORKSHOP = 'in_workshop',
  OUT_OF_SERVICE = 'out_of_service',
  MAINTENANCE_DUE = 'maintenance_due',
  RETIRED = 'retired',
}

export enum VehicleType {
  ELECTRIC = 'electric',
  DIESEL = 'diesel',
  HYBRID = 'hybrid',
}

// ============================================================================
// TYPES
// ============================================================================

export interface Vehicle {
  id: string;
  asset_id: string;
  model: string;
  type: VehicleType;
  manufacturer?: string;
  year?: number;
  status: VehicleStatus;
  max_speed_kmh?: number;
  power_kw?: number;
  weight_tons?: number;
  current_mileage_km: number;
  total_operating_hours: number;
  current_location?: string;
  home_depot?: string;
  notes?: string;
  specifications?: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_service_date?: string;
}

export interface VehicleCreate {
  asset_id: string;
  model: string;
  type: VehicleType;
  manufacturer?: string;
  year?: number;
  status?: VehicleStatus;
  max_speed_kmh?: number;
  power_kw?: number;
  weight_tons?: number;
  current_mileage_km?: number;
  total_operating_hours?: number;
  current_location?: string;
  home_depot?: string;
  notes?: string;
  specifications?: Record<string, any>;
}

export interface VehicleUpdate {
  model?: string;
  status?: VehicleStatus;
  manufacturer?: string;
  year?: number;
  current_mileage_km?: number;
  total_operating_hours?: number;
  current_location?: string;
  home_depot?: string;
  notes?: string;
  specifications?: Record<string, any>;
}

export interface ListVehiclesParams {
  skip?: number;
  limit?: number;
  status?: VehicleStatus;
  search?: string;
}

export interface VehicleListResponse {
  total: number;
  vehicles: Vehicle[];
}

// ============================================================================
// API CLIENT
// ============================================================================

export class VehiclesAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * List all vehicles with optional filtering
   */
  async listVehicles(params?: ListVehiclesParams): Promise<VehicleListResponse> {
    const response = await this.client.get<VehicleListResponse>('/vehicles', { params });
    return response.data;
  }

  /**
   * Get vehicle by ID or asset_id
   */
  async getVehicle(vehicleId: string): Promise<Vehicle> {
    const response = await this.client.get<Vehicle>(`/vehicles/${vehicleId}`);
    return response.data;
  }

  /**
   * Create a new vehicle
   */
  async createVehicle(vehicle: VehicleCreate): Promise<Vehicle> {
    const response = await this.client.post<Vehicle>('/vehicles', vehicle);
    return response.data;
  }

  /**
   * Update vehicle (partial updates allowed)
   */
  async updateVehicle(vehicleId: string, update: VehicleUpdate): Promise<Vehicle> {
    const response = await this.client.patch<Vehicle>(`/vehicles/${vehicleId}`, update);
    return response.data;
  }

  /**
   * Delete vehicle
   */
  async deleteVehicle(vehicleId: string): Promise<void> {
    await this.client.delete(`/vehicles/${vehicleId}`);
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

export const vehiclesApi = new VehiclesAPI();
