# FLEET-ONE Benutzerhandbuch

**Version 1.0.0**
**Sprache:** Deutsch
**Zeitzone:** Europe/Berlin

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Modi](#modi)
3. [Rollen und Berechtigungen](#rollen-und-berechtigungen)
4. [Anwendungsfälle](#anwendungsfälle)
5. [Beispielabfragen](#beispielabfragen)
6. [Konfliktlösung](#konfliktlösung)
7. [Fehlerbehebung](#fehlerbehebung)

---

## Überblick

FLEET-ONE ist ein zentraler, LLM-basierter Assistent für das Flottenmanagement von Streckenlokomotiven. Der Agent versteht natürlichsprachliche Anfragen auf Deutsch und orchestriert automatisch die Kommunikation mit 9 Backend-Diensten.

### Hauptfunktionen

- **Multi-Modus-Routing**: Automatische Erkennung des passenden Modus basierend auf Schlüsselwörtern
- **Rollenbasierte Zugriffskontrolle (RBAC)**: Sichere Berechtigungsprüfung für alle Operationen
- **Intelligente Konfliktlösung**: Policy-basierte Auflösung von konkurrierenden Änderungen
- **Session-Management**: Konversationshistorie für kontextbezogene Antworten
- **Event Sourcing**: Vollständige Nachverfolgbarkeit aller Aktionen

### Unterstützte Backend-Dienste

1. **fleet_db** - Flotten- und Lokomotivdaten
2. **maintenance_service** - Wartungsaufgaben und Fristen
3. **workshop_service** - Werkstattaufträge und Reparaturen
4. **transfer_service** - Fahrzeugüberführungen
5. **procurement_service** - Teile und Beschaffung
6. **reporting_service** - KPIs und Berichte
7. **finance_service** - Rechnungen und Budgets
8. **hr_service** - Personal und Zuweisungen
9. **docs_service** - Dokumente und Zertifizierungen

---

## Modi

FLEET-ONE arbeitet in 7 spezialisierten Modi. Der passende Modus wird automatisch anhand Ihrer Anfrage erkannt:

### 1. FLOTTE

**Zweck**: Flottenübersicht, Lokomotivstatus, Verfügbarkeit

**Schlüsselwörter**: `flotte`, `lok`, `loks`, `lokomotiven`, `verfügbarkeit`, `status`, `einsatzbereit`

**Beispiele**:
- "Zeige mir alle verfügbaren Loks"
- "Status von Lokomotive BR185-042"
- "Welche Fahrzeuge sind einsatzbereit?"

### 2. MAINTENANCE

**Zweck**: Wartungsplanung, HU-Fristen, Instandhaltungsaufgaben

**Schlüsselwörter**: `wartung`, `instandhaltung`, `HU`, `fristen`, `fällig`, `prüfung`

**Beispiele**:
- "Welche HU-Fristen laufen in den nächsten 30 Tagen ab?"
- "Erstelle Wartungsaufgabe für BR189-033"
- "Zeige überfällige Inspektionen"

### 3. WORKSHOP

**Zweck**: Werkstattplanung, Auftragsmanagement, Reparaturen

**Schlüsselwörter**: `werkstatt`, `reparatur`, `wo`, `auftrag`, `instandsetzung`, `planung`

**Beispiele**:
- "Plane HU für Werk München in 14 Tagen"
- "Status des Werkstattauftrags WO-12345"
- "Erstelle Reparaturauftrag für Bremsanlage"

### 4. PROCUREMENT

**Zweck**: Teilebeschaffung, Lagerbestand, Bestellungen

**Schlüsselwörter**: `teile`, `beschaffung`, `lager`, `bestellung`, `einkauf`, `bestellen`

**Beispiele**:
- "Prüfe Bestand von Teil P-45678 und bestelle bei Bedarf"
- "Lagerstand für Bremsscheiben"
- "Bestellung für 10 Luftfilter bis 2025-12-15"

### 5. FINANCE

**Zweck**: Rechnungsverwaltung, Budgets, Kostenberichte

**Schlüsselwörter**: `rechnung`, `finanzen`, `budget`, `kosten`, `faktura`, `invoice`

**Beispiele**:
- "Erfasse Rechnung RE-2025-001 von Lieferant XYZ"
- "Kostenbericht für November 2025"
- "Ordne Rechnung dem Werkstattauftrag WO-12345 zu"

### 6. HR

**Zweck**: Personalplanung, Zuweisungen, Qualifikationen

**Schlüsselwörter**: `personal`, `mitarbeiter`, `zuweisung`, `team`, `qualifikation`

**Beispiele**:
- "Liste Mitarbeiter mit Qualifikation 'Dieselmechaniker'"
- "Weise MA-123 der Überführung TF-456 zu"
- "Personalplanung für Werkstatt Hamburg"

### 7. DOCS

**Zweck**: Dokumentenmanagement, Zertifizierungen, Fristen

**Schlüsselwörter**: `dokument`, `zertifikat`, `ablauf`, `gültig`, `unterlagen`, `papiere`

**Beispiele**:
- "Zeige ablaufende Dokumente in den nächsten 60 Tagen"
- "Verknüpfe Zertifikat CERT-789 mit Lokomotive BR185-042"
- "Liste ungültige TÜV-Abnahmen"

---

## Rollen und Berechtigungen

FLEET-ONE implementiert ein striktes RBAC-System mit 6 Rollen:

### dispatcher (Disponent)

**Berechtigungen**:
- ✅ Planung erstellen (`plan:create`)
- ✅ Planung aktualisieren (`plan:update`)
- ✅ Werkstattaufträge erstellen (`wo:create`)
- ✅ Werkstattaufträge aktualisieren (`wo:update`)
- ✅ Überführungen planen (`transfer:plan`)

**Typische Aufgaben**:
- HU-Planung für Werkstätten
- Fahrzeugüberführungen koordinieren
- Werkstattaufträge anlegen

### workshop (Werkstatt)

**Berechtigungen**:
- ✅ Auftragsstatus aktualisieren (`wo:status`)
- ✅ Ist-Zeiten erfassen (`wo:actuals`)
- ✅ Teile verbrauchen (`parts:consume`)
- ✅ Medien anhängen (`media:append`)

**Typische Aufgaben**:
- Reparaturstatus melden
- Tatsächliche Arbeitszeiten erfassen
- Teileverbrauch dokumentieren

### procurement (Beschaffung)

**Berechtigungen**:
- ✅ Bestellanforderungen erstellen (`purchase:req`)
- ✅ Lagerbestand verwalten (`parts:stock`)
- ✅ Lieferanten anzeigen (`supplier:read`)

**Typische Aufgaben**:
- Teilebestellungen aufgeben
- Lagerbestände prüfen
- Lieferantenauswahl

### finance (Finanzen)

**Berechtigungen**:
- ✅ Rechnungen erstellen (`invoice:create`)
- ✅ Rechnungen freigeben (`invoice:approve`)
- ✅ Budgets einsehen (`budget:read`)

**Typische Aufgaben**:
- Lieferantenrechnungen erfassen
- Rechnungen Aufträgen zuordnen
- Kostenberichte erstellen

### ecm (ECM-Spezialist)

**Berechtigungen**:
- ✅ ECM-Daten lesen (`ecm:read`)
- ✅ ECM-Berichte erstellen (`ecm:report`)
- ✅ Dokumente verwalten (`docs:manage`)

**Typische Aufgaben**:
- Zertifizierungen prüfen
- Ablaufende Dokumente überwachen
- Compliance-Berichte generieren

### viewer (Betrachter)

**Berechtigungen**:
- ✅ Alles lesen (`read:*`)
- ❌ Keine Schreibrechte

**Typische Aufgaben**:
- Statusabfragen
- Berichte einsehen
- Nur-Lese-Zugriff

---

## Anwendungsfälle

FLEET-ONE implementiert 9 vordefinierte Anwendungsfälle aus dem Playbook:

### UC1: HU/Fristen planen → Werkstatt

**Rolle**: `dispatcher`

**Beschreibung**: Plant HU-Termine für Lokomotiven mit ablaufenden Fristen.

**Beispielabfrage**:
```
Plane HU für Werk München in 14 Tagen
```

**Werkzeugsequenz**:
1. `list_maintenance_tasks` - Fällige Wartungen abrufen
2. `create_workshop_order` - Werkstattauftrag erstellen
3. `patch_locomotive` - Fahrzeugstatus aktualisieren

**Ausgabe**: Liste geplanter Werkstattaufträge mit IDs und Zeitfenstern

---

### UC2: Teile-Beschaffung prüfen & bestellen

**Rolle**: `procurement`

**Beschreibung**: Prüft Lagerbestand und erstellt automatisch Bestellanforderungen bei Bedarf.

**Beispielabfrage**:
```
Prüfe Bestand von Teil P-45678 und bestelle 50 Stück bis 2025-12-15
```

**Werkzeugsequenz**:
1. `get_stock` - Lagerbestand abrufen
2. `request_purchase` - Bestellung erstellen (falls nötig)

**Ausgabe**: Bestandsstatus und Bestellbestätigung

---

### UC3: Personal für Überführungen planen

**Rolle**: `dispatcher` + `workshop`

**Beschreibung**: Plant Überführungen und weist qualifiziertes Personal zu.

**Beispielabfrage**:
```
Plane Überführung für Lok BR185-042 von Berlin nach München,
Zeitfenster 2025-12-01 bis 2025-12-03, Qualifikation: Dieselmechaniker
```

**Werkzeugsequenz**:
1. `plan_transfer` - Überführung planen
2. `list_staff` - Verfügbares Personal abrufen
3. `assign_transfer` - Personal zuweisen

**Ausgabe**: Transfer-ID mit zugewiesenen Mitarbeitern

---

### UC4: Rechnung erfassen & WO zuordnen

**Rolle**: `finance`

**Beschreibung**: Erfasst Lieferantenrechnungen und ordnet sie Werkstattaufträgen zu.

**Beispielabfrage**:
```
Erfasse Rechnung RE-2025-001, Lieferant Siemens Mobility,
Betrag 15000 EUR, Werkstattauftrag WO-12345
```

**Werkzeugsequenz**:
1. `create_invoice` - Rechnung erstellen

**Ausgabe**: Bestätigung mit Rechnungs-ID

---

### UC5: Dokumente: ablaufend & verknüpfen

**Rolle**: `ecm`

**Beschreibung**: Überwacht ablaufende Zertifikate und verknüpft neue Dokumente.

**Beispielabfrage**:
```
Zeige ablaufende Dokumente in 60 Tagen und
verknüpfe Zertifikat CERT-789 mit Lok BR185-042 (gültig bis 2026-12-31)
```

**Werkzeugsequenz**:
1. `list_expiring_documents` - Ablaufende Dokumente abrufen
2. `link_document` - Neues Dokument verknüpfen

**Ausgabe**: Liste ablaufender Dokumente + Bestätigung der Verknüpfung

---

### UC8: Verfügbarkeitsbericht

**Rolle**: `dispatcher` (oder `viewer` für Nur-Lesen)

**Beschreibung**: Generiert KPI-Bericht über Flottenverfügbarkeit.

**Beispielabfrage**:
```
Verfügbarkeitsbericht vom 2025-11-01 bis 2025-11-30
```

**Werkzeugsequenz**:
1. `get_availability_report` - Bericht abrufen

**Ausgabe**: Verfügbarkeits-KPI (z.B. 92,5%)

---

### UC9: Wartungsaufgabe anlegen & planen

**Rolle**: `dispatcher`

**Beschreibung**: Erstellt neue Wartungsaufgabe und plant sie zur Ausführung.

**Beispielabfrage**:
```
Erstelle Wartungsaufgabe für Lok BR189-033, Typ 'Bremsprüfung',
fällig am 2025-12-20, plane für Werk Leipzig
```

**Werkzeugsequenz**:
1. `create_maintenance_task` - Aufgabe erstellen
2. `create_workshop_order` - Werkstattauftrag erstellen
3. `patch_locomotive` - Status aktualisieren

**Ausgabe**: Task-ID und Werkstattauftrags-ID

---

## Beispielabfragen

### Flottenmanagement

```
Zeige mir alle Loks mit Status 'maintenance_due'
```

```
Wie viele Fahrzeuge sind aktuell einsatzbereit?
```

```
Setze planned_workshop_flag für Lok BR185-042 auf true
```

### Wartungsplanung

```
Liste alle HU-Fristen die in den nächsten 30 Tagen ablaufen
```

```
Erstelle Wartungsaufgabe für BR189-033, Typ 'Hauptuntersuchung', fällig 2025-12-31
```

```
Zeige überfällige Inspektionen
```

### Werkstattmanagement

```
Erstelle Werkstattauftrag für Lok BR185-042, Werk München,
geplant vom 2025-12-05 10:00 bis 2025-12-07 16:00,
Aufgaben: ['HU', 'Bremsprüfung', 'Ölwechsel']
```

```
Aktualisiere Status von Auftrag WO-12345 auf 'in_progress'
```

### Beschaffung

```
Lagerbestand für Teil P-45678
```

```
Bestelle 50 Stück von Teil P-99999, benötigt bis 2025-12-20, für WO-12345
```

### Personalplanung

```
Liste alle Mitarbeiter mit Qualifikation 'Dieselmechaniker'
```

```
Weise Mitarbeiter MA-123 zu: Lok BR185-042, Transfer TF-456,
von 2025-12-01 08:00 bis 2025-12-03 18:00
```

### Dokumentenmanagement

```
Zeige ablaufende Zertifikate in den nächsten 90 Tagen
```

```
Verknüpfe Dokument DOC-12345, Typ 'TÜV-Abnahme', mit Lok BR185-042,
gültig bis 2026-06-30
```

### Berichte

```
Verfügbarkeitsbericht vom 2025-10-01 bis 2025-10-31
```

```
Kostenbericht für Lok BR185-042 vom 2025-01-01 bis 2025-11-30
```

---

## Konfliktlösung

FLEET-ONE verwendet eine Policy-Matrix mit 11 Regeln zur automatischen Konfliktauflösung:

### 1. Register-Policy (Disponent-Autorität)

**Felder**:
- `work_order.scheduled_start_end`
- `work_order.priority`
- `work_order.planned_workshop_id`

**Regel**: Disponent hat Autorität. Bei Konflikten gewinnt der Disponent.

**Beispiel**: Zwei Disponenten ändern gleichzeitig die geplante Startzeit eines Auftrags. Die Änderung des autorisierten Disponenten wird übernommen.

### 2. Register-Authoritative (Werkstatt-Autorität)

**Felder**:
- `work_order.actual_start_end_ts`

**Regel**: Werkstatt ist die autoritative Quelle für Ist-Zeiten.

**Beispiel**: Werkstatt meldet tatsächliche Fertigstellung um 16:30 Uhr. Diese Zeit ist maßgeblich, auch wenn das System eine andere Prognose hatte.

### 3. Last-Writer-Wins (Gleiche Rolle)

**Felder**:
- `work_order.status`
- `work_order.description`

**Regel**: Bei gleicher Rolle gewinnt die letzte Änderung (nach Zeitstempel).

**Beispiel**: Zwei Werkstattmitarbeiter aktualisieren die Beschreibung. Die neueste Änderung wird übernommen.

### 4. Append-Only (Keine Konflikte)

**Felder**:
- `work_order.used_parts`
- `work_order.measurements`
- `work_order.media`

**Regel**: Alle Einträge werden zusammengeführt (Grow-Set).

**Beispiel**: Zwei Mechaniker dokumentieren Teileverbrauch. Beide Listen werden gemergt: `[Teil A, Teil B] + [Teil C] = [Teil A, Teil B, Teil C]`

### 5. Primary-Flag

**Felder**:
- `work_order.media` (mit `is_primary=true`)

**Regel**: Nur ein Medium kann primär sein. Konflikte erfordern manuelle Auflösung.

**Beispiel**: Zwei Benutzer markieren verschiedene Fotos als primär. System erfordert manuelle Entscheidung.

---

## Fehlerbehebung

### Häufige Fehler

#### 1. Berechtigung verweigert

**Fehler**: `"Zugriff verweigert. Rolle 'workshop' hat keine Berechtigung 'plan:create'"`

**Lösung**: Prüfen Sie Ihre Rolle. Manche Operationen erfordern spezifische Rollen:
- Planung: `dispatcher`
- Werkstattstatus: `workshop`
- Bestellungen: `procurement`
- Rechnungen: `finance`
- Dokumente: `ecm`

#### 2. Backend-Service nicht erreichbar

**Fehler**: `"HTTP 503: maintenance_service nicht erreichbar"`

**Lösung**:
- Prüfen Sie die Service-URLs in Umgebungsvariablen
- Stellen Sie sicher, dass der Backend-Service läuft
- Prüfen Sie Netzwerkverbindung und Firewall-Regeln

#### 3. Ungültige Eingabe

**Fehler**: `"Validierungsfehler: due_date muss im Format YYYY-MM-DD sein"`

**Lösung**: Verwenden Sie das korrekte Datumsformat:
- Datum: `2025-12-31`
- Datum + Zeit: `2025-12-31T14:30:00`

#### 4. Session nicht gefunden

**Fehler**: `"Session 'abc123' nicht gefunden"`

**Lösung**:
- Erstellen Sie eine neue Session via `/fleet-one/session`
- Session-IDs laufen nach 24 Stunden Inaktivität ab

#### 5. Werkzeugaufruf fehlgeschlagen

**Fehler**: `"Tool-Aufruf fehlgeschlagen: get_locomotives → HTTP 404"`

**Lösung**:
- Prüfen Sie, ob die angeforderte Ressource existiert
- Verifizieren Sie die API-Token-Konfiguration
- Prüfen Sie Backend-Logs für detaillierte Fehler

### Debug-Modus

Für detaillierte Fehleranalyse können Sie die Session-Historie abrufen:

```bash
GET /api/v1/fleet-one/session/{session_id}/history
```

Dies zeigt alle Anfragen, Tool-Aufrufe und Antworten der Session.

### Metriken

Überwachen Sie die Agent-Performance:

```bash
GET /api/v1/fleet-one/metrics
```

Liefert:
- Anzahl aktiver Sessions
- Durchschnittliche Antwortzeit
- Tool-Aufruf-Statistiken
- Fehlerrate

### Support

Bei weiteren Problemen:
1. Prüfen Sie die API-Referenz: `docs/FLEET_ONE_API_REFERENCE.md`
2. Konsultieren Sie die Integration-Anleitung: `docs/FLEET_ONE_INTEGRATION.md`
3. Kontaktieren Sie das Entwicklerteam mit Session-ID und Fehlermeldung

---

## Zeitzone

**Wichtig**: FLEET-ONE arbeitet intern mit UTC, konvertiert aber alle Ausgaben automatisch nach **Europe/Berlin**.

**Beispiel**:
- Eingabe: `"geplant vom 2025-12-05 10:00"`
- Intern: `2025-12-05T09:00:00Z` (UTC)
- Ausgabe: `"Geplant: 05.12.2025 10:00 Uhr"` (Berlin-Zeit)

---

## Best Practices

### 1. Session-Nutzung

- Erstellen Sie eine Session pro Benutzer/Schicht
- Verwenden Sie dieselbe Session für zusammenhängende Aufgaben
- Sessions merken sich Kontext (z.B. "erstelle noch einen Auftrag für Werk Hamburg")

### 2. Klare Anfragen

Gute Anfrage:
```
Erstelle Werkstattauftrag für Lok BR185-042, Werk München,
geplant vom 2025-12-05 10:00 bis 2025-12-07 16:00,
Aufgaben: HU, Bremsprüfung
```

Schlechte Anfrage:
```
Mach mal was mit der Lok
```

### 3. Modus forcieren

Wenn die automatische Erkennung nicht passt, können Sie den Modus explizit setzen:

```json
{
  "query": "Zeige Loks",
  "force_mode": "FLOTTE"
}
```

### 4. Fehlerbehandlung

Prüfen Sie immer `success: false` in der Antwort:

```json
{
  "success": false,
  "message": "Zugriff verweigert. Rolle 'viewer' hat keine Berechtigung 'wo:create'",
  "data": null
}
```

---

**Version**: 1.0.0
**Stand**: November 2025
**Entwickelt für**: RailFleet Manager Phase 3
