# 🔌 MCP Integration Guide - RailFleet Manager

**Model Context Protocol (MCP)** Integration für Supabase & SQLite

---

## 📋 Was ist MCP?

**MCP (Model Context Protocol)** ist ein offener Standard, der es AI-Assistenten ermöglicht, sicher auf externe Datenquellen zuzugreifen.

**Vorteile:**
- ✅ Standardisierte Schnittstelle
- ✅ Sichere Authentifizierung
- ✅ Automatische Ressourcen-Erkennung
- ✅ Tool-Integration

---

## 🎯 Ziel

Integration von **2 Datenquellen** via MCP:

1. **SQLite (Lokal)** - Aktuell in Verwendung
2. **Supabase (Self-Hosted)** - Sobald erreichbar

---

## 📁 Struktur

```
fleet-route-optimizer-cvrptw/
├── .mcp.json                          ← MCP-Konfiguration
├── mcp_servers/
│   ├── README.md                      ← Dokumentation
│   ├── supabase_selfhosted/
│   │   ├── server.py                  ← Supabase MCP Server
│   │   └── package.json
│   └── sqlite_local/
│       └── server.py                  ← SQLite MCP Server
```

---

## 🔧 Konfiguration (.mcp.json)

```json
{
  "mcpServers": {
    "supabase-selfhosted": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/supabase_selfhosted/server.py"],
      "env": {
        "SUPABASE_URL": "https://supabasekong-s0wkccwgk84w0o8ww8s8wccs.luli-server.de:8000",
        "SUPABASE_ANON_KEY": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "SUPABASE_SERVICE_KEY": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    },
    "sqlite-local": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/sqlite_local/server.py"],
      "env": {
        "DATABASE_PATH": "railfleet.db"
      }
    }
  }
}
```

---

## 🚀 Verwendung in Augment / Claude Code

### **Automatische Erkennung**

Augment/Claude Code erkennt `.mcp.json` automatisch und lädt die MCP-Server.

### **Beispiel-Anfragen**

```
User: "Zeige mir alle Fahrzeuge aus der Datenbank"

Agent: [Verwendet automatisch sqlite-local MCP Server]
       → Ruft Resource "sqlite://vehicles" ab
       → Zeigt Daten an
```

```
User: "Wie viele Wartungsaufgaben sind überfällig?"

Agent: [Verwendet sqlite-local MCP Server]
       → Ruft Tool "query" auf
       → SQL: SELECT COUNT(*) FROM maintenance_tasks WHERE due_date < date('now')
       → Zeigt Ergebnis an
```

---

## 📊 Verfügbare Ressourcen

### **SQLite Server (sqlite-local)**

| Resource | URI | Beschreibung |
|----------|-----|--------------|
| Schema | `sqlite://schema` | Vollständiges DB-Schema |
| Vehicles | `sqlite://vehicles` | Fahrzeug-Daten |
| Maintenance | `sqlite://maintenance_tasks` | Wartungsaufgaben |
| Work Orders | `sqlite://work_orders` | Werkstattaufträge |
| Parts | `sqlite://parts` | Ersatzteile |
| Staff | `sqlite://staff` | Personal |

### **Supabase Server (supabase-selfhosted)**

| Resource | URI | Beschreibung |
|----------|-----|--------------|
| Tables | `supabase://tables` | Liste aller Tabellen |
| Vehicles | `supabase://vehicles` | Fahrzeug-Daten |
| Maintenance | `supabase://maintenance_tasks` | Wartungsaufgaben |

---

## 🛠️ Verfügbare Tools

### **SQLite Server**

#### **1. query**
```json
{
  "name": "query",
  "description": "Execute a SQL query",
  "input": {
    "sql": "SELECT * FROM vehicles WHERE status = 'operational'"
  }
}
```

#### **2. get_table_stats**
```json
{
  "name": "get_table_stats",
  "description": "Get statistics for a table",
  "input": {
    "table": "vehicles"
  }
}
```

### **Supabase Server**

#### **1. query_table**
```json
{
  "name": "query_table",
  "description": "Query a Supabase table with filters",
  "input": {
    "table": "vehicles",
    "select": "*",
    "filter": {"status": "operational"},
    "limit": 100
  }
}
```

#### **2. insert_row**
```json
{
  "name": "insert_row",
  "description": "Insert a new row",
  "input": {
    "table": "vehicles",
    "data": {
      "vehicle_number": "BR185-999",
      "vehicle_type": "Electric Locomotive",
      "status": "operational"
    }
  }
}
```

---

## 🧪 Manueller Test

### **SQLite Server testen**
```bash
# Server starten
python mcp_servers/sqlite_local/server.py

# In anderem Terminal:
# (Sendet JSON-RPC Anfragen via stdin/stdout)
```

### **Supabase Server testen**
```bash
# Server starten (wenn Supabase erreichbar)
python mcp_servers/supabase_selfhosted/server.py
```

---

## 🔄 Automatischer Fallback

Das System verwendet **automatisch** den richtigen Server:

1. **Supabase erreichbar?** → Verwendet `supabase-selfhosted`
2. **Supabase nicht erreichbar?** → Verwendet `sqlite-local`

Dies wird durch `src/core/database_hybrid.py` gesteuert.

---

## 📝 Integration mit Database Agent

Der **Database Agent** kann MCP-Server nutzen:

```python
from src.agents.database_agent import database_agent

# Agent erkennt automatisch verfügbare MCP-Server
status = database_agent.execute_command("schema_info")

# Verwendet intern:
# - sqlite-local MCP Server (wenn SQLite aktiv)
# - supabase-selfhosted MCP Server (wenn Supabase aktiv)
```

---

## 🎯 Nächste Schritte

### **Phase 1: SQLite MCP (✅ Fertig)**
- [x] SQLite MCP Server erstellt
- [x] `.mcp.json` Konfiguration
- [x] Dokumentation

### **Phase 2: Supabase MCP (⏳ Wartet auf Server)**
- [x] Supabase MCP Server erstellt
- [ ] Verbindung testen
- [ ] Migration durchführen

### **Phase 3: Integration (🔜 Nächster Schritt)**
- [ ] MCP SDK installieren
- [ ] Server in Augment/Claude Code testen
- [ ] Database Agent mit MCP verbinden
- [ ] Automatische Ressourcen-Erkennung

---

## 📚 Ressourcen

- **MCP Specification:** https://modelcontextprotocol.io
- **MCP Python SDK:** https://github.com/modelcontextprotocol/python-sdk
- **Supabase MCP:** https://github.com/supabase/mcp-server-supabase
- **SQLite MCP:** https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite

---

**Erstellt:** 2025-11-25  
**Agent:** Augment DeepALL Orchestrator  
**Vault Run:** VLT-20251125-004  
**Status:** ✅ MCP-Server bereit, wartet auf Supabase-Verbindung

