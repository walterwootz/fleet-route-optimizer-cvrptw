/**
 * FLEET-ONE Zustand Store
 * Manages agent state, messages, and sessions
 */

import { create } from 'zustand';
import { fleetOneApi } from '@/services/fleetOneApi';
import type { Message, AgentMode, UserRole } from '@/types/fleetOne';

interface FleetOneStore {
  // State
  sessionId: string | null;
  userId: string | null;
  userRole: UserRole | null;
  messages: Message[];
  currentMode: AgentMode | null;
  modeConfidence: number | null;
  loading: boolean;
  error: string | null;
  isOpen: boolean;

  // Actions
  setIsOpen: (isOpen: boolean) => void;
  initSession: (userId: string, userRole: UserRole) => Promise<void>;
  sendQuery: (query: string, forceMode?: AgentMode) => Promise<void>;
  clearSession: () => Promise<void>;
  loadHistory: () => Promise<void>;
  clearError: () => void;
}

export const useFleetOneStore = create<FleetOneStore>((set, get) => ({
  // Initial state
  sessionId: null,
  userId: null,
  userRole: null,
  messages: [],
  currentMode: null,
  modeConfidence: null,
  loading: false,
  error: null,
  isOpen: false,

  // Set drawer open/closed
  setIsOpen: (isOpen: boolean) => {
    set({ isOpen });

    // Initialize session when opening for the first time
    if (isOpen && !get().sessionId && get().userId && get().userRole) {
      get().initSession(get().userId!, get().userRole!);
    }
  },

  // Initialize session
  initSession: async (userId: string, userRole: UserRole) => {
    try {
      const response = await fleetOneApi.createSession(userId, userRole);

      set({
        sessionId: response.session_id,
        userId,
        userRole,
        messages: [],
        error: null,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || error.message || 'Failed to create session',
      });
    }
  },

  // Send query
  sendQuery: async (query: string, forceMode?: AgentMode) => {
    const { sessionId, userId, userRole } = get();

    if (!userId || !userRole) {
      set({ error: 'User not initialized' });
      return;
    }

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      loading: true,
      error: null,
    }));

    try {
      const response = await fleetOneApi.query({
        session_id: sessionId || undefined,
        user_id: userId,
        user_role: userRole,
        query,
        force_mode: forceMode,
      });

      if (!response.success) {
        // Handle error response
        const errorMessage: Message = {
          role: 'system',
          content: response.message,
          timestamp: new Date(),
        };

        set((state) => ({
          messages: [...state.messages, errorMessage],
          loading: false,
          error: response.message,
        }));
        return;
      }

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        mode: response.mode,
        data: response.data,
        timestamp: new Date(response.timestamp),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        sessionId: response.session_id,
        currentMode: response.mode,
        modeConfidence: response.mode_confidence,
        loading: false,
      }));
    } catch (error: any) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to send query';

      const errorMessage: Message = {
        role: 'system',
        content: `Fehler: ${errorMsg}`,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, errorMessage],
        loading: false,
        error: errorMsg,
      }));
    }
  },

  // Clear session
  clearSession: async () => {
    const { sessionId } = get();
    if (!sessionId) return;

    try {
      await fleetOneApi.clearSession(sessionId);

      set({
        messages: [],
        currentMode: null,
        modeConfidence: null,
        error: null,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || error.message || 'Failed to clear session',
      });
    }
  },

  // Load history
  loadHistory: async () => {
    const { sessionId } = get();
    if (!sessionId) return;

    try {
      const history = await fleetOneApi.getHistory(sessionId);

      const messages: Message[] = history.history.flatMap((item) => [
        {
          role: 'user' as const,
          content: item.query,
          timestamp: new Date(item.timestamp),
        },
        {
          role: 'assistant' as const,
          content: item.response,
          mode: item.mode,
          timestamp: new Date(item.timestamp),
        },
      ]);

      set({ messages });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || error.message || 'Failed to load history',
      });
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
