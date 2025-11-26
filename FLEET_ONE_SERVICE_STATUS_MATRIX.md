# 🤖 FLEET-ONE Service Status Matrix

**Datum:** 2025-11-25  
**Zweck:** Visuelle Übersicht der Service-Funktionsfähigkeit

---

## 📊 **SERVICE-TABELLEN-MATRIX**

| Service | Tabelle 1 | Tabelle 2 | Tabelle 3 | Tabelle 4 | Abdeckung | Status |
|---------|-----------|-----------|-----------|-----------|-----------|--------|
| **1. fleet_db** | ✅ vehicles | - | - | - | **100%** | ✅ |
| **2. maintenance_service** | ✅ maintenance_tasks | ✅ workshop_orders | - | - | **100%** | ✅ |
| **3. workshop_service** | ✅ workshop_orders | ❌ workshops | ❌ tracks | ❌ wo_assignment | **25%** | ⚠️ |
| **4. transfer_service** | ❌ transfer_plans | ❌ staff | - | - | **0%** | ❌ |
| **5. procurement_service** | ❌ suppliers | ❌ purchase_orders | ❌ po_lines | ❌ part_inventory | **0%** | ❌ |
| **6. reporting_service** | ⚠️ (alle Tabellen) | - | - | - | **~20%** | ⚠️ |
| **7. finance_service** | ❌ invoices | ❌ cost_centers | ❌ budget_allocations | - | **0%** | ❌ |
| **8. hr_service** | ❌ staff | ❌ staff_assignments | - | - | **0%** | ❌ |
| **9. docs_service** | ❌ document_links | - | - | - | **0%** | ❌ |

**Legende:**
- ✅ = Tabelle vorhanden und funktionsfähig
- ❌ = Tabelle fehlt
- ⚠️ = Teilweise vorhanden

---

## 🎯 **FUNKTIONSFÄHIGKEIT PRO USE-CASE**

| Use-Case | Beschreibung | Benötigte Services | Status | Blockiert durch |
|----------|--------------|-------------------|--------|-----------------|
| **UC1: HU Planning** | Loks zur HU planen → Werkstatt | maintenance_service, workshop_service | ⚠️ **50%** | Fehlende `workshops` Tabelle |
| **UC2: Parts Procurement** | Teilebedarf prüfen & bestellen | procurement_service | ❌ **0%** | Alle Procurement-Tabellen fehlen |
| **UC3: Transfer Staff** | Personal für Überführungen | transfer_service, hr_service | ❌ **0%** | `transfer_plans`, `staff` fehlen |
| **UC4: Invoice Entry** | Rechnung erfassen & zuordnen | finance_service | ❌ **0%** | Alle Finance-Tabellen fehlen |
| **UC5: Documents** | Dokumente verknüpfen & überwachen | docs_service | ❌ **0%** | `document_links` fehlt |
| **UC6: Vehicle Status** | Lok-Status aktualisieren | fleet_db | ✅ **100%** | - |
| **UC8: Availability Report** | Verfügbarkeits-KPI | reporting_service | ⚠️ **50%** | Fehlende Kosten-/Inventory-Daten |
| **UC9: Maintenance Task** | Wartungsaufgabe erstellen | maintenance_service | ✅ **100%** | - |

**Zusammenfassung:**
- ✅ **2 Use-Cases** voll funktionsfähig (UC6, UC9)
- ⚠️ **2 Use-Cases** teilweise funktionsfähig (UC1, UC8)
- ❌ **4 Use-Cases** nicht funktionsfähig (UC2, UC3, UC4, UC5)

---

## 📈 **IMPLEMENTIERUNGS-FORTSCHRITT**

### **Aktueller Stand:**

```
Tabellen:     [████████░░░░░░░░░░░░░░░░░░] 5/27  (18.5%)
Services:     [████░░░░░░░░░░░░░░░░░░░░░░] 2/9   (22%)
Use-Cases:    [████░░░░░░░░░░░░░░░░░░░░░░] 2/8   (25%)
```

### **Nach Phase 1 (+ 50 Min):**

