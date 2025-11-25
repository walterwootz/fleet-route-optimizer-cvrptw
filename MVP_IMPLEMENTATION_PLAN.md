# 🚂 RailFleet Manager × DeepALL Hybrid – MVP Implementierungsplan

**Version:** 1.0
**Datum:** 2025-11-23
**Status:** Planning Phase

---

## 📊 Baseline Assessment

### ✅ Bereits vorhanden (Phase 1 & 2)
- FastAPI Backend (modulare Struktur)
- PostgreSQL + SQLAlchemy 2.0 + Alembic
- Docker-Compose (PostgreSQL, pgAdmin, Backend, Frontend)
- Authentication & Authorization (JWT, RBAC, 5 Rollen)
- Vehicle Management (CRUD, 7 Status-Typen)
- Maintenance Management (Tasks, Work Orders)
- Workshop Management (CRUD, Kapazität)
- Offline-First Sync (Basis: push/pull/conflicts)
- Policy Engine (SHA-256, Konfliktregeln)
- CVRPTW Route Optimizer (OR-Tools, Gurobi)
- 26 API Endpoints + 3 Solver

### 🔨 Zu implementieren (MVP-Erweiterung)
1. **CP-SAT Scheduler** - Werkstatt-/Ressourcenplanung
2. **Rail-Bimetrics** - Inventory, Procurement, Finance
3. **Enhanced Sync** - Eventlog, erweiterte Konflikte
4. **Reporting & KPIs** - Dashboard-APIs
5. **ECM-Compliance** - Audit Trail, signierte Policies

---

## 🎯 Work Packages Overview

| WP | Name | Priorität | Aufwand | Abhängigkeiten |
|----|------|-----------|---------|----------------|
| **WP1** | Datenmodell-Erweiterung | HOCH | 8h | - |
| **WP2** | CP-SAT Scheduler Core | HOCH | 16h | WP1 |
| **WP3** | Rail-Bimetrics: Inventory | HOCH | 12h | WP1 |
| **WP4** | Rail-Bimetrics: Procurement | MITTEL | 12h | WP1, WP3 |
| **WP5** | Rail-Bimetrics: Finance Light | MITTEL | 10h | WP1, WP4 |
| **WP6** | Enhanced Sync & Eventlog | HOCH | 8h | WP1 |
| **WP7** | Reporting & KPIs | NIEDRIG | 8h | WP2, WP3 |
| **WP8** | ECM-Compliance Layer | NIEDRIG | 6h | - |
| **WP9** | Integration & Testing | HOCH | 12h | WP2-WP6 |
| **WP10** | Postman Collection & Docs | MITTEL | 4h | WP9 |

**Gesamt:** ~96h (~12 Arbeitstage)

---

## 📋 Work Package Details

### WP1: Datenmodell-Erweiterung
**Priorität:** HOCH | **Aufwand:** 8h | **Abhängigkeiten:** -

#### Ziele
- Erweitere bestehende SQLAlchemy-Modelle
- Neue Tabellen für Scheduler-Ressourcen
- Neue Tabellen für Rail-Bimetrics

#### Tasks
- [ ] **Scheduler-Modelle** (3h)
  - `tracks` - Werkstattgleise (id, name, type, station_id, capabilities_json)
  - `teams` - Werkstattteams (id, name, skills_json, shift_pattern)
  - `shifts` - Schichten (id, team_id, track_id, start_ts, end_ts, capacity)
  - `schedule_slots` - Solver-Ergebnisse (id, work_order_id, track_id, team_id, start_ts, end_ts, status)

- [ ] **Inventory-Modelle** (2h)
  - `parts` - Teile (id, sku, name, railway_class, unit, min_stock, supplier_id)
  - `stock_locations` - Lagerorte (id, name, type, workshop_id)
  - `stock_moves` - Bewegungen (id, part_id, from_location, to_location, quantity, move_type, work_order_id, ts)

- [ ] **Procurement-Modelle** (2h)
  - `suppliers` - Lieferanten (id, name, iban, payment_terms, vat_id)
  - `purchase_orders` - Bestellungen (id, supplier_id, status, order_date, expected_delivery)
  - `purchase_order_lines` - Bestellpositionen (id, po_id, part_id, quantity, unit_price)

