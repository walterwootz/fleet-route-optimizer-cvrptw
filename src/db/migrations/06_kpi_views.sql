-- KPI Views Migration
-- Materialized views for reporting & dashboards

-- Track Utilization (normalized to availability windows)
CREATE OR REPLACE VIEW v_track_utilization AS
SELECT
    t.track_id,
    t.name AS track_name,
    t.workshop_id,
    COUNT(DISTINCT wa.id) AS total_assignments,
    SUM(EXTRACT(EPOCH FROM (wa.scheduled_end_ts - wa.scheduled_start_ts)) / 60) AS total_scheduled_min,
    SUM(
        EXTRACT(EPOCH FROM (ta.end_ts - ta.start_ts)) / 60
    ) AS total_available_min,
    CASE
        WHEN SUM(EXTRACT(EPOCH FROM (ta.end_ts - ta.start_ts)) / 60) > 0 THEN
            (SUM(EXTRACT(EPOCH FROM (wa.scheduled_end_ts - wa.scheduled_start_ts)) / 60) /
             SUM(EXTRACT(EPOCH FROM (ta.end_ts - ta.start_ts)) / 60) * 100)
        ELSE 0
    END AS utilization_pct
FROM tracks t
LEFT JOIN wo_assignment wa ON wa.track_id = t.id AND wa.status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS')
LEFT JOIN track_availability ta ON ta.track_id = t.id AND ta.is_available = true
GROUP BY t.track_id, t.name, t.workshop_id;

COMMENT ON VIEW v_track_utilization IS 'Track utilization normalized to availability windows';

-- On-Time Performance
CREATE OR REPLACE VIEW v_on_time_performance AS
SELECT
    wo.type,
    wo.priority,
    COUNT(*) AS total_orders,
    COUNT(CASE WHEN wo.actual_end <= wa.scheduled_end_ts THEN 1 END) AS on_time_count,
    COUNT(CASE WHEN wo.actual_end > wa.scheduled_end_ts THEN 1 END) AS late_count,
    CASE
        WHEN COUNT(*) > 0 THEN
            (COUNT(CASE WHEN wo.actual_end <= wa.scheduled_end_ts THEN 1 END)::DECIMAL / COUNT(*) * 100)
        ELSE 0
    END AS on_time_pct
FROM work_orders wo
LEFT JOIN wo_assignment wa ON wa.work_order_id = wo.id
WHERE wo.status = 'completed'
GROUP BY wo.type, wo.priority;

COMMENT ON VIEW v_on_time_performance IS 'On-time completion rate by work order type/priority';

-- Vehicle Availability (operational vs. in-workshop)
CREATE OR REPLACE VIEW v_vehicle_availability AS
SELECT
    v.type,
    COUNT(*) AS total_vehicles,
    COUNT(CASE WHEN v.status IN ('available', 'in_service') THEN 1 END) AS available_count,
    COUNT(CASE WHEN v.status IN ('workshop_planned', 'in_workshop') THEN 1 END) AS in_workshop_count,
    COUNT(CASE WHEN v.status = 'out_of_service' THEN 1 END) AS out_of_service_count,
    CASE
        WHEN COUNT(*) > 0 THEN
            (COUNT(CASE WHEN v.status IN ('available', 'in_service') THEN 1 END)::DECIMAL / COUNT(*) * 100)
        ELSE 0
    END AS availability_pct
FROM vehicles v
WHERE v.status != 'retired'
GROUP BY v.type;

COMMENT ON VIEW v_vehicle_availability IS 'Vehicle availability by type';

-- Parts Usage Summary
CREATE OR REPLACE VIEW v_parts_usage_summary AS
SELECT
    pi.part_no,
    pi.name,
    pi.railway_class,
    pi.current_stock,
    pi.min_stock,
    COUNT(up.id) AS usage_count,
    SUM(up.quantity_used) AS total_quantity_used,
    SUM(up.quantity_used * COALESCE(up.unit_price, pi.unit_price)) AS total_cost,
    MAX(up.used_at) AS last_used_at,
    CASE
        WHEN pi.current_stock <= pi.min_stock THEN 'LOW_STOCK'
        WHEN pi.current_stock = 0 THEN 'OUT_OF_STOCK'
        ELSE 'OK'
    END AS stock_status
FROM part_inventory pi
LEFT JOIN used_parts up ON up.part_no = pi.part_no
GROUP BY pi.part_no, pi.name, pi.railway_class, pi.current_stock, pi.min_stock;

COMMENT ON VIEW v_parts_usage_summary IS 'Parts usage and stock status';

-- Maintenance Backlog
CREATE OR REPLACE VIEW v_maintenance_backlog AS
SELECT
    v.type AS vehicle_type,
    wo.type AS maintenance_type,
    wo.priority,
    COUNT(*) AS backlog_count,
    COUNT(CASE WHEN wo.hard_deadline_ts < NOW() THEN 1 END) AS overdue_count,
    COUNT(CASE WHEN wo.hard_deadline_ts < NOW() + INTERVAL '30 days' THEN 1 END) AS due_soon_count,
    MIN(wo.hard_deadline_ts) AS earliest_deadline,
    AVG(EXTRACT(EPOCH FROM (wo.hard_deadline_ts - NOW())) / 86400) AS avg_days_until_deadline
FROM work_orders wo
JOIN vehicles v ON v.id = wo.vehicle_id
WHERE wo.status IN ('draft', 'scheduled')
  AND wo.hard_deadline_ts IS NOT NULL
GROUP BY v.type, wo.type, wo.priority;

COMMENT ON VIEW v_maintenance_backlog IS 'Maintenance backlog with deadline tracking';

-- Solver Performance Metrics
CREATE OR REPLACE VIEW v_solver_metrics AS
SELECT
    DATE_TRUNC('day', ss.created_at) AS solve_date,
    COUNT(*) AS total_solves,
    AVG(ss.solve_time_sec) AS avg_solve_time_sec,
    AVG(ss.objective_value) AS avg_objective_value,
    AVG(ss.scheduled_count::DECIMAL / NULLIF(ss.total_work_orders, 0) * 100) AS avg_scheduled_pct,
    SUM(ss.scheduled_count) AS total_scheduled,
    SUM(ss.unscheduled_count) AS total_unscheduled
FROM solver_solutions ss
GROUP BY DATE_TRUNC('day', ss.created_at)
ORDER BY solve_date DESC;

COMMENT ON VIEW v_solver_metrics IS 'Daily solver performance metrics';
