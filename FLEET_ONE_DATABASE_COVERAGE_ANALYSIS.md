# 🤖 FLEET-ONE Agent - Vollständige Datenbank-Abdeckungsanalyse

**Datum:** 2025-11-25  
**Zweck:** Detaillierte Analyse der Datenbank-Abdeckung für alle 9 FLEET-ONE Services  
**Frage:** "Ist das wirklich alles vollständig in der Datenbank?"

---

## 📊 **EXECUTIVE SUMMARY**

| Metrik | Wert | Status |
|--------|------|--------|
| **Dokumentierte Tabellen** | 27 | Aus Projekt-Historie |
| **Tatsächlich vorhanden** | 5 | In SQLite railfleet.db |
| **Fehlende Tabellen** | 22 | Nicht implementiert |
| **Gesamt-Abdeckung** | **18.5%** | ⚠️ **KRITISCH** |
| **Funktionsfähige Services** | 2 von 9 | ⚠️ **22%** |

---

## 🎯 **SERVICE-ÜBERSICHT**

| # | Service | Benötigte Tabellen | Vorhanden | Fehlend | Abdeckung | Status |
|---|---------|-------------------|-----------|---------|-----------|--------|
| 1 | **fleet_db** | 1 | ✅ 1 | - | **100%** | ✅ Vollständig |
| 2 | **maintenance_service** | 2 | ✅ 2 | - | **100%** | ✅ Vollständig |
| 3 | **workshop_service** | 4 | ⚠️ 1 | 3 | **25%** | ⚠️ Teilweise |
| 4 | **transfer_service** | 2 | ❌ 0 | 2 | **0%** | ❌ Fehlt |
| 5 | **procurement_service** | 4 | ❌ 0 | 4 | **0%** | ❌ Fehlt |
| 6 | **reporting_service** | * | ⚠️ - | - | **~20%** | ⚠️ Teilweise |
| 7 | **finance_service** | 3 | ❌ 0 | 3 | **0%** | ❌ Fehlt |
| 8 | **hr_service** | 2 | ❌ 0 | 2 | **0%** | ❌ Fehlt |
| 9 | **docs_service** | 1 | ❌ 0 | 1 | **0%** | ❌ Fehlt |

**\* reporting_service nutzt alle vorhandenen Tabellen für Aggregationen**

---

## 📋 **DETAILLIERTE SERVICE-ANALYSE**

### 1️⃣ **fleet_db** - ✅ **100% VOLLSTÄNDIG**

**Zweck:**
- Lok-Stammdaten (Fahrzeug-ID, Serie, Typ)
- Einsatzstatus (operational, maintenance, out_of_service)
- Standort, Kilometer, Kapazität

**Benötigte Tabellen:**
- ✅ `vehicles` (10 Einträge vorhanden)

**API-Endpunkte (FLEET-ONE):**
```python
fleet_db.get_locomotives(status=?, search=?)
fleet_db.get_locomotive(id)
fleet_db.patch_locomotive(id, status=?, planned_workshop_id=?)
```

**Status:** ✅ **Voll funktionsfähig**

**Beispiel-Use-Cases:**
- ✅ "Zeig mir alle Loks im Status 'operational'"
- ✅ "Setze Lok 185 123 auf Status 'in_maintenance'"
- ✅ "Welche Loks sind in München?"

---

### 2️⃣ **maintenance_service** - ✅ **100% VOLLSTÄNDIG**

**Zweck:**
- Wartungspläne (HU, Bremsprüfung, ECM)
- Fristen-Überwachung (due_date, is_overdue)
- Wartungsmaßnahmen (type, priority, status)

**Benötigte Tabellen:**
- ✅ `maintenance_tasks` (8 Einträge vorhanden)
- ✅ `workshop_orders` (6 Einträge vorhanden) - entspricht `work_orders`

**API-Endpunkte (FLEET-ONE):**
```python
maintenance_service.list_tasks(due_before=?, asset_id=?)
maintenance_service.create_task(locomotive_id, type, due_date)
```

**Status:** ✅ **Voll funktionsfähig**

**Beispiel-Use-Cases:**
- ✅ "Zeig mir alle Loks, die in den nächsten 30 Tagen zur HU müssen"
- ✅ "Erstelle eine Wartungsaufgabe für Lok 185 123"
- ✅ "Welche Wartungen sind überfällig?"

---