- [ ] **Finance-Modelle** (1h)
  - `invoices` - Rechnungen (id, supplier_id, invoice_number, invoice_date, total_net, total_vat, status)
  - `invoice_lines` - Rechnungspositionen (id, invoice_id, po_line_id, cost_center, cost_object)
  - `budgets` - Budgets (id, year, period, cost_center, amount_planned, amount_forecast, amount_actual)

#### Deliverables
- SQLAlchemy-Modelle in `src/models/railfleet/`
- Pydantic-Schemas in `src/api/schemas/`
- Alembic-Migration für alle neuen Tabellen

---

### WP2: CP-SAT Scheduler Core
**Priorität:** HOCH | **Aufwand:** 16h | **Abhängigkeiten:** WP1

#### Ziele
- Implementiere CP-SAT-basierten Werkstatt-Scheduler
- Berücksichtige Constraints (No-Overlap, Skills, Teile, Deadlines)
- Gewichtete Zielgrößen (minimize unscheduled, lateness, overtime)

#### Tasks
- [ ] **CP-SAT Modell** (8h)
  - `src/services/scheduler/cp_sat_model.py`
  - Variablen: Start-Zeit, Track-Zuweisung, Team-Zuweisung
  - Constraints:
    - No-Overlap (ein WO pro Track/Zeit)
    - Team-Skills matching WO-Requirements
    - Teileverfügbarkeit vor WO-Start
    - Deadline-Constraints (soft/hard)
  - Objective: `w1*unscheduled + w2*lateness + w3*overtime`

- [ ] **Solver Service** (4h)
  - `src/services/scheduler/solver_service.py`
  - Input: Work Orders, Tracks, Teams, Shifts, Parts-Availability
  - Output: `schedule_slots[]` + `explanations[]` + `metrics`
  - Explanations: Regel-Tags pro WO (why scheduled/unscheduled)

- [ ] **API Endpoints** (3h)
  - `POST /api/v1/scheduler/solve`
  - `GET /api/v1/scheduler/solutions/{id}`
  - `GET /api/v1/scheduler/metrics/{id}`

- [ ] **Tests** (1h)
  - Unit-Tests für Constraints
  - Integrationstests für Solve-Flow

#### Deliverables
- CP-SAT Scheduler Service
- 3 neue API Endpoints
- Test Coverage >80%

---

### WP3: Rail-Bimetrics - Inventory Management
**Priorität:** HOCH | **Aufwand:** 12h | **Abhängigkeiten:** WP1

#### Ziele
- Teile-Verwaltung (Parts)
- Lager-Management (Stock Locations)
- Bestandsbewegungen (Stock Moves)

#### Tasks
- [ ] **Parts Management** (4h)
  - CRUD für Teile
  - Min-Stock-Tracking
  - Railway-Class (kritisch/standard/verschleißteil)
  - Endpoints:
    - `POST /api/v1/parts`
    - `GET /api/v1/parts`
    - `GET /api/v1/parts/{id}`
    - `PATCH /api/v1/parts/{id}`

- [ ] **Stock Locations** (2h)
  - CRUD für Lagerorte (Werkstattlager, Zentrallager, Zuglager, Konsi)
  - Verknüpfung zu Workshops
  - Endpoints:
    - `POST /api/v1/stock/locations`
    - `GET /api/v1/stock/locations`

- [ ] **Stock Moves** (4h)
  - Bewegungen erfassen (WAR_EIN, VERBAUUNG, UMBUCHUNG, ABSCHR)
  - Verknüpfung zu Work Orders (Verbauung)
  - Bestandsaggregation
  - Endpoints:
    - `POST /api/v1/stock/moves`
    - `GET /api/v1/stock/moves`
    - `GET /api/v1/stock/overview` (aggregiert)

- [ ] **Tests** (2h)
  - Unit-Tests für Bestandslogik
  - Test: Verbauung reduziert Stock

#### Deliverables
- Inventory Service mit 3 Modulen
- 8 neue API Endpoints
- Stock-Aggregation funktioniert

---

### WP4: Rail-Bimetrics - Procurement
**Priorität:** MITTEL | **Aufwand:** 12h | **Abhängigkeiten:** WP1, WP3

#### Ziele
- Lieferanten-Management
- Bestellprozess (DRAFT → APPROVED → ORDERED → RECEIVED → CLOSED)
- Wareneingang → Stock Moves

