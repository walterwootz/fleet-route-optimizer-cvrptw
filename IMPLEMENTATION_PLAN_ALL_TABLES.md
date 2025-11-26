# 🚀 Implementierungsplan: Alle fehlenden Tabellen

**Datum:** 2025-11-25  
**Ziel:** Vollständige Datenbank-Implementierung für FLEET-ONE (100% Abdeckung)  
**Status:** PLANUNG

---

## 📊 **ÜBERSICHT**

| Phase | Tabellen | Aufwand | Services | Priorität |
|-------|----------|---------|----------|-----------|
| **Aktuell** | 5 | - | 2/9 (22%) | - |
| **Phase 1** | +3 | 50 Min | 5/9 (55%) | 🔴 HOCH |
| **Phase 2** | +3 | 45 Min | 7/9 (77%) | 🟡 MITTEL |
| **Phase 3** | +6 | 90 Min | 9/9 (100%) | 🟢 NIEDRIG |
| **Phase 4** | +10 | 120 Min | Event Sourcing/CRDT | 🔵 OPTIONAL |
| **GESAMT** | **27** | **~5h** | **100%** | - |

---

## 🎯 **PHASE 1: KRITISCHE TABELLEN (PRIORITÄT: HOCH)**

### **Ziel:** Basis-Services funktionsfähig machen

### **1. workshops** (Werkstatt-Stammdaten)

**Zweck:** Werkstätten mit Kapazitäten, Zertifizierungen, Standorten

**Felder:**
```sql
CREATE TABLE workshops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,           -- z.B. "WS-MUENCHEN"
    name VARCHAR(200) NOT NULL,                 -- z.B. "Werkstatt München"
    location VARCHAR(255) NOT NULL,             -- Standort
    contact_person VARCHAR(200),
    phone VARCHAR(50),
    email VARCHAR(255),
    total_tracks INTEGER NOT NULL DEFAULT 1,    -- Anzahl Gleise
    available_tracks INTEGER NOT NULL DEFAULT 1,
    is_ecm_certified BOOLEAN DEFAULT FALSE,
    specializations JSONB,                      -- ["electric", "diesel"]
    supported_vehicle_types JSONB,              -- ["BR185", "BR189"]
    rating FLOAT,                               -- 0-5
    total_completed_orders INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workshops_code ON workshops(code);
CREATE INDEX idx_workshops_location ON workshops(location);
CREATE INDEX idx_workshops_active ON workshops(is_active);
```

**Model:** `src/models/railfleet/workshop.py` → `class Workshop(Base)` ✅ **EXISTIERT BEREITS**

**Testdaten:**
- WS-MUENCHEN (München, 5 Gleise, ECM-zertifiziert)
- WS-BERLIN (Berlin, 3 Gleise)
- WS-HAMBURG (Hamburg, 4 Gleise, ECM-zertifiziert)

**Aufwand:** 15 Minuten

---

### **2. staff** (Personal-Stammdaten)

**Zweck:** Mitarbeiter mit Qualifikationen, Verfügbarkeiten, Schichten

**Felder:**
```sql
CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(50) UNIQUE NOT NULL,    -- z.B. "EMP-001"
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(50) NOT NULL,                  -- driver, mechanic, electrician, inspector
    qualifications JSONB NOT NULL,              -- ["BR185", "BR189", "electric"]
    certifications JSONB,                       -- ["ECM", "Safety"]
    shift_start TIME,                           -- z.B. 08:00
    shift_end TIME,                             -- z.B. 16:00
    availability_status VARCHAR(50) DEFAULT 'available',  -- available, on_leave, sick, assigned
    current_location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_staff_employee_id ON staff(employee_id);
CREATE INDEX idx_staff_role ON staff(role);
CREATE INDEX idx_staff_active ON staff(is_active);
CREATE INDEX idx_staff_availability ON staff(availability_status);
```

**Model:** `src/models/railfleet/hr.py` → `class Staff(Base)` ✅ **EXISTIERT BEREITS**

**Testdaten:**
- Schmidt, Hans (Fahrer, BR185/BR189)
- Müller, Anna (Mechaniker, Electric)
- Weber, Klaus (Elektriker, ECM-zertifiziert)

**Aufwand:** 15 Minuten

---

### **3. transfer_plans** (Überführungs-Planung)

**Zweck:** Lok-Überführungen zwischen Standorten mit Zeitfenstern

