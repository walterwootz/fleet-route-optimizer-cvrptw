# FLEET-ONE API Reference

**Version**: 1.0.0
**Base URL**: `/api/v1/fleet-one`
**Language**: German (Agent responses)
**Timezone**: Europe/Berlin

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
3. [Request/Response Models](#requestresponse-models)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)

---

## Authentication

All FLEET-ONE endpoints require authentication via the standard application authentication mechanism.

**Headers**:
```
Authorization: Bearer <your_token>
Content-Type: application/json
```

**User Context**:
- Each request must include `user_id` and `user_role` in the request body
- Roles: `dispatcher`, `workshop`, `procurement`, `finance`, `ecm`, `viewer`

---

## Endpoints

### 1. Query Agent

**Endpoint**: `POST /fleet-one/query`

**Description**: Main entry point for conversational queries. Processes natural language queries in German and routes to appropriate mode.

**Request Body**:
```json
{
  "session_id": "string (optional)",
  "user_id": "string (required)",
  "user_role": "string (required)",
  "query": "string (required)",
  "force_mode": "string (optional)"
}
```

**Response**:
```json
{
  "success": true,
  "message": "string (German response)",
  "session_id": "string",
  "mode": "string",
  "mode_confidence": 0.95,
  "data": {
    "tool_calls": [...],
    "results": {...}
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Modes**:
- `FLOTTE` - Fleet overview, locomotive status
- `MAINTENANCE` - Maintenance planning, deadlines
- `WORKSHOP` - Workshop orders, repairs
- `PROCUREMENT` - Parts, purchasing
- `FINANCE` - Invoices, budgets
- `HR` - Staff, assignments
- `DOCS` - Documents, certifications

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "user_role": "dispatcher",
    "query": "Zeige mir alle Loks mit Status maintenance_due"
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Ich habe 3 Lokomotiven mit Status 'maintenance_due' gefunden:\n1. BR185-042 - Fällig: 2025-12-05\n2. BR189-033 - Fällig: 2025-12-10\n3. BR152-123 - Fällig: 2025-12-15",
  "session_id": "sess_abc123",
  "mode": "FLOTTE",
  "mode_confidence": 0.98,
  "data": {
    "locomotives": [
      {"id": "BR185-042", "status": "maintenance_due", "due_date": "2025-12-05"},
      {"id": "BR189-033", "status": "maintenance_due", "due_date": "2025-12-10"},
      {"id": "BR152-123", "status": "maintenance_due", "due_date": "2025-12-15"}
    ]
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

---

### 2. Create Session

**Endpoint**: `POST /fleet-one/session`

**Description**: Creates a new conversation session for maintaining context across multiple queries.

**Request Body**:
```json
{
  "user_id": "string (required)",
  "user_role": "string (required)"
}
```

**Response**:
```json
{
  "session_id": "string",
  "user_id": "string",
  "user_role": "string",
  "created_at": "2025-11-24T10:30:00Z"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/session" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "user_role": "dispatcher"
  }'
```

---

### 3. Get Session History

**Endpoint**: `GET /fleet-one/session/{session_id}/history`

**Description**: Retrieves conversation history for a session.

**Path Parameters**:
- `session_id` (string, required): Session ID

**Response**:
```json
{
  "session_id": "string",
  "user_id": "string",
  "user_role": "string",
  "history": [
    {
      "query": "string",
      "response": "string",
      "mode": "string",
      "timestamp": "2025-11-24T10:30:00Z"
    }
  ],
  "created_at": "2025-11-24T10:00:00Z"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/fleet-one/session/sess_abc123/history" \
  -H "Authorization: Bearer <token>"
```

---

### 4. Clear Session

**Endpoint**: `DELETE /fleet-one/session/{session_id}`

**Description**: Clears conversation history for a session.

**Path Parameters**:
- `session_id` (string, required): Session ID

**Response**:
```json
{
  "message": "Session history cleared",
  "session_id": "string"
}
```

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/fleet-one/session/sess_abc123" \
  -H "Authorization: Bearer <token>"
```

---

### 5. List Modes

**Endpoint**: `GET /fleet-one/modes`

**Description**: Lists all available agent modes with descriptions and keywords.

**Response**:
```json
{
  "modes": [
    {
      "name": "FLOTTE",
      "description": "Fleet overview, locomotive status, availability",
      "keywords": ["flotte", "lok", "loks", "lokomotiven", "verfügbarkeit", "status"]
    },
    {
      "name": "MAINTENANCE",
      "description": "Maintenance planning, HU deadlines, inspections",
      "keywords": ["wartung", "instandhaltung", "HU", "fristen", "fällig"]
    }
  ]
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/fleet-one/modes" \
  -H "Authorization: Bearer <token>"
```

---

### 6. Get Metrics

**Endpoint**: `GET /fleet-one/metrics`

**Description**: Retrieves agent performance metrics.

**Response**:
```json
{
  "active_sessions": 15,
  "total_queries": 1234,
  "avg_response_time_ms": 450,
  "tool_calls": {
    "get_locomotives": 234,
    "create_workshop_order": 45,
    "list_maintenance_tasks": 89
  },
  "mode_distribution": {
    "FLOTTE": 0.35,
    "MAINTENANCE": 0.25,
    "WORKSHOP": 0.20,
    "PROCUREMENT": 0.10,
    "FINANCE": 0.05,
    "HR": 0.03,
    "DOCS": 0.02
  },
  "error_rate": 0.02
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/fleet-one/metrics" \
  -H "Authorization: Bearer <token>"
```

---

### 7. Health Check

**Endpoint**: `GET /fleet-one/health`

**Description**: Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy",
  "agent_version": "1.0.0",
  "backend_services": {
    "fleet_db": "connected",
    "maintenance_service": "connected",
    "workshop_service": "connected",
    "transfer_service": "connected",
    "procurement_service": "connected",
    "reporting_service": "connected",
    "finance_service": "connected",
    "hr_service": "connected",
    "docs_service": "connected"
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/fleet-one/health" \
  -H "Authorization: Bearer <token>"
```

---

### 8. Execute Use Case

**Endpoint**: `POST /fleet-one/use-case/{use_case_name}`

**Description**: Directly executes a predefined use case without conversational interface.

**Path Parameters**:
- `use_case_name` (string, required): Use case identifier

**Available Use Cases**:
- `hu_planning` - HU/Deadline planning → Workshop
- `parts_procurement` - Parts procurement check & ordering
- `transfer_staff` - Staff planning for workshop transfers
- `invoice_entry` - Invoice entry & WO assignment
- `documents` - Documents: expiring & linking
- `vehicle_status` - Vehicle status & plan flag setting
- `availability_report` - Availability report
- `maintenance_task` - Maintenance task creation & planning

**Request Body**: (varies by use case, see examples below)

**Response**:
```json
{
  "success": true,
  "message": "string (German response)",
  "data": {
    "result": {...}
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Example - HU Planning**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/use-case/hu_planning" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_role": "dispatcher",
    "params": {
      "workshop_id": "WERK-MUC",
      "days_ahead": 14
    }
  }'
```

**Example - Parts Procurement**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/use-case/parts_procurement" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_role": "procurement",
    "params": {
      "part_no": "P-45678",
      "required_qty": 50,
      "needed_by": "2025-12-15",
      "related_wo_id": "WO-12345"
    }
  }'
```

---

## Request/Response Models

### QueryRequest

```typescript
interface QueryRequest {
  session_id?: string;      // Optional: Reuse existing session
  user_id: string;          // Required: User identifier
  user_role: string;        // Required: User role (dispatcher, workshop, etc.)
  query: string;            // Required: Natural language query in German
  force_mode?: string;      // Optional: Force specific mode (FLOTTE, MAINTENANCE, etc.)
}
```

### QueryResponse

```typescript
interface QueryResponse {
  success: boolean;         // Operation success status
  message: string;          // German response message
  session_id: string;       // Session identifier
  mode: string;             // Detected/used mode
  mode_confidence: number;  // Confidence score (0-1)
  data?: any;               // Optional: Structured data
  timestamp: string;        // ISO 8601 timestamp (UTC)
}
```

### SessionRequest

```typescript
interface SessionRequest {
  user_id: string;          // Required: User identifier
  user_role: string;        // Required: User role
}
```

### SessionResponse

```typescript
interface SessionResponse {
  session_id: string;       // Generated session ID
  user_id: string;          // User identifier
  user_role: string;        // User role
  created_at: string;       // ISO 8601 timestamp (UTC)
}
```

### UseCaseRequest

```typescript
interface UseCaseRequest {
  user_role: string;        // Required: User role for RBAC
  params: any;              // Use case specific parameters
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "message": "Error description in German",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "additional context"
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RBAC_DENIED` | 403 | Permission denied for user role |
| `SESSION_NOT_FOUND` | 404 | Session ID not found |
| `INVALID_MODE` | 400 | Invalid mode specified |
| `BACKEND_ERROR` | 502 | Backend service error |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication failed |
| `RATE_LIMIT` | 429 | Too many requests |

### RBAC Errors

```json
{
  "success": false,
  "message": "Zugriff verweigert. Rolle 'workshop' hat keine Berechtigung 'plan:create'",
  "error_code": "RBAC_DENIED",
  "details": {
    "required_scope": "plan:create",
    "user_role": "workshop"
  }
}
```

### Backend Service Errors

```json
{
  "success": false,
  "message": "Backend-Dienst 'maintenance_service' nicht erreichbar",
  "error_code": "BACKEND_ERROR",
  "details": {
    "service": "maintenance_service",
    "http_status": 503,
    "error": "Connection timeout"
  }
}
```

### Validation Errors

```json
{
  "success": false,
  "message": "Validierungsfehler: 'due_date' muss im Format YYYY-MM-DD sein",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "due_date",
    "provided": "31.12.2025",
    "expected": "2025-12-31"
  }
}
```

---

## Rate Limiting

**Limits**:
- 100 requests per minute per user
- 1000 requests per hour per user

**Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1732445400
```

**Rate Limit Exceeded Response**:
```json
{
  "success": false,
  "message": "Anfragelimit überschritten. Bitte versuchen Sie es später erneut.",
  "error_code": "RATE_LIMIT",
  "details": {
    "limit": 100,
    "reset_at": "2025-11-24T10:35:00Z"
  }
}
```

---

## Examples

### Example 1: Complete Workflow - HU Planning

**Step 1: Create Session**
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/session" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "dispatcher_01",
    "user_role": "dispatcher"
  }'
```

Response:
```json
{
  "session_id": "sess_xyz789",
  "user_id": "dispatcher_01",
  "user_role": "dispatcher",
  "created_at": "2025-11-24T10:00:00Z"
}
```

**Step 2: Query - List Due Maintenance**
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_xyz789",
    "user_id": "dispatcher_01",
    "user_role": "dispatcher",
    "query": "Welche HU-Fristen laufen in den nächsten 14 Tagen ab?"
  }'
```

Response:
```json
{
  "success": true,
  "message": "In den nächsten 14 Tagen laufen 3 HU-Fristen ab:\n1. BR185-042 - Fällig: 05.12.2025\n2. BR189-033 - Fällig: 10.12.2025\n3. BR152-123 - Fällig: 13.12.2025",
  "session_id": "sess_xyz789",
  "mode": "MAINTENANCE",
  "mode_confidence": 0.97,
  "data": {
    "tasks": [
      {"locomotive_id": "BR185-042", "type": "HU", "due_date": "2025-12-05"},
      {"locomotive_id": "BR189-033", "type": "HU", "due_date": "2025-12-10"},
      {"locomotive_id": "BR152-123", "type": "HU", "due_date": "2025-12-13"}
    ]
  }
}
```

**Step 3: Follow-up Query - Create Workshop Order**
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_xyz789",
    "user_id": "dispatcher_01",
    "user_role": "dispatcher",
    "query": "Plane HU für BR185-042 in Werk München vom 05.12.2025 10:00 bis 07.12.2025 16:00"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Werkstattauftrag WO-98765 erstellt für Lokomotive BR185-042, Werk München. Geplant: 05.12.2025 10:00 - 07.12.2025 16:00 Uhr. Aufgaben: HU, Bremsprüfung.",
  "session_id": "sess_xyz789",
  "mode": "WORKSHOP",
  "mode_confidence": 0.99,
  "data": {
    "workshop_order_id": "WO-98765",
    "locomotive_id": "BR185-042",
    "workshop_id": "WERK-MUC",
    "planned_start": "2025-12-05T10:00:00",
    "planned_end": "2025-12-07T16:00:00"
  }
}
```

---

### Example 2: Direct Use Case Execution

**Execute Parts Procurement Use Case**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/use-case/parts_procurement" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_role": "procurement",
    "params": {
      "part_no": "P-45678",
      "required_qty": 50,
      "needed_by": "2025-12-15",
      "related_wo_id": "WO-12345"
    }
  }'
```

Response:
```json
{
  "success": true,
  "message": "Lagerbestand für Teil P-45678: 12 Stück verfügbar. Bestellanforderung PR-6789 erstellt für 50 Stück, Lieferdatum 15.12.2025.",
  "data": {
    "stock": {
      "part_no": "P-45678",
      "available": 12,
      "reserved": 5,
      "free": 7
    },
    "purchase_request": {
      "id": "PR-6789",
      "part_no": "P-45678",
      "qty": 50,
      "needed_by": "2025-12-15",
      "status": "pending"
    }
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

---

### Example 3: Error Handling

**Permission Denied**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "viewer_01",
    "user_role": "viewer",
    "query": "Erstelle Werkstattauftrag für BR185-042"
  }'
```

Response:
```json
{
  "success": false,
  "message": "Zugriff verweigert. Rolle 'viewer' hat keine Berechtigung 'wo:create'. Werkstattaufträge können nur von Disponenten erstellt werden.",
  "error_code": "RBAC_DENIED",
  "details": {
    "required_scope": "wo:create",
    "user_role": "viewer",
    "allowed_roles": ["dispatcher"]
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

---

## Webhooks (Future)

FLEET-ONE will support webhooks for async notifications:

- Workshop order status changes
- Maintenance deadline alerts
- Low stock warnings
- Document expiration notifications

**Configuration**: (Coming in v1.1.0)
```json
{
  "webhook_url": "https://your-app.com/webhooks/fleet-one",
  "events": ["wo:status_changed", "maintenance:deadline_approaching"],
  "secret": "your_webhook_secret"
}
```

---

## Changelog

### v1.0.0 (2025-11-24)
- Initial release
- 7 agent modes
- 9 playbook use cases
- RBAC with 6 roles
- Policy-based conflict resolution
- Event sourcing integration

---

**Maintained by**: RailFleet Manager Development Team
**Last Updated**: November 2025
