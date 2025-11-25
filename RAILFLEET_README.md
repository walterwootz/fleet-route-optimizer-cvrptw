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

### 📦 Operations Management (Phase 2 - NEW) ⭐

#### 1. Inventory Management
- ✅ Parts catalog with railway classifications
- ✅ Stock locations (Workshops, Warehouses, Vendors)
- ✅ Stock moves tracking (INCOMING, USAGE, TRANSFER, ADJUSTMENT)
- ✅ Min stock alerts and reordering
- ✅ Real-time inventory overview

#### 2. Procurement
- ✅ Supplier management
- ✅ Purchase orders with multi-line support
- ✅ PO workflow (DRAFT → APPROVED → ORDERED → RECEIVED)
- ✅ Goods receipt with automatic stock moves
- ✅ Purchase order tracking and history

#### 3. Finance & Budget
- ✅ Invoice management (DRAFT → REVIEWED → APPROVED → POSTED)
- ✅ Invoice-to-PO matching
- ✅ Budget planning by cost center and category
- ✅ Actual vs planned budget tracking
- ✅ Variance calculation and monitoring

#### 4. Reporting & Analytics
- ✅ Availability reports (fleet uptime metrics)
- ✅ On-Time ratio (workshop delivery performance)
- ✅ Parts usage reports (consumption by part)
- ✅ Cost reports (budget vs actual by cost center)
- ✅ Executive dashboard (all KPIs in one view)

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

### 📦 Inventory Management (`/api/v1/parts`, `/api/v1/stock`) - NEW ⭐

```bash
# Parts
POST   /api/v1/parts              # Create part
GET    /api/v1/parts              # List parts (with filters)
GET    /api/v1/parts/{id}         # Get part details
PATCH  /api/v1/parts/{id}         # Update part
DELETE /api/v1/parts/{id}         # Delete part

# Stock Locations
POST   /api/v1/stock/locations         # Create stock location
GET    /api/v1/stock/locations         # List locations
GET    /api/v1/stock/locations/{id}    # Get location details
PATCH  /api/v1/stock/locations/{id}    # Update location
DELETE /api/v1/stock/locations/{id}    # Delete location

# Stock Moves
POST /api/v1/stock/moves          # Create stock move
GET  /api/v1/stock/moves          # List stock moves (with filters)
GET  /api/v1/stock/overview       # Stock overview (aggregated)
```

### 🛒 Procurement (`/api/v1/suppliers`, `/api/v1/purchase_orders`) - NEW ⭐

```bash
# Suppliers
POST   /api/v1/suppliers          # Create supplier
GET    /api/v1/suppliers          # List suppliers
GET    /api/v1/suppliers/{id}     # Get supplier details
PATCH  /api/v1/suppliers/{id}     # Update supplier
DELETE /api/v1/suppliers/{id}     # Delete supplier

# Purchase Orders
POST  /api/v1/purchase_orders           # Create PO
GET   /api/v1/purchase_orders           # List POs (with filters)
GET   /api/v1/purchase_orders/{id}      # Get PO details
PATCH /api/v1/purchase_orders/{id}      # Update PO
POST  /api/v1/purchase_orders/{id}/approve  # Approve PO
POST  /api/v1/purchase_orders/{id}/order    # Order PO
POST  /api/v1/purchase_orders/{id}/receive  # Receive goods → Creates Stock Moves
```

### 💰 Finance & Budget (`/api/v1/invoices`, `/api/v1/budget`) - NEW ⭐

```bash
# Invoices
POST  /api/v1/invoices            # Create invoice
GET   /api/v1/invoices            # List invoices (with filters)
GET   /api/v1/invoices/{id}       # Get invoice details
PATCH /api/v1/invoices/{id}       # Update invoice
POST  /api/v1/invoices/{id}/match      # Match invoice to PO
POST  /api/v1/invoices/{id}/approve    # Approve invoice → Updates Budget
POST  /api/v1/invoices/{id}/post       # Post invoice

# Budget
POST /api/v1/budget               # Create budget entry
GET  /api/v1/budget               # List budget entries (with filters)
GET  /api/v1/budget/overview      # Budget overview (aggregated)
```

