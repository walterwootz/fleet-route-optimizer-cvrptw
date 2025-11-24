"""
FLEET-ONE Tool Orchestration Layer

Orchestrates tool calls across 9 backend services:
1. fleet_db - Fleet/locomotive data
2. maintenance_service - Maintenance tasks and deadlines
3. workshop_service - Workshop orders and repairs
4. transfer_service - Vehicle transfers
5. procurement_service - Parts and purchasing
6. reporting_service - KPIs and reports
7. finance_service - Invoices and budgets
8. hr_service - Staff and assignments
9. docs_service - Documents and certifications

Each service is accessed via HTTP REST API with bearer token auth.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import requests
from enum import Enum
from dataclasses import dataclass
import os


class ServiceType(Enum):
    """Backend service types"""
    FLEET_DB = "fleet_db"
    MAINTENANCE = "maintenance_service"
    WORKSHOP = "workshop_service"
    TRANSFER = "transfer_service"
    PROCUREMENT = "procurement_service"
    REPORTING = "reporting_service"
    FINANCE = "finance_service"
    HR = "hr_service"
    DOCS = "docs_service"


@dataclass
class ToolCallResult:
    """Result of a tool call"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    service: Optional[ServiceType] = None


class HTTPToolClient:
    """
    Generic HTTP client for backend services.

    Handles authentication, retries, and error handling.
    """

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for service
            auth_token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = requests.Session()

        if auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {auth_token}"
            })

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """HTTP GET request"""
        url = f"{self.base_url}{path}"

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )

            if response.status_code >= 200 and response.status_code < 300:
                return ToolCallResult(
                    success=True,
                    data=response.json() if response.content else None,
                    status_code=response.status_code
                )
            else:
                return ToolCallResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    status_code=response.status_code
                )

        except Exception as e:
            return ToolCallResult(
                success=False,
                error=str(e)
            )

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """HTTP POST request"""
        url = f"{self.base_url}{path}"

        try:
            response = self.session.post(
                url,
                data=data,
                json=json_data,
                timeout=self.timeout
            )

            if response.status_code >= 200 and response.status_code < 300:
                return ToolCallResult(
                    success=True,
                    data=response.json() if response.content else None,
                    status_code=response.status_code
                )
            else:
                return ToolCallResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    status_code=response.status_code
                )

        except Exception as e:
            return ToolCallResult(
                success=False,
                error=str(e)
            )

    def patch(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """HTTP PATCH request"""
        url = f"{self.base_url}{path}"

        try:
            response = self.session.patch(
                url,
                data=data,
                json=json_data,
                timeout=self.timeout
            )

            if response.status_code >= 200 and response.status_code < 300:
                return ToolCallResult(
                    success=True,
                    data=response.json() if response.content else None,
                    status_code=response.status_code
                )
            else:
                return ToolCallResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    status_code=response.status_code
                )

        except Exception as e:
            return ToolCallResult(
                success=False,
                error=str(e)
            )


