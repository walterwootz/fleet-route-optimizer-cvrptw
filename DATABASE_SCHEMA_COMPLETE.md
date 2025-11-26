# 🗄️ RailFleet Manager - Vollständiges Datenbank-Schema

**Datum:** 2025-11-25  
**Quelle:** RailFleet Manager chat summary claude code.md  
**Status:** Dokumentiert aus Projekt-Historie

---

## 📊 Übersicht

**Gesamt:** ~30+ Tabellen  
**Kategorien:** 10 Bereiche  
**Datenbank:** PostgreSQL (Production) / SQLite (Development)

---

## 1️⃣ **Core Models** (Basis-Tabellen)

### `users`
- **Zweck:** Benutzer mit RBAC (Role-Based Access Control)
- **Felder:** id (UUID), email, hashed_password, full_name, role, is_active, created_at, updated_at
- **Rollen:** dispatcher, workshop, procurement, finance, ecm, viewer
- **Model:** `src/models/railfleet/user.py` → `class User(Base)`

### `vehicles` (Locomotives)
- **Zweck:** Flotten-Management (Streckenlokomotiven)
- **Felder:** id, asset_id, model, type, status, current_location, last_maintenance, next_maintenance_due, metadata
- **Status:** operational, maintenance_due, in_maintenance, out_of_service, decommissioned
- **Types:** electric, diesel, hybrid
- **Model:** `src/models/railfleet/vehicle.py` → `class Vehicle(Base)`

### `workshops`
- **Zweck:** Werkstätten/Wartungseinrichtungen
- **Felder:** id, name, location, capacity, certifications, contact_email, contact_phone, is_active
- **Model:** `src/models/railfleet/workshop.py` → `class Workshop(Base)`

---

## 2️⃣ **Maintenance Management** (Wartung)

### `maintenance_tasks`
- **Zweck:** Wartungsaufgaben (HU, Bremsprüfung, etc.)
- **Felder:** id, vehicle_id, type, description, due_date, completed_date, priority, status, assigned_to
- **Types:** inspection, repair, preventive, corrective
- **Priorities:** low, medium, high, critical
- **Model:** `src/models/railfleet/maintenance.py` → `class MaintenanceTask(Base)`

### `work_orders`
- **Zweck:** Werkstattaufträge
- **Felder:** id, vehicle_id, workshop_id, scheduled_start, scheduled_end, actual_start, actual_end, status, priority, tasks[], assigned_team, used_parts[], findings[], media[]
- **Status:** draft, planned, in_progress, completed, cancelled, delayed
- **Model:** `src/models/railfleet/maintenance.py` → `class WorkOrder(Base)`

### `tracks`
- **Zweck:** Werkstatt-Gleise/Pits
- **Felder:** id, track_id, workshop_id, capacity, is_active, certifications
- **SQL:** `003_maintenance_tables.sql`

### `wo_assignment`
- **Zweck:** Zuordnung Work Order → Track + Team
- **Felder:** id, work_order_id, track_id, team_id, assigned_from, assigned_to
- **SQL:** `003_maintenance_tables.sql`

---

## 3️⃣ **Transfer Service** (Überführungen)

### `transfer_plans`
- **Zweck:** Lokomotiv-Überführungen zwischen Standorten
- **Felder:** id, plan_id, vehicle_id, from_location, to_location, window_start, window_end, team_skill, status, assigned_staff_id
- **Status:** planned, in_progress, completed, cancelled
- **SQL:** `004_transfer_service.sql`

---

## 4️⃣ **Inventory Management** (Lager)

### `part_inventory`
- **Zweck:** Ersatzteile-Lager
- **Felder:** id, part_no, description, quantity_available, quantity_reserved, min_stock, unit_price, supplier_id, location_id
- **SQL:** `003_maintenance_tables.sql`

### `stock_locations`
- **Zweck:** Lagerorte
- **Felder:** id, location_code, name, type, capacity, is_active
- **Types:** warehouse, workshop, mobile
- **SQL:** `WP9 - Inventory Management`

### `stock_moves`
- **Zweck:** Lagerbewegungen (Ein-/Ausgang)
- **Felder:** id, part_no, from_location, to_location, quantity, move_type, reference_id, timestamp
- **Types:** receipt, issue, transfer, adjustment
- **SQL:** `WP9`

---

## 5️⃣ **Procurement** (Beschaffung)

### `suppliers`
- **Zweck:** Lieferanten
- **Felder:** id, supplier_code, name, contact_email, contact_phone, payment_terms, is_active
- **SQL:** `WP10 - Procurement`

### `purchase_orders`
- **Zweck:** Bestellungen
- **Felder:** id, po_number, supplier_id, order_date, delivery_date, status, total_amount, currency, related_wo_id
- **Status:** draft, sent, confirmed, delivered, closed
- **SQL:** `WP10`

### `purchase_order_lines`
- **Zweck:** Bestellpositionen
- **Felder:** id, po_id, part_no, quantity, unit_price, total_price
- **SQL:** `WP10`

---

