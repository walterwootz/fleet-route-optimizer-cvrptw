# 🤖 FLEET-ONE Services → Datenbank Mapping

**Datum:** 2025-11-25  
**Zweck:** Prüfung ob alle 9 Services vollständig in der Datenbank abgebildet sind

---

## 📊 **Übersicht:**

| Service | Benötigte Tabellen | Vorhanden | Fehlend | Status |
|---------|-------------------|-----------|---------|--------|
| **1. fleet_db** | vehicles | ✅ | - | ✅ **100%** |
| **2. maintenance_service** | maintenance_tasks, work_orders | ✅ (2/2) | - | ✅ **100%** |
| **3. workshop_service** | workshops, tracks, workshop_orders, wo_assignment | ⚠️ (1/4) | 3 | ⚠️ **25%** |
| **4. transfer_service** | transfer_plans, staff | ❌ (0/2) | 2 | ❌ **0%** |
| **5. procurement_service** | suppliers, purchase_orders, purchase_order_lines, part_inventory | ❌ (0/4) | 4 | ❌ **0%** |
| **6. reporting_service** | (nutzt alle Tabellen) | ⚠️ | - | ⚠️ **Teilweise** |
| **7. finance_service** | invoices, cost_centers, budget_allocations | ❌ (0/3) | 3 | ❌ **0%** |
| **8. hr_service** | staff, staff_assignments | ❌ (0/2) | 2 | ❌ **0%** |
| **9. docs_service** | document_links | ❌ (0/1) | 1 | ❌ **0%** |

**GESAMT:** 5 von 27 Tabellen vorhanden = **18.5%**

---

## 1️⃣ **fleet_db** - ✅ **VOLLSTÄNDIG**

### **Zweck:**
- Lok-Stammdaten
- Einsatzstatus, Standort, Kilometer

### **Benötigte Tabellen:**
- ✅ `vehicles` (10 Einträge)

### **Status:** ✅ **100% funktionsfähig**

---

## 2️⃣ **maintenance_service** - ✅ **VOLLSTÄNDIG**

### **Zweck:**
- Wartungspläne, Fristen, Termine, Maßnahmen

### **Benötigte Tabellen:**
- ✅ `maintenance_tasks` (8 Einträge)
- ✅ `workshop_orders` (6 Einträge) - entspricht `work_orders`

### **Status:** ✅ **100% funktionsfähig**

---

## 3️⃣ **workshop_service** - ⚠️ **NUR 25%**

### **Zweck:**
- Werkstattaufträge, Auftragsstatus, geplante Zeiten
- Zuordnung zu Gleisen/Pits
- Team-Zuordnung

### **Benötigte Tabellen:**
- ✅ `workshop_orders` (6 Einträge)
- ❌ `workshops` - **FEHLT** (Werkstatt-Stammdaten)
- ❌ `tracks` - **FEHLT** (Gleise/Pits)
- ❌ `wo_assignment` - **FEHLT** (Zuordnung WO → Track + Team)

### **Status:** ⚠️ **Nur Aufträge, keine Werkstatt-Infrastruktur**

---

## 4️⃣ **transfer_service** - ❌ **FEHLT KOMPLETT**

### **Zweck:**
- Überführungsfahrten + zugeordnete Loks
- Personaleinsatz für Überführungen

### **Benötigte Tabellen:**
- ❌ `transfer_plans` - **FEHLT**
- ❌ `staff` - **FEHLT**

### **Status:** ❌ **0% - Nicht implementiert**

---

## 5️⃣ **procurement_service** - ❌ **FEHLT KOMPLETT**

### **Zweck:**
- Teilebedarf aus Aufträgen
- Bestellanforderungen

### **Benötigte Tabellen:**
- ❌ `suppliers` - **FEHLT**
- ❌ `purchase_orders` - **FEHLT**
- ❌ `purchase_order_lines` - **FEHLT**
- ❌ `part_inventory` - **FEHLT**

### **Status:** ❌ **0% - Nicht implementiert**

---