#### Tasks
- [ ] **Supplier Management** (2h)
  - CRUD für Lieferanten
  - Zahlungskonditionen, VAT-ID
  - Endpoints:
    - `POST /api/v1/suppliers`
    - `GET /api/v1/suppliers`

- [ ] **Purchase Orders** (6h)
  - CRUD für Bestellungen
  - Status-Workflow (DRAFT → APPROVED → ORDERED → RECEIVED → CLOSED)
  - Bestellpositionen (lines)
  - Verknüpfung zu Teilen & Work Orders
  - Endpoints:
    - `POST /api/v1/purchase_orders`
    - `GET /api/v1/purchase_orders`
    - `POST /api/v1/purchase_orders/{id}/approve`
    - `POST /api/v1/purchase_orders/{id}/order`
    - `POST /api/v1/purchase_orders/{id}/receive` (→ stock_moves generieren)

- [ ] **Receiving Logic** (2h)
  - Wareneingang generiert Stock Moves
  - PO-Line → Part → Location
  - Status-Update auf RECEIVED

- [ ] **Tests** (2h)
  - Test: PO-Workflow DRAFT → CLOSED
  - Test: Wareneingang erhöht Stock

#### Deliverables
- Procurement Service
- 7 neue API Endpoints
- PO-Workflow funktioniert
- Wareneingang → Stock Move Integration

---

### WP5: Rail-Bimetrics - Finance Light
**Priorität:** MITTEL | **Aufwand:** 10h | **Abhängigkeiten:** WP1, WP4

#### Ziele
- Eingangsrechnungen erfassen
- Matching gegen POs/WOs
- Kontierung (Kostenstelle, Kostenträger)
- Budget-Tracking

#### Tasks
- [ ] **Invoice Management** (4h)
  - CRUD für Rechnungen
  - Status-Workflow (DRAFT → REVIEWED → APPROVED → EXPORTED)
  - Rechnungspositionen mit Kontierung
  - Endpoints:
    - `POST /api/v1/invoices/inbox` (neue Rechnung)
    - `GET /api/v1/invoices`
    - `POST /api/v1/invoices/{id}/match` (gegen POs/WOs)
    - `POST /api/v1/invoices/{id}/approve`

- [ ] **Matching Logic** (3h)
  - Automatisches Matching: Invoice Line → PO Line
  - Kontierungsvorschlag basierend auf:
    - PO → Work Order → Cost Center
    - Teil-Kategorie → Standard-Kostenstelle
  - Abweichungsprüfung (Preis, Menge)

- [ ] **Budget Tracking** (2h)
  - Budget-Perioden (Jahr, Monat, Kostenstelle)
  - Aggregation: Planned, Forecast, Actual
  - Warnung bei Budget-Überschreitung
  - Endpoints:
    - `GET /api/v1/budget/overview?period=YYYY-MM&cost_center=X`
    - `POST /api/v1/budget`

- [ ] **Tests** (1h)
  - Test: Invoice Matching
  - Test: Budget-Warnung

#### Deliverables
- Finance Service
- 5 neue API Endpoints
- Automatisches Matching & Kontierung
- Budget-Warnsystem

---

### WP6: Enhanced Sync & Eventlog
**Priorität:** HOCH | **Aufwand:** 8h | **Abhängigkeiten:** WP1

#### Ziele
- Erweitere Eventlog für alle Entity-Typen
- Verbessere Cursor-basierte Pull-Mechanik
- Erweiterte Konfliktauflösung

#### Tasks
- [ ] **Eventlog-Erweiterung** (3h)
  - Append-only Tabelle: `event_log`
    - id, entity_type, entity_id, event_type, payload_json, actor_id, device_id, ts
  - Support für: work_orders, stock_moves, invoices, schedule_slots

- [ ] **Enhanced Pull** (2h)
  - Cursor-basierte Abfrage (since timestamp oder log-id)
  - Filterung nach entity_type
  - `GET /api/v1/sync/pull?cursor=log-123&entity_types=work_order,stock_move`

- [ ] **Konflikt-Matrix** (2h)
  - Erweitere Policy-Regeln:
    - Dispatcher: scheduled_*, priority
    - Workshop: actual_*, status, findings
    - Finance: invoice_*, budget_*
  - Neue Konflikt-Typen: STOCK_CONFLICT, BUDGET_CONFLICT

