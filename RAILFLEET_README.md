# 🚂 RailFleet Manager

**Complete Railway Fleet Management System with Route Optimization**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

---

## 📋 Overview

**RailFleet Manager** is a comprehensive railway fleet management system that combines:

- 🚂 **Fleet Management**: Track locomotives, status, mileage, and specifications
- 🔧 **Maintenance Management**: Schedule and track maintenance tasks (HU, Inspections, ECM)
- 🏭 **Workshop Management**: Manage workshops, capacity, and certifications
- 🔄 **Offline-First Sync**: Mobile-first with conflict detection and resolution
- 🔐 **Authentication & Authorization**: JWT-based RBAC with 5 role levels
- 📊 **Route Optimization**: CVRPTW solver with OR-Tools and Gurobi

**Integrated with FLEET-ONE Playbook** for professional railway operations.

---

## ✨ Key Features

### 🎯 Core System (Phase 1)

#### 1. Authentication & Authorization
- ✅ JWT-based authentication (Access + Refresh tokens)
- ✅ Role-based access control (5 roles: SUPER_ADMIN, FLEET_MANAGER, WORKSHOP_MANAGER, DISPATCHER, TECHNICIAN, VIEWER)
- ✅ Password validation & hashing (bcrypt)
- ✅ User management

#### 2. Vehicle Management
- ✅ Complete CRUD operations
- ✅ Status management (7 statuses: available, in_service, workshop_planned, in_workshop, out_of_service, maintenance_due, retired)
- ✅ Mileage tracking with validation (only increase!)
- ✅ Advanced filtering & search

#### 3. Maintenance Management
- ✅ Maintenance tasks (HU, Inspection, ECM, Repair, Preventive)
- ✅ Workshop work orders
- ✅ Due date tracking & alerts
- ✅ FLEET-ONE Playbook compatible

#### 4. Workshop Management
- ✅ Workshop CRUD operations
- ✅ Capacity management (tracks)
- ✅ ECM certification tracking
- ✅ Specialization management

### 🔄 FLEET-ONE Integration (Phase 2)

#### 1. Policy Engine
- ✅ Policy loader with SHA-256 hash verification
- ✅ Field authority checking (workshop vs dispatcher)
- ✅ Role-based permission validation
- ✅ Conflict detection rules
- ✅ Resolution strategies

#### 2. Sync Service
- ✅ Offline-first sync logic
- ✅ Event processing
- ✅ Conflict detection
- ✅ Policy enforcement
- ✅ Authority validation

#### 3. Route Optimization
- ✅ OR-Tools CVRPTW solver
- ✅ Gurobi support
- ✅ Real-world distance matrix (OSRM)
- ✅ Time-based routing (traffic patterns)
- ✅ Interactive visualization

---

## 🏗️ Architecture

```
railfleet-manager/
├── src/
│   ├── api/                      # API Layer
│   │   ├── v1/endpoints/         # RailFleet Manager endpoints
│   │   │   ├── auth.py           # Authentication (register, login, refresh)
│   │   │   ├── vehicles.py       # Vehicle management (CRUD)
│   │   │   ├── maintenance.py    # Maintenance tasks & work orders
│   │   │   ├── workshops.py      # Workshop management
│   │   │   └── sync.py           # Sync (push, pull, conflicts)
│   │   ├── routes.py             # CVRPTW solver routes
│   │   └── schemas/              # Pydantic schemas
│   │
│   ├── core/                     # Core Layer
│   │   ├── database.py           # SQLAlchemy setup
│   │   ├── security.py           # JWT, password hashing, RBAC
│   │   └── solvers/              # OR-Tools & Gurobi solvers
│   │
│   ├── models/                   # Data Models
│   │   ├── railfleet/            # Database models
│   │   │   ├── user.py
│   │   │   ├── vehicle.py
│   │   │   ├── maintenance.py
│   │   │   └── workshop.py
│   │   └── domain.py             # CVRPTW domain models
│   │
│   ├── services/                 # Business Logic
│   │   ├── railfleet/
│   │   │   └── sync_service.py   # Offline-first sync
│   │   └── solver_service.py     # Route optimization
│   │
│   ├── policy/                   # Policy Engine
│   │   └── loader.py             # Policy loader & validator
│   │
│   └── app.py                    # FastAPI application
│
├── policy/                       # FLEET-ONE policies
│   └── scheduler_conflict_policy.json
│
├── alembic/                      # Database migrations
│   ├── env.py
│   └── versions/
│
├── examples/                     # Example requests
│   └── push_request.json
│
├── docker/                       # Docker configuration
│   └── docker-compose.yml
│
├── Makefile                      # Common operations
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)

### 1. Clone & Setup

```bash
git clone <repository-url>
cd fleet-route-optimizer-cvrptw
```

### 2. Start with Docker (Recommended)

```bash
# Start all services (PostgreSQL, pgAdmin, Backend, Frontend)
make up

# Services will be available at:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
# - pgAdmin: http://localhost:5050
```

### 3. Run Database Migrations

```bash
make migrate
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# API documentation
open http://localhost:8000/docs
```

---

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)

```bash
POST /api/v1/auth/register     # Register new user
POST /api/v1/auth/login        # Login (get tokens)
POST /api/v1/auth/refresh      # Refresh access token
GET  /api/v1/auth/me           # Get current user info
```

### Vehicles (`/api/v1/vehicles`)

```bash
POST   /api/v1/vehicles              # Create vehicle
GET    /api/v1/vehicles              # List vehicles (with filters)
GET    /api/v1/vehicles/{id}         # Get vehicle details
PATCH  /api/v1/vehicles/{id}         # Update vehicle
DELETE /api/v1/vehicles/{id}         # Delete vehicle
```

### Maintenance (`/api/v1/maintenance`)

```bash
# Maintenance Tasks
POST /api/v1/maintenance/tasks       # Create maintenance task
GET  /api/v1/maintenance/tasks       # List tasks (with filters)

