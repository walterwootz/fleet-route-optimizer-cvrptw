# FLEET-ONE Demo Scenarios Walkthrough

**Version**: 1.0.0
**Sprache**: Deutsch (User Queries & Responses)
**Zweck**: Praktische Demonstration aller FLEET-ONE Features

## Inhaltsverzeichnis

1. [Setup](#setup)
2. [Szenario 1: HU-Planung für Werkstatt](#szenario-1-hu-planung-für-werkstatt)
3. [Szenario 2: Teile-Beschaffung mit Bestandsprüfung](#szenario-2-teile-beschaffung-mit-bestandsprüfung)
4. [Szenario 3: Personal für Überführungen planen](#szenario-3-personal-für-überführungen-planen)
5. [Szenario 4: Rechnungen erfassen und zuordnen](#szenario-4-rechnungen-erfassen-und-zuordnen)
6. [Szenario 5: Dokumenten-Management](#szenario-5-dokumenten-management)
7. [Szenario 6: Fahrzeugstatus abfragen](#szenario-6-fahrzeugstatus-abfragen)
8. [Szenario 7: Verfügbarkeitsbericht generieren](#szenario-7-verfügbarkeitsbericht-generieren)
9. [Szenario 8: Wartungsaufgabe erstellen](#szenario-8-wartungsaufgabe-erstellen)
10. [Szenario 9: RBAC & Fehlerbehandlung](#szenario-9-rbac--fehlerbehandlung)
11. [Szenario 10: Multi-Mode-Konversation](#szenario-10-multi-mode-konversation)

---

## Setup

### 1. Backend starten

```bash
# Terminal 1: Backend-Services
cd fleet-route-optimizer-cvrptw
uvicorn src.app:app --reload --port 8000

# Warte auf: "Application startup complete"
```

### 2. Session erstellen

```bash
# Terminal 2: Test-Client
curl -X POST "http://localhost:8000/api/v1/fleet-one/session" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_dispatcher",
    "user_role": "dispatcher"
  }'

# Response:
# {
#   "session_id": "sess_demo_123",
#   "user_id": "demo_dispatcher",
#   "user_role": "dispatcher",
#   "created_at": "2025-11-24T10:00:00Z"
# }
```

**Wichtig**: Speichern Sie die `session_id` für nachfolgende Abfragen.

### 3. Health Check

```bash
curl http://localhost:8000/api/v1/fleet-one/health

# Expected: {"status": "healthy", "agent_version": "1.0.0", ...}
```

---

## Szenario 1: HU-Planung für Werkstatt

### Kontext

**Rolle**: `dispatcher` (Disponent)
**Modus**: `WORKSHOP`
**Use Case**: UC1 - HU/Fristen planen → Werkstatt

**Situation**: Es ist Montagmorgen. Der Disponent will alle HU-Fristen der nächsten 14 Tage prüfen und Werkstattaufträge für das Werk München planen.

---

### Demo-Ablauf

#### Schritt 1: HU-Fristen abfragen

**User-Abfrage**:
```
Welche HU-Fristen laufen in den nächsten 14 Tagen ab?
```

**API-Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_demo_123",
    "user_id": "demo_dispatcher",
    "user_role": "dispatcher",
    "query": "Welche HU-Fristen laufen in den nächsten 14 Tagen ab?"
  }'
```

**Agent-Verarbeitung**:
```
1. Mode Detection → MAINTENANCE (Keywords: "HU", "Fristen", "ablaufen")
   Confidence: 0.98

2. RBAC Check → ✅ dispatcher hat Berechtigung "plan:read"

3. Tool Calls:
   - list_maintenance_tasks(due_before=2025-12-08)
     → Backend: GET /api/v1/maintenance/tasks?due_before=2025-12-08

4. Backend Response:
   {
     "tasks": [
       {
         "id": "TASK-001",
         "locomotive_id": "BR185-042",
         "type": "HU",
         "due_date": "2025-12-05",
         "status": "pending"
       },
       {
         "id": "TASK-002",
         "locomotive_id": "BR189-033",
         "type": "HU",
         "due_date": "2025-12-10",
         "status": "pending"
       },
       {
         "id": "TASK-003",
         "locomotive_id": "BR152-123",
         "type": "Bremsprüfung",
         "due_date": "2025-12-07",
         "status": "pending"
       }
     ]
   }

5. Response Generation (German):
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "In den nächsten 14 Tagen laufen 3 Fristen ab:\n\n1. BR185-042 - HU fällig am 05.12.2025\n2. BR189-033 - HU fällig am 10.12.2025\n3. BR152-123 - Bremsprüfung fällig am 07.12.2025\n\nSoll ich Werkstattaufträge für diese Fahrzeuge erstellen?",
  "session_id": "sess_demo_123",
  "mode": "MAINTENANCE",
  "mode_confidence": 0.98,
  "data": {
    "tasks": [
      {"id": "TASK-001", "locomotive_id": "BR185-042", "type": "HU", "due_date": "2025-12-05"},
      {"id": "TASK-002", "locomotive_id": "BR189-033", "type": "HU", "due_date": "2025-12-10"},
      {"id": "TASK-003", "locomotive_id": "BR152-123", "type": "Bremsprüfung", "due_date": "2025-12-07"}
    ]
  },
  "timestamp": "2025-11-24T10:01:23Z"
}
```

---

#### Schritt 2: Werkstattaufträge erstellen

**User-Abfrage** (Follow-up):
```
Ja, erstelle Werkstattaufträge für alle drei Fahrzeuge im Werk München
```

**Agent-Verarbeitung**:
```
1. Mode Detection → WORKSHOP (Keywords: "Werkstattaufträge", "Werk")
   Confidence: 0.95

2. Context: Agent merkt sich die 3 Fahrzeuge aus vorheriger Abfrage

3. RBAC Check → ✅ dispatcher hat Berechtigung "wo:create"

4. Tool Calls (für jedes Fahrzeug):

   A) BR185-042:
      - create_workshop_order(
          locomotive_id="BR185-042",
          workshop_id="WERK-MUC",
          planned_start="2025-12-05T08:00:00",
          planned_end="2025-12-06T16:00:00",
          tasks=["HU", "Bremsprüfung"]
        )
      → Backend: POST /api/v1/workshop/orders
      → Response: {"id": "WO-12345", "status": "planned"}

      - patch_locomotive(
          locomotive_id="BR185-042",
          status="planned_for_workshop"
        )
      → Backend: PATCH /api/v1/fleet/locomotives/BR185-042
      → Response: {"id": "BR185-042", "status": "planned_for_workshop"}

   B) BR189-033:
      [ähnliche Calls...]
      → WO-12346

   C) BR152-123:
      [ähnliche Calls...]
      → WO-12347
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "✅ Werkstattaufträge erstellt:\n\n1. WO-12345: BR185-042 im Werk München\n   Geplant: 05.12.2025 08:00 - 06.12.2025 16:00 Uhr\n   Aufgaben: HU, Bremsprüfung\n\n2. WO-12346: BR189-033 im Werk München\n   Geplant: 10.12.2025 08:00 - 11.12.2025 16:00 Uhr\n   Aufgaben: HU, Bremsprüfung\n\n3. WO-12347: BR152-123 im Werk München\n   Geplant: 07.12.2025 08:00 - 07.12.2025 16:00 Uhr\n   Aufgaben: Bremsprüfung\n\nAlle Fahrzeuge wurden auf Status 'planned_for_workshop' gesetzt.",
  "session_id": "sess_demo_123",
  "mode": "WORKSHOP",
  "mode_confidence": 0.95,
  "data": {
    "workshop_orders": [
      {"id": "WO-12345", "locomotive_id": "BR185-042", "status": "planned"},
      {"id": "WO-12346", "locomotive_id": "BR189-033", "status": "planned"},
      {"id": "WO-12347", "locomotive_id": "BR152-123", "status": "planned"}
    ]
  },
  "timestamp": "2025-11-24T10:02:45Z"
}
```

**Event Sourcing**:
```json
{
  "aggregate_type": "FleetOneAgent",
  "aggregate_id": "sess_demo_123",
  "event_type": "WorkshopOrdersCreated",
  "data": {
    "user_id": "demo_dispatcher",
    "user_role": "dispatcher",
    "order_ids": ["WO-12345", "WO-12346", "WO-12347"],
    "workshop_id": "WERK-MUC"
  },
  "timestamp": "2025-11-24T10:02:45Z"
}
```

---

## Szenario 2: Teile-Beschaffung mit Bestandsprüfung

### Kontext

**Rolle**: `procurement` (Beschaffung)
**Modus**: `PROCUREMENT`
**Use Case**: UC2 - Teile-Beschaffung prüfen & bestellen

**Situation**: Die Werkstatt braucht Bremsscheiben für WO-12345. Der Beschaffungsmitarbeiter prüft den Lagerbestand und bestellt bei Bedarf nach.

---

### Demo-Ablauf

#### Schritt 1: Bestand prüfen

**User-Abfrage**:
```
Prüfe Bestand von Teil P-45678 (Bremsscheiben). Wir brauchen 50 Stück für WO-12345 bis 2025-12-15
```

**API-Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/fleet-one/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_demo_456",
    "user_id": "demo_procurement",
    "user_role": "procurement",
    "query": "Prüfe Bestand von Teil P-45678 (Bremsscheiben). Wir brauchen 50 Stück für WO-12345 bis 2025-12-15"
  }'
```

**Agent-Verarbeitung**:
```
1. Mode Detection → PROCUREMENT (Keywords: "Bestand", "Teil", "brauchen")
   Confidence: 0.97

2. RBAC Check → ✅ procurement hat Berechtigung "parts:stock"

3. Tool Calls:
   A) get_stock(part_no="P-45678")
      → Backend: GET /api/v1/procurement/stock/P-45678
      → Response: {
           "part_no": "P-45678",
           "description": "Bremsscheibe 330mm",
           "available": 12,
           "reserved": 5,
           "free": 7,
           "reorder_level": 20
         }

   B) Analyse: free (7) < required (50) → Bestellung nötig

   C) request_purchase(
        part_no="P-45678",
        qty=50,
        needed_by="2025-12-15",
        related_wo_id="WO-12345",
        supplier="DEFAULT"
      )
      → Backend: POST /api/v1/procurement/purchase-requests
      → Response: {
           "id": "PR-6789",
           "part_no": "P-45678",
           "qty": 50,
           "status": "pending",
           "estimated_delivery": "2025-12-12"
         }
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "📦 Lagerbestand für Teil P-45678 (Bremsscheibe 330mm):\n\n✅ Verfügbar: 12 Stück\n⚠️  Reserviert: 5 Stück\n🔴 Frei: 7 Stück\n\nBenötigt: 50 Stück → ❌ Nicht ausreichend!\n\n✅ Bestellanforderung PR-6789 erstellt:\n• Menge: 50 Stück\n• Lieferdatum: 15.12.2025 (benötigt)\n• Voraussichtliche Lieferung: 12.12.2025\n• Zugeordnet zu: WO-12345\n• Status: Ausstehend (Genehmigung erforderlich)",
  "session_id": "sess_demo_456",
  "mode": "PROCUREMENT",
  "mode_confidence": 0.97,
  "data": {
    "stock": {
      "part_no": "P-45678",
      "available": 12,
      "reserved": 5,
      "free": 7
    },
    "purchase_request": {
      "id": "PR-6789",
      "qty": 50,
      "status": "pending",
      "estimated_delivery": "2025-12-12"
    }
  },
  "timestamp": "2025-11-24T10:10:30Z"
}
```

---

#### Alternative: Ausreichend Bestand

**Wenn Bestand ausreichend wäre**:

```
Lagerbestand: 60 Stück frei
Benötigt: 50 Stück

Agent-Antwort:
"✅ Lagerbestand für Teil P-45678 (Bremsscheibe 330mm):

✅ Verfügbar: 75 Stück
⚠️  Reserviert: 15 Stück
✅ Frei: 60 Stück

Benötigt: 50 Stück → ✅ Ausreichend vorhanden!

ℹ️  Keine Bestellung notwendig. Das Teil kann direkt für WO-12345 reserviert werden."
```

---

## Szenario 3: Personal für Überführungen planen

### Kontext

**Rolle**: `dispatcher` (Disponent)
**Modus**: `HR`
**Use Case**: UC3 - Personal für Überführungen planen

**Situation**: Lokomotive BR185-042 muss von Berlin nach München überführt werden. Der Disponent plant die Überführung und weist qualifiziertes Personal zu.

---

### Demo-Ablauf

**User-Abfrage**:
```
Plane Überführung für Lok BR185-042 von Berlin nach München, Zeitfenster 01.12.2025 bis 03.12.2025. Brauche Mitarbeiter mit Qualifikation Dieselmechaniker
```

**Agent-Verarbeitung**:
```
1. Mode Detection → HR (Keywords: "Personal", "Mitarbeiter", "Qualifikation")
   Confidence: 0.85 (auch WORKSHOP möglich, aber HR dominiert)

2. RBAC Check → ✅ dispatcher hat Berechtigung "transfer:plan", "staff:assign"

3. Tool Calls:
   A) plan_transfer(
        locomotive_id="BR185-042",
        from_location="Berlin",
        to_location="München",
        window_start="2025-12-01T08:00:00",
        window_end="2025-12-03T18:00:00"
      )
      → Backend: POST /api/v1/transfer/plans
      → Response: {
           "id": "TF-456",
           "locomotive_id": "BR185-042",
           "route": "Berlin → München",
           "distance_km": 580,
           "estimated_duration_hours": 8,
           "status": "planned"
         }

   B) list_staff(
        qualification="Dieselmechaniker",
        available_from="2025-12-01T08:00:00",
        available_to="2025-12-03T18:00:00"
      )
      → Backend: GET /api/v1/hr/staff?qualification=Dieselmechaniker&...
      → Response: {
           "staff": [
             {
               "id": "MA-123",
               "name": "Schmidt, Thomas",
               "qualification": "Dieselmechaniker",
               "available": true
             },
             {
               "id": "MA-456",
               "name": "Müller, Anna",
               "qualification": "Dieselmechaniker",
               "available": true
             }
           ]
         }

   C) assign_transfer(
        transfer_id="TF-456",
        staff_id="MA-123",
        locomotive_id="BR185-042",
        from_dt="2025-12-01T08:00:00",
        to_dt="2025-12-03T18:00:00"
      )
      → Backend: POST /api/v1/hr/assignments
      → Response: {"id": "ASSIGN-789", "status": "assigned"}
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "✅ Überführung TF-456 geplant:\n\n📍 Route: Berlin → München (580 km)\n🚂 Lokomotive: BR185-042\n⏱️  Zeitfenster: 01.12.2025 08:00 - 03.12.2025 18:00 Uhr\n⏳ Geschätzte Dauer: 8 Stunden\n\n👥 Verfügbares Personal (Dieselmechaniker):\n1. MA-123: Schmidt, Thomas ✅\n2. MA-456: Müller, Anna ✅\n\n✅ Zuweisung erstellt:\n• Mitarbeiter: MA-123 (Schmidt, Thomas)\n• Überführung: TF-456\n• Zeitraum: 01.12.2025 08:00 - 03.12.2025 18:00 Uhr\n\nÜberführung ist einsatzbereit!",
  "session_id": "sess_demo_123",
  "mode": "HR",
  "mode_confidence": 0.85,
  "data": {
    "transfer": {
      "id": "TF-456",
      "locomotive_id": "BR185-042",
      "route": "Berlin → München",
      "status": "planned"
    },
    "assigned_staff": {
      "id": "MA-123",
      "name": "Schmidt, Thomas"
    }
  },
  "timestamp": "2025-11-24T10:20:15Z"
}
```

---

## Szenario 4: Rechnungen erfassen und zuordnen

### Kontext

**Rolle**: `finance` (Finanzen)
**Modus**: `FINANCE`
**Use Case**: UC4 - Rechnung erfassen & WO zuordnen

**Situation**: Eine Rechnung von Siemens Mobility für 15.000 EUR ist eingegangen und muss dem Werkstattauftrag WO-12345 zugeordnet werden.

---

### Demo-Ablauf

**User-Abfrage**:
```
Erfasse Rechnung RE-2025-001, Lieferant Siemens Mobility, Betrag 15000 EUR, Werkstattauftrag WO-12345
```

**Agent-Verarbeitung**:
```
1. Mode Detection → FINANCE (Keywords: "Rechnung", "Lieferant", "Betrag", "EUR")
   Confidence: 0.99

2. RBAC Check → ✅ finance hat Berechtigung "invoice:create"

3. Tool Calls:
   - create_invoice(
       invoice_number="RE-2025-001",
       supplier="Siemens Mobility",
       amount=15000.00,
       currency="EUR",
       related_wo_id="WO-12345"
     )
     → Backend: POST /api/v1/finance/invoices
     → Response: {
          "id": "INV-987",
          "invoice_number": "RE-2025-001",
          "supplier": "Siemens Mobility",
          "amount": 15000.00,
          "currency": "EUR",
          "related_wo_id": "WO-12345",
          "status": "pending_approval",
          "created_at": "2025-11-24T10:25:00Z"
        }
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "✅ Rechnung erfolgreich erfasst:\n\n📄 Rechnungsnummer: RE-2025-001\n🏢 Lieferant: Siemens Mobility\n💰 Betrag: 15.000,00 EUR\n🔗 Zugeordnet zu: Werkstattauftrag WO-12345\n📊 Status: Ausstehende Genehmigung\n\n🆔 Interne ID: INV-987\n📅 Erstellt: 24.11.2025 10:25 Uhr\n\nDie Rechnung wurde zur Genehmigung weitergeleitet.",
  "session_id": "sess_demo_789",
  "mode": "FINANCE",
  "mode_confidence": 0.99,
  "data": {
    "invoice": {
      "id": "INV-987",
      "invoice_number": "RE-2025-001",
      "amount": 15000.00,
      "currency": "EUR",
      "status": "pending_approval"
    }
  },
  "timestamp": "2025-11-24T10:25:00Z"
}
```

---

## Szenario 5: Dokumenten-Management

### Kontext

**Rolle**: `ecm` (ECM-Spezialist)
**Modus**: `DOCS`
**Use Case**: UC5 - Dokumente: ablaufend & verknüpfen

**Situation**: Der ECM-Spezialist will ablaufende Zertifizierungen prüfen und ein neues TÜV-Zertifikat verknüpfen.

---

### Demo-Ablauf

#### Schritt 1: Ablaufende Dokumente anzeigen

**User-Abfrage**:
```
Zeige mir alle Dokumente die in den nächsten 60 Tagen ablaufen
```

**Agent-Verarbeitung**:
```
1. Mode Detection → DOCS (Keywords: "Dokumente", "ablaufen")
   Confidence: 0.96

2. RBAC Check → ✅ ecm hat Berechtigung "docs:read"

3. Tool Calls:
   - list_expiring_documents(days_ahead=60)
     → Backend: GET /api/v1/docs/expiring?days_ahead=60
     → Response: {
          "documents": [
            {
              "id": "DOC-111",
              "type": "TÜV-Abnahme",
              "locomotive_id": "BR185-042",
              "expires_at": "2025-12-20",
              "days_until_expiry": 26,
              "status": "expiring_soon"
            },
            {
              "id": "DOC-222",
              "type": "Betriebserlaubnis",
              "locomotive_id": "BR189-033",
              "expires_at": "2026-01-15",
              "days_until_expiry": 52,
              "status": "expiring_soon"
            }
          ]
        }
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "⚠️  In den nächsten 60 Tagen laufen 2 Dokumente ab:\n\n1. 🔴 TÜV-Abnahme (DOC-111)\n   • Lokomotive: BR185-042\n   • Läuft ab: 20.12.2025 (in 26 Tagen)\n   • Status: Bald ablaufend\n\n2. 🟡 Betriebserlaubnis (DOC-222)\n   • Lokomotive: BR189-033\n   • Läuft ab: 15.01.2026 (in 52 Tagen)\n   • Status: Bald ablaufend\n\n💡 Bitte neue Dokumente rechtzeitig beschaffen und verknüpfen.",
  "session_id": "sess_demo_ecm",
  "mode": "DOCS",
  "mode_confidence": 0.96,
  "data": {
    "expiring_documents": [
      {
        "id": "DOC-111",
        "type": "TÜV-Abnahme",
        "locomotive_id": "BR185-042",
        "expires_at": "2025-12-20",
        "days_until_expiry": 26
      },
      {
        "id": "DOC-222",
        "type": "Betriebserlaubnis",
        "locomotive_id": "BR189-033",
        "expires_at": "2026-01-15",
        "days_until_expiry": 52
      }
    ]
  },
  "timestamp": "2025-11-24T10:30:00Z"
}
```

---

#### Schritt 2: Neues Dokument verknüpfen

**User-Abfrage**:
```
Verknüpfe Zertifikat CERT-789, Typ TÜV-Abnahme, mit Lok BR185-042, gültig bis 31.12.2026
```

**Agent-Verarbeitung**:
```
1. Mode Detection → DOCS (Keywords: "Verknüpfe", "Zertifikat")
   Confidence: 0.98

2. RBAC Check → ✅ ecm hat Berechtigung "docs:manage"

3. Tool Calls:
   - link_document(
       document_id="CERT-789",
       doc_type="TÜV-Abnahme",
       locomotive_id="BR185-042",
       valid_until="2026-12-31"
     )
     → Backend: POST /api/v1/docs/link
     → Response: {
          "id": "DOC-333",
          "document_id": "CERT-789",
          "type": "TÜV-Abnahme",
          "locomotive_id": "BR185-042",
          "valid_until": "2026-12-31",
          "status": "active",
          "linked_at": "2025-11-24T10:31:00Z"
        }
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "✅ Zertifikat erfolgreich verknüpft:\n\n📄 Zertifikat: CERT-789\n📋 Typ: TÜV-Abnahme\n🚂 Lokomotive: BR185-042\n✅ Gültig bis: 31.12.2026\n📊 Status: Aktiv\n🔗 Interne ID: DOC-333\n\nDas alte Dokument DOC-111 wurde automatisch als 'ersetzt' markiert.",
  "session_id": "sess_demo_ecm",
  "mode": "DOCS",
  "mode_confidence": 0.98,
  "data": {
    "linked_document": {
      "id": "DOC-333",
      "document_id": "CERT-789",
      "locomotive_id": "BR185-042",
      "valid_until": "2026-12-31",
      "status": "active"
    }
  },
  "timestamp": "2025-11-24T10:31:00Z"
}
```

---

## Szenario 6: Fahrzeugstatus abfragen

### Kontext

**Rolle**: `dispatcher` (Disponent)
**Modus**: `FLOTTE`
**Use Case**: UC6 - Fahrzeugstatus & Plan-Flag setzen

**Situation**: Der Disponent will den Status aller Lokomotiven mit Status "maintenance_due" prüfen.

---

### Demo-Ablauf

**User-Abfrage**:
```
Zeige mir alle Loks mit Status maintenance_due
```

**Agent-Verarbeitung**:
```
1. Mode Detection → FLOTTE (Keywords: "Loks", "Status")
   Confidence: 0.97

2. RBAC Check → ✅ dispatcher hat Berechtigung "fleet:read"

3. Tool Calls:
   - get_locomotives(status="maintenance_due")
     → Backend: GET /api/v1/fleet/locomotives?status=maintenance_due
     → Response: {
          "locomotives": [
            {
              "id": "BR185-042",
              "series": "BR 185",
              "status": "maintenance_due",
              "location": "Berlin",
              "planned_workshop_flag": false,
              "last_maintenance": "2024-06-15"
            },
            {
              "id": "BR189-033",
              "series": "BR 189",
              "status": "maintenance_due",
              "location": "Hamburg",
              "planned_workshop_flag": true,
              "last_maintenance": "2024-07-20"
            },
            {
              "id": "BR152-123",
              "series": "BR 152",
              "status": "maintenance_due",
              "location": "München",
              "planned_workshop_flag": false,
              "last_maintenance": "2024-05-10"
            }
          ],
          "count": 3
        }
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "🚂 Lokomotiven mit Status 'maintenance_due': 3 Fahrzeuge\n\n1. BR185-042 (BR 185)\n   📍 Standort: Berlin\n   🏭 Werkstatt geplant: ❌ Nein\n   🔧 Letzte Wartung: 15.06.2024\n\n2. BR189-033 (BR 189)\n   📍 Standort: Hamburg\n   🏭 Werkstatt geplant: ✅ Ja\n   🔧 Letzte Wartung: 20.07.2024\n\n3. BR152-123 (BR 152)\n   📍 Standort: München\n   🏭 Werkstatt geplant: ❌ Nein\n   🔧 Letzte Wartung: 10.05.2024\n\n💡 2 Fahrzeuge haben noch keine Werkstattplanung.",
  "session_id": "sess_demo_123",
  "mode": "FLOTTE",
  "mode_confidence": 0.97,
  "data": {
    "locomotives": [
      {"id": "BR185-042", "status": "maintenance_due", "planned_workshop_flag": false},
      {"id": "BR189-033", "status": "maintenance_due", "planned_workshop_flag": true},
      {"id": "BR152-123", "status": "maintenance_due", "planned_workshop_flag": false}
    ],
    "count": 3
  },
  "timestamp": "2025-11-24T10:35:00Z"
}
```

---

## Szenario 7: Verfügbarkeitsbericht generieren

### Kontext

**Rolle**: `viewer` (Betrachter)
**Modus**: `FLOTTE` (mit Reporting)
**Use Case**: UC8 - Verfügbarkeitsbericht

**Situation**: Ein Manager will einen KPI-Bericht über die Flottenverfügbarkeit im November 2025 erstellen.

---

### Demo-Ablauf

**User-Abfrage**:
```
Verfügbarkeitsbericht vom 01.11.2025 bis 30.11.2025
```

**Agent-Verarbeitung**:
```
1. Mode Detection → FLOTTE (Keywords: "Verfügbarkeit", "Bericht")
   Confidence: 0.92

2. RBAC Check → ✅ viewer hat Berechtigung "report:read"

3. Tool Calls:
   - get_availability_report(
       from_date="2025-11-01",
       to_date="2025-11-30"
     )
     → Backend: GET /api/v1/reporting/availability?from=2025-11-01&to=2025-11-30
     → Response: {
          "period": {
            "from": "2025-11-01",
            "to": "2025-11-30"
          },
          "metrics": {
            "total_fleet": 25,
            "avg_availability": 0.925,
            "operational_days": 695,
            "maintenance_days": 55,
            "breakdown_days": 0,
            "total_possible_days": 750
          },
          "by_series": {
            "BR 185": {"count": 10, "availability": 0.95},
            "BR 189": {"count": 8, "availability": 0.91},
            "BR 152": {"count": 7, "availability": 0.89}
          }
        }
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "📊 Verfügbarkeitsbericht November 2025\n\n🚂 Flottengröße: 25 Lokomotiven\n📈 Durchschnittliche Verfügbarkeit: 92,5%\n\n📅 Zeitraum: 01.11.2025 - 30.11.2025 (30 Tage)\n\n✅ Betriebstage: 695\n🔧 Wartungstage: 55\n🔴 Ausfallstage: 0\n\n📊 Verfügbarkeit nach Baureihe:\n• BR 185 (10 Loks): 95,0% ✅\n• BR 189 (8 Loks): 91,0% ✅\n• BR 152 (7 Loks): 89,0% ⚠️\n\n💡 Ziel (90%) wurde erreicht!",
  "session_id": "sess_demo_viewer",
  "mode": "FLOTTE",
  "mode_confidence": 0.92,
  "data": {
    "availability": 0.925,
    "total_fleet": 25,
    "operational_days": 695,
    "maintenance_days": 55,
    "by_series": {
      "BR 185": 0.95,
      "BR 189": 0.91,
      "BR 152": 0.89
    }
  },
  "timestamp": "2025-11-24T10:40:00Z"
}
```

---

## Szenario 8: Wartungsaufgabe erstellen

### Kontext

**Rolle**: `dispatcher` (Disponent)
**Modus**: `MAINTENANCE` → `WORKSHOP`
**Use Case**: UC9 - Wartungsaufgabe anlegen & planen

**Situation**: Der Disponent will eine neue Wartungsaufgabe erstellen und direkt für die Werkstatt Leipzig planen.

---

### Demo-Ablauf

**User-Abfrage**:
```
Erstelle Wartungsaufgabe für Lok BR189-033, Typ Bremsprüfung, fällig am 20.12.2025, plane für Werk Leipzig
```

**Agent-Verarbeitung**:
```
1. Mode Detection → MAINTENANCE (Keywords: "Wartungsaufgabe", "fällig")
   Confidence: 0.94

2. RBAC Check → ✅ dispatcher hat "maint:create", "wo:create"

3. Tool Calls:
   A) create_maintenance_task(
        locomotive_id="BR189-033",
        task_type="Bremsprüfung",
        due_date="2025-12-20"
      )
      → Backend: POST /api/v1/maintenance/tasks
      → Response: {
           "id": "TASK-999",
           "locomotive_id": "BR189-033",
           "type": "Bremsprüfung",
           "due_date": "2025-12-20",
           "status": "pending"
         }

   B) create_workshop_order(
        locomotive_id="BR189-033",
        workshop_id="WERK-LEI",
        planned_start="2025-12-19T08:00:00",
        planned_end="2025-12-19T16:00:00",
        tasks=["Bremsprüfung"]
      )
      → Backend: POST /api/v1/workshop/orders
      → Response: {
           "id": "WO-99999",
           "locomotive_id": "BR189-033",
           "workshop_id": "WERK-LEI",
           "status": "planned"
         }

   C) patch_locomotive(
        locomotive_id="BR189-033",
        status="planned_for_workshop"
      )
      → Backend: PATCH /api/v1/fleet/locomotives/BR189-033
      → Response: {"id": "BR189-033", "status": "planned_for_workshop"}
```

**Agent-Antwort**:
```json
{
  "success": true,
  "message": "✅ Wartungsaufgabe erstellt und geplant:\n\n🔧 Wartungsaufgabe TASK-999\n   • Lokomotive: BR189-033\n   • Typ: Bremsprüfung\n   • Fällig: 20.12.2025\n   • Status: Ausstehend\n\n🏭 Werkstattauftrag WO-99999\n   • Werk: Leipzig (WERK-LEI)\n   • Geplant: 19.12.2025 08:00 - 16:00 Uhr\n   • Aufgaben: Bremsprüfung\n   • Status: Geplant\n\n🚂 Fahrzeugstatus aktualisiert:\n   BR189-033 → 'planned_for_workshop'\n\nAlles bereit für die Wartung!",
  "session_id": "sess_demo_123",
  "mode": "MAINTENANCE",
  "mode_confidence": 0.94,
  "data": {
    "maintenance_task": {
      "id": "TASK-999",
      "locomotive_id": "BR189-033",
      "type": "Bremsprüfung",
      "due_date": "2025-12-20"
    },
    "workshop_order": {
      "id": "WO-99999",
      "workshop_id": "WERK-LEI",
      "status": "planned"
    }
  },
  "timestamp": "2025-11-24T10:45:00Z"
}
```

---

## Szenario 9: RBAC & Fehlerbehandlung

### Kontext

**Rolle**: `viewer` (Betrachter - Nur Lesen)
**Modus**: Egal
**Zweck**: Demonstration der RBAC-Zugriffskontrolle

---

### Demo-Ablauf

#### Fall 1: Schreibversuch durch Viewer

**User-Abfrage**:
```
Erstelle Werkstattauftrag für BR185-042 im Werk München
```

**Agent-Verarbeitung**:
```
1. Mode Detection → WORKSHOP
   Confidence: 0.99

2. RBAC Check → ❌ viewer hat KEINE Berechtigung "wo:create"

   RBACEngine.check_access(user_role="viewer", required_scope="wo:create")
   → AccessResult(
        allowed=False,
        reason="Rolle 'viewer' hat keine Berechtigung 'wo:create'. "
               "Werkstattaufträge können nur von Disponenten erstellt werden."
      )

3. Handler wird NICHT ausgeführt
```

**Agent-Antwort**:
```json
{
  "success": false,
  "message": "❌ Zugriff verweigert\n\nRolle 'viewer' hat keine Berechtigung 'wo:create'.\n\nWerkstattaufträge können nur von Disponenten erstellt werden.\n\n💡 Erforderliche Rolle: dispatcher",
  "error_code": "RBAC_DENIED",
  "details": {
    "required_scope": "wo:create",
    "user_role": "viewer",
    "allowed_roles": ["dispatcher"]
  },
  "timestamp": "2025-11-24T10:50:00Z"
}
```

---

#### Fall 2: Backend-Service nicht erreichbar

**User-Abfrage** (als dispatcher):
```
Zeige alle Loks mit Status operational
```

**Angenommen**: Fleet-DB Service ist down

**Agent-Verarbeitung**:
```
1. Mode Detection → FLOTTE
   Confidence: 0.98

2. RBAC Check → ✅ dispatcher hat "fleet:read"

3. Tool Call:
   - get_locomotives(status="operational")
     → Backend: GET http://localhost:8001/api/v1/fleet/locomotives?status=operational
     → ❌ Connection Error: Connection refused

4. Error Handling:
   ToolCallResult(
     success=False,
     error="Backend-Dienst 'fleet_db' nicht erreichbar: Connection refused",
     http_status=503
   )
```

**Agent-Antwort**:
```json
{
  "success": false,
  "message": "❌ Fehler beim Abrufen der Daten\n\nBackend-Dienst 'fleet_db' ist nicht erreichbar.\n\nFehlerdetails: Connection refused\n\n💡 Bitte prüfen Sie:\n• Ist der Fleet-DB-Service gestartet?\n• Ist die Service-URL korrekt konfiguriert?\n• Gibt es Netzwerkprobleme?",
  "error_code": "BACKEND_ERROR",
  "details": {
    "service": "fleet_db",
    "http_status": 503,
    "error": "Connection refused"
  },
  "timestamp": "2025-11-24T10:55:00Z"
}
```

---

#### Fall 3: Validierungsfehler

**User-Abfrage**:
```
Erstelle Wartungsaufgabe für Lok BR189-033, fällig am 31.13.2025
```

**Problem**: Ungültiges Datum (13. Monat existiert nicht)

**Agent-Antwort**:
```json
{
  "success": false,
  "message": "❌ Validierungsfehler\n\n'due_date' hat ungültiges Format.\n\nGegeben: '31.13.2025'\nErwartet: 'YYYY-MM-DD' (z.B. '2025-12-31')\n\n💡 Bitte verwenden Sie das ISO-Format für Daten.",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "due_date",
    "provided": "31.13.2025",
    "expected_format": "YYYY-MM-DD"
  },
  "timestamp": "2025-11-24T10:58:00Z"
}
```

---

## Szenario 10: Multi-Mode-Konversation

### Kontext

**Rolle**: `dispatcher` (Disponent)
**Zweck**: Demonstration der Mode-Wechsel innerhalb einer Session

---

### Demo-Ablauf

#### Nachricht 1: FLOTTE-Modus

**User**: `Zeige mir alle Loks`

**Agent**:
```
Mode: FLOTTE (Confidence: 0.98)

"Ich habe 25 Lokomotiven in der Flotte gefunden:
• 10x BR 185 (8 operational, 2 maintenance_due)
• 8x BR 189 (7 operational, 1 in_workshop)
• 7x BR 152 (5 operational, 2 maintenance_due)

Gesamtverfügbarkeit: 80% (20 von 25 Loks einsatzbereit)"
```

---

#### Nachricht 2: MAINTENANCE-Modus

**User**: `Welche HU-Fristen laufen diese Woche ab?`

**Agent**:
```
Mode: MAINTENANCE (Confidence: 0.97)
(Mode-Wechsel: FLOTTE → MAINTENANCE)

"Diese Woche (24.11-30.11.2025) läuft 1 HU-Frist ab:

1. BR185-042 - HU fällig am 28.11.2025 (in 4 Tagen)

⚠️  Dringend! Bitte Werkstattauftrag erstellen."
```

---

#### Nachricht 3: WORKSHOP-Modus

**User**: `Erstelle Auftrag für München`

**Agent**:
```
Mode: WORKSHOP (Confidence: 0.85)
(Mode-Wechsel: MAINTENANCE → WORKSHOP)
(Kontext: Agent merkt sich BR185-042 aus vorheriger Nachricht)

"✅ Werkstattauftrag WO-55555 erstellt:
• Lokomotive: BR185-042 (aus vorheriger Abfrage)
• Werk: München (WERK-MUC)
• Geplant: 26.11.2025 08:00 - 27.11.2025 16:00 Uhr
• Aufgaben: HU, Bremsprüfung

Fahrzeugstatus aktualisiert auf 'planned_for_workshop'."
```

---

#### Nachricht 4: PROCUREMENT-Modus

**User**: `Brauchen wir Teile für den Auftrag?`

**Agent**:
```
Mode: PROCUREMENT (Confidence: 0.80)
(Mode-Wechsel: WORKSHOP → PROCUREMENT)
(Kontext: Agent merkt sich WO-55555)

"📦 Teilebedarf für WO-55555 (BR185-042, HU):

1. Bremsscheiben (P-45678): 4 Stück
   Lagerbestand: 12 verfügbar → ✅ Ausreichend

2. Luftfilter (P-99999): 2 Stück
   Lagerbestand: 0 verfügbar → ❌ Bestellung nötig

⚠️  Bestellung PR-7777 wurde erstellt für 10x Luftfilter,
Lieferung bis 25.11.2025."
```

---

#### Nachricht 5: HR-Modus

**User**: `Wer kann das machen?`

**Agent**:
```
Mode: HR (Confidence: 0.75)
(Mode-Wechsel: PROCUREMENT → HR)
(Kontext: Agent merkt sich WO-55555 und Werk München)

"👥 Verfügbares Personal für WO-55555 (Werk München):

HU-Qualifikation erforderlich:
1. MA-111: Schneider, Peter ✅ (verfügbar 26.-27.11.)
2. MA-222: Weber, Lisa ✅ (verfügbar 26.-27.11.)
3. MA-333: Fischer, Jan ❌ (im Urlaub)

Möchten Sie eine Zuweisung vornehmen?"
```

---

#### Nachricht 6: FINANCE-Modus

**User**: `Was kostet das?`

**Agent**:
```
Mode: FINANCE (Confidence: 0.82)
(Mode-Wechsel: HR → FINANCE)
(Kontext: Agent merkt sich WO-55555)

"💰 Kostenübersicht für WO-55555:

📋 Plankosten:
• Arbeitsstunden: 16h × 85 EUR = 1.360 EUR
• Teile: 450 EUR (Bremsscheiben, Luftfilter)
• Gemeinkosten: 200 EUR
• Gesamt (geplant): 2.010 EUR

📊 Budget:
• Verfügbar: 25.000 EUR
• Nach Auftrag: 22.990 EUR

✅ Budget ausreichend."
```

---

### Session-Historie

```json
{
  "session_id": "sess_demo_123",
  "user_id": "demo_dispatcher",
  "user_role": "dispatcher",
  "history": [
    {"query": "Zeige mir alle Loks", "mode": "FLOTTE", "timestamp": "10:00:00"},
    {"query": "Welche HU-Fristen laufen diese Woche ab?", "mode": "MAINTENANCE", "timestamp": "10:01:15"},
    {"query": "Erstelle Auftrag für München", "mode": "WORKSHOP", "timestamp": "10:02:30"},
    {"query": "Brauchen wir Teile für den Auftrag?", "mode": "PROCUREMENT", "timestamp": "10:03:45"},
    {"query": "Wer kann das machen?", "mode": "HR", "timestamp": "10:05:00"},
    {"query": "Was kostet das?", "mode": "FINANCE", "timestamp": "10:06:15"}
  ],
  "mode_transitions": [
    "FLOTTE → MAINTENANCE",
    "MAINTENANCE → WORKSHOP",
    "WORKSHOP → PROCUREMENT",
    "PROCUREMENT → HR",
    "HR → FINANCE"
  ],
  "context_carried": [
    "BR185-042 (locomotive)",
    "WO-55555 (workshop order)",
    "WERK-MUC (workshop)"
  ]
}
```

**Insights**:
- 6 Nachrichten, 5 Mode-Wechsel
- Agent merkt sich Kontext (Lok, Auftrag, Werk)
- Nahtlose Konversation über mehrere Domänen
- Keine wiederholte Eingabe von IDs nötig

---

## Zusammenfassung & Key Takeaways

### ✅ Demonstrierte Features

1. **Mode-Routing**: Automatische Erkennung von 7 Modi basierend auf Keywords
2. **RBAC**: Strikte Berechtigungsprüfung für alle Operationen
3. **Tool-Orchestration**: Koordination von 9 Backend-Services
4. **Session-Management**: Kontext über mehrere Abfragen hinweg
5. **Error-Handling**: Klare Fehlermeldungen bei RBAC, Backend-Fehlern, Validierung
6. **Multi-Mode-Konversation**: Nahtlose Wechsel zwischen Modi
7. **Structured Data**: Tabellen, Listen, KPIs in Antworten
8. **German Language**: Alle Antworten auf Deutsch mit Berlin-Zeitzone

### 📊 Performance-Metriken (Beispiel-Session)

```
Session Duration: 15 Minuten
Total Queries: 15
Mode Distribution:
  - FLOTTE: 4 (26,7%)
  - MAINTENANCE: 3 (20,0%)
  - WORKSHOP: 3 (20,0%)
  - PROCUREMENT: 2 (13,3%)
  - FINANCE: 1 (6,7%)
  - HR: 1 (6,7%)
  - DOCS: 1 (6,7%)

Avg Response Time: 450ms
RBAC Denials: 2 (13,3%)
Backend Errors: 0
Success Rate: 86,7%
```

### 🎯 Use Case Coverage

| Use Case | Demonstrated | Notes |
|----------|--------------|-------|
| UC1: HU Planning | ✅ | Szenario 1 |
| UC2: Parts Procurement | ✅ | Szenario 2 |
| UC3: Transfer Staff | ✅ | Szenario 3 |
| UC4: Invoice Entry | ✅ | Szenario 4 |
| UC5: Documents | ✅ | Szenario 5 |
| UC6: Vehicle Status | ✅ | Szenario 6 |
| UC8: Availability Report | ✅ | Szenario 7 |
| UC9: Maintenance Task | ✅ | Szenario 8 |

**Coverage**: 8/8 Use Cases (100%)

### 🔧 Next Steps für Production

1. **Load Testing**: 100+ concurrent users, 1000+ queries/hour
2. **Integration Testing**: Mit echten Backend-Services
3. **User Acceptance Testing**: Mit echten Disponenten, Werkstatt, etc.
4. **Performance-Optimierung**: Caching, Query-Optimization
5. **Monitoring**: Prometheus, Grafana Dashboards
6. **Documentation**: API-Docs, Runbooks, Troubleshooting-Guides

---

**Version**: 1.0.0
**Erstellt**: November 2025
**Status**: Demo-Ready ✅
