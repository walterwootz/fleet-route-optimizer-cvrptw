# 🔍 Open-Source Reuse Decision Log

**Projekt:** RailFleet Manager - Phase 2
**Datum:** 2025-11-23
**Autor:** Claude Code
**Status:** In Progress

---

## 📋 Suchstrategie

**Kriterien:**
- ✅ Aktive Pflege (letzte Commits ≤ 12 Monate)
- ✅ ≥ 50 ⭐ (Richtwert für Community-Akzeptanz)
- ✅ Permissive Lizenz (MIT/BSD/Apache-2.0)
- ✅ Gute Dokumentation & Beispiele
- ✅ API-Fit zu unseren Anforderungen
- ✅ Test-Coverage & Issue-Gesundheit

**Bewertungsskala:**
- 🟢 **ADOPT** - Produktiv nutzen, direkt integrieren
- 🟡 **TRIAL** - Testen, PoC erstellen
- 🔴 **HOLD** - Nicht produktiv, nur für Learning/Forschung
- ⚫ **REJECT** - Nicht geeignet

---

## 🤖 Bereich 1: Scheduler / OR-Tools CP-SAT

### 1.1 PyJobShop

**Repository:** https://github.com/PyJobShop/PyJobShop
**Lizenz:** MIT ✅
**Stars:** ~200+ ⭐
**Letzte Commits:** Aktiv (2024) ✅
**Sprache:** Python

**Beschreibung:**
OR-Tools-basierte Library für Job Shop Scheduling (JSSP), Flexible Job Shop (FJSP), Flow Shop (FSP). Modulare Architektur mit CP-SAT Backend.

**Features:**
- ✅ CP-SAT Integration out-of-the-box
- ✅ No-Overlap Constraints (Maschinen/Ressourcen)
- ✅ Flexible Modellierung (Jobs, Operations, Machines)
- ✅ Gute Dokumentation & Beispiele
- ✅ Aktive Community

**API-Fit für RailFleet:**
- ✅ **Tracks** → Machines
- ✅ **Work Orders** → Jobs
- ✅ **Tasks** → Operations
- ⚠️ **Skills** - Teilweise mappbar (Setup Times)
- ⚠️ **Teile-Verfügbarkeit** - Custom Constraint nötig
- ⚠️ **Schicht-Fenster** - Custom Availability Windows

**Pros:**
- Reduziert Implementierungszeit drastisch (12h statt 20h)
- Battle-tested CP-SAT-Modelle
- Erweiterbar durch Custom Constraints
- MIT-Lizenz = kommerzielle Nutzung OK

**Cons:**
- Nicht alle Constraints out-of-the-box (Teile, Skills, Shifts)
- Zusätzliche Lernkurve für Library-API
- Overhead durch Abstraktion

**Integration:**
```python
# Adapter-Pattern
from pyjobshop import Model, Job, Operation, Machine

def build_railfleet_model(work_orders, tracks, teams, parts):
    model = Model()

    # Map Tracks -> Machines
    machines = {track.id: Machine(name=track.name) for track in tracks}

    # Map Work Orders -> Jobs
    for wo in work_orders:
        job = Job(name=wo.id)
        op = Operation(duration=wo.duration_min, machine=machines[wo.assigned_track])
        job.add_operation(op)
        model.add_job(job)

    # Add custom constraints (parts, skills, shifts)
    # ... (etwa 200 LOC zusätzlich)

    return model.solve()
```

**Entscheidung:** 🟢 **ADOPT** (mit Custom Extensions)

**Aufwand-Schätzung:**
- Basis-Integration: 4h
- Custom Constraints (Skills, Teile, Shifts): 6h
- Testing & Refinement: 2h
- **Total: 12h** (vs. 20h Eigenbau)

---

### 1.2 JobShopLib

**Repository:** https://github.com/Pabloo22/job_shop_lib
**Lizenz:** MIT ✅
**Stars:** ~50+ ⭐
**Letzte Commits:** Aktiv (2024) ✅
**Sprache:** Python

**Beschreibung:**
Modulare Job Shop Problem Library mit Fokus auf Benchmarking & Algorithmen-Vergleich. Unterstützt OR-Tools, aber auch andere Solver.

