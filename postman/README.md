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

### `phase2_scheduler.json` (Planned)
Dedicated scheduler & sync collection:
- Solver endpoints
- What-If scenarios
- Event log queries
- Conflict resolution flows

## Usage

### Import Collection

1. Open Postman
2. Click "Import"
3. Select `railfleet_manager_mvp.json`
4. Collection will be imported with pre-configured requests

### Environment Variables

Create a Postman environment with:

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

### Scenario 1: HU Planning
1. List vehicles with upcoming HU
2. Create maintenance task
3. Create work order
4. Run solver to schedule
5. Update vehicle status

### Scenario 2: Offline Sync
1. Workshop updates work order (offline)
2. Push events to server
3. Check for conflicts
4. Resolve conflicts (if any)

### Scenario 3: Inventory Management
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

**Version:** 2.0.0
**Last Updated:** 2025-11-23
**Status:** In Progress (WP1)