### 3️⃣ **workshop_service** - ⚠️ **NUR 25% FUNKTIONSFÄHIG**

**Zweck:**
- Werkstattaufträge (Planung, Status, Zeiten)
- Zuordnung zu Werkstätten
- Zuordnung zu Gleisen/Pits
- Team-Zuordnung

**Benötigte Tabellen:**
- ✅ `workshop_orders` (6 Einträge vorhanden)
- ❌ `workshops` - **FEHLT** (Werkstatt-Stammdaten: Name, Standort, Kapazität, Zertifizierungen)
- ❌ `tracks` - **FEHLT** (Gleise/Pits: track_id, workshop_id, capacity, certifications)
- ❌ `wo_assignment` - **FEHLT** (Zuordnung: work_order_id → track_id + team_id)

**API-Endpunkte (FLEET-ONE):**
```python
workshop_service.create_order(locomotive_id, workshop_id, planned_from, planned_to, tasks[])
workshop_service.update_order_status(id, status)
```

**Status:** ⚠️ **Nur Aufträge, keine Werkstatt-Infrastruktur**

**Funktioniert:**
- ✅ Werkstattaufträge erstellen
- ✅ Status aktualisieren

**Funktioniert NICHT:**
- ❌ Werkstatt-Auswahl (keine Werkstatt-Stammdaten)
- ❌ Gleis-Zuordnung (keine Gleise)
- ❌ Team-Zuordnung (keine Teams)
- ❌ Kapazitäts-Prüfung (keine Werkstatt-Kapazitäten)

**Beispiel-Use-Cases:**
- ⚠️ "Plane Werkstattauftrag bei Werkstatt München" → **Werkstatt existiert nicht in DB**
- ⚠️ "Weise Auftrag A-123 Gleis 3 zu" → **Gleise existieren nicht**
- ⚠️ "Welche Werkstätten haben freie Kapazität?" → **Keine Werkstatt-Daten**

---

### 4️⃣ **transfer_service** - ❌ **0% - FEHLT KOMPLETT**

**Zweck:**
- Überführungsfahrten (Lok-Bewegungen zwischen Standorten)
- Zeitfenster (window_start, window_end)
- Personaleinsatz für Überführungen
- Qualifikations-Matching (team_skill)

**Benötigte Tabellen:**
- ❌ `transfer_plans` - **FEHLT**
  - Felder: id, plan_id, vehicle_id, from_location, to_location, window_start, window_end, team_skill, status, assigned_staff_id
- ❌ `staff` - **FEHLT**
  - Felder: id, employee_id, name, qualifications[], availability, shift_start, shift_end, is_active

**API-Endpunkte (FLEET-ONE):**
```python
transfer_service.plan_transfer(locomotive_id, from, to, window_start, window_end, team_skill)
```

**Status:** ❌ **Nicht implementiert - Service kann nicht funktionieren**

**Beispiel-Use-Cases:**
- ❌ "Plane Überführung von Lok 185 123 von München nach Berlin"
- ❌ "Welche Überführungen sind für nächste Woche geplant?"
- ❌ "Weise Fahrer Schmidt der Überführung T-456 zu"

---

### 5️⃣ **procurement_service** - ❌ **0% - FEHLT KOMPLETT**

**Zweck:**
- Teilebedarf aus Werkstattaufträgen
- Bestellanforderungen
- Lieferanten-Management
- Lagerbestand-Prüfung

**Benötigte Tabellen:**
- ❌ `suppliers` - **FEHLT**
  - Felder: id, supplier_code, name, contact_email, payment_terms, is_active
- ❌ `purchase_orders` - **FEHLT**
  - Felder: id, po_number, supplier_id, order_date, delivery_date, status, total_amount
- ❌ `purchase_order_lines` - **FEHLT**
  - Felder: id, po_id, part_no, quantity, unit_price, total_price
- ❌ `part_inventory` - **FEHLT**
  - Felder: id, part_no, description, quantity_available, quantity_reserved, min_stock, supplier_id

**API-Endpunkte (FLEET-ONE):**
```python
procurement_service.request_purchase(part_no, qty, needed_by, related_wo_id=?)
procurement_service.get_stock(part_no)
```

**Status:** ❌ **Nicht implementiert - Service kann nicht funktionieren**

