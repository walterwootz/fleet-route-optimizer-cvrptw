# 🗄️ SQLite vs. Dokumentiertes Schema - Vergleich

**Datum:** 2025-11-25  
**Zweck:** Vergleich zwischen tatsächlicher SQLite-Datenbank und dokumentiertem Schema

---

## ✅ **Tatsächlich in railfleet.db vorhanden:**

Basierend auf vorherigen Tests:

1. **`activity_log`** - Aktivitätsprotokoll
2. **`maintenance_tasks`** - Wartungsaufgaben (8 Einträge)
3. **`users`** - Benutzer
4. **`vehicles`** - Fahrzeuge/Lokomotiven (10 Einträge)
5. **`workshop_orders`** - Werkstattaufträge (6 Einträge)

**Total: 5 Tabellen**

---

## 📋 **Dokumentiert in RailFleet Manager Historie:**

Aus `DATABASE_SCHEMA_COMPLETE.md`:

### **Core Models** (3)
- ✅ `users` - **VORHANDEN**
- ✅ `vehicles` - **VORHANDEN**
- ❌ `workshops` - **FEHLT**

### **Maintenance** (4)
- ✅ `maintenance_tasks` - **VORHANDEN**
- ⚠️ `work_orders` → `workshop_orders` - **VORHANDEN (anderer Name)**
- ❌ `tracks` - **FEHLT**
- ❌ `wo_assignment` - **FEHLT**

### **Transfer** (1)
- ❌ `transfer_plans` - **FEHLT**

### **Inventory** (3)
- ❌ `part_inventory` - **FEHLT**
- ❌ `stock_locations` - **FEHLT**
- ❌ `stock_moves` - **FEHLT**

### **Procurement** (3)
- ❌ `suppliers` - **FEHLT**
- ❌ `purchase_orders` - **FEHLT**
- ❌ `purchase_order_lines` - **FEHLT**

### **Finance** (3)
- ❌ `invoices` - **FEHLT**
- ❌ `cost_centers` - **FEHLT**
- ❌ `budget_allocations` - **FEHLT**

### **HR** (2)
- ❌ `staff` - **FEHLT**
- ❌ `staff_assignments` - **FEHLT**

### **Documents** (1)
- ❌ `document_links` - **FEHLT**

### **Event Sourcing/CRDT** (5)
- ❌ `event_log` - **FEHLT** (aber `activity_log` vorhanden)
- ❌ `events` - **FEHLT**
- ❌ `crdt_metadata` - **FEHLT**
- ❌ `crdt_operations` - **FEHLT**
- ❌ `sync_devices` - **FEHLT**

### **ML & Analytics** (2)
- ❌ `ml_models` - **FEHLT**
- ❌ `predictions` - **FEHLT**

---

## 📊 **Zusammenfassung:**

| Status | Anzahl | Tabellen |
|--------|--------|----------|
| ✅ **Vorhanden** | 4 | users, vehicles, maintenance_tasks, workshop_orders |
| ⚠️ **Teilweise** | 1 | activity_log (statt event_log) |
| ❌ **Fehlt** | 22 | Alle anderen |
| **GESAMT** | **27** | **Dokumentiert** |
| **TATSÄCHLICH** | **5** | **In SQLite** |

---

## 🎯 **Empfehlung:**

### **Option 1: Minimales Schema (AKTUELL)**
- ✅ Funktioniert mit 5 Tabellen
- ✅ Ausreichend für Basis-Features
- ✅ Database Agent funktioniert
- ⚠️ Viele Features nicht verfügbar

### **Option 2: Vollständiges Schema erstellen**
- 📝 Alembic Migrations ausführen
- 📝 Alle 27 Tabellen anlegen
- 📝 Testdaten einfügen
- ⏱️ Aufwand: ~2-3 Stunden

### **Option 3: Schrittweise erweitern**
- 📝 Nur benötigte Tabellen hinzufügen
- 📝 Z.B. `workshops`, `tracks`, `staff`
- 📝 Nach Bedarf erweitern
- ⏱️ Aufwand: ~30 Min pro Modul

---

## 🔧 **Nächste Schritte:**

**Was möchtest du?**

1. **Mit 5 Tabellen weiterarbeiten** → Database Agent testen & Git Commit
2. **Vollständiges Schema erstellen** → Alle 27 Tabellen anlegen
3. **Wichtigste Tabellen hinzufügen** → workshops, tracks, staff, suppliers
4. **Supabase-Migration** → SSH Tunnel + PostgreSQL mit vollem Schema
5. **Etwas anderes?**

---

**Erstellt:** 2025-11-25  
**Agent:** DeepALL Orchestrator  
**Vault Run:** VLT-20251125-006

