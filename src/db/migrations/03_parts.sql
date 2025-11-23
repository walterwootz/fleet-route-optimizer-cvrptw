-- Parts & Inventory Migration
-- Part inventory, stock locations, used parts tracking

-- Part Inventory (extends if exists, creates if not)
CREATE TABLE IF NOT EXISTS part_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_no VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    railway_class VARCHAR(50),
    unit VARCHAR(20) DEFAULT 'pc',
    min_stock INTEGER DEFAULT 0,
    current_stock INTEGER DEFAULT 0,
    preferred_supplier_id UUID,
    unit_price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT part_inv_stock_positive CHECK (current_stock >= 0)
);

CREATE INDEX IF NOT EXISTS idx_part_inv_part_no ON part_inventory(part_no);
CREATE INDEX IF NOT EXISTS idx_part_inv_active ON part_inventory(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_part_inv_low_stock ON part_inventory(current_stock) WHERE current_stock <= min_stock;

COMMENT ON TABLE part_inventory IS 'Part catalog and stock levels';
COMMENT ON COLUMN part_inventory.railway_class IS 'Criticality: CRITICAL, STANDARD, WEAR_PART';

-- Part Availability (for scheduler)
CREATE TABLE IF NOT EXISTS part_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_no VARCHAR(100) REFERENCES part_inventory(part_no),
    available_qty INTEGER NOT NULL,
    available_from_ts TIMESTAMPTZ NOT NULL,
    location VARCHAR(255),
    reservation_work_order_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT part_avail_qty_positive CHECK (available_qty > 0)
);

CREATE INDEX IF NOT EXISTS idx_part_avail_part ON part_availability(part_no);
CREATE INDEX IF NOT EXISTS idx_part_avail_time ON part_availability(available_from_ts);

COMMENT ON TABLE part_availability IS 'Part availability windows for scheduler';

-- Used Parts (consumption tracking per work order)
CREATE TABLE IF NOT EXISTS used_parts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_id UUID REFERENCES work_orders(id) ON DELETE CASCADE,
    part_no VARCHAR(100) REFERENCES part_inventory(part_no),
    quantity_used INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    used_at TIMESTAMPTZ DEFAULT NOW(),
    recorded_by UUID,
    notes VARCHAR(500),
    CONSTRAINT used_parts_qty_positive CHECK (quantity_used > 0)
);

CREATE INDEX IF NOT EXISTS idx_used_parts_wo ON used_parts(work_order_id);
CREATE INDEX IF NOT EXISTS idx_used_parts_part ON used_parts(part_no);
CREATE INDEX IF NOT EXISTS idx_used_parts_time ON used_parts(used_at);

COMMENT ON TABLE used_parts IS 'Parts consumption per work order (append-only)';

-- Trigger for stock updates on used_parts insert
CREATE OR REPLACE FUNCTION decrement_part_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE part_inventory
    SET current_stock = current_stock - NEW.quantity_used,
        updated_at = NOW()
    WHERE part_no = NEW.part_no;

    -- Warn if stock goes negative (but allow for tracking)
    IF (SELECT current_stock FROM part_inventory WHERE part_no = NEW.part_no) < 0 THEN
        RAISE WARNING 'Part % stock is negative', NEW.part_no;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER used_parts_decrement_stock
AFTER INSERT ON used_parts
FOR EACH ROW EXECUTE FUNCTION decrement_part_stock();

-- Trigger for updated_at
CREATE TRIGGER update_part_inventory_updated_at BEFORE UPDATE ON part_inventory
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
