-- Work Order Assignments Migration
-- Stores solver results (scheduled assignments)

CREATE TABLE IF NOT EXISTS wo_assignment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_id UUID REFERENCES work_orders(id) ON DELETE CASCADE,
    solution_id UUID,
    track_id UUID REFERENCES tracks(id),
    team_id UUID REFERENCES teams(id),
    scheduled_start_ts TIMESTAMPTZ NOT NULL,
    scheduled_end_ts TIMESTAMPTZ NOT NULL,
    start_slot INTEGER,
    end_slot INTEGER,
    status VARCHAR(50) DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT wo_assign_valid_window CHECK (scheduled_end_ts > scheduled_start_ts)
);

CREATE INDEX IF NOT EXISTS idx_wo_assign_wo ON wo_assignment(work_order_id);
CREATE INDEX IF NOT EXISTS idx_wo_assign_solution ON wo_assignment(solution_id);
CREATE INDEX IF NOT EXISTS idx_wo_assign_track ON wo_assignment(track_id);
CREATE INDEX IF NOT EXISTS idx_wo_assign_team ON wo_assignment(team_id);
CREATE INDEX IF NOT EXISTS idx_wo_assign_window ON wo_assignment(scheduled_start_ts, scheduled_end_ts);
CREATE INDEX IF NOT EXISTS idx_wo_assign_status ON wo_assignment(status);

COMMENT ON TABLE wo_assignment IS 'Scheduler solution results - work order assignments to tracks/teams';
COMMENT ON COLUMN wo_assignment.solution_id IS 'Groups assignments from same solver run';
COMMENT ON COLUMN wo_assignment.start_slot IS 'Slot number for 15-min intervals';
COMMENT ON COLUMN wo_assignment.status IS 'SCHEDULED, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED';

-- Solver Solutions Metadata
CREATE TABLE IF NOT EXISTS solver_solutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solution_id UUID UNIQUE NOT NULL,
    solver_status VARCHAR(50),
    objective_value DECIMAL(12,2),
    solve_time_sec DECIMAL(8,3),
    total_work_orders INTEGER,
    scheduled_count INTEGER,
    unscheduled_count INTEGER,
    problem_spec JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_solver_sol_created ON solver_solutions(created_at DESC);

COMMENT ON TABLE solver_solutions IS 'Solver run metadata and metrics';