- [ ] **Tests** (1h)
  - Test: Eventlog Append
  - Test: Pull mit Cursor
  - Test: Erweiterte Konflikte

#### Deliverables
- Universelles Eventlog
- Verbesserte Pull-API
- Erweiterte Konfliktmatrix

---

### WP7: Reporting & KPIs
**Priorität:** NIEDRIG | **Aufwand:** 8h | **Abhängigkeiten:** WP2, WP3

#### Ziele
- Dashboard-APIs für KPIs
- Verfügbarkeits-Metriken
- Kosten-Tracking

#### Tasks
- [ ] **Availability Report** (2h)
  - KPI: Fahrzeugverfügbarkeit (%)
  - Gruppierung: Fahrzeugtyp, Zeitraum
  - `GET /api/v1/reports/availability?period=2025-11&type=electric`

- [ ] **On-Time-Ratio** (2h)
  - KPI: Pünktlichkeit von Work Orders (%)
  - Actual_End vs. Scheduled_End
  - `GET /api/v1/reports/on_time_ratio?period=2025-11`

- [ ] **Parts Usage** (2h)
  - KPI: Teileverbrauch pro 1.000 km / WO-Typ
  - Aggregation: Stock Moves (VERBAUUNG) + Vehicle Mileage
  - `GET /api/v1/reports/parts_usage?part_id=X&period=2025-11`

- [ ] **Cost Report** (2h)
  - KPI: Kosten vs. Budget
  - Gruppierung: Kostenstelle, Periode
  - `GET /api/v1/reports/costs?cost_center=X&period=2025-11`

#### Deliverables
- 4 Report-Endpoints
- Aggregierte KPIs
- Dashboard-ready JSON-Format

---

### WP8: ECM-Compliance Layer
**Priorität:** NIEDRIG | **Aufwand:** 6h | **Abhängigkeiten:** -

#### Ziele
- Audit Trail für kritische Änderungen
- Signierte Policies (Ed25519)
- Compliance-Hooks

#### Tasks
- [ ] **Audit Trail** (3h)
  - Tabelle: `audit_log`
    - id, entity_type, entity_id, action, old_value_json, new_value_json, actor_id, ts
  - Auto-Logging für:
    - Work Order Status-Änderungen
    - Budget-Approvals
    - Invoice-Approvals

- [ ] **Signierte Policies** (2h)
  - Erweitere Policy-Loader um Ed25519-Signatur-Verifikation
  - `policy/scheduler_conflict_policy.json` + `.sig`
  - Admin-Endpoint: `POST /api/v1/policy` (nur SUPER_ADMIN)

- [ ] **Compliance Hooks** (1h)
  - Hooks für externe ECM-Systeme (z.B. DATEV-Export)
  - `GET /api/v1/compliance/export?period=2025-11&format=datev`

#### Deliverables
- Audit Trail funktioniert
- Ed25519-Signatur-Verifikation
- Export-Endpoints

---

### WP9: Integration & Testing
**Priorität:** HOCH | **Aufwand:** 12h | **Abhängigkeiten:** WP2-WP6

#### Ziele
- End-to-End Integration Tests
- Performance-Tests
- Bug-Fixes

#### Tasks
- [ ] **E2E-Tests** (6h)
  - Szenario 1: WO → Scheduler → Slot → Sync
  - Szenario 2: Teil-Bestellung → Wareneingang → Verbauung → Stock
  - Szenario 3: Rechnung → Matching → Kontierung → Budget-Check

- [ ] **Performance-Tests** (3h)
  - Scheduler mit 100+ WOs
  - Sync mit 1000+ Events
  - Stock-Aggregation mit 10.000+ Moves

- [ ] **Bug-Fixes & Refactoring** (3h)
  - Code-Review aller WPs
  - Refactoring für bessere Testbarkeit
  - Error-Handling verbessern

#### Deliverables
- 3 E2E-Szenarien laufen
- Performance-Benchmarks dokumentiert
- Code-Quality verbessert

---

### WP10: Postman Collection & Dokumentation
**Priorität:** MITTEL | **Aufwand:** 4h | **Abhängigkeiten:** WP9