# Work Orders
POST  /api/v1/maintenance/orders     # Create work order
GET   /api/v1/maintenance/orders     # List work orders
PATCH /api/v1/maintenance/orders/{id} # Update work order
```

### Workshops (`/api/v1/workshops`)

```bash
POST  /api/v1/workshops              # Create workshop
GET   /api/v1/workshops              # List workshops
GET   /api/v1/workshops/{id}         # Get workshop details
PATCH /api/v1/workshops/{id}         # Update workshop
```

### Sync (`/api/v1/sync`)

```bash
POST /api/v1/sync/push               # Push offline changes
GET  /api/v1/sync/pull               # Pull server changes
GET  /api/v1/sync/conflicts          # List conflicts
POST /api/v1/sync/conflicts/{id}/resolve  # Resolve conflict
```

### Route Optimization (`/api/v1/solver`)

```bash
POST /api/v1/solver/solve            # Solve CVRPTW problem
POST /api/v1/solver/solve-stream     # Solve with SSE streaming
GET  /api/v1/solver/download-examples # Download example files
```

---

## 🔐 Authentication Example

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@railfleet.com",
    "password": "Admin123!",
    "role": "SUPER_ADMIN"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'

# Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 3. Use Token

```bash
TOKEN="your_access_token_here"

curl -X GET http://localhost:8000/api/v1/vehicles \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 FLEET-ONE Use Cases

### Use-Case 1: Plan HU in 30 Days

```bash
# 1. List vehicles needing HU
GET /api/v1/maintenance/tasks?overdue_only=true

# 2. Create work order
POST /api/v1/maintenance/orders
{
  "vehicle_id": "185123",
  "workshop_id": "WS-MUENCHEN",
  "priority": "high",
  "scheduled_start": "2026-01-15T08:00:00Z",
  "scheduled_end": "2026-01-15T16:00:00Z",
  "tasks": ["HU"]
}

# 3. Update vehicle status
PATCH /api/v1/vehicles/185123
{
  "status": "workshop_planned"
}
```

### Use-Case 7: Offline Sync with Conflict Detection

```bash
# Workshop updates actual start time (authoritative!)
POST /api/v1/sync/push
{
  "device_id": "MOB-001",
  "events": [{
    "id": "7d0c1234",
    "source_role": "workshop",
    "entity_type": "work_order",
    "entity_id": "WO-2025-0012",
    "field_changes": {
      "status": "in_progress",
      "actual_start_ts": "2026-01-04T08:05:00Z"
    }
  }]
}

# Response: No conflicts (workshop is authoritative for actual_start)
{
  "applied": ["7d0c1234"],
  "conflicts": [],
  "rejected": []
}
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# Database
DATABASE_URL=postgresql://railfleet:railfleet123@localhost:5432/railfleet_db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Solver
DEFAULT_SOLVER=ortools
ORTOOLS_VEHICLE_PENALTY=100000.0
GUROBI_VEHICLE_PENALTY=1000.0
```

---

## 🛠️ Development

### Local Development (without Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start PostgreSQL (or use Docker)
docker run -d \
  --name postgres \
  -e POSTGRES_USER=railfleet \
  -e POSTGRES_PASSWORD=railfleet123 \
  -e POSTGRES_DB=railfleet_db \
  -p 5432:5432 \
  postgres:15-alpine

# 3. Run migrations
alembic upgrade head

# 4. Start API server
make dev
# or
uvicorn src.app:app --reload --port 8000
```

### Create Database Migration

```bash
# Auto-generate migration from model changes
make migrate-create

# Apply migrations
make migrate
```

### Database Shell

```bash
make db-shell
```

---

## 📦 Database Schema

### Tables

- **users** - User accounts with RBAC
- **vehicles** - Locomotive fleet (asset_id, model, status, mileage)
- **maintenance_tasks** - Maintenance requirements (HU, Inspection, ECM)
- **work_orders** - Workshop work orders (PLAN + IST)
- **workshops** - Maintenance facilities
- **sync_conflicts** - Conflict tracking for offline sync

---

## 🔄 Policy Engine

The policy engine enforces FLEET-ONE rules:

### Field Authorities

- **Workshop (authoritative):**
  - `actual_start_ts` (IST)
  - `actual_end_ts` (IST)
  - `status`
  - `findings`
  - `work_performed`

- **Dispatcher (authoritative):**
  - `scheduled_start` (PLAN)
  - `scheduled_end` (PLAN)
  - `priority`
  - `assigned_track`
  - `assigned_team`

### Conflict Resolution

- `workshop_authoritative` - Workshop wins (IST)
- `dispatcher_authoritative` - Dispatcher wins (PLAN)
- `last_write_wins` - Last change wins
- `flag_conflict` - Require manual resolution

---

## 📊 Technology Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic
- **Database:** PostgreSQL 15
- **Authentication:** JWT (python-jose), bcrypt
- **Optimization:** OR-Tools, Gurobi
- **Routing:** OSRM
- **Frontend:** React 18
- **DevOps:** Docker, Docker Compose, Makefile

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **FLEET-ONE** - Railway fleet management best practices
- **Google OR-Tools** - Optimization solver
- **Gurobi** - Commercial optimization solver
- **FastAPI** - Modern web framework
- **PostgreSQL** - Robust database

---

**Made with ❤️ for Professional Railway Fleet Management** 🚂

**Version:** 2.0.0
**Status:** Production-Ready ✅
