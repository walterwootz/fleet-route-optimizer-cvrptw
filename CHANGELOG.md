# Changelog - RailFleet Manager

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-11-25

### 🎉 Phase 2 Abgeschlossen - Backend ↔ Frontend Integration mit echter Datenbank

### Added (Neu)

#### Backend
- **SQLite-Datenbank Integration** (`railfleet.db`)
  - Vollständiges Schema für alle RailFleet-Entitäten
  - 10 Beispiel-Lokomotiven mit realistischen Daten
  - 8 Wartungsaufgaben mit Fälligkeitsdaten
  - 6 Werkstattaufträge
  - Teile-Inventar und Personal-Daten
  
- **Neue API-Routen** (`src/api/routes_db/`)
  - `vehicles_db.py` - CRUD-Operationen für Fahrzeuge
  - `maintenance_db.py` - Wartungsplanung und HU-Fristen
  - `workshop_db.py` - Werkstattaufträge und Reparaturen
  
- **Datenbank-Setup-Skripte**
  - `scripts/create_local_db.py` - Erstellt SQLite-DB mit Beispieldaten
  - `scripts/setup_supabase_db.py` - Vorbereitung für Supabase-Migration

#### Frontend
- **Vite Proxy-Konfiguration** für Backend-Integration
  - Proxy von `/api` zu `http://localhost:8080`
  - Automatische Weiterleitung aller API-Anfragen

### Changed (Geändert)

#### Backend-Korrekturen (11 kritische Fixes)

1. **VectorClock Import-Fehler behoben** (`src/services/sync_engine.py`)
   - `VectorClockComparison` → `ClockRelation` (3 Vorkommen)
   - Zeilen: 14, 35, 47, 310, 325-326

2. **Database Import-Pfade korrigiert**
   - `src/api/v1/endpoints/analytics.py` (Zeile 23)
   - `src/api/v1/endpoints/fleet_one.py` (Zeile 22)
   - Von: `from src.database import get_db`
   - Nach: `from ....core.database import get_db`

3. **Model Import-Pfade korrigiert** (`src/services/analytics/metrics_calculator.py`)
   - Zeile 15: `event` → `events` (Event-Klasse)
   - Zeile 17: `workorder` → `maintenance` (WorkOrder-Klasse)
   - Zeile 18: `InventoryItem` → `Part`
   - Zeile 19: `staff.StaffMember` → `hr.Staff`

4. **Model Import-Pfade korrigiert** (`src/services/analytics/dashboard_service.py`)
   - Zeile 14: `event` → `events` (Event-Klasse)
   - Zeile 16: `workorder` → `maintenance` (WorkOrder-Klasse)
   - Zeile 17: `InventoryItem` → `Part`
   - Zeile 18: `staff.StaffMember` → `hr.Staff`

5. **SQLAlchemy Reserved Attribute Names behoben**
   - `src/models/railfleet/events.py` (Zeile 40): `metadata` → `event_metadata`
   - `src/models/railfleet/ml_models.py` (Zeile 76): `metadata` → `prediction_metadata`

6. **Directory Naming Conflict behoben**
   - `src/api/routes/` → `src/api/routes_db/` (Umbenennung)

7. **OAuth2 Dependency Order korrigiert** (`src/api/v1/endpoints/auth.py`)
   - `oauth2_scheme` und `get_current_user` an den Anfang verschoben

8. **Pydantic v2 Kompatibilität** (`src/api/schemas/finance.py`)
   - `regex=` → `pattern=` (Field-Parameter)

9. **Base Import-Pfade korrigiert** (4 Dateien)
   - Von: `from ..database import Base`
   - Nach: `from ...core.database import Base`

#### Frontend
- **Vite Config aktualisiert** (`frontend/vite.config.ts`)
  - Backend-Port von 8000 → 8080 geändert

### Fixed (Behoben)

- ✅ Backend startet ohne Import-Fehler
- ✅ Alle API-Endpunkte liefern echte Daten aus SQLite
- ✅ Frontend lädt Daten erfolgreich vom Backend
- ✅ Flotten-Seite zeigt 10 Lokomotiven aus Datenbank
- ✅ Wartungs-Seite zeigt 8 Aufgaben aus Datenbank
- ✅ Dashboard zeigt Echtzeit-Statistiken
- ✅ FLEET-ONE Chat-Agent öffnet korrekt

### Technical Details

#### Server-Konfiguration
- **Backend:** FastAPI auf Port 8080 (uvicorn)
- **Frontend:** Vite Dev Server auf Port 3000
- **Datenbank:** SQLite (`railfleet.db`)

#### Datenbank-Schema
- **Vehicles:** 10 Lokomotiven (BR 152, BR 185, BR 189)
- **Maintenance:** 8 Aufgaben (HU, Bremsprüfung, Ölwechsel, Klimaanlage)
- **Workshop:** 6 Werkstattaufträge
- **Parts:** Ersatzteile-Inventar
- **Staff:** Personal-Daten

### Testing

#### Getestete Komponenten
- ✅ Backend API (`/api/vehicles/`, `/api/maintenance/`, `/docs`)
- ✅ Frontend Dashboard (Statistiken, Charts, Aktivitäten)
- ✅ Frontend Flotten-Seite (Tabelle, Filter, Suche)
- ✅ Frontend Wartungs-Seite (Aufgaben, Prioritäten, Typen)
- ✅ FLEET-ONE Chat-Agent (UI, Willkommensnachricht)

#### Screenshots erstellt
1. `railfleet-dashboard-real-data.png`
2. `railfleet-fleet-real-data.png`
3. `railfleet-maintenance-real-data.png`
4. `railfleet-fleet-one-chat-real-data.png`

### Known Issues

- ⚠️ Supabase self-hosted instance nicht erreichbar (Connection Timeout)
- ⚠️ WebSocket für Echtzeit-Updates noch nicht implementiert
- ⚠️ Dashboard verwendet teilweise Mock-Daten für Statistiken

### Migration Notes

- SQLite wird als temporäre Lösung verwendet
- Migration zu Supabase PostgreSQL geplant (wenn Server erreichbar)
- Alle Daten können mit `scripts/setup_supabase_db.py` migriert werden

---

## [1.0.0] - 2025-11-24

### Initial Release - Phase 1 & Phase 3 Features

#### Added
- FastAPI Backend mit 140+ Endpunkten
- React/TypeScript Frontend mit 8 Dashboard-Seiten
- Event Sourcing System
- CRDT-basierte Offline-Synchronisation
- ML Pipeline für prädiktive Wartung
- Time Travel Debugging
- Policy Engine
- 140 Playwright E2E Tests
- FLEET-ONE AI Agent Integration
- CVRPTW Route Optimization Solver

---

## Legende

- **Added** - Neue Features
- **Changed** - Änderungen an bestehenden Features
- **Deprecated** - Bald zu entfernende Features
- **Removed** - Entfernte Features
- **Fixed** - Bugfixes
- **Security** - Sicherheits-Updates

