# 🤖 Database Agent - RailFleet Manager

**Version:** 1.0.0  
**Status:** ✅ Active  
**Teil des DeepALL Agent-Systems**

---

## 📋 Übersicht

Der **Database Agent** ist ein spezialisierter Agent für Datenbank-Operationen, Schema-Management und Daten-Synchronisation im RailFleet Manager System.

---

## 🎯 Verantwortlichkeiten

1. **Schema-Verwaltung** - Tabellen, Indizes, Foreign Keys
2. **Daten-Validierung** - Integrität und Konsistenz
3. **Performance-Optimierung** - Query-Analyse und Tuning
4. **Backup & Recovery** - Automatische Backups
5. **Daten-Synchronisation** - Lokale ↔ Remote Sync
6. **Health Monitoring** - Gesundheitschecks und Alerts

---

## 🔧 Verfügbare Befehle

### 1. **Status** - Agent-Informationen
```bash
GET /api/v1/database-agent/status
```

**Response:**
```json
{
  "name": "DatabaseAgent",
  "version": "1.0.0",
  "status": "active",
  "available_commands": [
    "schema_info",
    "validate",
    "stats",
    "health",
    "backup",
    "analyze",
    "sync_status"
  ]
}
```

---

### 2. **Schema Info** - Vollständige Schema-Informationen
```bash
GET /api/v1/database-agent/schema
```

**Response:**
```json
{
  "database_type": "sqlite",
  "total_tables": 5,
  "tables": {
    "vehicles": {
      "columns": [...],
      "indexes": [...],
      "foreign_keys": [...]
    },
    ...
  },
  "timestamp": "2025-11-25T20:30:00Z"
}
```

---

### 3. **Validate** - Schema-Validierung
```bash
GET /api/v1/database-agent/validate
```

**Response:**
```json
{
  "valid": true,
  "missing_tables": [],
  "extra_tables": [],
  "issues": []
}
```

---

### 4. **Stats** - Datenbank-Statistiken
```bash
GET /api/v1/database-agent/stats
```

**Response:**
```json
{
  "vehicles": {
    "total": 10,
    "operational": 6,
    "maintenance_due": 3,
    "in_workshop": 1
  },
  "maintenance_tasks": {
    "total": 8,
    "overdue": 1,
    "upcoming": 7
  },
  "work_orders": {
    "total": 6,
    "planned": 2,
    "in_progress": 2,
    "completed": 2
  },
  "timestamp": "2025-11-25T20:30:00Z"
}
```

---

### 5. **Health** - Gesundheitscheck
```bash
GET /api/v1/database-agent/health
```

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "connection": "ok",
    "schema": "ok",
    "data_integrity": "ok (10 vehicles)"
  },
  "timestamp": "2025-11-25T20:30:00Z"
}
```

---

### 6. **Backup** - Datenbank-Backup erstellen
```bash
POST /api/v1/database-agent/backup?backup_path=./backups
```

**Response:**
```json
{
  "status": "success",
  "backup_file": "./backups/railfleet_backup_20251125_203000.db",
  "timestamp": "2025-11-25T20:30:00Z",
  "size_bytes": 51200
}
```

---

### 7. **Analyze** - Query-Performance analysieren
```bash
POST /api/v1/database-agent/analyze
Content-Type: application/json

{
  "query": "SELECT * FROM vehicles WHERE status = 'operational'"
}
```

**Response:**
```json
{
  "status": "success",
  "query": "SELECT * FROM vehicles WHERE status = 'operational'",
  "execution_plan": [...],
  "timestamp": "2025-11-25T20:30:00Z"
}
```

---

### 8. **Sync Status** - Synchronisations-Status
```bash
GET /api/v1/database-agent/sync-status
```

**Response:**
```json
{
  "local_db": "sqlite",
  "remote_db": "supabase (not connected)",
  "last_sync": null,
  "pending_changes": 0,
  "status": "local_only",
  "timestamp": "2025-11-25T20:30:00Z"
}
```

---

## 🧪 Verwendung

### Python
```python
from src.agents.database_agent import database_agent

# Status abrufen
status = database_agent.execute_command("schema_info")
print(status)

# Statistiken abrufen
stats = database_agent.execute_command("stats")
print(stats)

# Backup erstellen
backup = database_agent.execute_command("backup", {"path": "./backups"})
print(backup)
```

### cURL
```bash
# Status
curl http://localhost:8080/api/v1/database-agent/status

# Statistiken
curl http://localhost:8080/api/v1/database-agent/stats

# Health Check
curl http://localhost:8080/api/v1/database-agent/health

# Backup
curl -X POST "http://localhost:8080/api/v1/database-agent/backup?backup_path=./backups"
```

---

## 📊 Integration mit DeepALL

Der Database Agent ist Teil des **DeepALL Agent-Systems** und arbeitet mit folgenden Agenten zusammen:

- **Supervisor Agent** - Koordination und Überwachung
- **Data/RAG Agent** - Daten-Retrieval und Analyse
- **Monitor Agent** - Performance-Monitoring
- **Ops Agent** - Deployment und Operations
- **Vault-Manager** - Audit-Trail und Versionierung

---

## 🔐 Security & Compliance

- ✅ Alle Operationen werden im **DeepVault** protokolliert
- ✅ Automatische **Backups** vor kritischen Operationen
- ✅ **Audit-Trail** für alle Schema-Änderungen
- ✅ **Health-Checks** alle 60 Minuten
- ✅ **Validierung** vor jeder Datenbank-Operation

---

## 📝 Changelog

### Version 1.0.0 (2025-11-25)
- ✅ Initiale Implementierung
- ✅ Schema-Management
- ✅ Statistiken und Health-Checks
- ✅ Backup-Funktionalität
- ✅ Query-Analyse
- ✅ API-Endpunkte

---

## 🚀 Nächste Schritte

### Phase 3 (Geplant)
- [ ] **Supabase-Integration** - Remote-Sync
- [ ] **Automatische Migrations** - Schema-Updates
- [ ] **Performance-Alerts** - Slow-Query-Detection
- [ ] **Data-Archiving** - Alte Daten archivieren
- [ ] **Real-time Monitoring** - WebSocket-Updates

---

**Erstellt:** 2025-11-25  
**Agent:** Augment DeepALL Orchestrator  
**Vault Run:** VLT-20251125-002