class ToolOrchestrator:
    """
    Orchestrates tool calls across backend services.

    Manages service clients and provides high-level methods
    for common operations.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with service configuration.

        Args:
            config: Configuration with service URLs and tokens
        """
        self.config = config
        self.clients = self._init_clients()

    def _init_clients(self) -> Dict[ServiceType, HTTPToolClient]:
        """Initialize HTTP clients for all services"""
        clients = {}

        # Fleet DB
        clients[ServiceType.FLEET_DB] = HTTPToolClient(
            base_url=os.getenv("FLEET_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("FLEET_API_TOKEN")
        )

        # Maintenance Service
        clients[ServiceType.MAINTENANCE] = HTTPToolClient(
            base_url=os.getenv("MAINT_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("MAINT_API_TOKEN")
        )

        # Workshop Service
        clients[ServiceType.WORKSHOP] = HTTPToolClient(
            base_url=os.getenv("WORKSHOP_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("WORKSHOP_API_TOKEN")
        )

        # Transfer Service
        clients[ServiceType.TRANSFER] = HTTPToolClient(
            base_url=os.getenv("TRANSFER_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("TRANSFER_API_TOKEN")
        )

        # Procurement Service
        clients[ServiceType.PROCUREMENT] = HTTPToolClient(
            base_url=os.getenv("PROC_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("PROC_API_TOKEN")
        )

        # Reporting Service
        clients[ServiceType.REPORTING] = HTTPToolClient(
            base_url=os.getenv("REPORT_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("REPORT_API_TOKEN")
        )

        # Finance Service
        clients[ServiceType.FINANCE] = HTTPToolClient(
            base_url=os.getenv("FIN_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("FIN_API_TOKEN")
        )

        # HR Service
        clients[ServiceType.HR] = HTTPToolClient(
            base_url=os.getenv("HR_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("HR_API_TOKEN")
        )

        # Docs Service
        clients[ServiceType.DOCS] = HTTPToolClient(
            base_url=os.getenv("DOCS_BASE_URL", "http://localhost:8000/api/v1"),
            auth_token=os.getenv("DOCS_API_TOKEN")
        )

        return clients

    # =========================================================================
    # Fleet DB Operations
    # =========================================================================

    def get_locomotives(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> ToolCallResult:
        """Get list of locomotives"""
        params = {}
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        result = self.clients[ServiceType.FLEET_DB].get(
            "/fleet/locomotives",
            params=params
        )
        result.service = ServiceType.FLEET_DB
        return result

    def get_locomotive(self, locomotive_id: str) -> ToolCallResult:
        """Get single locomotive by ID"""
        result = self.clients[ServiceType.FLEET_DB].get(
            f"/fleet/locomotives/{locomotive_id}"
        )
        result.service = ServiceType.FLEET_DB
        return result

    def patch_locomotive(
        self,
        locomotive_id: str,
        status: Optional[str] = None,
        planned_workshop_id: Optional[str] = None
    ) -> ToolCallResult:
        """Update locomotive data"""
        data = {}
        if status:
            data["status"] = status
        if planned_workshop_id:
            data["planned_workshop_id"] = planned_workshop_id

        result = self.clients[ServiceType.FLEET_DB].patch(
            f"/fleet/locomotives/{locomotive_id}",
            json_data=data
        )
        result.service = ServiceType.FLEET_DB
        return result

    # =========================================================================
    # Maintenance Service Operations
    # =========================================================================

    def list_maintenance_tasks(
        self,
        due_before: Optional[date] = None,
        asset_id: Optional[str] = None
    ) -> ToolCallResult:
        """List maintenance tasks"""
        params = {}
        if due_before:
            params["due_before"] = due_before.isoformat()
        if asset_id:
            params["asset_id"] = asset_id

        result = self.clients[ServiceType.MAINTENANCE].get(
            "/maintenance/tasks",
            params=params
        )
        result.service = ServiceType.MAINTENANCE
        return result

    def create_maintenance_task(
        self,
        locomotive_id: str,
        task_type: str,
        due_date: date
    ) -> ToolCallResult:
        """Create maintenance task"""
        data = {
            "locomotive_id": locomotive_id,
            "type": task_type,
            "due_date": due_date.isoformat()
        }

        result = self.clients[ServiceType.MAINTENANCE].post(
            "/maintenance/tasks",
            json_data=data
        )
        result.service = ServiceType.MAINTENANCE
        return result

    # =========================================================================
    # Workshop Service Operations
    # =========================================================================

    def create_workshop_order(
        self,
        locomotive_id: str,
        workshop_id: str,
        planned_from: datetime,
        planned_to: datetime,
        tasks: List[str]
    ) -> ToolCallResult:
        """Create workshop order"""
        data = {
            "locomotive_id": locomotive_id,
            "workshop_id": workshop_id,
            "planned_from": planned_from.isoformat(),
            "planned_to": planned_to.isoformat(),
            "tasks": tasks
        }

        result = self.clients[ServiceType.WORKSHOP].post(
            "/workshop/orders",
            json_data=data
        )
        result.service = ServiceType.WORKSHOP
        return result

    def update_workshop_order_status(
        self,
        order_id: str,
        status: str
    ) -> ToolCallResult:
        """Update workshop order status"""
        data = {"status": status}

        result = self.clients[ServiceType.WORKSHOP].patch(
            f"/workshop/orders/{order_id}",
            json_data=data
        )
        result.service = ServiceType.WORKSHOP
        return result

    # =========================================================================
    # Transfer Service Operations
    # =========================================================================

    def plan_transfer(
        self,
        locomotive_id: str,
        from_location: str,
        to_location: str,
        window_start: datetime,
        window_end: datetime,
        team_skill: str
    ) -> ToolCallResult:
        """Plan vehicle transfer"""
        data = {
            "locomotive_id": locomotive_id,
            "from": from_location,
            "to": to_location,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "team_skill": team_skill
        }

        result = self.clients[ServiceType.TRANSFER].post(
            "/transfer/plans",
            json_data=data
        )
        result.service = ServiceType.TRANSFER
        return result

    # =========================================================================
    # Procurement Service Operations
    # =========================================================================

    def request_purchase(
        self,
        part_no: str,
        qty: int,
        needed_by: date,
        related_wo_id: Optional[str] = None
    ) -> ToolCallResult:
        """Create purchase request"""
        data = {
            "part_no": part_no,
            "qty": qty,
            "needed_by": needed_by.isoformat(),
            "related_wo_id": related_wo_id
        }

        result = self.clients[ServiceType.PROCUREMENT].post(
            "/procurement/requests",
            json_data=data
        )
        result.service = ServiceType.PROCUREMENT
        return result

    def get_stock(self, part_no: str) -> ToolCallResult:
        """Get stock level for part"""
        result = self.clients[ServiceType.PROCUREMENT].get(
            "/procurement/stock",
            params={"part_no": part_no}
        )
        result.service = ServiceType.PROCUREMENT
        return result

    # =========================================================================
    # Reporting Service Operations
    # =========================================================================

    def get_availability_report(
        self,
        from_date: date,
        to_date: date
    ) -> ToolCallResult:
        """Get availability KPI report"""
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }

        result = self.clients[ServiceType.REPORTING].get(
            "/reports/availability",
            params=params
        )
        result.service = ServiceType.REPORTING
        return result

    def get_cost_report(
        self,
        from_date: date,
        to_date: date,
        asset_id: Optional[str] = None
    ) -> ToolCallResult:
        """Get cost report"""
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }
        if asset_id:
            params["asset_id"] = asset_id

        result = self.clients[ServiceType.REPORTING].get(
            "/reports/costs",
            params=params
        )
        result.service = ServiceType.REPORTING
        return result

    # =========================================================================
    # Finance Service Operations
    # =========================================================================

    def create_invoice(
        self,
        invoice_number: str,
        supplier: str,
        amount: float,
        currency: str,
        related_workshop_order_id: Optional[str] = None
    ) -> ToolCallResult:
        """Create invoice"""
        data = {
            "invoice_number": invoice_number,
            "supplier": supplier,
            "amount": amount,
            "currency": currency,
            "related_workshop_order_id": related_workshop_order_id
        }

        result = self.clients[ServiceType.FINANCE].post(
            "/finance/invoices",
            json_data=data
        )
        result.service = ServiceType.FINANCE
        return result

    # =========================================================================
    # HR Service Operations
    # =========================================================================

    def list_staff(self, skill: Optional[str] = None) -> ToolCallResult:
        """List staff members"""
        params = {}
        if skill:
            params["skill"] = skill

        result = self.clients[ServiceType.HR].get(
            "/hr/staff",
            params=params
        )
        result.service = ServiceType.HR
        return result

    def assign_transfer(
        self,
        staff_id: str,
        locomotive_id: str,
        transfer_id: str,
        from_time: datetime,
        to_time: datetime
    ) -> ToolCallResult:
        """Assign staff to transfer"""
        data = {
            "staff_id": staff_id,
            "locomotive_id": locomotive_id,
            "transfer_id": transfer_id,
            "from": from_time.isoformat(),
            "to": to_time.isoformat()
        }

        result = self.clients[ServiceType.HR].post(
            "/hr/assignments",
            json_data=data
        )
        result.service = ServiceType.HR
        return result

    # =========================================================================
    # Docs Service Operations
    # =========================================================================

    def link_document(
        self,
        asset_id: str,
        doc_type: str,
        doc_id: str,
        valid_until: Optional[date] = None
    ) -> ToolCallResult:
        """Link document to asset"""
        data = {
            "asset_id": asset_id,
            "doc_type": doc_type,
            "doc_id": doc_id
        }
        if valid_until:
            data["valid_until"] = valid_until.isoformat()

        result = self.clients[ServiceType.DOCS].post(
            "/docs/link",
            json_data=data
        )
        result.service = ServiceType.DOCS
        return result

    def list_expiring_documents(
        self,
        before: date
    ) -> ToolCallResult:
        """List documents expiring before date"""
        params = {"before": before.isoformat()}

        result = self.clients[ServiceType.DOCS].get(
            "/docs/expiring",
            params=params
        )
        result.service = ServiceType.DOCS
        return result


# Singleton instance
_orchestrator: Optional[ToolOrchestrator] = None


def init_orchestrator(config: Dict[str, Any]) -> ToolOrchestrator:
    """Initialize global tool orchestrator"""
    global _orchestrator
    _orchestrator = ToolOrchestrator(config)
    return _orchestrator


def get_orchestrator() -> Optional[ToolOrchestrator]:
    """Get global tool orchestrator instance"""
    return _orchestrator
