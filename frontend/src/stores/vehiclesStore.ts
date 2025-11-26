/**
 * Vehicles Zustand Store
 *
 * Global state management for vehicle/fleet data.
 */

import { create } from 'zustand';
import {
  vehiclesApi,
  type Vehicle,
  type VehicleCreate,
  type VehicleUpdate,
  type ListVehiclesParams,
  VehicleStatus,
} from '@/services/vehiclesApi';

// ============================================================================
// STATE INTERFACE
// ============================================================================

interface VehiclesStore {
  // State
  vehicles: Vehicle[];
  selectedVehicle: Vehicle | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchVehicles: (params?: ListVehiclesParams) => Promise<void>;
  getVehicle: (vehicleId: string) => Promise<Vehicle | null>;
  createVehicle: (vehicle: VehicleCreate) => Promise<Vehicle>;
  updateVehicle: (vehicleId: string, update: VehicleUpdate) => Promise<Vehicle>;
  deleteVehicle: (vehicleId: string) => Promise<void>;
  selectVehicle: (vehicle: Vehicle | null) => void;
  clearError: () => void;
}

// ============================================================================
// STORE IMPLEMENTATION
// ============================================================================

export const useVehiclesStore = create<VehiclesStore>((set, get) => ({
  // Initial state
  vehicles: [],
  selectedVehicle: null,
  loading: false,
  error: null,

  /**
   * Fetch all vehicles with optional filters
   */
  fetchVehicles: async (params?: ListVehiclesParams) => {
    set({ loading: true, error: null });
    try {
      const response = await vehiclesApi.listVehicles(params);
      set({ vehicles: response.vehicles, loading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to fetch vehicles',
        loading: false,
      });
    }
  },

  /**
   * Get a single vehicle by ID
   */
  getVehicle: async (vehicleId: string): Promise<Vehicle | null> => {
    set({ loading: true, error: null });
    try {
      const vehicle = await vehiclesApi.getVehicle(vehicleId);
      set({ selectedVehicle: vehicle, loading: false });
      return vehicle;
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to fetch vehicle',
        loading: false,
      });
      return null;
    }
  },

  /**
   * Create a new vehicle
   */
  createVehicle: async (vehicleData: VehicleCreate): Promise<Vehicle> => {
    set({ loading: true, error: null });
    try {
      const newVehicle = await vehiclesApi.createVehicle(vehicleData);
      set((state) => ({
        vehicles: [...state.vehicles, newVehicle],
        loading: false,
      }));
      return newVehicle;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create vehicle';
      set({ error: errorMessage, loading: false });
      throw new Error(errorMessage);
    }
  },

  /**
   * Update an existing vehicle
   */
  updateVehicle: async (vehicleId: string, update: VehicleUpdate): Promise<Vehicle> => {
    set({ loading: true, error: null });
    try {
      const updatedVehicle = await vehiclesApi.updateVehicle(vehicleId, update);
      set((state) => ({
        vehicles: state.vehicles.map((v) =>
          v.id === vehicleId ? updatedVehicle : v
        ),
        selectedVehicle: state.selectedVehicle?.id === vehicleId ? updatedVehicle : state.selectedVehicle,
        loading: false,
      }));
      return updatedVehicle;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update vehicle';
      set({ error: errorMessage, loading: false });
      throw new Error(errorMessage);
    }
  },

  /**
   * Delete a vehicle
   */
  deleteVehicle: async (vehicleId: string): Promise<void> => {
    set({ loading: true, error: null });
    try {
      await vehiclesApi.deleteVehicle(vehicleId);
      set((state) => ({
        vehicles: state.vehicles.filter((v) => v.id !== vehicleId),
        selectedVehicle: state.selectedVehicle?.id === vehicleId ? null : state.selectedVehicle,
        loading: false,
      }));
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete vehicle';
      set({ error: errorMessage, loading: false });
      throw new Error(errorMessage);
    }
  },

  /**
   * Select a vehicle for detailed view
   */
  selectVehicle: (vehicle: Vehicle | null) => {
    set({ selectedVehicle: vehicle });
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
