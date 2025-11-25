-- Work Orders Migration
-- Extends existing work_orders table with scheduler-specific fields

-- Add scheduler-specific columns to work_orders (if not exists)
ALTER TABLE work_orders
ADD COLUMN IF NOT EXISTS duration_min INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS required_skills JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS required_parts JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS earliest_start_ts TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS latest_end_ts TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS hard_deadline_ts TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS incompatible_assets JSONB DEFAULT '[]'::jsonb;

-- Indices for scheduler queries
CREATE INDEX IF NOT EXISTS idx_wo_earliest_start ON work_orders(earliest_start_ts) WHERE earliest_start_ts IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_wo_hard_deadline ON work_orders(hard_deadline_ts) WHERE hard_deadline_ts IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_wo_status_priority ON work_orders(status, priority);

-- Comments
COMMENT ON COLUMN work_orders.duration_min IS 'Duration in minutes (15-min slots)';
COMMENT ON COLUMN work_orders.required_skills IS 'Array of required skills (e.g., ["HU", "INSPECTION"])';
COMMENT ON COLUMN work_orders.required_parts IS 'Array of required parts with quantities';
COMMENT ON COLUMN work_orders.earliest_start_ts IS 'Earliest possible start time (UTC)';
COMMENT ON COLUMN work_orders.latest_end_ts IS 'Latest acceptable end time (UTC)';
COMMENT ON COLUMN work_orders.hard_deadline_ts IS 'Hard deadline - must finish before this (UTC)';
COMMENT ON COLUMN work_orders.incompatible_assets IS 'Asset IDs that cannot be in workshop simultaneously';
