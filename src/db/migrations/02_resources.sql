-- Resources Migration
-- Tracks, Teams, Shifts, Availabilities

-- Tracks (Workshop Gleise/Pits)
CREATE TABLE IF NOT EXISTS tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    workshop_id UUID REFERENCES workshops(id) ON DELETE CASCADE,
    location VARCHAR(255),
    capabilities JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tracks_workshop ON tracks(workshop_id);
CREATE INDEX IF NOT EXISTS idx_tracks_active ON tracks(is_active) WHERE is_active = true;

COMMENT ON TABLE tracks IS 'Workshop tracks (Gleise/Gruben) for vehicle placement';
COMMENT ON COLUMN tracks.capabilities IS 'Array of capabilities (e.g., ["HU", "ECM", "REPAIR"])';

-- Track Availability Windows
CREATE TABLE IF NOT EXISTS track_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    is_available BOOLEAN DEFAULT true,
    reason VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT track_avail_valid_window CHECK (end_ts > start_ts)
);

CREATE INDEX IF NOT EXISTS idx_track_avail_track ON track_availability(track_id);
CREATE INDEX IF NOT EXISTS idx_track_avail_window ON track_availability(start_ts, end_ts);

COMMENT ON TABLE track_availability IS 'Track availability windows (scheduled or blocked periods)';

-- Teams (Workshop Teams)
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    workshop_id UUID REFERENCES workshops(id) ON DELETE CASCADE,
    skills JSONB DEFAULT '[]'::jsonb,
    max_concurrent_work_orders INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_workshop ON teams(workshop_id);
CREATE INDEX IF NOT EXISTS idx_teams_active ON teams(is_active) WHERE is_active = true;

COMMENT ON TABLE teams IS 'Workshop teams with skills';
COMMENT ON COLUMN teams.skills IS 'Array of team skills (e.g., ["HU", "INSPECTION", "WELDING"])';

-- Team Availability (Shifts)
CREATE TABLE IF NOT EXISTS team_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    is_available BOOLEAN DEFAULT true,
    shift_type VARCHAR(50),
    notes VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT team_avail_valid_window CHECK (end_ts > start_ts)
);

CREATE INDEX IF NOT EXISTS idx_team_avail_team ON team_availability(team_id);
CREATE INDEX IF NOT EXISTS idx_team_avail_window ON team_availability(start_ts, end_ts);

COMMENT ON TABLE team_availability IS 'Team shift windows and availability';
COMMENT ON COLUMN team_availability.shift_type IS 'Shift type (e.g., "EARLY", "LATE", "NIGHT")';

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