## 6️⃣ **reporting_service** - ⚠️ **TEILWEISE**

### **Zweck:**
- Aggregierte Kennzahlen
- Fahrzeugverfügbarkeit, Einsatzzeiten, Werkstattzeiten

### **Benötigte Tabellen:**
- ✅ `vehicles` - Verfügbarkeit
- ✅ `maintenance_tasks` - Wartungszeiten
- ✅ `workshop_orders` - Werkstattzeiten
- ❌ `transfer_plans` - **FEHLT** (Überführungszeiten)
- ❌ `invoices` - **FEHLT** (Kosten)
- ❌ `staff_assignments` - **FEHLT** (Personaleinsatz)

### **Status:** ⚠️ **Basis-Reports möglich, erweiterte Reports fehlen**

---

## 7️⃣ **finance_service** - ❌ **FEHLT KOMPLETT**

### **Zweck:**
- Eingangsrechnungen
- Kostenstellen
- Budgetzahlen

### **Benötigte Tabellen:**
- ❌ `invoices` - **FEHLT**
- ❌ `cost_centers` - **FEHLT**
- ❌ `budget_allocations` - **FEHLT**

### **Status:** ❌ **0% - Nicht implementiert**

---

## 8️⃣ **hr_service** - ❌ **FEHLT KOMPLETT**

### **Zweck:**
- Mitarbeiter, Verfügbarkeiten, Qualifikationen
- Personaleinsatzplanung für Werkstattzuführungen

### **Benötigte Tabellen:**
- ❌ `staff` - **FEHLT**
- ❌ `staff_assignments` - **FEHLT**

### **Status:** ❌ **0% - Nicht implementiert**

---

## 9️⃣ **docs_service** - ❌ **FEHLT KOMPLETT**

### **Zweck:**
- Dokumente, Gültigkeiten
- Verknüpfungen zu Loks/Aktionen
- ECM-Dokumentation

### **Benötigte Tabellen:**
- ❌ `document_links` - **FEHLT**

### **Status:** ❌ **0% - Nicht implementiert**

---

## 📊 **Zusammenfassung:**

| Status | Services | Prozent |
|--------|----------|---------|
| ✅ **Vollständig** | 2 | 22% |
| ⚠️ **Teilweise** | 2 | 22% |
| ❌ **Fehlt** | 5 | 56% |

### **Funktionsfähig JETZT:**
- ✅ Flotten-Management (vehicles)
- ✅ Wartungs-Management (maintenance_tasks)
- ⚠️ Werkstatt-Aufträge (ohne Infrastruktur)
- ⚠️ Basis-Reports (ohne Kosten/Personal)

### **NICHT funktionsfähig:**
- ❌ Überführungen (transfer_service)
- ❌ Beschaffung (procurement_service)
- ❌ Finanzen (finance_service)
- ❌ Personal (hr_service)
- ❌ Dokumente (docs_service)

---

## 🎯 **Empfehlung:**

### **Phase 1: Kritische Tabellen (Priorität HOCH)**
1. `workshops` - Werkstatt-Stammdaten
2. `staff` - Personal-Stammdaten
3. `transfer_plans` - Überführungen

**Aufwand:** ~1 Stunde  
**Nutzen:** workshop_service + transfer_service + hr_service zu 50% funktionsfähig

### **Phase 2: Erweiterte Funktionen (Priorität MITTEL)**
4. `suppliers` - Lieferanten
5. `part_inventory` - Ersatzteile
6. `document_links` - Dokumente

**Aufwand:** ~1 Stunde  
**Nutzen:** procurement_service + docs_service funktionsfähig

### **Phase 3: Finanzen & Analytics (Priorität NIEDRIG)**
7. `invoices` - Rechnungen
8. `cost_centers` - Kostenstellen
9. Alle restlichen Tabellen

**Aufwand:** ~2 Stunden  
**Nutzen:** finance_service + vollständige Reports

---

**Erstellt:** 2025-11-25  
**Agent:** DeepALL Orchestrator  
**Vault Run:** VLT-20251125-007