**Features:**
- ✅ Modularer Aufbau
- ✅ Mehrere Solver-Backends (OR-Tools, Gurobi, Heuristiken)
- ✅ Benchmark-Instances
- ⚠️ Weniger dokumentiert als PyJobShop
- ⚠️ Kleinere Community

**API-Fit für RailFleet:**
- Ähnlich wie PyJobShop, aber weniger ausgefeilt

**Entscheidung:** 🟡 **TRIAL** (Fallback zu PyJobShop)

**Grund:** PyJobShop ist reifer und besser dokumentiert. JobShopLib nur als Backup, falls PyJobShop nicht passt.

---

### 1.3 CP-SAT Primer

**Repository:** https://github.com/d-krupke/cpsat-primer
**Lizenz:** MIT (Dokumentation) ✅
**Stars:** ~300+ ⭐
**Letzte Commits:** Aktiv (2024) ✅

**Beschreibung:**
Umfassende Patterns & Best Practices für OR-Tools CP-SAT. Kein Library-Code, sondern Lern-Ressource.

**Entscheidung:** 🟢 **ADOPT** (als Referenz)

**Nutzung:** Dokumentation für Custom Constraints (optionale Intervalle, Implikationen, etc.)

---

### 1.4 Awesome OR-Tools

**Repository:** https://github.com/or-tools/awesome_or_tools
**Lizenz:** N/A (Link-Sammlung)
**Stars:** ~200+ ⭐

**Beschreibung:**
Kuratierte Liste von OR-Tools-Ressourcen, Beispielen, Projekten.

**Entscheidung:** 🟢 **ADOPT** (als Ressource)

---

## 🔄 Bereich 2: FastAPI × Celery (Async/What-If)

### 2.1 testdrivenio/fastapi-celery

**Repository:** https://github.com/testdrivenio/fastapi-celery
**Lizenz:** MIT ✅
**Stars:** ~500+ ⭐
**Letzte Commits:** Aktiv (2023-2024) ✅

**Beschreibung:**
Template für FastAPI + Celery + Redis Integration. Docker-ready, Production-Patterns.

**Features:**
- ✅ FastAPI + Celery + Redis Setup
- ✅ Task Queue Management
- ✅ Docker-Compose ready
- ✅ Beispiele für Long-Running Tasks

**API-Fit für RailFleet:**
- ✅ **What-If-Szenarien** → Background Tasks
- ✅ **Solver-Jobs** → Celery Tasks
- ✅ **Status-Polling** → Task Status API

**Integration:**
```python
# backend/app/tasks/solver_tasks.py
from celery import Celery

celery_app = Celery("railfleet", broker="redis://redis:6379/0")

@celery_app.task
def solve_what_if(work_orders, scenario_id):
    # Call solver microservice
    result = requests.post("http://solver:7070/solve", json=work_orders)
    return {"scenario_id": scenario_id, "result": result.json()}
```

**Entscheidung:** 🟢 **ADOPT** (für What-If-Feature)

**Aufwand-Schätzung:**
- Setup (Redis + Celery): 2h
- What-If Endpoints: 3h
- Testing: 1h
- **Total: 6h**

**Priorität:** Medium (Nice-to-Have für MVP, nicht kritisch)

---

### 2.2 Madi-S/fastapi-celery-template

**Repository:** https://github.com/Madi-S/fastapi-celery-template
**Lizenz:** Nicht spezifiziert ⚠️
**Stars:** ~20+ ⭐
**Letzte Commits:** 2023

**Entscheidung:** 🔴 **HOLD** (testdrivenio ist besser dokumentiert & aktiver)

---

## 📝 Bereich 3: Event-Sourcing / Event-Log

### 3.1 pyeventsourcing/eventsourcing

**Repository:** https://github.com/pyeventsourcing/eventsourcing
**Lizenz:** BSD-3-Clause ✅
**Stars:** ~1500+ ⭐
**Letzte Commits:** Sehr aktiv (2024) ✅

**Beschreibung:**
Vollständiges Event-Sourcing Framework für Python. Aggregates, Events, Snapshots, Projections.

**Features:**
- ✅ Append-only Event Store
- ✅ Aggregate-Pattern
- ✅ Mehrere Backends (PostgreSQL, EventStoreDB)
- ✅ Sehr gute Dokumentation
- ✅ Production-ready