### 📊 Reporting & Analytics (`/api/v1/reports`) - NEW ⭐

```bash
GET /api/v1/reports/availability    # Availability report (fleet uptime %)
GET /api/v1/reports/on_time_ratio   # On-Time ratio (workshop performance)
GET /api/v1/reports/parts_usage     # Parts usage report (consumption)
GET /api/v1/reports/costs           # Cost report (budget vs actual)
GET /api/v1/reports/dashboard       # Dashboard summary (all KPIs)
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

### Use-Case 14: Complete Procurement-to-Finance Workflow (Phase 2) ⭐

```bash
# 1. Create Part
POST /api/v1/parts
{
  "part_no": "BRK-PAD-001",
  "name": "Brake Pad - Standard",
  "railway_class": "STANDARD",
  "unit": "pc",
  "min_stock": 10,
  "current_stock": 5,
  "unit_price": 250.00
}

# 2. Create Supplier
POST /api/v1/suppliers
{
  "supplier_code": "SUP-KNORR",
  "name": "Knorr-Bremse AG",
  "email": "orders@knorr-bremse.com",
  "payment_terms": "NET30"
}

# 3. Create Purchase Order
POST /api/v1/purchase_orders
{
  "supplier_id": "SUP-KNORR",
  "order_date": "2025-11-23",
  "expected_delivery": "2025-12-15",
  "lines": [{
    "part_no": "BRK-PAD-001",
    "quantity": 50,
    "unit_price": 250.00
  }]
}

# 4. Approve & Order PO
POST /api/v1/purchase_orders/{po_id}/approve
POST /api/v1/purchase_orders/{po_id}/order

# 5. Receive Goods (Wareneingang) → Automatically creates Stock Moves
POST /api/v1/purchase_orders/{po_id}/receive
{
  "delivery_location_id": "LOC-WORKSHOP-MUC",
  "lines_received": [{
    "line_id": "{line_id}",
    "quantity_received": 50
  }]
}

# 6. Create Invoice
POST /api/v1/invoices
{
  "invoice_number": "INV-2025-001",
  "supplier_id": "SUP-KNORR",
  "invoice_date": "2025-12-15",
  "total_amount": 12500.00,
  "currency": "EUR"
}

# 7. Match Invoice to PO
POST /api/v1/invoices/{invoice_id}/match
{
  "purchase_order_id": "{po_id}"
}

# 8. Approve Invoice → Automatically updates Budget
POST /api/v1/invoices/{invoice_id}/approve
{
  "cost_center": "CC-MAINTENANCE",
  "approved_by": "admin@railfleet.com"
}

# 9. Check Budget Impact
GET /api/v1/budget/overview?period=2025-12
```

**Result:**
- ✅ Part stock increased from 5 to 55 units
- ✅ Stock moves automatically created
- ✅ Purchase order marked as RECEIVED
- ✅ Invoice matched and approved
- ✅ Budget actual_amount updated
- ✅ Full audit trail maintained

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

**Version:** 2.1.0 (Phase 2 Complete)
**Status:** Production-Ready ✅

## 📦 Phase 2 Deliverables

- ✅ **WP9:** Inventory Management (Parts, Stock Locations, Stock Moves) - 8 API endpoints
- ✅ **WP10:** Procurement (Suppliers, Purchase Orders) - 7 API endpoints
- ✅ **WP11:** Finance (Invoices, Budget, Cost Centers) - 6 API endpoints
- ✅ **WP12:** Reporting (Availability, On-Time, Parts Usage, Cost Reports) - 5 API endpoints
- ✅ **WP13:** Integration & Testing (E2E tests, Performance benchmarks)
- ✅ **WP14:** Postman Collection & Documentation

**Total:** 26+ new API endpoints, 3,415+ lines of production code, 987 lines of test code
