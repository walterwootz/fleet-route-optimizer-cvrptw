# UTC Timezone Convention

**Version:** 1.0
**Date:** 2025-11-23
**Status:** Active

---

## Overview

All backend services in RailFleet Manager operate exclusively in **UTC** (Coordinated Universal Time). This ensures consistency across distributed systems, mobile/offline clients, and international operations.

## Core Principles

### 1. Backend is UTC-Only
- All timestamps stored in the database use `TIMESTAMPTZ` (timezone-aware)
- All Python `datetime` objects use `datetime.utcnow()`
- API responses return ISO 8601 format with explicit `Z` suffix: `2025-11-23T10:30:00Z`

### 2. Database Layer
```sql
-- All timestamp columns use TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT NOW(),
updated_at TIMESTAMPTZ DEFAULT NOW(),

-- PostgreSQL NOW() returns UTC when timezone is set to UTC
-- Verify with: SHOW TIMEZONE; (should be 'UTC')
```

### 3. Application Layer (Python/SQLAlchemy)
```python
from datetime import datetime

# ✓ CORRECT: Always use utcnow()
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# ✗ WRONG: Never use now()
created_at = Column(DateTime, default=datetime.now, nullable=False)  # DON'T DO THIS!
```

### 4. API Layer (FastAPI/Pydantic)
```python
from pydantic import BaseModel
from datetime import datetime

class Response(BaseModel):
    created_at: datetime  # Pydantic serializes to ISO 8601 with 'Z'

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%SZ')  # Explicit Z suffix
        }
```

### 5. Frontend/Client Responsibility
- **Backend sends:** `2025-11-23T10:30:00Z` (UTC)
- **Frontend localizes:** `23.11.2025 11:30 CET` (Europe/Berlin)
- **Mobile apps localize:** Based on device timezone

---

## Implementation Checklist

### ✅ Database
- [x] All `created_at`, `updated_at` columns use `TIMESTAMPTZ`
- [x] All `*_ts` columns use `TIMESTAMPTZ`
- [x] PostgreSQL timezone set to UTC
- [x] Migration SQL uses `NOW()` (which returns UTC)

### ✅ Models (SQLAlchemy)
- [x] Vehicle model: `datetime.utcnow()`
- [x] MaintenanceTask model: `datetime.utcnow()`
- [x] WorkOrder model: `datetime.utcnow()`
- [x] Workshop model: `datetime.utcnow()`
- [x] TransferPlan model: `datetime.utcnow()`
- [x] Staff model: `datetime.utcnow()`
- [x] DocumentLink model: `datetime.utcnow()`

### ✅ API Responses
- [x] Pydantic schemas serialize to ISO 8601
- [x] All datetime fields have `datetime` type
- [x] FastAPI JSON encoder configured for UTC

### ✅ Documentation
- [x] UTC convention documented
- [x] API docs specify UTC format
- [x] Frontend integration guide

---

## Examples

### Storing Timestamps
```python
# Backend stores in UTC
from datetime import datetime

new_vehicle = Vehicle(
    asset_id="185123",
    created_at=datetime.utcnow(),  # Stored as UTC
    last_service_date=datetime.utcnow()
)
```

### API Request/Response
```json
{
  "scheduled_departure_ts": "2025-11-23T08:00:00Z",
  "scheduled_arrival_ts": "2025-11-23T14:00:00Z",
  "created_at": "2025-11-23T10:30:45Z"
}
```

### Client-Side Localization (Frontend)
```javascript
// JavaScript example
const utcTimestamp = "2025-11-23T10:30:00Z";
const localTime = new Date(utcTimestamp).toLocaleString('de-DE', {
  timeZone: 'Europe/Berlin',
  dateStyle: 'short',
  timeStyle: 'short'
});
// Output: "23.11.25, 11:30" (CET = UTC+1)
```

### Python Client Localization
```python
from datetime import datetime
import pytz

# Parse UTC from API
utc_time = datetime.fromisoformat("2025-11-23T10:30:00Z")

# Convert to Berlin timezone
berlin_tz = pytz.timezone('Europe/Berlin')
berlin_time = utc_time.astimezone(berlin_tz)
# Output: 2025-11-23 11:30:00+01:00 CET
```

---

## Common Pitfalls

### ❌ DON'T: Use `datetime.now()`
```python
# This uses local system time, NOT UTC!
created_at = datetime.now()  # WRONG!
```

### ❌ DON'T: Assume client timezone
```python
# Backend should never make timezone assumptions
user_timezone = "Europe/Berlin"  # WRONG! Backend stays UTC
```

### ❌ DON'T: Store timezone-naive datetimes
```python
# Always use timezone-aware
naive_dt = datetime(2025, 11, 23, 10, 30)  # WRONG!
aware_dt = datetime(2025, 11, 23, 10, 30, tzinfo=timezone.utc)  # CORRECT
```

### ✅ DO: Always use UTC in backend
```python
from datetime import datetime

utc_now = datetime.utcnow()  # CORRECT!
```

### ✅ DO: Let frontend handle timezones
```python
# Backend returns UTC
return {"created_at": datetime.utcnow()}

# Frontend localizes to user's timezone
// JavaScript handles conversion automatically
```

---

## Testing UTC Compliance

### Database Check
```sql
-- Verify PostgreSQL timezone
SHOW TIMEZONE;  -- Should return 'UTC'

-- Check timestamp column types
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type LIKE '%timestamp%';
```

### Python Check
```python
import datetime

# Verify UTC usage
dt = datetime.datetime.utcnow()
assert dt.tzinfo is None  # utcnow() returns naive datetime
assert dt.hour <= 23  # UTC always in 0-23 range

# For timezone-aware, use:
from datetime import timezone
dt_aware = datetime.datetime.now(timezone.utc)
assert dt_aware.tzinfo == timezone.utc
```

---

## References

- **ISO 8601**: International datetime format standard
- **PostgreSQL TIMESTAMPTZ**: [Docs](https://www.postgresql.org/docs/current/datatype-datetime.html)
- **Python datetime**: [Docs](https://docs.python.org/3/library/datetime.html)
- **FastAPI datetime**: [Docs](https://fastapi.tiangolo.com/tutorial/encoder/)

---

## Compliance Status

✅ **Phase 2 compliant**
All backend services follow UTC convention as specified in GAP_ANALYSIS.md WP6.

**Last Audit:** 2025-11-23
**Next Review:** Every major release