```
Tabellen:     [████████████████░░░░░░░░░░] 8/27  (30%)
Services:     [████████████░░░░░░░░░░░░░░] 5/9   (55%)
Use-Cases:    [████████████░░░░░░░░░░░░░░] 5/8   (62%)
```

### **Nach Phase 2 (+ 45 Min):**

```
Tabellen:     [████████████████████░░░░░░] 11/27 (41%)
Services:     [████████████████████░░░░░░] 7/9   (77%)
Use-Cases:    [████████████████████░░░░░░] 6/8   (75%)
```

### **Nach Phase 3 (+ 90 Min):**

```
Tabellen:     [██████████████████████████] 17/27 (63%)
Services:     [██████████████████████████] 9/9   (100%)
Use-Cases:    [██████████████████████████] 8/8   (100%)
```

---

## 🚨 **KRITISCHE ABHÄNGIGKEITEN**

### **Blockierte Features:**

1. **Werkstatt-Auswahl** → Blockiert durch fehlende `workshops` Tabelle
   - Betrifft: UC1 (HU Planning)
   - Auswirkung: Kann keine Werkstatt auswählen, nur generische Aufträge

2. **Überführungs-Planung** → Blockiert durch fehlende `transfer_plans` + `staff`
   - Betrifft: UC3 (Transfer Staff)
   - Auswirkung: Keine Lok-Bewegungen planbar

3. **Beschaffung** → Blockiert durch fehlende `suppliers`, `purchase_orders`, `part_inventory`
   - Betrifft: UC2 (Parts Procurement)
   - Auswirkung: Keine Teile-Bestellungen möglich

4. **Rechnungs-Erfassung** → Blockiert durch fehlende `invoices`, `cost_centers`
   - Betrifft: UC4 (Invoice Entry)
   - Auswirkung: Keine Finanz-Verwaltung

5. **Dokumenten-Verwaltung** → Blockiert durch fehlende `document_links`
   - Betrifft: UC5 (Documents)
   - Auswirkung: Keine ECM-Dokumentation

---

## 💡 **EMPFEHLUNG**

### **Für Produktiv-Einsatz:**

**Minimum:** Phase 1 implementieren (50 Min)
- Ermöglicht 5 von 9 Services (55%)
- Ermöglicht 5 von 8 Use-Cases (62%)
- Kritische Funktionen: Werkstatt-Auswahl, Überführungen, Personal

**Optimal:** Phase 1 + Phase 2 implementieren (95 Min)
- Ermöglicht 7 von 9 Services (77%)
- Ermöglicht 6 von 8 Use-Cases (75%)
- Zusätzlich: Beschaffung, Dokumente

**Vollständig:** Alle 3 Phasen (3 Stunden)
- Ermöglicht 9 von 9 Services (100%)
- Ermöglicht 8 von 8 Use-Cases (100%)
- Produktionsreif für alle FLEET-ONE Funktionen

---

## 📋 **QUICK-START GUIDE**

### **Option 1: Minimale Erweiterung (Phase 1)**

```bash
# 1. Migration erstellen
alembic revision -m "Add critical tables: workshops, staff, transfer_plans"

# 2. Migration ausführen
alembic upgrade head

# 3. Testdaten einfügen
python scripts/seed_phase1_tables.py

# 4. Database Agent testen
python scripts/test_database_agent.py

# 5. FLEET-ONE Use-Cases testen
curl -X POST http://localhost:8080/api/v1/fleet-one/use-case/hu_planning \
  -H "Content-Type: application/json" \
  -d '{"workshop_id": "WS-MUENCHEN", "days_ahead": 30, "user_role": "dispatcher"}'
```

### **Option 2: Mit aktuellen 5 Tabellen weiterarbeiten**

```bash
# Nur Basis-Funktionen nutzen:
# - fleet_db (Lok-Stammdaten)
# - maintenance_service (Wartungsaufgaben)
# - Eingeschränkter workshop_service (nur Aufträge, keine Werkstätten)

# FLEET-ONE Use-Cases die funktionieren:
# - UC6: Vehicle Status
# - UC9: Maintenance Task
```

---

**Erstellt:** 2025-11-25  
**Agent:** DeepALL Orchestrator  
**Vault Run:** VLT-20251125-008

