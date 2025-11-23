-- Docs Service Migration (ECM-Light)
-- Document management with expiration tracking and audit trail

-- Document Links (Main document registry)
CREATE TABLE IF NOT EXISTS document_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    description VARCHAR(2000),
    file_url VARCHAR(1000),
    file_hash VARCHAR(64),
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    issue_date TIMESTAMPTZ,
    expiration_date TIMESTAMPTZ,
    reminder_days_before INTEGER DEFAULT 30 NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
    staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
    workshop_id UUID REFERENCES workshops(id) ON DELETE SET NULL,
    work_order_id UUID REFERENCES work_orders(id) ON DELETE SET NULL,
    tags_json JSONB DEFAULT '[]'::jsonb,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    is_public BOOLEAN DEFAULT false NOT NULL,
    access_level VARCHAR(50) DEFAULT 'internal' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    last_accessed_at TIMESTAMPTZ,
    last_accessed_by UUID,
    CONSTRAINT document_valid_type CHECK (document_type IN (
        'certificate', 'license', 'inspection_report', 'maintenance_log',
        'technical_drawing', 'compliance_doc', 'invoice', 'contract', 'other'
    )),
    CONSTRAINT document_valid_status CHECK (status IN (
        'active', 'expired', 'expiring_soon', 'archived', 'revoked'
    )),
    CONSTRAINT document_valid_access CHECK (access_level IN (
        'public', 'internal', 'restricted', 'confidential'
    ))
);

CREATE INDEX IF NOT EXISTS idx_doc_id ON document_links(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_type ON document_links(document_type);
CREATE INDEX IF NOT EXISTS idx_doc_status ON document_links(status);
CREATE INDEX IF NOT EXISTS idx_doc_expiration ON document_links(expiration_date) WHERE expiration_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_vehicle ON document_links(vehicle_id) WHERE vehicle_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_staff ON document_links(staff_id) WHERE staff_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_workshop ON document_links(workshop_id) WHERE workshop_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_work_order ON document_links(work_order_id) WHERE work_order_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_tags ON document_links USING gin(tags_json);

COMMENT ON TABLE document_links IS 'ECM-Light document registry with expiration tracking';
COMMENT ON COLUMN document_links.file_hash IS 'SHA-256 hash for file integrity verification';
COMMENT ON COLUMN document_links.reminder_days_before IS 'Days before expiration to trigger alerts';
COMMENT ON COLUMN document_links.tags_json IS 'Tags for categorization: ["safety", "critical", "regulatory"]';

-- Document Versions (Version control)
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_link_id UUID REFERENCES document_links(id) ON DELETE CASCADE NOT NULL,
    version_number INTEGER NOT NULL,
    version_label VARCHAR(50),
    change_description VARCHAR(1000),
    file_url VARCHAR(1000),
    file_hash VARCHAR(64),
    file_size_bytes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT version_positive CHECK (version_number > 0),
    UNIQUE (document_link_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_doc_version_link ON document_versions(document_link_id);
CREATE INDEX IF NOT EXISTS idx_doc_version_number ON document_versions(document_link_id, version_number);

COMMENT ON TABLE document_versions IS 'Document version history for audit and rollback';

-- Document Access Log (Audit trail - append-only)
CREATE TABLE IF NOT EXISTS document_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_link_id UUID REFERENCES document_links(id) ON DELETE CASCADE NOT NULL,
    accessed_by UUID NOT NULL,
    access_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT access_valid_type CHECK (access_type IN ('view', 'download', 'edit', 'delete', 'share'))
);

CREATE INDEX IF NOT EXISTS idx_access_log_doc ON document_access_log(document_link_id);
CREATE INDEX IF NOT EXISTS idx_access_log_user ON document_access_log(accessed_by);
CREATE INDEX IF NOT EXISTS idx_access_log_time ON document_access_log(accessed_at);

COMMENT ON TABLE document_access_log IS 'Append-only audit trail for document access';

-- Prevent UPDATE/DELETE on access log (WORM - Write Once Read Many)
CREATE RULE document_access_log_no_update AS ON UPDATE TO document_access_log DO INSTEAD NOTHING;
CREATE RULE document_access_log_no_delete AS ON DELETE TO document_access_log DO INSTEAD NOTHING;

-- Trigger to update updated_at for document_links
CREATE TRIGGER update_document_links_updated_at BEFORE UPDATE ON document_links
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View: Expiring Documents (documents expiring within reminder window)
CREATE OR REPLACE VIEW v_expiring_documents AS
SELECT
    dl.id,
    dl.document_id,
    dl.title,
    dl.document_type,
    dl.expiration_date,
    dl.reminder_days_before,
    (dl.expiration_date - NOW()) AS days_until_expiration,
    dl.vehicle_id,
    dl.staff_id,
    dl.workshop_id,
    dl.work_order_id,
    dl.status,
    CASE
        WHEN dl.expiration_date < NOW() THEN 'expired'
        WHEN dl.expiration_date < NOW() + (dl.reminder_days_before || ' days')::INTERVAL THEN 'expiring_soon'
        ELSE 'ok'
    END AS expiration_status
FROM document_links dl
WHERE dl.expiration_date IS NOT NULL
  AND dl.status IN ('active', 'expiring_soon')
ORDER BY dl.expiration_date ASC;

COMMENT ON VIEW v_expiring_documents IS 'Documents expiring within reminder window for alerts';
