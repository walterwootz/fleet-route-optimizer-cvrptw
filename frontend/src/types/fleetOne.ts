/**
 * FLEET-ONE Agent Types
 * Based on docs/FLEET_ONE_API_REFERENCE.md
 */

export type AgentMode =
  | 'FLOTTE'
  | 'MAINTENANCE'
  | 'WORKSHOP'
  | 'PROCUREMENT'
  | 'FINANCE'
  | 'HR'
  | 'DOCS';

export type UserRole =
  | 'dispatcher'
  | 'workshop'
  | 'procurement'
  | 'finance'
  | 'ecm'
  | 'viewer';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  mode?: AgentMode;
  data?: any;
  timestamp: Date;
}

export interface QueryRequest {
  session_id?: string;
  user_id: string;
  user_role: UserRole;
  query: string;
  force_mode?: AgentMode;
}

export interface QueryResponse {
  success: boolean;
  message: string;
  session_id: string;
  mode: AgentMode;
  mode_confidence: number;
  data?: any;
  timestamp: string;
  error_code?: string;
  details?: any;
}

export interface SessionRequest {
  user_id: string;
  user_role: UserRole;
}

export interface SessionResponse {
  session_id: string;
  user_id: string;
  user_role: UserRole;
  created_at: string;
}

export interface HistoryResponse {
  session_id: string;
  user_id: string;
  user_role: UserRole;
  history: HistoryItem[];
  created_at: string;
}

export interface HistoryItem {
  query: string;
  response: string;
  mode: AgentMode;
  timestamp: string;
}

export interface ModesResponse {
  modes: ModeInfo[];
}

export interface ModeInfo {
  name: AgentMode;
  description: string;
  keywords: string[];
}

export interface MetricsResponse {
  active_sessions: number;
  total_queries: number;
  avg_response_time_ms: number;
  tool_calls: Record<string, number>;
  mode_distribution: Record<AgentMode, number>;
  error_rate: number;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  agent_version: string;
  backend_services: Record<string, string>;
  timestamp: string;
}
