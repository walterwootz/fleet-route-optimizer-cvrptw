-- Procurement Migration (WP10)
-- Supplier management and purchase order workflow

-- Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    vat_id VARCHAR(50),
    payment_terms VARCHAR(100),
    currency VARCHAR(3) DEFAULT 'EUR' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code);
CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active) WHERE is_active = true;

COMMENT ON TABLE suppliers IS 'Supplier master data for procurement';
COMMENT ON COLUMN suppliers.payment_terms IS 'Payment terms (e.g., NET30, NET60)';
COMMENT ON COLUMN suppliers.vat_id IS 'VAT identification number';

-- Trigger for updated_at on suppliers
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Purchase Orders Table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id UUID REFERENCES suppliers(id) NOT NULL,
    work_order_id UUID,
    status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL,
    order_date TIMESTAMPTZ,
    expected_delivery_date TIMESTAMPTZ,
    received_date TIMESTAMPTZ,
    delivery_location_id UUID REFERENCES stock_locations(id),
    total_amount NUMERIC(12,2) DEFAULT 0 NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR' NOT NULL,
    notes TEXT,
    created_by UUID,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_work_order ON purchase_orders(work_order_id) WHERE work_order_id IS NOT NULL;

COMMENT ON TABLE purchase_orders IS 'Purchase orders for procurement';
COMMENT ON COLUMN purchase_orders.status IS 'DRAFT, APPROVED, ORDERED, RECEIVED, CLOSED';

-- Trigger for updated_at on purchase_orders
CREATE TRIGGER update_purchase_orders_updated_at BEFORE UPDATE ON purchase_orders
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Purchase Order Lines Table
CREATE TABLE IF NOT EXISTS purchase_order_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE NOT NULL,
    line_number INTEGER NOT NULL,
    part_no VARCHAR(100) REFERENCES part_inventory(part_no) NOT NULL,
    description TEXT,
    quantity_ordered INTEGER NOT NULL CHECK (quantity_ordered > 0),
    quantity_received INTEGER DEFAULT 0 NOT NULL CHECK (quantity_received >= 0),
    unit_price NUMERIC(10,2) NOT NULL,
    line_total NUMERIC(12,2) NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_po_lines_po ON purchase_order_lines(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_po_lines_part ON purchase_order_lines(part_no);
CREATE UNIQUE INDEX IF NOT EXISTS idx_po_lines_unique ON purchase_order_lines(purchase_order_id, line_number);

COMMENT ON TABLE purchase_order_lines IS 'Purchase order line items';
COMMENT ON COLUMN purchase_order_lines.line_number IS 'Sequential line number within PO';
