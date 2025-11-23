-- Event Log & Conflicts Migration
-- Append-only event log for sync, conflict tracking

-- Event Log (Append-Only, WORM)
CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload_json JSONB NOT NULL,
    actor_id UUID,
    actor_role VARCHAR(50),
    device_id VARCHAR(100),
    source_ts TIMESTAMPTZ,
    server_received_ts TIMESTAMPTZ DEFAULT NOW(),
    idempotency_key VARCHAR(100),
    CONSTRAINT event_log_append_only CHECK (id > 0)
);

CREATE INDEX IF NOT EXISTS idx_event_log_entity ON event_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_event_log_received ON event_log(server_received_ts DESC);
CREATE INDEX IF NOT EXISTS idx_event_log_device ON event_log(device_id);
CREATE INDEX IF NOT EXISTS idx_event_log_idempotency ON event_log(idempotency_key) WHERE idempotency_key IS NOT NULL;

COMMENT ON TABLE event_log IS 'Append-only event log for offline-first sync (WORM)';
COMMENT ON COLUMN event_log.source_ts IS 'Timestamp from client (may be backdated if offline)';
COMMENT ON COLUMN event_log.server_received_ts IS 'Server timestamp (authoritative, UTC)';

-- Enforce append-only (no UPDATE/DELETE)
CREATE RULE event_log_no_update AS ON UPDATE TO event_log DO INSTEAD NOTHING;
CREATE RULE event_log_no_delete AS ON DELETE TO event_log DO INSTEAD NOTHING;

-- Conflicts (extends existing sync_conflicts or creates)
CREATE TABLE IF NOT EXISTS sync_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conflict_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    server_value JSONB,
    client_value JSONB,
    conflict_type VARCHAR(50),
    is_resolved BOOLEAN DEFAULT false,
    resolved_value JSONB,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID,
    source_device VARCHAR(100),
    source_role VARCHAR(50),
    source_event_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_conflict_entity ON sync_conflicts(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_conflict_unresolved ON sync_conflicts(is_resolved) WHERE is_resolved = false;
CREATE INDEX IF NOT EXISTS idx_conflict_created ON sync_conflicts(created_at DESC);

COMMENT ON TABLE sync_conflicts IS 'Sync conflicts detected by policy engine';
COMMENT ON COLUMN sync_conflicts.conflict_type IS 'PLAN_CONFLICT, AUTHORITY_VIOLATION, CONCURRENT_UPDATE, etc.';

-- Audit Log (for compliance - ECM)
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value_json JSONB,
    new_value_json JSONB,
    actor_id UUID,
    actor_role VARCHAR(50),
    actor_ip VARCHAR(45),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor_id);

COMMENT ON TABLE audit_log IS 'Audit trail for compliance (ECM, regulatory)';

-- Enforce audit_log append-only
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