**Beispiel-Use-Cases:**
- ❌ "Prüfe Lagerbestand für Bremsbeläge"
- ❌ "Erstelle Bestellung für 10x Bremsbeläge bei Lieferant XYZ"
- ❌ "Welche Teile sind unter Mindestbestand?"

---

### 6️⃣ **reporting_service** - ⚠️ **~20% FUNKTIONSFÄHIG**

**Zweck:**
- Aggregierte Kennzahlen (KPIs)
- Verfügbarkeits-Reports
- Einsatzzeiten-Analysen
- Kosten-Reports

**Benötigte Tabellen:**
- ⚠️ Nutzt **alle vorhandenen Tabellen** für Aggregationen
- ✅ `vehicles` → Verfügbarkeit
- ✅ `maintenance_tasks` → Wartungs-Backlog
- ✅ `workshop_orders` → Werkstatt-Auslastung
- ❌ `invoices` → Kosten-Analysen **FEHLT**
- ❌ `part_inventory` → Teile-Verbrauch **FEHLT**

**API-Endpunkte (FLEET-ONE):**
```python
reporting_service.kpi_availability(from, to)
reporting_service.kpi_costs(from, to, asset_id=?)
```

**Status:** ⚠️ **Basis-Reports möglich, erweiterte Reports fehlen**

**Funktioniert:**
- ✅ Verfügbarkeits-KPI (basierend auf vehicles.status)
- ✅ Wartungs-Backlog (basierend auf maintenance_tasks)

**Funktioniert NICHT:**
- ❌ Kosten-Reports (keine Rechnungs-Daten)
- ❌ Teile-Verbrauch (keine Inventory-Daten)
- ❌ Personal-Auslastung (keine Staff-Daten)

---

### 7️⃣ **finance_service** - ❌ **0% - FEHLT KOMPLETT**

**Zweck:**
- Eingangsrechnungen erfassen
- Kostenstellen-Zuordnung
- Budget-Überwachung
- Verknüpfung zu Werkstattaufträgen

**Benötigte Tabellen:**
- ❌ `invoices` - **FEHLT**
- ❌ `cost_centers` - **FEHLT**
- ❌ `budget_allocations` - **FEHLT**

**API-Endpunkte (FLEET-ONE):**
```python
finance_service.create_invoice(invoice_number, supplier, amount, currency, related_workshop_order_id=?)
```

**Status:** ❌ **Nicht implementiert**

---

### 8️⃣ **hr_service** - ❌ **0% - FEHLT KOMPLETT**

**Zweck:**
- Mitarbeiter-Stammdaten
- Verfügbarkeiten, Schichten
- Qualifikationen (Fahrer, Mechaniker, etc.)
- Personaleinsatzplanung

**Benötigte Tabellen:**
- ❌ `staff` - **FEHLT**
- ❌ `staff_assignments` - **FEHLT**

**API-Endpunkte (FLEET-ONE):**
```python
hr_service.list_staff(skill=?)
hr_service.assign_transfer(staff_id, locomotive_id, transfer_id, from, to)
```

**Status:** ❌ **Nicht implementiert**

---

### 9️⃣ **docs_service** - ❌ **0% - FEHLT KOMPLETT**

**Zweck:**
- Dokumente (Zulassungen, Berichte, Protokolle)
- Gültigkeits-Überwachung (valid_until)
- Verknüpfungen zu Loks/Aktionen
- ECM-Dokumentation

**Benötigte Tabellen:**
- ❌ `document_links` - **FEHLT**

**API-Endpunkte (FLEET-ONE):**
```python
docs_service.link_document(asset_id, doc_type, doc_id, valid_until=?)
docs_service.list_expiring(before)
```

**Status:** ❌ **Nicht implementiert**

---

## 🚨 **KRITISCHE LÜCKEN**

### **Was funktioniert NICHT:**
1. ❌ **Werkstatt-Auswahl** → Keine Werkstatt-Stammdaten
2. ❌ **Überführungen** → Keine Transfer-Planung möglich
3. ❌ **Beschaffung** → Keine Teile-Bestellungen
4. ❌ **Finanzen** → Keine Rechnungs-Erfassung
5. ❌ **Personal** → Keine Mitarbeiter-Planung
6. ❌ **Dokumente** → Keine Dokumenten-Verwaltung

### **Auswirkung auf FLEET-ONE:**
- **7 von 9 Services** sind **nicht funktionsfähig**
- **Nur 2 Services** (fleet_db, maintenance_service) arbeiten vollständig
- **FLEET-ONE kann nur 22% seiner Funktionen ausführen**

