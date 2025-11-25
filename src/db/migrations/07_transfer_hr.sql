-- Transfer & HR Services Migration
-- Transfer plans, staff management, and assignments

-- Transfer Plans (Locomotive movements between locations)
CREATE TABLE IF NOT EXISTS transfer_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id VARCHAR(50) UNIQUE NOT NULL,
    from_location VARCHAR(255) NOT NULL,
    to_location VARCHAR(255) NOT NULL,
    scheduled_departure_ts TIMESTAMPTZ NOT NULL,
    scheduled_arrival_ts TIMESTAMPTZ NOT NULL,
    actual_departure_ts TIMESTAMPTZ,
    actual_arrival_ts TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    priority VARCHAR(50) NOT NULL DEFAULT 'normal',
    distance_km INTEGER,
    estimated_duration_min INTEGER,
    route_notes VARCHAR(1000),
    metadata_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT transfer_plan_valid_schedule CHECK (scheduled_arrival_ts > scheduled_departure_ts),
    CONSTRAINT transfer_plan_valid_status CHECK (status IN ('draft', 'scheduled', 'in_progress', 'completed', 'cancelled')),
    CONSTRAINT transfer_plan_valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

CREATE INDEX IF NOT EXISTS idx_transfer_plan_id ON transfer_plans(plan_id);
CREATE INDEX IF NOT EXISTS idx_transfer_departure ON transfer_plans(scheduled_departure_ts);
CREATE INDEX IF NOT EXISTS idx_transfer_status ON transfer_plans(status);
CREATE INDEX IF NOT EXISTS idx_transfer_from_location ON transfer_plans(from_location);
CREATE INDEX IF NOT EXISTS idx_transfer_to_location ON transfer_plans(to_location);

COMMENT ON TABLE transfer_plans IS 'Locomotive transfer/movement plans between depots and locations';
COMMENT ON COLUMN transfer_plans.metadata_json IS 'Route details, track restrictions, special handling notes';

-- Transfer Assignments (Vehicle-to-Plan assignments)
CREATE TABLE IF NOT EXISTS transfer_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_plan_id UUID REFERENCES transfer_plans(id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    position_in_convoy INTEGER,
    driver_id UUID,
    is_confirmed VARCHAR(50) DEFAULT 'pending' NOT NULL,
    confirmation_notes VARCHAR(500),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    assigned_by UUID,
    CONSTRAINT transfer_assign_valid_status CHECK (is_confirmed IN ('pending', 'confirmed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_transfer_assign_plan ON transfer_assignments(transfer_plan_id);
CREATE INDEX IF NOT EXISTS idx_transfer_assign_vehicle ON transfer_assignments(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_transfer_assign_driver ON transfer_assignments(driver_id);
CREATE INDEX IF NOT EXISTS idx_transfer_assign_status ON transfer_assignments(is_confirmed);

COMMENT ON TABLE transfer_assignments IS 'Assigns vehicles and drivers to transfer plans';
COMMENT ON COLUMN transfer_assignments.position_in_convoy IS 'Order in multi-vehicle transfers (1, 2, 3...)';

-- Staff (Personnel)
CREATE TABLE IF NOT EXISTS staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    employee_number VARCHAR(50),
    skills_json JSONB DEFAULT '[]'::jsonb,
    certifications_json JSONB DEFAULT '[]'::jsonb,
    home_depot VARCHAR(255),
    workshop_id UUID REFERENCES workshops(id),
    max_weekly_hours INTEGER DEFAULT 40 NOT NULL,
    is_available BOOLEAN DEFAULT true NOT NULL,
    availability_notes VARCHAR(500),
    hired_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT staff_valid_role CHECK (role IN ('driver', 'mechanic', 'technician', 'dispatcher', 'supervisor', 'manager')),
    CONSTRAINT staff_valid_status CHECK (status IN ('active', 'on_leave', 'sick_leave', 'training', 'inactive'))
);

CREATE INDEX IF NOT EXISTS idx_staff_id ON staff(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_employee_number ON staff(employee_number);
CREATE INDEX IF NOT EXISTS idx_staff_role ON staff(role);
CREATE INDEX IF NOT EXISTS idx_staff_status ON staff(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_staff_workshop ON staff(workshop_id);
CREATE INDEX IF NOT EXISTS idx_staff_available ON staff(is_available) WHERE is_available = true;

COMMENT ON TABLE staff IS 'Personnel/staff management for drivers, mechanics, technicians';
COMMENT ON COLUMN staff.skills_json IS 'Array of skills: ["HU", "INSPECTION", "WELDING", etc.]';
COMMENT ON COLUMN staff.certifications_json IS 'Licenses, certifications with validity dates';

-- Staff Assignments (Work assignments for personnel)
CREATE TABLE IF NOT EXISTS staff_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID REFERENCES staff(id) ON DELETE CASCADE NOT NULL,
    work_order_id UUID REFERENCES work_orders(id) ON DELETE CASCADE,
    transfer_plan_id UUID REFERENCES transfer_plans(id) ON DELETE CASCADE,
    scheduled_start_ts TIMESTAMPTZ NOT NULL,
    scheduled_end_ts TIMESTAMPTZ NOT NULL,
    actual_start_ts TIMESTAMPTZ,
    actual_end_ts TIMESTAMPTZ,
    role_on_assignment VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    planned_hours INTEGER,
    actual_hours INTEGER,
    assignment_notes VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT staff_assign_valid_window CHECK (scheduled_end_ts > scheduled_start_ts),
    CONSTRAINT staff_assign_valid_status CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    CONSTRAINT staff_assign_one_target CHECK (
        (work_order_id IS NOT NULL AND transfer_plan_id IS NULL) OR
        (work_order_id IS NULL AND transfer_plan_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_staff_assign_staff ON staff_assignments(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_assign_wo ON staff_assignments(work_order_id);
CREATE INDEX IF NOT EXISTS idx_staff_assign_transfer ON staff_assignments(transfer_plan_id);
CREATE INDEX IF NOT EXISTS idx_staff_assign_window ON staff_assignments(scheduled_start_ts, scheduled_end_ts);
CREATE INDEX IF NOT EXISTS idx_staff_assign_status ON staff_assignments(status);

COMMENT ON TABLE staff_assignments IS 'Assigns staff to work orders, transfers, or shifts';
COMMENT ON COLUMN staff_assignments.role_on_assignment IS 'Role on specific assignment: Lead Mechanic, Assistant, etc.';
COMMENT ON CONSTRAINT staff_assign_one_target ON staff_assignments IS 'Assignment must be to either work_order OR transfer, not both';

-- Trigger to update updated_at for transfer_plans
CREATE TRIGGER update_transfer_plans_updated_at BEFORE UPDATE ON transfer_plans
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at for staff
CREATE TRIGGER update_staff_updated_at BEFORE UPDATE ON staff
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
