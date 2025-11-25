# 📮 Postman Collection - RailFleet Manager

## Overview

This directory contains Postman collections for testing the RailFleet Manager API.

## Collections

### `railfleet_manager_mvp.json`
Complete MVP collection covering:
- **Authentication** (Register, Login, Refresh Token)
- **Fleet Management** (CRUD vehicles)
- **Maintenance** (Tasks, Work Orders)
- **Workshops** (CRUD workshops)
- **Sync** (Push, Pull, Conflicts)
- **Scheduler** (Solve, What-If scenarios)

### `RailFleet_Manager_Phase2.postman_collection.json` ⭐ NEW
Complete Phase 2 MVP collection with 3 demo scenarios:
- **Authentication** (Login with automatic token management)
- **Demo 1: Inventory Flow** (8 requests)
  - Part → Stock Location → Supplier → Purchase Order → Approve → Order → Receive → Stock Moves
- **Demo 2: Finance Flow** (5 requests)
  - Budget → Invoice → Match against PO → Approve → Verify Budget Update
- **Demo 3: Reports** (5 requests)
  - Availability, On-Time Ratio, Parts Usage, Cost Report, Dashboard Summary

## Usage

### Import Phase 2 Collection (Recommended)

1. **Import Collection**
   - Open Postman
   - Click "Import"
   - Select `RailFleet_Manager_Phase2.postman_collection.json`
   - Collection imported with pre-configured requests

2. **Import Environment**
   - Click "Import"
   - Select `RailFleet_Manager.postman_environment.json`
   - All variables pre-configured (base_url, username, password, etc.)

3. **Run Demo Scenarios**
   - Open collection → Select "Demo 1: Inventory Flow"
   - Click "Run folder" to execute all 8 requests sequentially
   - Check test results and console logs

### Import Phase 1 Collection

1. Open Postman
2. Click "Import"
3. Select `railfleet_manager_mvp.json`
4. Collection will be imported with pre-configured requests

### Environment Variables

#### Phase 2 Environment (included in `RailFleet_Manager.postman_environment.json`)

```json
{
  "base_url": "http://localhost:8000",
  "username": "admin@railfleet.com",
  "password": "admin123",
  "auth_token": "",
  "token_expiry": "",
  "period": "2025-11",
  "part_id": "",
  "location_id": "",
  "supplier_id": "",
  "po_id": "",
  "invoice_id": "",
  "budget_id": ""
}
```

#### Phase 1 Environment (manual setup)

```json
{
  "BASE_URL": "http://localhost:8000",
  "SOLVER_URL": "http://localhost:7070",
  "ACCESS_TOKEN": "",
  "REFRESH_TOKEN": "",
  "DEVICE_ID": "MOB-001"
}
```

### Quick Start Flow

1. **Register User**
   ```
   POST {{BASE_URL}}/api/v1/auth/register
   ```

2. **Login**
   ```
   POST {{BASE_URL}}/api/v1/auth/login
   ```
   → Save `access_token` to environment

3. **Create Vehicle**
   ```
   POST {{BASE_URL}}/api/v1/vehicles
   Headers: Authorization: Bearer {{ACCESS_TOKEN}}
   ```

4. **Solve Schedule**
   ```
   POST {{SOLVER_URL}}/solve
   Body: @examples/solve_request.json
   ```

## Pre-Request Scripts

The collection includes automatic token refresh:

```javascript
// Refresh token if expired
pm.sendRequest({
    url: pm.environment.get("BASE_URL") + "/api/v1/auth/refresh",
    method: 'POST',
    header: {
        'Content-Type': 'application/json'
    },
    body: {
        mode: 'raw',
        raw: JSON.stringify({
            refresh_token: pm.environment.get("REFRESH_TOKEN")
        })
    }
}, function (err, res) {
    if (!err) {
        pm.environment.set("ACCESS_TOKEN", res.json().access_token);
    }
});
```

## Example Scenarios

### Phase 2 Demo Scenarios (NEW) ⭐

#### Demo 1: Complete Inventory-Procurement Flow
**Goal:** Create part, receive goods via PO, track stock moves

1. **Login** → Save auth token (automatic)
2. **Create Part** (e.g., "Brake Pad - Standard")
3. **Create Stock Location** (e.g., "Munich Workshop")
4. **Create Supplier** (e.g., "Knorr-Bremse")
5. **Create Purchase Order** (Status: DRAFT)
6. **Approve PO** → Status: APPROVED
7. **Order PO** → Status: ORDERED
8. **Receive Goods** → Automatically generates Stock Moves ✨
9. **Verify Stock Moves** → Check inventory updated

