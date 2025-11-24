/**
 * FLEET-ONE API Service
 * Handles all HTTP communication with the FLEET-ONE backend
 */

import axios, { AxiosInstance } from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  SessionRequest,
  SessionResponse,
  HistoryResponse,
  ModesResponse,
  MetricsResponse,
  HealthResponse,
} from '@/types/fleetOne';

export class FleetOneAPI {
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

  /**
   * Create a new conversation session
   */
  async createSession(userId: string, userRole: string): Promise<SessionResponse> {
    const request: SessionRequest = {
      user_id: userId,
      user_role: userRole as any,
    };

    const response = await this.client.post<SessionResponse>(
      '/fleet-one/session',
      request
    );
    return response.data;
  }

  /**
   * Send a query to the agent
   */
  async query(
    request: QueryRequest
  ): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>(
      '/fleet-one/query',
      request
    );
    return response.data;
  }

  /**
   * Get session history
   */
  async getHistory(sessionId: string): Promise<HistoryResponse> {
    const response = await this.client.get<HistoryResponse>(
      `/fleet-one/session/${sessionId}/history`
    );
    return response.data;
  }

  /**
   * Clear session history
   */
  async clearSession(sessionId: string): Promise<void> {
    await this.client.delete(`/fleet-one/session/${sessionId}`);
  }

  /**
   * Get available modes
   */
  async getModes(): Promise<ModesResponse> {
    const response = await this.client.get<ModesResponse>('/fleet-one/modes');
    return response.data;
  }

  /**
   * Get agent metrics
   */
  async getMetrics(): Promise<MetricsResponse> {
    const response = await this.client.get<MetricsResponse>('/fleet-one/metrics');
    return response.data;
  }

  /**
   * Health check
   */
  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/fleet-one/health');
    return response.data;
  }
}

// Export singleton instance
export const fleetOneApi = new FleetOneAPI();
