# 🔍 Gap-Analyse: MVP Plan vs. Phase 2 Auftrag & FLEET-ONE

**Datum:** 2025-11-23
**Status:** Analysis

---

## 📊 Vergleich der Anforderungen

### ✅ Was bereits im MVP Plan ist

1. **Datenmodell-Erweiterung** (WP1)
   - ✅ Scheduler-Modelle (tracks, teams, shifts, schedule_slots)
   - ✅ Inventory-Modelle (parts, stock_locations, stock_moves)
   - ✅ Procurement-Modelle (suppliers, purchase_orders)
   - ✅ Finance-Modelle (invoices, budgets)

2. **CP-SAT Scheduler** (WP2)
   - ✅ OR-Tools Integration geplant
   - ✅ Constraints (No-Overlap, Skills, Teile, Deadlines)

3. **Enhanced Sync** (WP6)
   - ✅ Eventlog-Erweiterung
   - ✅ Konflikt-Matrix

4. **Reporting & KPIs** (WP7)
   - ✅ Availability, On-Time-Ratio, Costs

---

## ⚠️ Was FEHLT im aktuellen Plan

### 1. **T0 - Open-Source-Reuse (KRITISCH!)**

Der Phase 2 Auftrag verlangt **obligatorisch zuerst**:
- GitHub-Reuse-Scan vor jedem Neuaufbau
- Dokumentation in `docs/REUSE_DECISION.md`
- Kuratierte Kandidaten prüfen:
  - **PyJobShop** (https://github.com/PyJobShop/PyJobShop) - MIT
  - **JobShopLib** (https://github.com/Pabloo22/job_shop_lib) - MIT
  - **fastapi-celery** Templates
  - **pyeventsourcing** für Event Log
  - **PyNaCl** für Ed25519-Signaturen

**→ Dies fehlt komplett in WP2!**

### 2. **Microservice-Architektur vs. Monolith**

**Phase 2 Auftrag:**
- Solver als **eigener Microservice** (`solver_service/`) auf Port 7070
- Backend als **Proxy** zu Solver-Service
- ODER: Bibliotheks-Adapter (PyJobShop/JobShopLib)

**Aktueller Plan (WP2):**
- Scheduler als Teil des Backend-Service
- Keine Microservice-Struktur

**→ Architektur-Entscheidung fehlt!**

### 3. **FLEET-ONE Tool-Integration**

**FLEET-ONE.json definiert:**
- 9 verschiedene Services (fleet_db, maintenance_service, workshop_service, transfer_service, procurement_service, reporting_service, finance_service, hr_service, docs_service)
- Jeder Service hat eigene Base-URL und Auth-Token
- Agent-basierte Tool-Calls

**Aktueller Plan:**
- Monolithische API-Struktur
- Keine separaten Service-URLs
- Keine Transfer-Service, HR-Service, Docs-Service

**→ Service-Architektur nicht aligned!**

### 4. **Policy-Signing mit Ed25519**

**Phase 2 Auftrag:**
- SHA-256 Hash **verpflichtend**
- Ed25519-Signatur **optional**
- PyNaCl Integration

**Aktueller Plan (WP8):**
- Ed25519 nur als "optional" markiert

**→ Needs clarification: Pflicht oder optional?**

### 5. **Spezifische DB-Migrations-Dateien**

**Phase 2 Auftrag nennt spezifisch:**
```
01_work_orders.sql
02_resources.sql
03_parts.sql
04_assignments.sql
05_event_log_conflicts.sql
06_kpi_views.sql
```

**Aktueller Plan:**
- Generische Alembic-Migration ohne SQL-Dateien
- Keine KPI-Views

**→ SQL-basierte Migrationen fehlen!**

### 6. **UTC-Zeitkonvention & Timezone-Handling**

**Phase 2 Auftrag:**
- Backend führt **UTC** (Pflicht!)
- UI lokalisiert (Europe/Berlin)
- FLEET-ONE.json: timezone = "Europe/Berlin"

**Aktueller Plan:**
- Keine explizite UTC-Konvention

**→ Timezone-Strategie fehlt!**

### 7. **What-If-Szenarien mit Celery**

**Phase 2 Auftrag:**
- Redis/Celery für länger laufende Solver-Jobs
- What-If-Szenarien async

**Aktueller Plan:**
- Keine Celery-Integration
- Keine What-If-Endpoints

**→ Async-Job-System fehlt!**

### 8. **Transfer-Service & HR-Service**

**FLEET-ONE.json:**
- **transfer_service**: Lokzuführungen planen
- **hr_service**: Personaleinsatz-Planung

**Aktueller Plan:**
- Nur Vehicles, Maintenance, Workshops, Procurement, Finance
- **Kein Transfer/HR**

**→ 2 Services fehlen komplett!**

### 9. **Postman Collection & Examples**

**Phase 2 Auftrag:**
- Policy JSON: `policy/scheduler_conflict_policy.json` ✅ (bereits erstellt)
- Postman Collection: `postman/postman_collection_scheduler_mvp.json`
- Examples: `solve_request.json`, `push_request.json` ✅ (push_request.json bereits erstellt)

**Aktueller Plan:**
- Postman Collection in WP10
- Examples in WP10

**→ Artefakte müssen zuerst platziert werden (T1)!**

### 10. **Spezifische Solver-Constraints**

**Phase 2 Auftrag nennt explizit:**
- Optionale Basisintervalle (`sched_i` = Präsenz-Variable)
- Asset-Inkompatibilitäten **nur wenn beide geplant**
- Verfügbarkeiten per Implikation
- Teiledeckung global mit `start ≥ available_from(p)` **nur wenn geplant**
- Lateness/Overtime **nur wenn `sched_i=1`**

**Aktueller Plan (WP2):**
- Generische CP-SAT-Beschreibung ohne diese Details

**→ Spezifische Constraint-Logik fehlt!**

---

## 🎯 Kritische Lücken (High Priority)

### Prio 1 - MUST HAVE
1. ❌ **T0 - Reuse-Scan** (obligatorisch vor Coding!)
2. ❌ **Microservice vs. Monolith Entscheidung**
3. ❌ **UTC-Zeitkonvention** (Backend-weit)
4. ❌ **SQL-basierte Migrationen** (statt Alembic-only)
5. ❌ **Policy-Signing** (Ed25519 - Pflicht oder optional?)

### Prio 2 - SHOULD HAVE
6. ❌ **FLEET-ONE Service-Architektur** (9 Services mit eigenen URLs)
7. ❌ **Transfer-Service & HR-Service**
8. ❌ **Celery für What-If-Jobs**
9. ❌ **Spezifische CP-SAT Constraints** (optionale Intervalle)

### Prio 3 - NICE TO HAVE
10. ❌ **Postman Collection & Examples** (früher im Prozess)

---

## 🔄 Empfohlene Anpassungen

### Option A: Monolith mit Service-Separation (Pragmatisch)

**Struktur:**
```
backend/
├── app/
│   ├── services/
│   │   ├── fleet/          # → /api/v1/fleet/*
│   │   ├── maintenance/    # → /api/v1/maintenance/*
│   │   ├── workshop/       # → /api/v1/workshop/*
│   │   ├── transfer/       # → /api/v1/transfer/*      (NEU)
│   │   ├── procurement/    # → /api/v1/procurement/*
│   │   ├── finance/        # → /api/v1/finance/*
│   │   ├── hr/             # → /api/v1/hr/*            (NEU)
│   │   ├── docs/           # → /api/v1/docs/*          (NEU)
│   │   ├── reporting/      # → /api/v1/reports/*
│   │   └── scheduler/      # → /api/v1/scheduler/*
│   └── solver/
│       ├── adapter.py      # Adapter zu PyJobShop/JobShopLib
│       └── cp_sat_core.py  # Falls Eigenbau nötig

solver_service/              # Microservice (optional)
├── app.py
└── solver_core.py
```

**Pro:**
- Schnellere Entwicklung
- Einfacheres Deployment (ein Container)
- Alle Services in einem Repo

**Contra:**
- Weniger skalierbar
- Nicht FLEET-ONE-Tool-Architektur konform

### Option B: Microservices (FLEET-ONE-konform)

**Struktur:**
```
railfleet-manager/
├── services/
│   ├── fleet/              # Port 8001
│   ├── maintenance/        # Port 8002
│   ├── workshop/           # Port 8003
│   ├── transfer/           # Port 8004 (NEU)
│   ├── procurement/        # Port 8005
│   ├── finance/            # Port 8006
│   ├── hr/                 # Port 8007 (NEU)
│   ├── docs/               # Port 8008 (NEU)
│   ├── reporting/          # Port 8009
│   └── scheduler/          # Port 8010
├── solver_service/         # Port 7070
└── gateway/                # API Gateway (Port 8000)
```

**Pro:**
- FLEET-ONE Tool-Architektur konform
- Unabhängig skalierbar
- Klare Service-Grenzen

**Contra:**
- Hoher Setup-Aufwand
- Komplexes Deployment
- Service-Discovery nötig

### Option C: Hybrid (Empfohlen für MVP)

**Struktur:**
```
backend/                    # Monolith Port 8000
├── app/
│   └── api/v1/
│       ├── fleet/
│       ├── maintenance/
│       ├── workshop/
│       ├── transfer/       (NEU)
│       ├── procurement/
│       ├── finance/
│       ├── hr/             (NEU)
│       ├── docs/           (NEU)
│       ├── reports/
│       └── scheduler/

solver_service/             # Microservice Port 7070
└── (PyJobShop Adapter ODER Eigenbau)
```

**Pro:**
- Kompromiss: Solver isoliert, Rest monolithisch
- FLEET-ONE Tools können gegen Monolith-Endpoints zeigen
- Einfacher als Full-Microservices

---

## 📝 Aktualisierter Implementierungsplan

### Neue Work Package Struktur

**WP0 - Reuse-Scan & Architecture Decision** (8h) ⭐ NEU
- [ ] GitHub-Reuse-Scan durchführen
- [ ] `docs/REUSE_DECISION.md` erstellen
- [ ] Architektur-Entscheidung (Monolith/Microservices/Hybrid)
- [ ] Service-Map erstellen (welche URLs, Ports, Auth)

**WP1 - Artefakte & Foundation** (6h) - Angepasst
- [ ] Policy JSON platzieren ✅ (bereits da)
- [ ] Postman Collection platzieren (bereitgestellt)
- [ ] Solve/Push Request Examples erstellen
- [ ] `docs/REUSE_DECISION.md` Template

**WP2 - Solver-Service** (20h) - Erweitert
- [ ] **Variante A**: PyJobShop/JobShopLib Adapter (12h)
- [ ] **Variante B**: CP-SAT Eigenbau mit spezifischen Constraints (20h)
  - Optionale Intervalle (`sched_i`)
  - Asset-Inkompatibilitäten
  - Implikations-basierte Verfügbarkeiten
  - Globale Teiledeckung
- [ ] Solver als Microservice ODER Library-Modul
- [ ] Docker-Setup
- [ ] Celery-Integration für What-If (optional)

**WP3 - SQL-Migrationen** (8h) - Neu strukturiert
- [ ] `01_work_orders.sql`
- [ ] `02_resources.sql` (tracks, teams, shifts, availabilities)
- [ ] `03_parts.sql` (inventory, used_parts)
- [ ] `04_assignments.sql` (wo_assignment)
- [ ] `05_event_log_conflicts.sql` (append-only event_log, conflict)
- [ ] `06_kpi_views.sql` (v_track_utilization, etc.)

**WP4 - Transfer & HR Services** (12h) ⭐ NEU
- [ ] Transfer Service (Lokzuführungen)
  - Models: `transfer_plan`, `transfer_assignment`
  - Endpoints: `POST /transfer/plans`, `GET /transfer/plans`
- [ ] HR Service (Personaleinsatz)
  - Models: `staff`, `staff_assignment`
  - Endpoints: `GET /hr/staff`, `POST /hr/assignments`

**WP5 - Docs Service** (6h) ⭐ NEU
- [ ] Document Management (ECM-Light)
  - Models: `document_link`, `expiration_tracking`
  - Endpoints: `POST /docs/link`, `GET /docs/expiring`

**WP6 - UTC-Zeitkonvention** (4h) ⭐ NEU
- [ ] Backend: Alle Timestamps UTC
- [ ] Database: `TIMESTAMPTZ` für alle Zeitfelder
- [ ] API: ISO 8601 Zulu-Format (`2025-11-23T10:00:00Z`)
- [ ] Frontend-Hint: Lokalisierung Europe/Berlin

**WP7 - Policy-Signing (Ed25519)** (4h) - Erweitert
- [ ] SHA-256 Hash-Verifikation (Pflicht)
- [ ] Ed25519-Signatur-Verifikation (PyNaCl)
- [ ] Policy-Loader mit Canonical-JSON
- [ ] Admin-Endpoint: `POST /policy`

**Rest bleibt wie MVP Plan:**
- WP8: Enhanced Sync (bereits im Plan)
- WP9: Inventory (bereits im Plan)
- WP10: Procurement (bereits im Plan)
- WP11: Finance (bereits im Plan)
- WP12: Reporting (bereits im Plan)
- WP13: Integration & Testing
- WP14: Postman & Docs

---

## ⏱️ Zeitschätzung (aktualisiert)

**Phase 2 MVP (vollständig):**
- WP0: 8h (Reuse-Scan)
- WP1: 6h (Artefakte)
- WP2: 20h (Solver - falls Eigenbau)
- WP3: 8h (SQL-Migrationen)
- WP4: 12h (Transfer & HR)
- WP5: 6h (Docs)
- WP6: 4h (UTC)
- WP7: 4h (Policy-Signing)
- WP8: 8h (Enhanced Sync)
- WP9: 12h (Inventory)
- WP10: 12h (Procurement)
- WP11: 10h (Finance)
- WP12: 8h (Reporting)
- WP13: 12h (Integration & Testing)
- WP14: 4h (Postman & Docs)

**Total: ~134h (~17 Arbeitstage / 3-4 Wochen)**

**Mit Reuse (PyJobShop):**
- WP2 nur 12h statt 20h
- **Total: ~126h (~16 Arbeitstage / 3 Wochen)**

---

## 🚨 Kritische Entscheidungen JETZT

### 1. Architektur
**Frage:** Monolith, Microservices oder Hybrid?
**Empfehlung:** Hybrid (Monolith + Solver-Microservice)

### 2. Solver-Reuse
**Frage:** PyJobShop, JobShopLib oder Eigenbau?
**Empfehlung:** PyJobShop testen, falls nicht passend → Eigenbau

### 3. Policy-Signing
**Frage:** Ed25519 Pflicht oder optional?
**Empfehlung:** SHA-256 Pflicht, Ed25519 optional

### 4. Service-URLs
**Frage:** Separate URLs für FLEET-ONE Tools oder Monolith-Endpoints?
**Empfehlung:** Monolith mit strukturierten Endpoints `/api/v1/{service}/*`

---

## 📋 Nächste Schritte

**Sofort:**
1. Architektur-Entscheidung treffen
2. WP0 starten: Reuse-Scan durchführen
3. PyJobShop/JobShopLib evaluieren

**Dann:**
4. WP1: Artefakte platzieren
5. WP2: Solver implementieren
6. WP3: SQL-Migrationen

**Frage an dich:**
Welche Architektur bevorzugst du? (Monolith/Microservices/Hybrid)

