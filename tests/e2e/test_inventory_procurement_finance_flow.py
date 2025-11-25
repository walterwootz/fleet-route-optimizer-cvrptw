"""
E2E Integration Test: Inventory → Procurement → Finance Flow

Test Scenario:
1. Create Part
2. Create Stock Location
3. Create Supplier
4. Create Purchase Order with lines
5. Approve PO
6. Order PO
7. Receive PO (generates Stock Moves)
8. Verify Stock Moves created
9. Create Invoice
10. Match Invoice against PO
11. Approve Invoice (updates Budget)
12. Verify Budget updated
13. Check Reports
"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime, timedelta
from src.app import app

client = TestClient(app)


@pytest.fixture
def auth_token(test_db):
    """Get authentication token for tests."""
    # Login with test user
    response = client.post("/api/v1/auth/login", data={
        "username": "test@railfleet.com",
        "password": "test123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestInventoryProcurementFinanceFlow:
    """E2E test for complete inventory-procurement-finance workflow."""

    def test_complete_workflow(self, test_db, auth_headers):
        """Test complete workflow from part creation to budget update."""

        # ===== 1. Create Part =====
        part_data = {
            "part_no": "TEST-BRK-001",
            "name": "Test Brake Pad Set",
            "railway_class": "CRITICAL",
            "unit": "set",
            "min_stock": 10,
            "current_stock": 0,
            "unit_price": 125.50,
            "is_active": True
        }
        response = client.post("/api/v1/parts", json=part_data, headers=auth_headers)
        assert response.status_code == 201
        part = response.json()
        part_id = part["id"]
        assert part["part_no"] == "TEST-BRK-001"
        print(f"✅ Part created: {part_id}")

        # ===== 2. Create Stock Location =====
        location_data = {
            "location_code": "TEST-WS-001",
            "name": "Test Workshop Storage",
            "location_type": "WORKSHOP",
            "is_active": True
        }
        response = client.post("/api/v1/stock/locations", json=location_data, headers=auth_headers)
        assert response.status_code == 201
        location = response.json()
        location_id = location["id"]
        assert location["location_code"] == "TEST-WS-001"
        print(f"✅ Location created: {location_id}")

        # ===== 3. Create Supplier =====
        supplier_data = {
            "supplier_code": "TEST-SUP-001",
            "name": "Test Railway Parts GmbH",
            "email": "test@railparts.de",
            "vat_id": "DE999999999",
            "payment_terms": "NET30",
            "is_active": True
        }
        response = client.post("/api/v1/suppliers", json=supplier_data, headers=auth_headers)
        assert response.status_code == 201
        supplier = response.json()
        supplier_id = supplier["id"]
        assert supplier["supplier_code"] == "TEST-SUP-001"
        print(f"✅ Supplier created: {supplier_id}")

        # ===== 4. Create Purchase Order =====
        po_data = {
            "po_number": "TEST-PO-001",
            "supplier_id": supplier_id,
            "expected_delivery_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "delivery_location_id": location_id,
            "lines": [
                {
                    "line_number": 1,
                    "part_no": "TEST-BRK-001",
                    "quantity_ordered": 50,
                    "unit_price": 125.50
                }
            ]
        }
        response = client.post("/api/v1/purchase_orders", json=po_data, headers=auth_headers)
        assert response.status_code == 201
        po = response.json()
        po_id = po["id"]
        po_line_id = po["lines"][0]["id"]
        assert po["status"] == "DRAFT"
        assert po["total_amount"] == "6275.00"  # 50 * 125.50
        print(f"✅ PO created: {po_id} (Status: DRAFT)")

        # ===== 5. Approve PO =====
        response = client.post(f"/api/v1/purchase_orders/{po_id}/approve",
                              json={"notes": "Test approval"},
                              headers=auth_headers)
        assert response.status_code == 200
        po = response.json()
        assert po["status"] == "APPROVED"
        assert po["approved_by"] is not None
        print(f"✅ PO approved (Status: APPROVED)")

        # ===== 6. Order PO =====
        response = client.post(f"/api/v1/purchase_orders/{po_id}/order",
                              json={},
                              headers=auth_headers)
        assert response.status_code == 200
        po = response.json()
        assert po["status"] == "ORDERED"
        assert po["order_date"] is not None
        print(f"✅ PO ordered (Status: ORDERED)")

        # ===== 7. Receive PO (generates Stock Moves) =====
        receive_data = {
            "delivery_location_id": location_id,
            "lines_received": [
                {"line_id": po_line_id, "quantity_received": 50}
            ]
        }
        response = client.post(f"/api/v1/purchase_orders/{po_id}/receive",
                              json=receive_data,
                              headers=auth_headers)
        assert response.status_code == 200
        receive_result = response.json()
        assert receive_result["status"] == "RECEIVED"
        assert receive_result["stock_moves_created"] == 1
        print(f"✅ PO received (Status: RECEIVED, Stock Moves: {receive_result['stock_moves_created']})")

        # ===== 8. Verify Stock Moves Created =====
        response = client.get(f"/api/v1/stock/moves?part_no=TEST-BRK-001", headers=auth_headers)
        assert response.status_code == 200
        moves = response.json()
        assert moves["total"] == 1
        assert moves["moves"][0]["move_type"] == "INCOMING"
        assert moves["moves"][0]["quantity"] == 50
        print(f"✅ Stock Move verified: INCOMING, Qty: 50")

        # ===== 9. Create Budget for testing =====
        budget_data = {
            "period": datetime.utcnow().strftime("%Y-%m"),
            "cost_center": "TEST-WS-MAINT",
            "category": "PARTS",
            "planned_amount": 10000,
            "forecast_amount": 9500
        }
        response = client.post("/api/v1/budget", json=budget_data, headers=auth_headers)
        assert response.status_code == 201
        budget = response.json()
        print(f"✅ Budget created: Planned={budget['planned_amount']}, Actual={budget['actual_amount']}")

        # ===== 10. Create Invoice =====
        invoice_data = {
            "invoice_number": "TEST-INV-001",
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "invoice_date": datetime.utcnow().isoformat(),
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "lines": [
                {
                    "line_number": 1,
                    "description": "Test Brake Pad Set",
                    "part_no": "TEST-BRK-001",
                    "quantity": 50,
                    "unit_price": 125.50,
                    "tax_amount": 1191.75,
                    "cost_center": "TEST-WS-MAINT"
                }
            ]
        }
        response = client.post("/api/v1/invoices/inbox", json=invoice_data, headers=auth_headers)
        assert response.status_code == 201
        invoice = response.json()
        invoice_id = invoice["id"]
        assert invoice["status"] == "DRAFT"
        print(f"✅ Invoice created: {invoice_id} (Status: DRAFT)")

        # ===== 11. Match Invoice against PO =====
        match_data = {
            "purchase_order_id": po_id,
            "auto_allocate_cost": True
        }
        response = client.post(f"/api/v1/invoices/{invoice_id}/match",
                              json=match_data,
                              headers=auth_headers)
        assert response.status_code == 200
        match_result = response.json()
        assert match_result["matched_lines"] == 1
        assert match_result["unmatched_lines"] == 0
        print(f"✅ Invoice matched: {match_result['matched_lines']} lines, Variance: {match_result['total_variance']}")

        # ===== 12. Approve Invoice (updates Budget) =====
        response = client.post(f"/api/v1/invoices/{invoice_id}/approve",
                              json={"notes": "Test approval"},
                              headers=auth_headers)
        assert response.status_code == 200
        invoice = response.json()
        assert invoice["status"] == "APPROVED"
        print(f"✅ Invoice approved (Status: APPROVED)")

        # ===== 13. Verify Budget Updated =====
        period = datetime.utcnow().strftime("%Y-%m")
        response = client.get(f"/api/v1/budget/overview?period={period}&cost_center=TEST-WS-MAINT",
                             headers=auth_headers)
        assert response.status_code == 200
        budget_overview = response.json()
        assert len(budget_overview["items"]) > 0
        # Budget should now have actual amount updated
        for item in budget_overview["items"]:
            if item["cost_center"] == "TEST-WS-MAINT":
                assert float(item["actual"]) > 0
                print(f"✅ Budget updated: Actual={item['actual']}, Variance={item['variance']}")

        # ===== 14. Check Reports =====
        # Parts Usage Report
        response = client.get(f"/api/v1/reports/parts_usage?period={period}", headers=auth_headers)
        assert response.status_code == 200
        parts_report = response.json()
        print(f"✅ Parts Usage Report: {parts_report['total_quantity']} parts, Cost: {parts_report['total_parts_cost']}")

        # Cost Report
        response = client.get(f"/api/v1/reports/costs?period={period}", headers=auth_headers)
        assert response.status_code == 200
        cost_report = response.json()
        print(f"✅ Cost Report: Planned={cost_report['total_planned']}, Actual={cost_report['total_actual']}")

        print("\n🎉 Complete E2E workflow passed!")


class TestInventoryFlow:
    """Test inventory-only operations."""

    def test_stock_move_flow(self, test_db, auth_headers):
        """Test stock move creation and aggregation."""
        # Create part and location (simplified, assumes they exist or creates them)
        # Then test various move types
        pass


class TestProcurementFlow:
    """Test procurement-only operations."""

    def test_po_workflow_transitions(self, test_db, auth_headers):
        """Test PO status transitions."""
        # Test: DRAFT → APPROVED → ORDERED → RECEIVED → CLOSED
        pass


class TestFinanceFlow:
    """Test finance-only operations."""

    def test_invoice_matching_logic(self, test_db, auth_headers):
        """Test invoice matching with variance calculation."""
        pass

    def test_budget_tracking(self, test_db, auth_headers):
        """Test budget creation and utilization tracking."""
        pass