## 6️⃣ **Finance** (Finanzen)

### `invoices`
- **Zweck:** Rechnungen
- **Felder:** id, invoice_number, supplier_id, invoice_date, due_date, amount, currency, status, related_po_id, related_wo_id
- **Status:** pending, approved, paid, overdue, rejected
- **SQL:** `WP11 - Finance`

### `cost_centers`
- **Zweck:** Kostenstellen
- **Felder:** id, code, name, budget, spent, is_active
- **SQL:** `WP11`

### `budget_allocations`
- **Zweck:** Budget-Zuordnungen
- **Felder:** id, cost_center_id, fiscal_year, allocated_amount, spent_amount
- **SQL:** `WP11`

---

## 7️⃣ **HR Service** (Personal)

### `staff`
- **Zweck:** Mitarbeiter
- **Felder:** id, employee_id, name, qualifications[], availability, shift_start, shift_end, is_active
- **Qualifications:** driver, mechanic, electrician, inspector
- **SQL:** `WP12 - HR Service`

### `staff_assignments`
- **Zweck:** Personaleinsätze
- **Felder:** id, staff_id, assignment_type, reference_id, from_datetime, to_datetime
- **Types:** transfer, workshop, inspection
- **SQL:** `WP12`

---

## 8️⃣ **Document Management** (ECM-Light)

### `document_links`
- **Zweck:** Dokumente (Zulassungen, Berichte, etc.)
- **Felder:** id, document_id, asset_id, doc_type, doc_url, valid_from, valid_until, is_expired, audit_trail[]
- **Types:** certificate, report, permit, inspection_report
- **SQL:** `WP13 - Document Management`

---

## 9️⃣ **Event Sourcing & CRDT** (Sync)

### `event_log` (WORM - Write-Once-Read-Many)
- **Zweck:** Append-Only Event Store für Audit Trail
- **Felder:** id (BIGSERIAL), event_id, entity_type, entity_id, event_type, payload (JSONB), user_id, device_id, timestamp, hash
- **Model:** `src/models/railfleet/event_log.py` → `class EventLog(Base)`
- **SQL:** `003_maintenance_tables.sql`

### `events`
- **Zweck:** Event Store (Event Sourcing Pattern)
- **Felder:** id, aggregate_id, aggregate_type, event_type, event_data (JSONB), metadata (JSONB), version, timestamp, user_id
- **Model:** `src/models/event_sourcing/event.py` → `class Event(Base)`
- **SQL:** `WP15-16 - Event Sourcing`

### `crdt_metadata`
- **Zweck:** CRDT State für Offline-First Sync
- **Felder:** entity_type, entity_id, device_id, vector_clock (JSONB), crdt_data (JSONB), last_updated
- **Model:** `src/models/railfleet/crdt_metadata.py` → `class CRDTMetadataModel(Base)`
- **SQL:** `005_crdt_tables.py` (Alembic Migration)

### `crdt_operations`
- **Zweck:** CRDT Operations Audit Log
- **Felder:** id, entity_type, entity_id, operation_type, operation_data (JSONB), device_id, timestamp
- **SQL:** `005_crdt_tables.py`

### `sync_devices`
- **Zweck:** Device Registration für Local-First Sync
- **Felder:** id, device_id, device_name, device_type, user_id, last_sync, is_active
- **Model:** `src/models/sync/device.py` → `class SyncDevice(Base)`
- **SQL:** `WP18 - Local-First Sync`

---

## 🔟 **ML & Analytics** (Machine Learning)

### `ml_models`
- **Zweck:** ML Model Metadata
- **Felder:** id, model_name, model_type, version, file_path, metrics (JSONB), is_active, trained_at
- **Types:** maintenance_predictor, completion_predictor, demand_forecaster
- **Model:** `src/models/ml/model.py` → `class MLModel(Base)`
- **SQL:** `WP20-21 - ML Pipeline`

### `predictions`
- **Zweck:** ML Predictions Log
- **Felder:** id, model_id, entity_type, entity_id, prediction_data (JSONB), confidence, created_at
- **SQL:** `WP20-21`

---

## 📊 **Zusammenfassung**

| Kategorie | Tabellen | Status |
|-----------|----------|--------|
| **Core Models** | 3 | ✅ Implementiert |
| **Maintenance** | 4 | ✅ Implementiert |
| **Transfer** | 1 | ✅ Implementiert |
| **Inventory** | 3 | ✅ Implementiert |
| **Procurement** | 3 | ✅ Implementiert |
| **Finance** | 3 | ✅ Implementiert |
| **HR** | 2 | ✅ Implementiert |
| **Documents** | 1 | ✅ Implementiert |
| **Event Sourcing/CRDT** | 5 | ✅ Implementiert |
| **ML & Analytics** | 2 | ✅ Implementiert |
| **GESAMT** | **27 Tabellen** | ✅ Vollständig |

---

**Erstellt:** 2025-11-25  
**Quelle:** RailFleet Manager Projekt-Historie  
**Agent:** DeepALL Orchestrator