---

## 🎯 **HANDLUNGSEMPFEHLUNGEN**

### **PHASE 1: Kritische Tabellen (PRIORITÄT: HOCH)**

**Ziel:** workshop_service, transfer_service, hr_service zu 50-75% funktionsfähig machen

| # | Tabelle | Zweck | Aufwand | Nutzen |
|---|---------|-------|---------|--------|
| 1 | `workshops` | Werkstatt-Stammdaten | 15 Min | workshop_service → 50% |
| 2 | `staff` | Personal-Stammdaten | 15 Min | hr_service → 50%, transfer_service → 50% |
| 3 | `transfer_plans` | Überführungs-Planung | 20 Min | transfer_service → 100% |

**Gesamt-Aufwand:** ~50 Minuten
**Ergebnis:** 5 von 9 Services funktionsfähig (55%)

---

### **PHASE 2: Erweiterte Funktionen (PRIORITÄT: MITTEL)**

**Ziel:** procurement_service, docs_service funktionsfähig machen

| # | Tabelle | Zweck | Aufwand | Nutzen |
|---|---------|-------|---------|--------|
| 4 | `suppliers` | Lieferanten | 10 Min | procurement_service → 25% |
| 5 | `part_inventory` | Ersatzteile-Lager | 20 Min | procurement_service → 75% |
| 6 | `document_links` | Dokumenten-Verwaltung | 15 Min | docs_service → 100% |

**Gesamt-Aufwand:** ~45 Minuten
**Ergebnis:** 7 von 9 Services funktionsfähig (77%)

---

### **PHASE 3: Vollständige Implementierung (PRIORITÄT: NIEDRIG)**

**Ziel:** Alle Services zu 100% funktionsfähig

| # | Tabelle | Zweck | Aufwand | Nutzen |
|---|---------|-------|---------|--------|
| 7 | `tracks` | Werkstatt-Gleise | 15 Min | workshop_service → 75% |
| 8 | `wo_assignment` | Zuordnungen | 10 Min | workshop_service → 100% |
| 9 | `purchase_orders` | Bestellungen | 20 Min | procurement_service → 100% |
| 10 | `invoices` | Rechnungen | 20 Min | finance_service → 75% |
| 11 | `cost_centers` | Kostenstellen | 10 Min | finance_service → 100% |
| 12 | `staff_assignments` | Personal-Einsätze | 15 Min | hr_service → 100% |

**Gesamt-Aufwand:** ~90 Minuten
**Ergebnis:** 9 von 9 Services zu 100% funktionsfähig

---

### **GESAMT-AUFWAND:**

| Phase | Tabellen | Aufwand | Services funktionsfähig |
|-------|----------|---------|-------------------------|
| **Aktuell** | 5 | - | 2 von 9 (22%) |
| **Phase 1** | +3 | 50 Min | 5 von 9 (55%) |
| **Phase 2** | +3 | 45 Min | 7 von 9 (77%) |
| **Phase 3** | +6 | 90 Min | 9 von 9 (100%) |
| **GESAMT** | **17** | **~3 Stunden** | **100%** |

---

## 📝 **NÄCHSTE SCHRITTE**

**Sofort-Maßnahmen:**

1. **Entscheidung treffen:**
   - Option A: Mit 5 Tabellen weiterarbeiten (nur 22% funktionsfähig)
   - Option B: Phase 1 implementieren (50 Min → 55% funktionsfähig)
   - Option C: Vollständig implementieren (3h → 100% funktionsfähig)

2. **Wenn Phase 1 gewählt:**
   ```bash
   # Alembic Migrations erstellen
   alembic revision -m "Add workshops, staff, transfer_plans tables"

   # Migration ausführen
   alembic upgrade head

   # Testdaten einfügen
   python scripts/seed_critical_tables.py
   ```

3. **Database Agent aktualisieren:**
   - `validate_schema()` erweitern für neue Tabellen
   - Neue Statistiken hinzufügen

4. **FLEET-ONE testen:**
   - Use-Case "HU Planning" mit Werkstatt-Auswahl
   - Use-Case "Transfer Planning" mit Personal-Zuordnung

---

**Erstellt:** 2025-11-25
**Agent:** DeepALL Orchestrator
**Vault Run:** VLT-20251125-007

