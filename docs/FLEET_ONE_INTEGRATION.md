# FLEET-ONE Integration Guide

**Version**: 1.0.0
**Target Audience**: Frontend Developers, System Integrators

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Configuration](#setup--configuration)
4. [Frontend Integration](#frontend-integration)
5. [Backend Service Integration](#backend-service-integration)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)

---

## Overview

This guide helps developers integrate FLEET-ONE Agent into their applications. FLEET-ONE is a conversational AI agent for fleet management that:

- Processes natural language queries in German
- Routes to 7 specialized modes
- Enforces role-based access control (RBAC)
- Orchestrates 9 backend services
- Resolves conflicts via policy engine
- Logs all actions via event sourcing

**Integration Levels**:

1. **REST API Integration** - Call FLEET-ONE via HTTP endpoints
2. **SDK Integration** - Use Python SDK for direct integration
3. **Frontend Widget** - Embed chat widget in web applications
4. **Webhook Integration** - Receive async notifications (v1.1.0)

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Application                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │ Chat Widget│  │  Dashboard │  │  Direct API Calls  │    │
│  └─────┬──────┘  └─────┬──────┘  └──────────┬─────────┘    │
└────────┼───────────────┼────────────────────┼──────────────┘
         │               │                    │
         └───────────────┴────────────────────┘
                         │
                    HTTP/REST
                         │
┌────────────────────────┴─────────────────────────────────────┐
│                    FLEET-ONE Agent API                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              agent_core.py                            │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│  │  │ Mode Router │  │  Session Mgr │  │  Metrics   │  │   │
│  │  └─────────────┘  └──────────────┘  └────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           rbac_policy.py                              │   │
│  │  ┌──────────────┐  ┌─────────────────────────────┐  │   │
│  │  │ RBAC Engine  │  │    Policy Engine            │  │   │
│  │  └──────────────┘  └─────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        tool_orchestrator.py                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │   │
│  │  │ Fleet  │ │ Maint  │ │Workshop│ │Transfer│  ...   │   │
│  │  │  DB    │ │Service │ │Service │ │Service │        │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      use_case_handlers.py                             │   │
│  │  UC1│UC2│UC3│UC4│UC5│UC8│UC9                          │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
         │       │       │       │       │
    ┌────┴───┬───┴───┬───┴───┬───┴───┬───┴────┐
    │        │       │       │       │        │
┌───▼───┐┌───▼──┐┌───▼───┐┌───▼──┐┌───▼───┐  │
│Fleet  ││Maint ││Workshop││Transf││Procure│ ...│
│  DB   ││Servic││Service ││Servic││ment   │  │
└───────┘└──────┘└────────┘└──────┘└───────┘  │
                  Backend Services              │
```

### Data Flow

1. **User Query** → Frontend sends query to `/fleet-one/query`
2. **Mode Routing** → Agent detects mode (FLOTTE, MAINTENANCE, etc.)
3. **RBAC Check** → Validates user role has required permissions
4. **Tool Orchestration** → Calls backend services via HTTP
5. **Policy Resolution** → Resolves conflicts if concurrent updates
6. **Event Logging** → Logs action to event store
7. **Response** → Returns German response to frontend

---

## Setup & Configuration

### 1. Environment Variables

Create `.env` file with backend service configuration:

```bash
# FLEET-ONE Configuration
FLEET_ONE_LANGUAGE=de
FLEET_ONE_TIMEZONE=Europe/Berlin

# Backend Service URLs
FLEET_BASE_URL=http://localhost:8001/api/v1
MAINT_BASE_URL=http://localhost:8002/api/v1
WORKSHOP_BASE_URL=http://localhost:8003/api/v1
TRANSFER_BASE_URL=http://localhost:8004/api/v1
PROC_BASE_URL=http://localhost:8005/api/v1
REPORT_BASE_URL=http://localhost:8006/api/v1
FIN_BASE_URL=http://localhost:8007/api/v1
HR_BASE_URL=http://localhost:8008/api/v1
DOCS_BASE_URL=http://localhost:8009/api/v1

# Backend Service API Tokens
FLEET_API_TOKEN=your_fleet_token
MAINT_API_TOKEN=your_maint_token
WORKSHOP_API_TOKEN=your_workshop_token
TRANSFER_API_TOKEN=your_transfer_token
PROC_API_TOKEN=your_proc_token
REPORT_API_TOKEN=your_report_token
FIN_API_TOKEN=your_fin_token
HR_API_TOKEN=your_hr_token
DOCS_API_TOKEN=your_docs_token

# LLM Configuration (if using external LLM)
LLM_API_KEY=your_llm_api_key
LLM_MODEL=claude-3-sonnet
LLM_TEMPERATURE=0.7
```

### 2. Policy Configuration

Configure conflict resolution policy in `config/fleet_one_policy.json`:

```json
{
  "name": "FLEET-ONE",
  "version": "1.0.0",
  "language": "de",
  "timezone": "Europe/Berlin",
  "policy": {
    "conflict_matrix": [
      {
        "field": "work_order.scheduled_start_end",
        "authority": "dispatcher",
        "resolver": "register-policy",
        "description": "Dispatcher has authority over planned times"
      },
      {
        "field": "work_order.actual_start_end_ts",
        "authority": "workshop",
        "resolver": "register-authoritative",
        "description": "Workshop is authoritative source for actual times"
      }
    ]
  }
}
```

### 3. Initialize Agent

In your application startup (`src/app.py`):

```python
from src.services.fleet_one import (
    get_agent,
    init_orchestrator,
    init_policy_engine,
    get_orchestrator
)
from src.api.v1.endpoints import fleet_one

# Initialize orchestrator with config
orchestrator_config = {
    "language": "de",
    "timezone": "Europe/Berlin"
}
init_orchestrator(orchestrator_config)

# Initialize policy engine
with open("config/fleet_one_policy.json") as f:
    policy_config = json.load(f)
init_policy_engine(policy_config["policy"]["conflict_matrix"])

# Register API router
app.include_router(
    fleet_one.router,
    prefix="/api/v1",
    tags=["FLEET-ONE Agent"]
)
```

---

## Frontend Integration

### Option 1: REST API Integration (Recommended)

**TypeScript/JavaScript Example**:

```typescript
// fleet-one-client.ts
export class FleetOneClient {
  private baseUrl: string;
  private token: string;
  private sessionId?: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
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

    const data = await response.json();
    this.sessionId = data.session_id;
    return this.sessionId;
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
        session_id: this.sessionId,
        user_id: userId,
        user_role: userRole,
        query,
        force_mode: forceMode
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }

    return await response.json();
  }

  async getHistory(): Promise<HistoryResponse> {
    if (!this.sessionId) throw new Error('No active session');

    const response = await fetch(
      `${this.baseUrl}/fleet-one/session/${this.sessionId}/history`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );

    return await response.json();
  }

  async clearSession(): Promise<void> {
    if (!this.sessionId) return;

    await fetch(
      `${this.baseUrl}/fleet-one/session/${this.sessionId}`,
      {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );

    this.sessionId = undefined;
  }
}

// Types
interface QueryResponse {
  success: boolean;
  message: string;
  session_id: string;
  mode: string;
  mode_confidence: number;
  data?: any;
  timestamp: string;
}

interface HistoryResponse {
  session_id: string;
  user_id: string;
  user_role: string;
  history: Array<{
    query: string;
    response: string;
    mode: string;
    timestamp: string;
  }>;
}
```

**React Component Example**:

```typescript
// FleetOneChat.tsx
import React, { useState, useEffect } from 'react';
import { FleetOneClient } from './fleet-one-client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  mode?: string;
  timestamp: Date;
}

export const FleetOneChat: React.FC<{
  userId: string;
  userRole: string;
  token: string;
}> = ({ userId, userRole, token }) => {
  const [client] = useState(() => new FleetOneClient(
    'http://localhost:8000/api/v1',
    token
  ));
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Create session on mount
    client.createSession(userId, userRole);

    return () => {
      // Clear session on unmount
      client.clearSession();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Query agent
      const response = await client.query(userId, userRole, input);

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        mode: response.mode,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Handle error
      const errorMessage: Message = {
        role: 'assistant',
        content: `Fehler: ${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fleet-one-chat">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.mode && (
              <div className="mode-badge">{msg.mode}</div>
            )}
            <div className="timestamp">
              {msg.timestamp.toLocaleTimeString('de-DE')}
            </div>
          </div>
        ))}
        {loading && <div className="loading">Agent denkt nach...</div>}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Stellen Sie eine Frage... (z.B. 'Zeige alle Loks mit Status maintenance_due')"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Senden
        </button>
      </form>
    </div>
  );
};
```

### Option 2: Python SDK Integration

**Direct Python Usage**:

```python
from src.services.fleet_one import (
    get_agent,
    init_orchestrator,
    init_policy_engine
)

# Initialize (once at startup)
orchestrator_config = {"language": "de", "timezone": "Europe/Berlin"}
init_orchestrator(orchestrator_config)

policy_rules = [...]  # Load from config
init_policy_engine(policy_rules)

# Get agent instance
agent = get_agent()

# Create session
session_id = agent.create_session(
    user_id="user123",
    role="dispatcher"
)

# Process query
response = agent.process_query(
    session_id=session_id,
    query="Zeige mir alle Loks mit Status maintenance_due"
)

print(response.message)  # German response
print(response.mode)     # Detected mode (e.g., "FLOTTE")
print(response.data)     # Structured data
```

### Option 3: Chat Widget (Pre-built Component)

**HTML/JavaScript Widget** (Coming in v1.1.0):

```html
<!-- Include widget script -->
<script src="https://cdn.example.com/fleet-one-widget.js"></script>

<!-- Initialize widget -->
<script>
  FleetOneWidget.init({
    apiUrl: 'http://localhost:8000/api/v1',
    token: 'your_token',
    userId: 'user123',
    userRole: 'dispatcher',
    language: 'de',
    theme: 'light',
    position: 'bottom-right'
  });
</script>
```

---

## Backend Service Integration

### Creating a Backend Service

If you're developing a new backend service that FLEET-ONE should orchestrate:

**1. Implement REST API Endpoints**:

```python
# your_service/api.py
from fastapi import APIRouter, Depends
from typing import List

router = APIRouter()

@router.get("/your-resource")
def list_resources(
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """List resources with optional filters"""
    # Your implementation
    return {"resources": [...]}

@router.post("/your-resource")
def create_resource(data: ResourceCreate):
    """Create new resource"""
    # Your implementation
    return {"id": "RES-123", "status": "created"}

@router.patch("/your-resource/{id}")
def update_resource(id: str, data: ResourceUpdate):
    """Update resource"""
    # Your implementation
    return {"id": id, "status": "updated"}
```

**2. Register Service in ToolOrchestrator**:

```python
# src/services/fleet_one/tool_orchestrator.py

class ServiceType(Enum):
    # ... existing services
    YOUR_SERVICE = "your_service"

class ToolOrchestrator:
    def _init_clients(self):
        # ... existing clients

        # Your Service
        clients[ServiceType.YOUR_SERVICE] = HTTPToolClient(
            base_url=os.getenv("YOUR_SERVICE_BASE_URL", "http://localhost:8010/api/v1"),
            auth_token=os.getenv("YOUR_SERVICE_API_TOKEN")
        )

        return clients

    # Add methods for your service
    def list_your_resources(
        self,
        status: Optional[str] = None
    ) -> ToolCallResult:
        """List your resources"""
        params = {}
        if status:
            params["status"] = status

        result = self.clients[ServiceType.YOUR_SERVICE].get(
            "/your-resource",
            params=params
        )
        result.service = ServiceType.YOUR_SERVICE
        return result
```

**3. Add Mode Keywords (if new mode)**:

```python
# src/services/fleet_one/agent_core.py

class AgentMode(Enum):
    # ... existing modes
    YOUR_MODE = "YOUR_MODE"

class ModeRouter:
    MODE_PATTERNS = {
        # ... existing patterns
        AgentMode.YOUR_MODE: [
            r'\b(your|keywords|here)\b',
            r'\b(another|set)\b'
        ]
    }
```

**4. Implement Use Case Handler**:

```python
# src/services/fleet_one/use_case_handlers.py

class UseCaseHandlers:
    def handle_your_use_case(
        self,
        param1: str,
        param2: int,
        user_role: str
    ) -> HandlerResult:
        """
        Your use case description.

        Sequence:
        1. List resources
        2. Create resource
        3. Update status
        """
        # RBAC check
        rbac = get_rbac_engine()
        access = rbac.check_access(user_role, "your:scope")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert. {access.reason}",
                data=None
            )

        # Tool calls
        orchestrator = get_orchestrator()

        # 1. List resources
        result1 = orchestrator.list_your_resources(status="active")
        if not result1.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Abrufen: {result1.error}",
                data=None
            )

        # 2. Create resource
        result2 = orchestrator.create_your_resource(...)

        # Generate German response
        message = f"Erfolgreich verarbeitet. {len(result1.data)} Ressourcen gefunden."

        return HandlerResult(
            success=True,
            message=message,
            data={
                "resources": result1.data,
                "created": result2.data
            }
        )
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_fleet_one_mode_router.py
import pytest
from src.services.fleet_one.agent_core import ModeRouter, AgentMode

def test_flotte_mode_detection():
    router = ModeRouter()
    mode, confidence = router.detect_mode("Zeige mir alle Loks")

    assert mode == AgentMode.FLOTTE
    assert confidence > 0.5

def test_maintenance_mode_detection():
    router = ModeRouter()
    mode, confidence = router.detect_mode("Welche HU-Fristen laufen ab?")

    assert mode == AgentMode.MAINTENANCE
    assert confidence > 0.5
```

### Integration Tests with Mocks

```python
# tests/integration/test_fleet_one_use_cases.py
import pytest
from unittest.mock import Mock, MagicMock
from src.services.fleet_one.use_case_handlers import UseCaseHandlers

@pytest.fixture
def mock_orchestrator():
    orchestrator = Mock()

    # Mock get_locomotives response
    orchestrator.get_locomotives.return_value = MagicMock(
        success=True,
        data=[
            {"id": "BR185-042", "status": "maintenance_due"},
            {"id": "BR189-033", "status": "maintenance_due"}
        ]
    )

    return orchestrator

def test_vehicle_status_handler(mock_orchestrator):
    handlers = UseCaseHandlers()
    handlers.orchestrator = mock_orchestrator

    result = handlers.handle_vehicle_status(
        status="maintenance_due",
        user_role="dispatcher"
    )

    assert result.success
    assert "2 Lokomotiven" in result.message
    assert len(result.data["locomotives"]) == 2

    # Verify orchestrator was called correctly
    mock_orchestrator.get_locomotives.assert_called_once_with(
        status="maintenance_due"
    )
```

### End-to-End Tests

```python
# tests/e2e/test_fleet_one_api.py
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_query_endpoint_success():
    response = client.post(
        "/api/v1/fleet-one/query",
        json={
            "user_id": "test_user",
            "user_role": "dispatcher",
            "query": "Zeige mir alle Loks"
        },
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "session_id" in data
    assert data["mode"] in ["FLOTTE", "MAINTENANCE", "WORKSHOP", ...]

def test_rbac_denied():
    response = client.post(
        "/api/v1/fleet-one/query",
        json={
            "user_id": "test_user",
            "user_role": "viewer",
            "query": "Erstelle Werkstattauftrag"
        },
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "Zugriff verweigert" in data["message"]
```

---

## Deployment

### Docker Deployment

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV FLEET_ONE_LANGUAGE=de
ENV FLEET_ONE_TIMEZONE=Europe/Berlin

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  fleet-one-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLEET_ONE_LANGUAGE=de
      - FLEET_ONE_TIMEZONE=Europe/Berlin
      - FLEET_BASE_URL=http://fleet-db:8001/api/v1
      - MAINT_BASE_URL=http://maintenance:8002/api/v1
      # ... other service URLs
    env_file:
      - .env
    depends_on:
      - fleet-db
      - maintenance-service
      # ... other services
    networks:
      - fleet-network

  fleet-db:
    image: your-fleet-db:latest
    ports:
      - "8001:8001"
    networks:
      - fleet-network

  maintenance-service:
    image: your-maintenance-service:latest
    ports:
      - "8002:8002"
    networks:
      - fleet-network

  # ... other services

networks:
  fleet-network:
    driver: bridge
```

### Kubernetes Deployment

**deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleet-one-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fleet-one-agent
  template:
    metadata:
      labels:
        app: fleet-one-agent
    spec:
      containers:
      - name: fleet-one-agent
        image: your-registry/fleet-one-agent:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: FLEET_ONE_LANGUAGE
          value: "de"
        - name: FLEET_ONE_TIMEZONE
          value: "Europe/Berlin"
        envFrom:
        - configMapRef:
            name: fleet-one-config
        - secretRef:
            name: fleet-one-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/fleet-one/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/fleet-one/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fleet-one-agent
spec:
  selector:
    app: fleet-one-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/api/v1/fleet-one/health

# Metrics endpoint
curl http://localhost:8000/api/v1/fleet-one/metrics
```

### Prometheus Integration

**metrics.py**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
queries_total = Counter(
    'fleet_one_queries_total',
    'Total number of queries processed',
    ['mode', 'user_role']
)

query_duration = Histogram(
    'fleet_one_query_duration_seconds',
    'Query processing duration',
    ['mode']
)

active_sessions = Gauge(
    'fleet_one_active_sessions',
    'Number of active sessions'
)

tool_calls_total = Counter(
    'fleet_one_tool_calls_total',
    'Total number of tool calls',
    ['service', 'operation']
)

rbac_denied = Counter(
    'fleet_one_rbac_denied_total',
    'Number of RBAC denials',
    ['user_role', 'required_scope']
)
```

### Logging

```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in agent
logger.info(
    "query_processed",
    session_id=session_id,
    mode=mode,
    user_role=user_role,
    duration_ms=duration
)
```

---

## Troubleshooting

### Common Issues

**1. Backend service not reachable**
```bash
# Check service URLs
echo $FLEET_BASE_URL

# Test connectivity
curl -v http://localhost:8001/api/v1/health

# Check Docker network
docker network inspect fleet-network
```

**2. RBAC permission denied**
```bash
# Verify user role
curl -X POST http://localhost:8000/api/v1/fleet-one/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "user_role": "dispatcher", "query": "test"}'

# Check RBAC configuration
# Ensure role has required scope in rbac_policy.py
```

**3. Mode detection not working**
```bash
# Force specific mode
curl -X POST http://localhost:8000/api/v1/fleet-one/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "user_role": "dispatcher",
    "query": "Zeige Loks",
    "force_mode": "FLOTTE"
  }'
```

---

## Support

- **Documentation**: See `FLEET_ONE_BENUTZERHANDBUCH.md` for user guide
- **API Reference**: See `FLEET_ONE_API_REFERENCE.md` for detailed API docs
- **Issues**: Report bugs on GitHub Issues
- **Contact**: fleet-one-support@example.com

---

**Version**: 1.0.0
**Last Updated**: November 2025
**Maintained by**: RailFleet Manager Development Team