**Expected Result:**
- Part stock increased by received quantity
- Stock moves created automatically
- Purchase order completed

#### Demo 2: Finance & Budget Management Flow
**Goal:** Create invoice, match to PO, update budget

1. **Create Budget** for period (e.g., 2025-11)
2. **Create Invoice** (Status: DRAFT)
3. **Match Invoice vs PO** → Status: REVIEWED
4. **Approve Invoice** → Automatically updates Budget ✨
5. **Verify Budget Updated** → Check actual_amount increased

**Expected Result:**
- Invoice approved and posted
- Budget actual_amount updated
- Variance calculation complete

#### Demo 3: Reporting & Analytics
**Goal:** Generate KPI reports and dashboard

1. **Availability Report** → Overall fleet availability %
2. **On-Time Ratio** → Workshop delivery performance
3. **Parts Usage Report** → Consumption by part
4. **Cost Report** → Budget vs actual by cost center
5. **Dashboard Summary** → All KPIs in one view

**Expected Result:**
- Comprehensive metrics and KPIs
- Data aggregated from all modules
- Ready for management reporting

### Phase 1 Scenarios

#### Scenario 1: HU Planning
1. List vehicles with upcoming HU
2. Create maintenance task
3. Create work order
4. Run solver to schedule
5. Update vehicle status

#### Scenario 2: Offline Sync
1. Workshop updates work order (offline)
2. Push events to server
3. Check for conflicts
4. Resolve conflicts (if any)

#### Scenario 3: Inventory Management
1. Create parts
2. Stock moves (Wareneingang)
3. Create purchase order
4. Receive goods → Stock update
5. Create invoice → Match to PO

## Troubleshooting

**401 Unauthorized:**
- Check if ACCESS_TOKEN is set
- Try refreshing token
- Re-login if needed

**404 Not Found:**
- Verify BASE_URL is correct
- Check if service is running (`make up`)

**500 Internal Server Error:**
- Check backend logs (`make logs-backend`)
- Verify database is initialized (`make migrate`)

## Notes

- All timestamps in examples use UTC (Zulu time)
- Backend converts to Europe/Berlin for display
- Device-ID header required for sync endpoints
- Idempotency-Key recommended for duplicate prevention

## Collection Structure

### Phase 2 Collection Structure ⭐

```
RailFleet Manager - Phase 2 MVP
├── 📁 Authentication
│   └── Login (with automatic token management)
│
├── 📁 Demo 1: Inventory Flow
│   ├── 1. Create Part
│   ├── 2. Create Stock Location
│   ├── 3. Create Supplier
│   ├── 4. Create Purchase Order
│   ├── 5. Approve PO
│   ├── 6. Order PO
│   ├── 7. Receive Goods (Creates Stock Moves)
│   └── 8. Verify Stock Moves
│
├── 📁 Demo 2: Finance Flow
│   ├── 1. Create Budget
│   ├── 2. Create Invoice
│   ├── 3. Match Invoice vs PO
│   ├── 4. Approve Invoice (Updates Budget)
│   └── 5. Verify Budget Updated
│
└── 📁 Demo 3: Reports
    ├── Availability Report
    ├── On-Time Ratio
    ├── Parts Usage
    ├── Cost Report
    └── Dashboard Summary
```

### Phase 1 Collection Structure

```
RailFleet Manager MVP
├── 📁 Authentication
│   ├── Register User
│   ├── Login
│   ├── Refresh Token
│   └── Get Current User
├── 📁 Vehicles
│   ├── Create Vehicle
│   ├── List Vehicles
│   ├── Get Vehicle
│   ├── Update Vehicle
│   └── Delete Vehicle
├── 📁 Maintenance
│   ├── Create Task
│   ├── List Tasks
│   ├── Create Work Order
│   ├── List Work Orders
│   └── Update Work Order
├── 📁 Workshops
│   ├── Create Workshop
│   ├── List Workshops
│   ├── Get Workshop
│   └── Update Workshop
├── 📁 Sync
│   ├── Push Events
│   ├── Pull Events
│   ├── List Conflicts
│   └── Resolve Conflict
└── 📁 Scheduler
    ├── Solve (Direct)
    ├── Solve via Backend (Proxy)
    ├── Get Solution
    └── List Solutions
```

---

**Version:** 2.1.0 (Phase 2)
**Last Updated:** 2025-11-23
**Status:** ✅ Complete (WP14)