**Felder:**
```sql
CREATE TABLE transfer_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id VARCHAR(50) UNIQUE NOT NULL,        -- z.B. "TRF-2025-001"
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    from_location VARCHAR(100) NOT NULL,
    to_location VARCHAR(100) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    required_skill VARCHAR(50),                 -- z.B. "BR185"
    priority VARCHAR(20) DEFAULT 'normal',      -- low, normal, high, urgent
    status VARCHAR(50) DEFAULT 'planned',       -- planned, in_progress, completed, cancelled
    assigned_staff_id UUID REFERENCES staff(id),
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    distance_km INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transfer_vehicle ON transfer_plans(vehicle_id);
CREATE INDEX idx_transfer_status ON transfer_plans(status);
CREATE INDEX idx_transfer_window ON transfer_plans(window_start, window_end);
CREATE INDEX idx_transfer_assigned ON transfer_plans(assigned_staff_id);
```

**Model:** `src/models/railfleet/transfer.py` → `class TransferPlan(Base)` ✅ **EXISTIERT BEREITS**

**Testdaten:**
- TRF-2025-001 (185 123: München → Berlin)
- TRF-2025-002 (185 456: Berlin → Hamburg)

**Aufwand:** 20 Minuten

---

**PHASE 1 GESAMT:**
- **Tabellen:** 3
- **Aufwand:** 50 Minuten
- **Ergebnis:** 5 von 9 Services funktionsfähig (55%)
- **Use-Cases:** UC1, UC3, UC6, UC8, UC9 funktionieren

---

## 🎯 **PHASE 2: ERWEITERTE FUNKTIONEN (PRIORITÄT: MITTEL)**

### **4. suppliers** (Lieferanten)

**Felder:**
```sql
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    payment_terms VARCHAR(100),                 -- z.B. "30 Tage netto"
    rating FLOAT,                               -- 0-5
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Aufwand:** 10 Minuten

---

### **5. part_inventory** (Ersatzteile-Lager)

**Felder:**
```sql
CREATE TABLE part_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_no VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),                      -- brake, electric, mechanical
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    unit_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    supplier_id UUID REFERENCES suppliers(id),
    location_code VARCHAR(50),
    last_restocked TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Aufwand:** 20 Minuten

---

### **6. document_links** (Dokumenten-Verwaltung)

**Felder:**
```sql
CREATE TABLE document_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(100) UNIQUE NOT NULL,
    asset_id UUID,                              -- vehicle_id, staff_id, etc.
    asset_type VARCHAR(50),                     -- vehicle, staff, workshop
    doc_type VARCHAR(50) NOT NULL,              -- certificate, license, inspection_report
    doc_url TEXT NOT NULL,
    file_hash VARCHAR(64),                      -- SHA-256
    valid_from DATE,
    valid_until DATE,
    is_expired BOOLEAN DEFAULT FALSE,
    reminder_days_before INTEGER DEFAULT 30,
    access_level VARCHAR(20) DEFAULT 'internal', -- public, internal, restricted
    tags JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Aufwand:** 15 Minuten

---

**PHASE 2 GESAMT:**
- **Tabellen:** 3
- **Aufwand:** 45 Minuten
- **Ergebnis:** 7 von 9 Services funktionsfähig (77%)

---

## 🎯 **PHASE 3: VOLLSTÄNDIGE IMPLEMENTIERUNG (PRIORITÄT: NIEDRIG)**

### **7-12. Restliche Tabellen**

7. `tracks` - Werkstatt-Gleise (15 Min)
8. `wo_assignment` - Zuordnungen WO → Track + Team (10 Min)
9. `purchase_orders` - Bestellungen (20 Min)
10. `purchase_order_lines` - Bestellpositionen (10 Min)
11. `invoices` - Rechnungen (20 Min)
12. `cost_centers` - Kostenstellen (10 Min)
13. `staff_assignments` - Personal-Einsätze (15 Min)

**PHASE 3 GESAMT:**
- **Tabellen:** 7
- **Aufwand:** 100 Minuten
- **Ergebnis:** 9 von 9 Services zu 100% funktionsfähig

---

## 📝 **IMPLEMENTIERUNGS-SCHRITTE**

Siehe: `IMPLEMENTATION_STEPS.md`

**Erstellt:** 2025-11-25  
**Agent:** DeepALL Orchestrator