#### Ziele
- Postman-Collection mit Demo-Flows
- README aktualisieren
- API-Dokumentation

#### Tasks
- [ ] **Postman Collection** (2h)
  - Collection mit 3 Demo-Szenarien:
    1. Scheduler-Flow: WO anlegen → Solve → Slots abrufen
    2. Inventory-Flow: Teil anlegen → Bestellung → Wareneingang → Verbauung
    3. Finance-Flow: Rechnung erfassen → Matching → Kontierung → Budget-Check
  - Environment-Variablen (Token, URLs)
  - Pre-Request-Scripts für Auth

- [ ] **README Update** (1h)
  - Aktualisiere RAILFLEET_README.md:
    - Neue Features (Scheduler, Rail-Bimetrics)
    - Setup-Anleitung
    - Demo-Szenarien

- [ ] **API-Dokumentation** (1h)
  - OpenAPI/Swagger up-to-date
  - Beschreibungen für alle neuen Endpoints
  - Beispiel-Requests & Responses

#### Deliverables
- Postman Collection (.json)
- Aktualisiertes README
- Vollständige API-Docs

---

## 🎯 Definition of Done (MVP)

### Funktionale Anforderungen
- [ ] System startet mit `make up` ohne Fehler
- [ ] Alle 3 Demo-Szenarien laufen in Postman durch
- [ ] Scheduler löst 100+ WOs in <60s
- [ ] Sync verarbeitet 1000+ Events ohne Datenverlust
- [ ] Budget-Warnung bei Überschreitung funktioniert

### Technische Anforderungen
- [ ] Test Coverage >80% für Kernlogik
- [ ] Alle API-Endpoints haben OpenAPI-Dokumentation
- [ ] Alembic-Migrationen laufen fehlerfrei
- [ ] Docker-Images bauen erfolgreich
- [ ] Keine kritischen Security-Issues (SQL-Injection, etc.)

### Dokumentation
- [ ] README erklärt Setup, Architektur, Demo-Szenarien
- [ ] Postman Collection ist lauffähig
- [ ] Alle neuen Modelle haben Docstrings
- [ ] API-Dokumentation ist vollständig

---

## 📈 Implementierungs-Reihenfolge (Empfohlen)

### Sprint 1: Foundation (24h / 3 Tage)
1. **WP1** - Datenmodell-Erweiterung (8h)
2. **WP6** - Enhanced Sync & Eventlog (8h)
3. **WP2** - CP-SAT Scheduler Core (8h Start)

### Sprint 2: Core Features (32h / 4 Tage)
4. **WP2** - CP-SAT Scheduler Core (8h Fertigstellung)
5. **WP3** - Rail-Bimetrics: Inventory (12h)
6. **WP4** - Rail-Bimetrics: Procurement (12h)

### Sprint 3: Finance & Reporting (18h / 2-3 Tage)
7. **WP5** - Rail-Bimetrics: Finance Light (10h)
8. **WP7** - Reporting & KPIs (8h)

### Sprint 4: Compliance & Testing (22h / 3 Tage)
9. **WP8** - ECM-Compliance Layer (6h)
10. **WP9** - Integration & Testing (12h)
11. **WP10** - Postman Collection & Docs (4h)

**Total: 96h (~12 Arbeitstage / 2-3 Wochen)**

---

## 🚨 Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| CP-SAT Solver zu langsam für Praxis | MITTEL | HOCH | Benchmarks früh, ggf. Heuristiken, Timeout-Limits |
| Konfliktlogik zu komplex | NIEDRIG | MITTEL | Schrittweise erweitern, klare Regeln dokumentieren |
| Performance-Probleme bei Stock-Aggregation | MITTEL | MITTEL | Materialized Views, Caching, Indizes |
| Scope Creep (zu viele Features) | HOCH | HOCH | Strikte MVP-Definition, "Nice-to-Have" in Backlog |

---

## 📞 Nächste Schritte

1. **Review & Approval** - Plan mit Team/Stakeholdern reviewen
2. **Sprint Planning** - Sprint 1 detailliert planen
3. **Setup Environment** - Entwicklungsumgebung vorbereiten
4. **Kick-off WP1** - Datenmodell-Erweiterung starten

---

**Erstellt:** 2025-11-23
**Version:** 1.0
**Status:** Ready for Implementation 🚀