**API-Fit für RailFleet:**
- ⚠️ **Overkill** für einfaches Event-Log
- ⚠️ Steile Lernkurve (Domain-Driven Design)
- ⚠️ Architektur-Umstellung nötig

**Entscheidung:** 🟡 **TRIAL** (für Phase 3+, nicht MVP)

**Grund:** Für MVP reicht einfache `event_log`-Tabelle (Append-only). pyeventsourcing ist sehr mächtig, aber zu komplex für aktuellen Scope. Später für Advanced Features (Event Replay, CQRS) interessant.

---

### 3.2 Eigenbau: Append-Only Event Log

**Ansatz:**
```sql
CREATE TABLE event_log (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload_json JSONB NOT NULL,
    actor_id UUID,
    device_id VARCHAR(100),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT event_log_append_only CHECK (id > 0)
);

-- Append-only enforcement (no UPDATE/DELETE)
CREATE RULE event_log_no_update AS ON UPDATE TO event_log DO INSTEAD NOTHING;
CREATE RULE event_log_no_delete AS ON DELETE TO event_log DO INSTEAD NOTHING;
```

**Entscheidung:** 🟢 **ADOPT** (für MVP)

**Aufwand:** 2h (SQL + API)

---

## 🔐 Bereich 4: Signaturen & Merkle (Policy-Integrity)

### 4.1 PyNaCl (Ed25519)

**Repository:** https://github.com/pyca/pynacl
**Lizenz:** Apache-2.0 ✅
**Stars:** ~1000+ ⭐
**Letzte Commits:** Aktiv (2024) ✅
**Maintainer:** Python Cryptographic Authority

**Beschreibung:**
Python-Binding für libsodium (NaCl). Ed25519-Signaturen, Verschlüsselung, Hashing.

**Features:**
- ✅ Ed25519-Signaturen (schnell, sicher)
- ✅ Production-ready
- ✅ Einfache API
- ✅ Gut dokumentiert

**Integration:**
```python
from nacl.signing import SigningKey, VerifyKey

# Policy signing (Admin)
signing_key = SigningKey.generate()
signature = signing_key.sign(policy_hash.encode())

# Policy verification (Backend)
verify_key = VerifyKey(public_key_bytes)
verify_key.verify(signature)  # Raises if invalid
```

**Entscheidung:** 🟢 **ADOPT** (für Ed25519-Signatur)

**Aufwand:** 2h (Integration + Admin-Endpoint)

**Priorität:** Optional für MVP, aber einfach zu integrieren

---

### 4.2 pymerkle / pymerkletools

**Repository:** https://github.com/fmerg/pymerkle
**Lizenz:** MIT ✅
**Stars:** ~100+ ⭐

**Beschreibung:**
Merkle-Tree-Implementierung für Tamper-Proof Logs.

**Entscheidung:** 🟡 **TRIAL** (für Advanced Auditing, Phase 3+)

**Grund:** Für MVP nicht nötig. Einfaches SHA-256-Hashing der Policy genügt. Merkle-Trees interessant für Multi-Policy-Versioning später.

---

## 🌐 Bereich 5: Local-First / CRDT (Optional PoC)

### 5.1 vlcn-io/cr-sqlite

**Repository:** https://github.com/vlcn-io/cr-sqlite
**Lizenz:** MIT ✅
**Stars:** ~3000+ ⭐
**Letzte Commits:** Sehr aktiv (2024) ✅

**Beschreibung:**
Conflict-Free Replicated Data Types (CRDTs) für SQLite. Ermöglicht Multi-Writer-Sync.

**Entscheidung:** 🟡 **TRIAL** (für Advanced Offline-Sync, Phase 3+)

**Grund:** Sehr interessant für echte Local-First-Architektur, aber zu komplex für MVP. Aktuelle Konfliktauflösung (Policy-basiert) genügt.

---

### 5.2 sqliteai/sqlite-sync

**Repository:** https://github.com/sqliteai/sqlite-sync
**Lizenz:** Elastic License 2.0 ⚠️ **NICHT produktiv!**
**Stars:** ~100+ ⭐

