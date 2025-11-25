# FLEET-ONE Frontend Integration Plan

**Version**: 1.0.0
**Target**: RailFleet Manager Web Application
**Technology Stack**: React + TypeScript + TailwindCSS

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Architektur](#architektur)
3. [Komponenten](#komponenten)
4. [State Management](#state-management)
5. [UI/UX Design](#uiux-design)
6. [API Integration](#api-integration)
7. [Implementierungsplan](#implementierungsplan)
8. [Testing-Strategie](#testing-strategie)

---

## Überblick

### Ziele

- Integration von FLEET-ONE Agent als **zentrales Konversations-Interface**
- **Multi-Mode-Unterstützung** mit visueller Mode-Anzeige
- **Session-Management** mit Konversationshistorie
- **Echtzeit-Feedback** über Tool-Aufrufe und Status
- **RBAC-Integration** basierend auf Benutzerrolle
- **Responsives Design** für Desktop und Tablet

### Scope

**Phase 1** (MVP - 2 Wochen):
- Chat-Interface als Overlay/Drawer
- Grundlegende Mode-Anzeige
- Session-Management
- Einfaches Error-Handling

**Phase 2** (Erweitert - 2 Wochen):
- Dashboard-Integration mit Widgets
- Erweiterte Visualisierungen (Charts, Tables)
- Keyboard-Shortcuts
- Voice-Input (optional)

**Phase 3** (Enterprise - 2 Wochen):
- Multi-Session-Support
- Konversations-Export
- Analytics Dashboard
- Admin-Panel für Policy-Konfiguration

---

## Architektur

### Komponentenhierarchie

```
App
├── Navigation
├── MainContent
│   ├── Dashboard
│   │   ├── FleetOverview
│   │   ├── MaintenanceWidget
│   │   └── WorkshopWidget
│   └── DetailViews
│       ├── LocomotiveDetail
│       ├── WorkshopDetail
│       └── MaintenanceDetail
└── FleetOneContainer (Global)
    ├── FleetOneTrigger (Button)
    └── FleetOneDrawer
        ├── ChatHeader
        ├── MessageList
        │   ├── UserMessage
        │   ├── AssistantMessage
        │   └── SystemMessage
        ├── ModeIndicator
        ├── LoadingIndicator
        ├── ErrorDisplay
        └── ChatInput
            ├── TextInput
            ├── ModeSelectorDropdown
            └── SendButton
```

### Datenfluss

```
┌──────────────────────────────────────────────────────────┐
│                    User Action                            │
│  (User types "Zeige alle Loks mit Status maintenance_due")│
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│              ChatInput Component                          │
│  - Validates input                                        │
│  - Triggers send action                                   │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│            FleetOne Store (Zustand)                       │
│  - Adds user message to history                           │
│  - Dispatches API call                                    │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│           FleetOneAPI Service                             │
│  POST /api/v1/fleet-one/query                             │
│  {                                                         │
│    session_id: "sess_123",                                │
│    user_id: "user_01",                                    │
│    user_role: "dispatcher",                               │
│    query: "Zeige alle Loks..."                            │
│  }                                                         │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│         FLEET-ONE Backend (FastAPI)                       │
│  - Mode detection (FLOTTE detected)                       │
│  - RBAC check (dispatcher OK)                             │
│  - Tool orchestration (get_locomotives)                   │
│  - Response generation                                    │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│           Response Processing                             │
│  {                                                         │
│    success: true,                                         │
│    message: "Ich habe 3 Lokomotiven...",                  │
│    mode: "FLOTTE",                                        │
│    data: {locomotives: [...]}                             │
│  }                                                         │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│            FleetOne Store Update                          │
│  - Adds assistant message to history                      │
│  - Updates mode indicator                                 │
│  - Stores structured data for rendering                   │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│         Component Re-render                               │
│  - MessageList shows new message                          │
│  - ModeIndicator shows "FLOTTE"                           │
│  - StructuredDataRenderer shows table (optional)          │
└──────────────────────────────────────────────────────────┘
```

---

## Komponenten

### 1. FleetOneContainer

**Verantwortung**: Root-Komponente für FLEET-ONE Integration

```typescript
// src/components/FleetOne/FleetOneContainer.tsx
import React, { useState } from 'react';
import { FleetOneTrigger } from './FleetOneTrigger';
import { FleetOneDrawer } from './FleetOneDrawer';

export const FleetOneContainer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <FleetOneTrigger onClick={() => setIsOpen(true)} />
      <FleetOneDrawer
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  );
};
```

**Props**: Keine
**State**: `isOpen` (boolean)

---

### 2. FleetOneTrigger

**Verantwortung**: Button zum Öffnen des Chat-Interfaces

```typescript
// src/components/FleetOne/FleetOneTrigger.tsx
import React from 'react';
import { MessageSquare } from 'lucide-react';

interface FleetOneTriggerProps {
  onClick: () => void;
}

export const FleetOneTrigger: React.FC<FleetOneTriggerProps> = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700
                 text-white rounded-full p-4 shadow-lg transition-all
                 hover:scale-110 z-50"
      aria-label="FLEET-ONE Agent öffnen"
    >
      <MessageSquare size={24} />
      <span className="absolute -top-1 -right-1 bg-green-500 w-3 h-3
                       rounded-full border-2 border-white" />
    </button>
  );
};
```

**Design**:
- Fixed position: bottom-right
- Blue primary color (matches RailFleet branding)
- Green indicator dot (agent online)
- Hover animation (scale 1.1)

---

### 3. FleetOneDrawer

**Verantwortung**: Haupt-Chat-Interface als Drawer/Overlay

```typescript
// src/components/FleetOne/FleetOneDrawer.tsx
import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ModeIndicator } from './ModeIndicator';
import { useFleetOneStore } from '@/stores/fleetOneStore';

interface FleetOneDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FleetOneDrawer: React.FC<FleetOneDrawerProps> = ({
  isOpen,
  onClose
}) => {
  const { initSession, sessionId } = useFleetOneStore();

  useEffect(() => {
    if (isOpen && !sessionId) {
      // Initialize session when drawer opens
      initSession();
    }
  }, [isOpen, sessionId]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 h-full w-full md:w-[480px]
                   bg-white shadow-2xl z-50 flex flex-col
                   animate-slide-in-right"
      >
        {/* Header */}
        <ChatHeader onClose={onClose} />

        {/* Mode Indicator */}
        <ModeIndicator />

        {/* Messages */}
        <MessageList />

        {/* Input */}
        <ChatInput />
      </div>
    </>
  );
};
```

**Features**:
- Slide-in animation from right
- Full-height drawer
- Responsive width (480px desktop, full mobile)
- Overlay with backdrop blur

---

### 4. ChatHeader

**Verantwortung**: Drawer-Header mit Titel und Close-Button

```typescript
// src/components/FleetOne/ChatHeader.tsx
import React from 'react';
import { X, Info } from 'lucide-react';
import { useFleetOneStore } from '@/stores/fleetOneStore';

interface ChatHeaderProps {
  onClose: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ onClose }) => {
  const { sessionId, userRole } = useFleetOneStore();

  return (
    <div className="flex items-center justify-between p-4 border-b bg-blue-600 text-white">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
          <span className="text-blue-600 font-bold text-lg">F1</span>
        </div>
        <div>
          <h2 className="font-semibold text-lg">FLEET-ONE</h2>
          <p className="text-xs text-blue-100">
            {userRole === 'dispatcher' ? 'Disponent' :
             userRole === 'workshop' ? 'Werkstatt' :
             userRole === 'procurement' ? 'Beschaffung' :
             userRole === 'finance' ? 'Finanzen' :
             userRole === 'ecm' ? 'ECM' : 'Betrachter'}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          className="p-2 hover:bg-blue-700 rounded transition"
          title="Informationen"
        >
          <Info size={20} />
        </button>
        <button
          onClick={onClose}
          className="p-2 hover:bg-blue-700 rounded transition"
          aria-label="Schließen"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  );
};
```

**Elemente**:
- Logo/Avatar (F1 Badge)
- Titel "FLEET-ONE"
- Rollenanzeige (Disponent, Werkstatt, etc.)
- Info-Button (öffnet Hilfe-Modal)
- Close-Button

---

### 5. MessageList

**Verantwortung**: Scrollbare Liste aller Nachrichten

```typescript
// src/components/FleetOne/MessageList.tsx
import React, { useRef, useEffect } from 'react';
import { useFleetOneStore } from '@/stores/fleetOneStore';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { SystemMessage } from './SystemMessage';

export const MessageList: React.FC = () => {
  const { messages, loading } = useFleetOneStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <p className="text-lg font-medium mb-2">
              Willkommen bei FLEET-ONE
            </p>
            <p className="text-sm">
              Stellen Sie mir eine Frage zum Flottenmanagement
            </p>
          </div>
        </div>
      )}

      {messages.map((msg, idx) => {
        if (msg.role === 'user') {
          return <UserMessage key={idx} message={msg} />;
        } else if (msg.role === 'assistant') {
          return <AssistantMessage key={idx} message={msg} />;
        } else {
          return <SystemMessage key={idx} message={msg} />;
        }
      })}

      {loading && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-pulse">●</div>
          <div className="animate-pulse animation-delay-200">●</div>
          <div className="animate-pulse animation-delay-400">●</div>
          <span className="ml-2">Agent denkt nach...</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};
```

**Features**:
- Auto-scroll to bottom on new message
- Empty state with welcome message
- Loading indicator (animated dots)
- Different message components based on role

---

### 6. UserMessage / AssistantMessage

**Verantwortung**: Darstellung einzelner Nachrichten

```typescript
// src/components/FleetOne/UserMessage.tsx
import React from 'react';
import { User } from 'lucide-react';
import { Message } from '@/types/fleetOne';

interface UserMessageProps {
  message: Message;
}

export const UserMessage: React.FC<UserMessageProps> = ({ message }) => {
  return (
    <div className="flex items-start space-x-3 justify-end">
      <div className="bg-blue-600 text-white rounded-lg p-3 max-w-[80%]">
        <p className="text-sm">{message.content}</p>
        <span className="text-xs text-blue-200 mt-1 block">
          {new Date(message.timestamp).toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>
      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <User size={16} className="text-blue-600" />
      </div>
    </div>
  );
};

// src/components/FleetOne/AssistantMessage.tsx
import React from 'react';
import { Bot } from 'lucide-react';
import { Message } from '@/types/fleetOne';
import { StructuredDataRenderer } from './StructuredDataRenderer';

interface AssistantMessageProps {
  message: Message;
}

export const AssistantMessage: React.FC<AssistantMessageProps> = ({ message }) => {
  return (
    <div className="flex items-start space-x-3">
      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-green-600" />
      </div>
      <div className="bg-white rounded-lg p-3 max-w-[80%] shadow-sm border">
        <p className="text-sm text-gray-800 whitespace-pre-wrap">
          {message.content}
        </p>

        {/* Structured Data (tables, charts, etc.) */}
        {message.data && (
          <StructuredDataRenderer data={message.data} />
        )}

        {/* Mode Badge */}
        {message.mode && (
          <span className="inline-block mt-2 px-2 py-1 bg-gray-100
                         text-xs rounded text-gray-600">
            {message.mode}
          </span>
        )}

        <span className="text-xs text-gray-400 mt-1 block">
          {new Date(message.timestamp).toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>
    </div>
  );
};
```

**Design**:
- User messages: Right-aligned, blue background
- Assistant messages: Left-aligned, white background with border
- Avatars: User icon vs Bot icon
- Mode badge for assistant messages
- Timestamp

---

### 7. ChatInput

**Verantwortung**: Eingabefeld mit Send-Button

```typescript
// src/components/FleetOne/ChatInput.tsx
import React, { useState, useRef } from 'react';
import { Send, ChevronDown } from 'lucide-react';
import { useFleetOneStore } from '@/stores/fleetOneStore';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const [showModePicker, setShowModePicker] = useState(false);
  const [forceMode, setForceMode] = useState<string | undefined>();
  const { sendQuery, loading } = useFleetOneStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    sendQuery(input, forceMode);
    setInput('');
    setForceMode(undefined);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
      {/* Mode Picker (optional) */}
      {showModePicker && (
        <div className="mb-2 flex items-center space-x-2">
          <span className="text-xs text-gray-600">Modus erzwingen:</span>
          <select
            value={forceMode || ''}
            onChange={(e) => setForceMode(e.target.value || undefined)}
            className="text-xs border rounded px-2 py-1"
          >
            <option value="">Automatisch</option>
            <option value="FLOTTE">FLOTTE</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
            <option value="WORKSHOP">WORKSHOP</option>
            <option value="PROCUREMENT">PROCUREMENT</option>
            <option value="FINANCE">FINANCE</option>
            <option value="HR">HR</option>
            <option value="DOCS">DOCS</option>
          </select>
        </div>
      )}

      <div className="flex items-end space-x-2">
        <button
          type="button"
          onClick={() => setShowModePicker(!showModePicker)}
          className="p-2 text-gray-400 hover:text-gray-600 transition"
          title="Modus auswählen"
        >
          <ChevronDown size={20} />
        </button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Stellen Sie eine Frage... (z.B. 'Zeige alle Loks mit Status maintenance_due')"
          className="flex-1 resize-none border rounded-lg px-3 py-2
                     focus:outline-none focus:ring-2 focus:ring-blue-600
                     text-sm max-h-32"
          rows={1}
          disabled={loading}
        />

        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="p-2 bg-blue-600 text-white rounded-lg
                     hover:bg-blue-700 disabled:opacity-50
                     disabled:cursor-not-allowed transition"
          aria-label="Nachricht senden"
        >
          <Send size={20} />
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        Drücken Sie Enter zum Senden, Shift+Enter für neue Zeile
      </p>
    </form>
  );
};
```

**Features**:
- Auto-expanding textarea (max 4 rows)
- Mode picker dropdown (optional, collapsed by default)
- Send button (disabled wenn leer oder loading)
- Keyboard shortcuts (Enter = send, Shift+Enter = new line)
- Helper text

---

### 8. ModeIndicator

**Verantwortung**: Anzeige des aktuellen Modus

```typescript
// src/components/FleetOne/ModeIndicator.tsx
import React from 'react';
import { useFleetOneStore } from '@/stores/fleetOneStore';
import { Ship, Wrench, Factory, ShoppingCart, DollarSign, Users, FileText } from 'lucide-react';

const MODE_CONFIG = {
  FLOTTE: { label: 'Flotte', icon: Ship, color: 'blue' },
  MAINTENANCE: { label: 'Wartung', icon: Wrench, color: 'orange' },
  WORKSHOP: { label: 'Werkstatt', icon: Factory, color: 'purple' },
  PROCUREMENT: { label: 'Beschaffung', icon: ShoppingCart, color: 'green' },
  FINANCE: { label: 'Finanzen', icon: DollarSign, color: 'yellow' },
  HR: { label: 'Personal', icon: Users, color: 'pink' },
  DOCS: { label: 'Dokumente', icon: FileText, color: 'gray' }
};

export const ModeIndicator: React.FC = () => {
  const { currentMode, modeConfidence } = useFleetOneStore();

  if (!currentMode) return null;

  const config = MODE_CONFIG[currentMode as keyof typeof MODE_CONFIG];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div className={`px-4 py-2 bg-${config.color}-50 border-b border-${config.color}-200`}>
      <div className="flex items-center space-x-2">
        <Icon size={16} className={`text-${config.color}-600`} />
        <span className="text-sm font-medium text-gray-700">
          Modus: {config.label}
        </span>
        {modeConfidence !== undefined && (
          <span className="text-xs text-gray-500">
            ({Math.round(modeConfidence * 100)}% sicher)
          </span>
        )}
      </div>
    </div>
  );
};
```

**Design**:
- Colored badge based on mode
- Icon per mode
- Confidence percentage
- Smooth transition between modes

---

### 9. StructuredDataRenderer

**Verantwortung**: Darstellung strukturierter Daten (Tabellen, Charts)

```typescript
// src/components/FleetOne/StructuredDataRenderer.tsx
import React from 'react';

interface StructuredDataRendererProps {
  data: any;
}

export const StructuredDataRenderer: React.FC<StructuredDataRendererProps> = ({ data }) => {
  // Check if data contains locomotives array
  if (data.locomotives && Array.isArray(data.locomotives)) {
    return (
      <div className="mt-3 overflow-x-auto">
        <table className="min-w-full text-xs border">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1 border">ID</th>
              <th className="px-2 py-1 border">Status</th>
              <th className="px-2 py-1 border">Fällig</th>
            </tr>
          </thead>
          <tbody>
            {data.locomotives.map((loco: any, idx: number) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-2 py-1 border">{loco.id}</td>
                <td className="px-2 py-1 border">
                  <span className={`px-1 py-0.5 rounded text-xs ${
                    loco.status === 'maintenance_due' ? 'bg-red-100 text-red-700' :
                    loco.status === 'operational' ? 'bg-green-100 text-green-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {loco.status}
                  </span>
                </td>
                <td className="px-2 py-1 border">{loco.due_date || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Generic JSON display for other data
  return (
    <pre className="mt-3 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
};
```

**Rendering Types**:
- Locomotives → Table with status badges
- Tasks → Checklist
- Reports → Key-value pairs
- Fallback → JSON display

---

## State Management

### Zustand Store

```typescript
// src/stores/fleetOneStore.ts
import { create } from 'zustand';
import { FleetOneAPI } from '@/services/fleetOneApi';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  mode?: string;
  data?: any;
  timestamp: Date;
}

interface FleetOneStore {
  // State
  sessionId: string | null;
  userId: string | null;
  userRole: string | null;
  messages: Message[];
  currentMode: string | null;
  modeConfidence: number | null;
  loading: boolean;
  error: string | null;

  // Actions
  initSession: (userId: string, userRole: string) => Promise<void>;
  sendQuery: (query: string, forceMode?: string) => Promise<void>;
  clearSession: () => Promise<void>;
  loadHistory: () => Promise<void>;
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

  // Initialize session
  initSession: async (userId: string, userRole: string) => {
    try {
      const api = new FleetOneAPI();
      const sessionId = await api.createSession(userId, userRole);

      set({
        sessionId,
        userId,
        userRole,
        messages: [],
        error: null
      });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // Send query
  sendQuery: async (query: string, forceMode?: string) => {
    const { sessionId, userId, userRole } = get();
    if (!userId || !userRole) return;

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      loading: true,
      error: null
    }));

    try {
      const api = new FleetOneAPI();
      const response = await api.query(userId, userRole, query, forceMode);

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        mode: response.mode,
        data: response.data,
        timestamp: new Date()
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        sessionId: response.session_id,
        currentMode: response.mode,
        modeConfidence: response.mode_confidence,
        loading: false
      }));
    } catch (error) {
      set({
        loading: false,
        error: (error as Error).message
      });

      // Add error message
      const errorMessage: Message = {
        role: 'system',
        content: `Fehler: ${(error as Error).message}`,
        timestamp: new Date()
      };

      set((state) => ({
        messages: [...state.messages, errorMessage]
      }));
    }
  },

  // Clear session
  clearSession: async () => {
    const { sessionId } = get();
    if (!sessionId) return;

    try {
      const api = new FleetOneAPI();
      await api.clearSession(sessionId);

      set({
        sessionId: null,
        messages: [],
        currentMode: null,
        modeConfidence: null
      });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // Load history
  loadHistory: async () => {
    const { sessionId } = get();
    if (!sessionId) return;

    try {
      const api = new FleetOneAPI();
      const history = await api.getHistory(sessionId);

      const messages: Message[] = history.history.map((item: any) => [
        {
          role: 'user' as const,
          content: item.query,
          timestamp: new Date(item.timestamp)
        },
        {
          role: 'assistant' as const,
          content: item.response,
          mode: item.mode,
          timestamp: new Date(item.timestamp)
        }
      ]).flat();

      set({ messages });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  }
}));
```

---

## UI/UX Design

### Design System

**Farben**:
```css
/* Primary */
--blue-600: #2563eb  /* FLEET-ONE Brand */
--blue-700: #1d4ed8

/* Mode Colors */
--flotte: #2563eb (blue)
--maintenance: #ea580c (orange)
--workshop: #9333ea (purple)
--procurement: #16a34a (green)
--finance: #eab308 (yellow)
--hr: #db2777 (pink)
--docs: #6b7280 (gray)

/* Status */
--success: #16a34a
--warning: #eab308
--error: #dc2626
--info: #0ea5e9
```

**Typography**:
```css
/* Font Family */
font-family: 'Inter', sans-serif;

/* Sizes */
--text-xs: 0.75rem   /* 12px */
--text-sm: 0.875rem  /* 14px */
--text-base: 1rem    /* 16px */
--text-lg: 1.125rem  /* 18px */
--text-xl: 1.25rem   /* 20px */
```

**Spacing**:
```css
/* Padding/Margin */
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-6: 1.5rem    /* 24px */
```

### Animations

```css
/* Slide-in from right */
@keyframes slide-in-right {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}

/* Pulse for loading */
@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.animate-pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

.animation-delay-200 {
  animation-delay: 0.2s;
}

.animation-delay-400 {
  animation-delay: 0.4s;
}
```

### Responsive Design

**Breakpoints**:
```typescript
const breakpoints = {
  mobile: '320px',
  tablet: '768px',
  desktop: '1024px',
  wide: '1440px'
};
```

**Drawer Behavior**:
- Mobile (< 768px): Full-screen overlay
- Tablet/Desktop (>= 768px): 480px drawer from right

---

## API Integration

### FleetOneAPI Service

```typescript
// src/services/fleetOneApi.ts
export class FleetOneAPI {
  private baseUrl: string;
  private token: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    this.token = localStorage.getItem('auth_token') || '';
  }

  async createSession(userId: string, userRole: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/fleet-one/session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: userId, user_role: userRole })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Session creation failed');
    }

    const data = await response.json();
    return data.session_id;
  }

  async query(
    userId: string,
    userRole: string,
    query: string,
    forceMode?: string
  ): Promise<QueryResponse> {
    const response = await fetch(`${this.baseUrl}/fleet-one/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        user_role: userRole,
        query,
        force_mode: forceMode
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Query failed');
    }

    return await response.json();
  }

  async getHistory(sessionId: string): Promise<HistoryResponse> {
    const response = await fetch(
      `${this.baseUrl}/fleet-one/session/${sessionId}/history`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to load history');
    }

    return await response.json();
  }

  async clearSession(sessionId: string): Promise<void> {
    await fetch(`${this.baseUrl}/fleet-one/session/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
  }
}
```

---

## Implementierungsplan

### Sprint 1 (Woche 1): Core Components

**Tag 1-2**: Setup & Infrastruktur
- [ ] Zustand Store erstellen
- [ ] FleetOneAPI Service implementieren
- [ ] Types & Interfaces definieren

**Tag 3-4**: Basis-Komponenten
- [ ] FleetOneContainer
- [ ] FleetOneTrigger
- [ ] FleetOneDrawer (Shell)

**Tag 5**: Basic Chat
- [ ] ChatInput
- [ ] MessageList
- [ ] UserMessage / AssistantMessage

### Sprint 2 (Woche 2): Features & Polish

**Tag 6-7**: Advanced Features
- [ ] ModeIndicator
- [ ] StructuredDataRenderer
- [ ] ErrorDisplay & LoadingIndicator

**Tag 8-9**: Integration
- [ ] Session-Management
- [ ] History-Loading
- [ ] RBAC-Integration

**Tag 10**: Testing & Bugfixes
- [ ] Unit Tests (Components)
- [ ] Integration Tests (Store)
- [ ] E2E Tests (User Flows)

### Sprint 3 (Woche 3-4): Phase 2 Features

**Optional Erweiterungen**:
- [ ] Dashboard-Widgets
- [ ] Keyboard-Shortcuts (Cmd+K to open)
- [ ] Voice-Input
- [ ] Export-Funktion (Chat-Historie als PDF)
- [ ] Multi-Session-Tabs

---

## Testing-Strategie

### Unit Tests

```typescript
// src/components/FleetOne/__tests__/ChatInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput', () => {
  it('should render input field', () => {
    render(<ChatInput />);
    const input = screen.getByPlaceholderText(/Stellen Sie eine Frage/i);
    expect(input).toBeInTheDocument();
  });

  it('should disable send button when input is empty', () => {
    render(<ChatInput />);
    const button = screen.getByRole('button', { name: /senden/i });
    expect(button).toBeDisabled();
  });

  it('should call sendQuery on submit', () => {
    const mockSendQuery = jest.fn();
    jest.mock('@/stores/fleetOneStore', () => ({
      useFleetOneStore: () => ({
        sendQuery: mockSendQuery,
        loading: false
      })
    }));

    render(<ChatInput />);
    const input = screen.getByPlaceholderText(/Stellen Sie eine Frage/i);
    const button = screen.getByRole('button', { name: /senden/i });

    fireEvent.change(input, { target: { value: 'Test query' } });
    fireEvent.click(button);

    expect(mockSendQuery).toHaveBeenCalledWith('Test query', undefined);
  });
});
```

### Integration Tests

```typescript
// src/stores/__tests__/fleetOneStore.test.ts
import { renderHook, act } from '@testing-library/react-hooks';
import { useFleetOneStore } from '../fleetOneStore';

