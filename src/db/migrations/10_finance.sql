-- Finance Migration (WP11)
-- Invoice management, budget tracking, and cost centers

-- Cost Centers Table
CREATE TABLE IF NOT EXISTS cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_code VARCHAR(50),
    is_active BOOLEAN DEFAULT true NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cost_centers_code ON cost_centers(code);
CREATE INDEX IF NOT EXISTS idx_cost_centers_active ON cost_centers(is_active) WHERE is_active = true;

COMMENT ON TABLE cost_centers IS 'Cost center master data (Kostenstellen)';

-- Trigger for updated_at on cost_centers
CREATE TRIGGER update_cost_centers_updated_at BEFORE UPDATE ON cost_centers
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Invoices Table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    supplier_id UUID REFERENCES suppliers(id) NOT NULL,
    purchase_order_id UUID REFERENCES purchase_orders(id),
    work_order_id UUID,
    invoice_date TIMESTAMPTZ NOT NULL,
    due_date TIMESTAMPTZ,
    payment_date TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL,
    tax_amount NUMERIC(12,2) DEFAULT 0 NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR' NOT NULL,
    notes TEXT,
    attachment_url VARCHAR(500),
    created_by UUID,
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_supplier ON invoices(supplier_id);
CREATE INDEX IF NOT EXISTS idx_invoices_po ON invoices(purchase_order_id) WHERE purchase_order_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_wo ON invoices(work_order_id) WHERE work_order_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);

COMMENT ON TABLE invoices IS 'Invoice management (Eingangsrechnungen)';
COMMENT ON COLUMN invoices.status IS 'DRAFT, REVIEWED, APPROVED, EXPORTED';

-- Trigger for updated_at on invoices
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Invoice Lines Table
CREATE TABLE IF NOT EXISTS invoice_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE NOT NULL,
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    part_no VARCHAR(100) REFERENCES part_inventory(part_no),
    purchase_order_line_id UUID REFERENCES purchase_order_lines(id),
    quantity INTEGER,
    unit_price NUMERIC(10,2) NOT NULL,
    line_total NUMERIC(12,2) NOT NULL,
    tax_amount NUMERIC(12,2) DEFAULT 0 NOT NULL,
    cost_center VARCHAR(50),
    cost_bearer VARCHAR(50),
    account_code VARCHAR(50),
    variance NUMERIC(12,2),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_invoice_lines_invoice ON invoice_lines(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_lines_part ON invoice_lines(part_no) WHERE part_no IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoice_lines_po_line ON invoice_lines(purchase_order_line_id) WHERE purchase_order_line_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoice_lines_cost_center ON invoice_lines(cost_center) WHERE cost_center IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_invoice_lines_unique ON invoice_lines(invoice_id, line_number);

COMMENT ON TABLE invoice_lines IS 'Invoice line items with cost allocation';
COMMENT ON COLUMN invoice_lines.cost_center IS 'Kostenstelle';
COMMENT ON COLUMN invoice_lines.cost_bearer IS 'Kostenträger';
COMMENT ON COLUMN invoice_lines.variance IS 'Price/quantity variance vs PO';

-- Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period VARCHAR(7) NOT NULL,
    cost_center VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    planned_amount NUMERIC(12,2) DEFAULT 0 NOT NULL,
    forecast_amount NUMERIC(12,2) DEFAULT 0 NOT NULL,
    actual_amount NUMERIC(12,2) DEFAULT 0 NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR' NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(period);
CREATE INDEX IF NOT EXISTS idx_budgets_cost_center ON budgets(cost_center);
CREATE UNIQUE INDEX IF NOT EXISTS idx_budgets_unique ON budgets(period, cost_center, category);

COMMENT ON TABLE budgets IS 'Budget tracking by period and cost center';
COMMENT ON COLUMN budgets.period IS 'Period in YYYY-MM format';
COMMENT ON COLUMN budgets.category IS 'Budget category (parts, labor, overhead)';

-- Trigger for updated_at on budgets
CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON budgets
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
