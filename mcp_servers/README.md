# 🔌 MCP Servers für RailFleet Manager

**Model Context Protocol (MCP)** Server für Datenbank-Zugriff

---

## 📋 Übersicht

Dieses Verzeichnis enthält **2 MCP-Server**:

1. **`supabase-selfhosted`** - Für selbst-gehostete Supabase-Instanz
2. **`sqlite-local`** - Für lokale SQLite-Datenbank

---

## 🚀 Installation

### **1. MCP Python SDK installieren**
```bash
pip install mcp
```

### **2. MCP-Server testen**
```bash
# SQLite Server
python mcp_servers/sqlite_local/server.py

# Supabase Server (wenn erreichbar)
python mcp_servers/supabase_selfhosted/server.py
```

---

## 🔧 Konfiguration

### **Augment / Claude Code**

Die Konfiguration ist bereits in `.mcp.json` vorhanden:

```json
{
  "mcpServers": {
    "supabase-selfhosted": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/supabase_selfhosted/server.py"],
      "env": {
        "SUPABASE_URL": "https://supabasekong-s0wkccwgk84w0o8ww8s8wccs.luli-server.de:8000",
        "SUPABASE_ANON_KEY": "...",
        "SUPABASE_SERVICE_KEY": "..."
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

### **Claude Desktop**

Füge zu `~/Library/Application Support/Claude/claude_desktop_config.json` hinzu:

```json
{
  "mcpServers": {
    "railfleet-db": {
      "command": "python",
      "args": [
        "C:/Download/Fleet_one/fleet-route-optimizer-cvrptw/mcp_servers/sqlite_local/server.py"
      ],
      "env": {
        "DATABASE_PATH": "C:/Download/Fleet_one/fleet-route-optimizer-cvrptw/railfleet.db"
      }
    }
  }
}
```

---

## 📊 Verfügbare Ressourcen

### **SQLite Server**

#### **Resources:**
- `sqlite://schema` - Vollständiges Datenbank-Schema
- `sqlite://vehicles` - Fahrzeug-Daten
- `sqlite://maintenance_tasks` - Wartungsaufgaben
- `sqlite://work_orders` - Werkstattaufträge
- `sqlite://parts` - Ersatzteile
- `sqlite://staff` - Personal

#### **Tools:**
- `query` - SQL-Abfrage ausführen
- `get_table_stats` - Tabellen-Statistiken abrufen

### **Supabase Server**

#### **Resources:**
- `supabase://tables` - Liste aller Tabellen
- `supabase://vehicles` - Fahrzeug-Daten
- `supabase://maintenance_tasks` - Wartungsaufgaben

#### **Tools:**
- `query_table` - Tabelle mit Filtern abfragen
- `insert_row` - Neue Zeile einfügen
- `update_row` - Zeilen aktualisieren

---

## 🧪 Verwendung

### **In Augment / Claude Code**

```
User: Zeige mir alle Fahrzeuge aus der Datenbank

Agent: [Verwendet automatisch MCP Server]
       Ruft sqlite://vehicles Resource ab
       Zeigt Daten an
```

### **Programmatisch**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to SQLite MCP Server
server_params = StdioServerParameters(
    command="python",
    args=["mcp_servers/sqlite_local/server.py"],
    env={"DATABASE_PATH": "railfleet.db"}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()
        
        # List resources
        resources = await session.list_resources()
        print(resources)
        
        # Read resource
        data = await session.read_resource("sqlite://vehicles")
        print(data)
        
        # Call tool
        result = await session.call_tool("query", {
            "sql": "SELECT * FROM vehicles WHERE status = 'operational'"
        })
        print(result)
```

---

## 🔍 Beispiele

### **1. Schema abrufen**
```python
# Resource: sqlite://schema
{
  "vehicles": [
    {"name": "id", "type": "INTEGER", "primary_key": true},
    {"name": "vehicle_number", "type": "VARCHAR(50)", "nullable": false},
    ...
  ],
  ...
}
```

### **2. Daten abfragen**
```python
# Tool: query
{
  "sql": "SELECT * FROM vehicles WHERE status = 'operational' LIMIT 10"
}

# Response:
{
  "rows": [
    {"id": 1, "vehicle_number": "BR185-042", "status": "operational", ...},
    ...
  ],
  "count": 10
}
```

### **3. Statistiken abrufen**
```python
# Tool: get_table_stats
{
  "table": "vehicles"
}

# Response:
{
  "table": "vehicles",
  "row_count": 10,
  "column_count": 12,
  "columns": ["id", "vehicle_number", "vehicle_type", ...]
}
```

---

## 🛠️ Entwicklung

### **Neuen MCP Server erstellen**

1. **Verzeichnis erstellen:**
   ```bash
   mkdir mcp_servers/my_server
   ```

2. **Server implementieren:**
   ```python
   # mcp_servers/my_server/server.py
   from mcp.server import Server
   
   app = Server("my-server")
   
   @app.list_resources()
   async def list_resources():
       return [...]
   
   @app.read_resource()
   async def read_resource(uri: str):
       return "..."
   ```

3. **In `.mcp.json` registrieren:**
   ```json
   {
     "mcpServers": {
       "my-server": {
         "type": "stdio",
         "command": "python",
         "args": ["mcp_servers/my_server/server.py"]
       }
     }
   }
   ```

---

## 📚 Weitere Informationen

- **MCP Specification:** https://modelcontextprotocol.io
- **MCP Python SDK:** https://github.com/modelcontextprotocol/python-sdk
- **Supabase Docs:** https://supabase.com/docs

---

**Erstellt:** 2025-11-25  
**Agent:** Augment DeepALL Orchestrator  
**Vault Run:** VLT-20251125-004