describe('fleetOneStore', () => {
  it('should initialize session', async () => {
    const { result } = renderHook(() => useFleetOneStore());

    await act(async () => {
      await result.current.initSession('user123', 'dispatcher');
    });

    expect(result.current.sessionId).toBeTruthy();
    expect(result.current.userId).toBe('user123');
    expect(result.current.userRole).toBe('dispatcher');
  });

  it('should send query and update messages', async () => {
    const { result } = renderHook(() => useFleetOneStore());

    await act(async () => {
      await result.current.initSession('user123', 'dispatcher');
    });

    await act(async () => {
      await result.current.sendQuery('Zeige alle Loks');
    });

    expect(result.current.messages.length).toBeGreaterThan(0);
    expect(result.current.messages[0].role).toBe('user');
  });
});
```

### E2E Tests (Cypress)

```typescript
// cypress/e2e/fleet-one.cy.ts
describe('FLEET-ONE Integration', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.login('dispatcher@example.com', 'password');
  });

  it('should open chat drawer', () => {
    cy.get('[aria-label="FLEET-ONE Agent öffnen"]').click();
    cy.contains('FLEET-ONE').should('be.visible');
  });

  it('should send query and receive response', () => {
    cy.get('[aria-label="FLEET-ONE Agent öffnen"]').click();
    cy.get('textarea[placeholder*="Stellen Sie eine Frage"]')
      .type('Zeige alle Loks mit Status maintenance_due{enter}');

    cy.contains('Ich habe').should('be.visible');
    cy.contains('FLOTTE').should('be.visible'); // Mode badge
  });

  it('should display RBAC error for viewer role', () => {
    cy.logout();
    cy.login('viewer@example.com', 'password');

    cy.get('[aria-label="FLEET-ONE Agent öffnen"]').click();
    cy.get('textarea[placeholder*="Stellen Sie eine Frage"]')
      .type('Erstelle Werkstattauftrag{enter}');

    cy.contains('Zugriff verweigert').should('be.visible');
  });
});
```

---

## Zusammenfassung

### Key Deliverables

✅ **9 React Components** (Container, Trigger, Drawer, Header, Messages, Input, Mode, Data)
✅ **Zustand Store** (Session, Query, History)
✅ **FleetOneAPI Service** (HTTP Client)
✅ **Design System** (Colors, Typography, Animations)
✅ **Testing Suite** (Unit, Integration, E2E)

### Timeline

- **Phase 1 (MVP)**: 2 Wochen
- **Phase 2 (Extended)**: +2 Wochen
- **Phase 3 (Enterprise)**: +2 Wochen

**Total**: 6 Wochen für vollständige Integration

### Next Steps

1. Review & Approval dieses Plans
2. Setup Development Environment
3. Sprint 1 Start: Core Components
4. Wöchentliche Reviews & Iterationen

---

**Version**: 1.0.0
**Erstellt**: November 2025
**Autor**: RailFleet Manager Development Team