**Beschreibung:**
SQLite-Sync-Mechanismus.

**Entscheidung:** 🔴 **HOLD** (Lizenz-Problem!)

**Grund:** Elastic License 2.0 ist **nicht** produktiv nutzbar (ähnlich wie SSPL). Nur für Forschung/Learning.

---

## 📊 Zusammenfassung & Finale Entscheidungen

### ✅ ADOPT (Produktiv nutzen)

| Bereich | Library | Lizenz | Aufwand | Priorität |
|---------|---------|--------|---------|-----------|
| **Scheduler** | **PyJobShop** | MIT | 12h | **HOCH** |
| Scheduler-Docs | CP-SAT Primer | MIT | 0h (Ref) | HOCH |
| Async/What-If | fastapi-celery | MIT | 6h | MITTEL |
| Event-Log | **Eigenbau** (Append-only SQL) | N/A | 2h | **HOCH** |
| Policy-Signing | **PyNaCl** (Ed25519) | Apache-2.0 | 2h | NIEDRIG |

**Total Aufwand (ADOPT):** 22h

### 🟡 TRIAL (Testen, später evaluieren)

| Library | Use-Case | Phase |
|---------|----------|-------|
| JobShopLib | Fallback zu PyJobShop | MVP (Backup) |
| pyeventsourcing | Advanced Event-Sourcing | Phase 3+ |
| cr-sqlite | Local-First CRDT | Phase 3+ |
| pymerkle | Merkle-Trees für Audit | Phase 3+ |

### 🔴 HOLD/REJECT

| Library | Grund |
|---------|-------|
| sqlite-sync | Elastic License 2.0 (nicht produktiv) |
| Madi-S/fastapi-celery | Schlechtere Doku als testdrivenio |

---

## 🏗️ Architektur-Entscheidung: Hybrid

**Finale Struktur:**

```
┌─────────────────────────────────────────────────────┐
│  Backend (FastAPI Monolith) - Port 8000             │
│  ┌─────────────────────────────────────────────┐   │
│  │ /api/v1/auth/*          (Phase 1 ✅)        │   │
│  │ /api/v1/vehicles/*      (Phase 1 ✅)        │   │
│  │ /api/v1/maintenance/*   (Phase 1 ✅)        │   │
│  │ /api/v1/workshops/*     (Phase 1 ✅)        │   │
│  │ /api/v1/sync/*          (Phase 1 ✅)        │   │
│  │ /api/v1/transfer/*      (Phase 2 🆕)        │   │
│  │ /api/v1/hr/*            (Phase 2 🆕)        │   │
│  │ /api/v1/docs/*          (Phase 2 🆕)        │   │
│  │ /api/v1/procurement/*   (Phase 2 🆕)        │   │
│  │ /api/v1/finance/*       (Phase 2 🆕)        │   │
│  │ /api/v1/reports/*       (Phase 2 🆕)        │   │
│  │ /api/v1/scheduler/*     (Phase 2 🆕 Proxy)  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                      ↓ HTTP Call
┌─────────────────────────────────────────────────────┐
│  Solver Microservice - Port 7070                    │
│  ┌─────────────────────────────────────────────┐   │
│  │ POST /solve                                  │   │
│  │ ├─ PyJobShop Adapter (MIT)                  │   │
│  │ └─ Custom Constraints (Skills, Teile, ...)  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

Optional (What-If):
┌─────────────────────────────────────────────────────┐
│  Redis + Celery Worker                              │
│  ├─ Background Jobs (Solver What-If)                │
│  └─ Task Status API                                 │
└─────────────────────────────────────────────────────┘
```

---

## 📝 Nächste Schritte

1. ✅ **Reuse-Scan abgeschlossen** (WP0)
2. ⏭️ **WP1**: Artefakte platzieren
   - Policy JSON ✅ (bereits da)
   - Postman Collection (bereitgestellt)
   - Examples erstellen
3. ⏭️ **WP2**: Solver-Service mit PyJobShop
   - PyJobShop installieren & testen
   - Adapter entwickeln
   - Docker-Setup

---

**Erstellt:** 2025-11-23
**Aktualisiert:** 2025-11-23
**Status:** ✅ Complete
**Nächster Schritt:** WP1 - Artefakte platzieren
