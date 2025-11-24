"""
FLEET-ONE Use Case Handlers

Implements the 9 use cases from the playbook:
1. HU/Deadlines planning → Workshop
2. Parts procurement check & ordering
3. Staff planning for workshop transfers
4. Invoice entry & WO assignment
5. Documents: expiring & linking
6. Vehicle status & plan flag setting
7. Conflict resolution (Policy)
8. Reporting: Availability KPI
9. Maintenance task creation & planning

Each handler follows the tool call sequences defined in the playbook.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date, timezone
from dataclasses import dataclass
import pytz

from src.services.fleet_one.tool_orchestrator import ToolOrchestrator, ToolCallResult
from src.services.fleet_one.rbac_policy import get_rbac_engine, AccessResult


@dataclass
class HandlerResult:
    """Result of use case handler"""
    success: bool
    message: str  # German response message
    tool_calls: List[Dict[str, Any]]
    data: Optional[Dict[str, Any]] = None
    warnings: List[str] = None
    suggestions: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


class UseCaseHandlers:
    """
    Use case handler implementations.

    Each method implements one complete use case from the playbook,
    orchestrating multiple tool calls in sequence.
    """

    def __init__(self, orchestrator: ToolOrchestrator):
        """
        Initialize handlers.

        Args:
            orchestrator: Tool orchestrator for backend calls
        """
        self.orchestrator = orchestrator
        self.rbac = get_rbac_engine()
        self.berlin_tz = pytz.timezone("Europe/Berlin")

    def _to_berlin_time(self, utc_dt: datetime) -> str:
        """Convert UTC datetime to Berlin timezone string"""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        berlin_dt = utc_dt.astimezone(self.berlin_tz)
        return berlin_dt.strftime("%d.%m.%Y %H:%M")

    def _from_berlin_time(self, berlin_str: str) -> datetime:
        """Parse Berlin timezone string to UTC datetime"""
        berlin_dt = datetime.strptime(berlin_str, "%d.%m.%Y %H:%M")
        berlin_dt = self.berlin_tz.localize(berlin_dt)
        return berlin_dt.astimezone(timezone.utc)

    # =========================================================================
    # Use Case 1: HU/Fristen planen → Werkstatt
    # =========================================================================

    def handle_hu_planning(
        self,
        workshop_id: str,
        days_ahead: int = 30,
        user_role: str = "dispatcher"
    ) -> HandlerResult:
        """
        Use Case 1: Plan HU/maintenance for locomotives due in next N days.

        Playbook sequence:
        1. List maintenance tasks due in N days
        2. (Optional) Call solver for schedule proposal
        3. Create workshop orders
        4. Update locomotive status

        Args:
            workshop_id: Target workshop ID (e.g., "WS-MUENCHEN")
            days_ahead: Look-ahead window in days
            user_role: User role for RBAC

        Returns:
            HandlerResult with planned orders
        """
        tool_calls = []

        # Check RBAC
        access = self.rbac.check_access(user_role, "wo:create")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Step 1: List HU tasks
        due_before = date.today() + timedelta(days=days_ahead)
        result = self.orchestrator.list_maintenance_tasks(due_before=due_before)

        tool_calls.append({
            "service": "maintenance_service",
            "endpoint": "list_tasks",
            "params": {"due_before": due_before.isoformat()},
            "result": "success" if result.success else "error"
        })

        if not result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Abrufen der Wartungsaufgaben: {result.error}",
                tool_calls=tool_calls
            )

        tasks = result.data if result.data else []

        if not tasks:
            return HandlerResult(
                success=True,
                message=f"Keine HU-Aufgaben in den nächsten {days_ahead} Tagen fällig.",
                tool_calls=tool_calls
            )

        # Step 2: Create workshop orders for each task
        created_orders = []
        for task in tasks:
            # Plan window: Start 2 days before due date, duration 1 day
            due_date = datetime.fromisoformat(task["due_date"])
            planned_from = due_date - timedelta(days=2)
            planned_to = planned_from + timedelta(hours=8)

            wo_result = self.orchestrator.create_workshop_order(
                locomotive_id=task["asset_id"],
                workshop_id=workshop_id,
                planned_from=planned_from,
                planned_to=planned_to,
                tasks=[task["type"]]
            )

            tool_calls.append({
                "service": "workshop_service",
                "endpoint": "create_order",
                "params": {
                    "locomotive_id": task["asset_id"],
                    "workshop_id": workshop_id
                },
                "result": "success" if wo_result.success else "error"
            })

            if wo_result.success:
                order = wo_result.data
                created_orders.append(order)

                # Step 3: Update locomotive status
                patch_result = self.orchestrator.patch_locomotive(
                    locomotive_id=task["asset_id"],
                    status="workshop_planned",
                    planned_workshop_id=order.get("id")
                )

                tool_calls.append({
                    "service": "fleet_db",
                    "endpoint": "patch_locomotive",
                    "params": {"locomotive_id": task["asset_id"]},
                    "result": "success" if patch_result.success else "error"
                })

        # Generate German response
        message = f"✅ {len(created_orders)} Werkstattaufträge für Werkstatt {workshop_id} angelegt:\n"
        for order in created_orders:
            lok_id = order.get("locomotive_id")
            planned_from_str = self._to_berlin_time(datetime.fromisoformat(order.get("planned_from")))
            message += f"  • Lok {lok_id}: {planned_from_str}\n"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"orders": created_orders}
        )

    # =========================================================================
    # Use Case 2: Teilebedarf prüfen & Beschaffung
    # =========================================================================

    def handle_parts_procurement(
        self,
        part_no: str,
        required_qty: int,
        related_wo_id: Optional[str] = None,
        needed_by: Optional[date] = None,
        user_role: str = "procurement"
    ) -> HandlerResult:
        """
        Use Case 2: Check parts availability and create purchase request if needed.

        Playbook sequence:
        1. Get stock level
        2. If stock < required, create purchase request

        Args:
            part_no: Part number (e.g., "P_BRK")
            required_qty: Required quantity
            related_wo_id: Related work order ID
            needed_by: Date when parts are needed
            user_role: User role for RBAC

        Returns:
            HandlerResult with procurement status
        """
        tool_calls = []

        # Check RBAC
        access = self.rbac.check_access(user_role, "purchase:req")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Step 1: Check stock
        stock_result = self.orchestrator.get_stock(part_no)

        tool_calls.append({
            "service": "procurement_service",
            "endpoint": "get_stock",
            "params": {"part_no": part_no},
            "result": "success" if stock_result.success else "error"
        })

        if not stock_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Abrufen des Lagerbestands: {stock_result.error}",
                tool_calls=tool_calls
            )

        stock_data = stock_result.data
        available_qty = stock_data.get("available_qty", 0)

        # Check if order needed
        if available_qty >= required_qty:
            return HandlerResult(
                success=True,
                message=f"✅ Teil {part_no}: Ausreichend Lagerbestand ({available_qty} Stück verfügbar, {required_qty} benötigt).",
                tool_calls=tool_calls,
                data={"stock": stock_data}
            )

        # Step 2: Create purchase request
        order_qty = required_qty - available_qty
        if not needed_by:
            needed_by = date.today() + timedelta(days=7)  # Default: 7 days

        purchase_result = self.orchestrator.request_purchase(
            part_no=part_no,
            qty=order_qty,
            needed_by=needed_by,
            related_wo_id=related_wo_id
        )

        tool_calls.append({
            "service": "procurement_service",
            "endpoint": "request_purchase",
            "params": {
                "part_no": part_no,
                "qty": order_qty,
                "needed_by": needed_by.isoformat()
            },
            "result": "success" if purchase_result.success else "error"
        })

        if not purchase_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Anlegen der Bestellanforderung: {purchase_result.error}",
                tool_calls=tool_calls
            )

        message = f"📦 Bestellanforderung angelegt:\n"
        message += f"  • Teil: {part_no}\n"
        message += f"  • Menge: {order_qty} Stück (Lagerbestand: {available_qty})\n"
        message += f"  • Benötigt bis: {needed_by.strftime('%d.%m.%Y')}\n"
        if related_wo_id:
            message += f"  • Auftrag: {related_wo_id}\n"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"purchase_request": purchase_result.data}
        )

    # =========================================================================
    # Use Case 3: Personaleinsatz für Werkstattzuführungen
    # =========================================================================

    def handle_transfer_staff_planning(
        self,
        transfers: List[Dict[str, Any]],
        user_role: str = "dispatcher"
    ) -> HandlerResult:
        """
        Use Case 3: Plan staff assignments for workshop transfers.

        Playbook sequence:
        1. Plan transfers (one per locomotive)
        2. List available staff with required skill
        3. Assign staff to transfers

        Args:
            transfers: List of transfer requests, each with:
                - locomotive_id
                - from_location
                - to_location
                - window_start (datetime)
                - window_end (datetime)
            user_role: User role for RBAC

        Returns:
            HandlerResult with staff assignments
        """
        tool_calls = []

        # Check RBAC
        access_transfer = self.rbac.check_access(user_role, "transfer:plan")
        if not access_transfer.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access_transfer.reason}",
                tool_calls=[]
            )

        # Step 1: Plan all transfers
        planned_transfers = []
        for transfer_req in transfers:
            transfer_result = self.orchestrator.plan_transfer(
                locomotive_id=transfer_req["locomotive_id"],
                from_location=transfer_req["from_location"],
                to_location=transfer_req["to_location"],
                window_start=transfer_req["window_start"],
                window_end=transfer_req["window_end"],
                team_skill="transfer_driver"
            )

            tool_calls.append({
                "service": "transfer_service",
                "endpoint": "plan_transfer",
                "params": {"locomotive_id": transfer_req["locomotive_id"]},
                "result": "success" if transfer_result.success else "error"
            })

            if transfer_result.success:
                planned_transfers.append(transfer_result.data)

        # Step 2: List available staff
        staff_result = self.orchestrator.list_staff(skill="transfer_driver")

        tool_calls.append({
            "service": "hr_service",
            "endpoint": "list_staff",
            "params": {"skill": "transfer_driver"},
            "result": "success" if staff_result.success else "error"
        })

        if not staff_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Abrufen der Mitarbeiterliste: {staff_result.error}",
                tool_calls=tool_calls
            )

        available_staff = staff_result.data if staff_result.data else []

        if len(available_staff) < len(planned_transfers):
            return HandlerResult(
                success=False,
                message=f"⚠️ Nicht genügend Fahrer verfügbar ({len(available_staff)} verfügbar, {len(planned_transfers)} benötigt).",
                tool_calls=tool_calls,
                warnings=["Personalmangel"]
            )

        # Step 3: Assign staff to transfers
        assignments = []
        for i, transfer in enumerate(planned_transfers):
            if i >= len(available_staff):
                break

            staff = available_staff[i]
            assignment_result = self.orchestrator.assign_transfer(
                staff_id=staff.get("id"),
                locomotive_id=transfer.get("locomotive_id"),
                transfer_id=transfer.get("id"),
                from_time=datetime.fromisoformat(transfer.get("window_start")),
                to_time=datetime.fromisoformat(transfer.get("window_end"))
            )

            tool_calls.append({
                "service": "hr_service",
                "endpoint": "assign_transfer",
                "params": {
                    "staff_id": staff.get("id"),
                    "transfer_id": transfer.get("id")
                },
                "result": "success" if assignment_result.success else "error"
            })

            if assignment_result.success:
                assignments.append(assignment_result.data)

        # Generate response
        message = f"✅ {len(assignments)} Werkstattzuführungen geplant und Personal zugewiesen:\n"
        for assignment in assignments:
            message += f"  • Lok {assignment.get('locomotive_id')}: Fahrer {assignment.get('staff_id')}\n"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"assignments": assignments}
        )

    # =========================================================================
    # Use Case 4: Eingangsrechnung erfassen
    # =========================================================================

    def handle_invoice_entry(
        self,
        invoice_number: str,
        supplier: str,
        amount: float,
        currency: str,
        related_wo_id: Optional[str] = None,
        user_role: str = "finance"
    ) -> HandlerResult:
        """
        Use Case 4: Enter incoming invoice and assign to work order.

        Playbook sequence:
        1. Create invoice

        Args:
            invoice_number: Invoice number
            supplier: Supplier name
            amount: Invoice amount
            currency: Currency (e.g., "EUR")
            related_wo_id: Related work order ID
            user_role: User role for RBAC

        Returns:
            HandlerResult with invoice data
        """
        tool_calls = []

        # Check RBAC
        access = self.rbac.check_access(user_role, "invoice:create")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Create invoice
        invoice_result = self.orchestrator.create_invoice(
            invoice_number=invoice_number,
            supplier=supplier,
            amount=amount,
            currency=currency,
            related_workshop_order_id=related_wo_id
        )

        tool_calls.append({
            "service": "finance_service",
            "endpoint": "create_invoice",
            "params": {
                "invoice_number": invoice_number,
                "supplier": supplier,
                "amount": amount
            },
            "result": "success" if invoice_result.success else "error"
        })

        if not invoice_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Erfassen der Rechnung: {invoice_result.error}",
                tool_calls=tool_calls
            )

        message = f"✅ Rechnung {invoice_number} erfasst:\n"
        message += f"  • Lieferant: {supplier}\n"
        message += f"  • Betrag: {amount:,.2f} {currency}\n"
        if related_wo_id:
            message += f"  • Auftrag: {related_wo_id}\n"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"invoice": invoice_result.data}
        )

    # =========================================================================
    # Use Case 5: Dokumente: Ablauf & Verknüpfen
    # =========================================================================

    def handle_documents(
        self,
        days_ahead: int = 60,
        link_document: Optional[Dict[str, Any]] = None,
        user_role: str = "ecm"
    ) -> HandlerResult:
        """
        Use Case 5: List expiring documents and link new document.

        Playbook sequence:
        1. List expiring documents
        2. (Optional) Link new document

        Args:
            days_ahead: Look-ahead window for expiring docs
            link_document: Optional document to link (dict with asset_id, doc_type, doc_id, valid_until)
            user_role: User role for RBAC

        Returns:
            HandlerResult with document info
        """
        tool_calls = []

        # Check RBAC
        access = self.rbac.check_access(user_role, "docs:manage")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Step 1: List expiring documents
        before_date = date.today() + timedelta(days=days_ahead)
        expiring_result = self.orchestrator.list_expiring_documents(before=before_date)

        tool_calls.append({
            "service": "docs_service",
            "endpoint": "list_expiring",
            "params": {"before": before_date.isoformat()},
            "result": "success" if expiring_result.success else "error"
        })

        expiring_docs = []
        if expiring_result.success and expiring_result.data:
            expiring_docs = expiring_result.data

        # Step 2: Link new document if provided
        linked_doc = None
        if link_document:
            link_result = self.orchestrator.link_document(
                asset_id=link_document["asset_id"],
                doc_type=link_document["doc_type"],
                doc_id=link_document["doc_id"],
                valid_until=link_document.get("valid_until")
            )

            tool_calls.append({
                "service": "docs_service",
                "endpoint": "link_document",
                "params": {"asset_id": link_document["asset_id"]},
                "result": "success" if link_result.success else "error"
            })

            if link_result.success:
                linked_doc = link_result.data

        # Generate response
        message = f"📄 Dokumente (ablaufend in {days_ahead} Tagen): {len(expiring_docs)}\n"
        for doc in expiring_docs[:5]:  # Show first 5
            message += f"  • {doc.get('doc_type')} ({doc.get('asset_id')}): {doc.get('valid_until')}\n"

        if linked_doc:
            message += f"\n✅ Dokument {linked_doc.get('doc_id')} verknüpft mit {linked_doc.get('asset_id')}"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"expiring_docs": expiring_docs, "linked_doc": linked_doc}
        )

    # =========================================================================
    # Use Case 6: Fahrzeugstatus setzen
    # =========================================================================

    def handle_vehicle_status_update(
        self,
        locomotive_id: str,
        status: str,
        planned_workshop_id: Optional[str] = None,
        user_role: str = "dispatcher"
    ) -> HandlerResult:
        """
        Use Case 6: Update vehicle status and plan flag.

        Playbook sequence:
        1. Patch locomotive

        Args:
            locomotive_id: Locomotive ID
            status: New status
            planned_workshop_id: Workshop order ID
            user_role: User role for RBAC

        Returns:
            HandlerResult with updated vehicle data
        """
        tool_calls = []

        # Check RBAC
        access = self.rbac.check_access(user_role, "plan:update")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Patch locomotive
        patch_result = self.orchestrator.patch_locomotive(
            locomotive_id=locomotive_id,
            status=status,
            planned_workshop_id=planned_workshop_id
        )

        tool_calls.append({
            "service": "fleet_db",
            "endpoint": "patch_locomotive",
            "params": {"locomotive_id": locomotive_id, "status": status},
            "result": "success" if patch_result.success else "error"
        })

        if not patch_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Aktualisieren des Fahrzeugstatus: {patch_result.error}",
                tool_calls=tool_calls
            )

        message = f"✅ Lok {locomotive_id} Status aktualisiert: {status}"
        if planned_workshop_id:
            message += f"\n  • Auftrag: {planned_workshop_id}"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"locomotive": patch_result.data}
        )

    # =========================================================================
    # Use Case 8: Reporting - Verfügbarkeit
    # =========================================================================

    def handle_availability_report(
        self,
        from_date: date,
        to_date: date,
        user_role: str = "viewer"
    ) -> HandlerResult:
        """
        Use Case 8: Generate availability KPI report.

        Playbook sequence:
        1. Get availability report

        Args:
            from_date: Start date
            to_date: End date
            user_role: User role for RBAC

        Returns:
            HandlerResult with availability data
        """
        tool_calls = []

        # Check RBAC (viewers can read reports)
        access = self.rbac.check_access(user_role, "read:*")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Get availability report
        report_result = self.orchestrator.get_availability_report(
            from_date=from_date,
            to_date=to_date
        )

        tool_calls.append({
            "service": "reporting_service",
            "endpoint": "get_availability_report",
            "params": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            },
            "result": "success" if report_result.success else "error"
        })

        if not report_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Abrufen des Verfügbarkeitsberichts: {report_result.error}",
                tool_calls=tool_calls
            )

        report_data = report_result.data
        avg_availability = report_data.get("avg_availability", 0) * 100

        message = f"📊 Verfügbarkeitsbericht ({from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')}):\n"
        message += f"  • Durchschnittliche Verfügbarkeit: {avg_availability:.1f}%\n"

        by_asset = report_data.get("by_asset", [])
        if by_asset:
            message += "\n  Top 5 Fahrzeuge:\n"
            for asset in by_asset[:5]:
                asset_avail = asset.get("availability", 0) * 100
                message += f"    • {asset.get('asset_id')}: {asset_avail:.1f}%\n"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"report": report_data}
        )

    # =========================================================================
    # Use Case 9: Wartungsmaßnahme anlegen
    # =========================================================================

    def handle_maintenance_task_creation(
        self,
        locomotive_id: str,
        task_type: str,
        due_date: date,
        workshop_id: Optional[str] = None,
        user_role: str = "dispatcher"
    ) -> HandlerResult:
        """
        Use Case 9: Create maintenance task and plan workshop window.

        Playbook sequence:
        1. Create maintenance task
        2. (Optional) Create workshop order

        Args:
            locomotive_id: Locomotive ID
            task_type: Task type (e.g., "HU")
            due_date: Due date
            workshop_id: Optional workshop ID for order
            user_role: User role for RBAC

        Returns:
            HandlerResult with task and order data
        """
        tool_calls = []

        # Check RBAC
        access = self.rbac.check_access(user_role, "wo:create")
        if not access.allowed:
            return HandlerResult(
                success=False,
                message=f"Zugriff verweigert: {access.reason}",
                tool_calls=[]
            )

        # Step 1: Create maintenance task
        task_result = self.orchestrator.create_maintenance_task(
            locomotive_id=locomotive_id,
            task_type=task_type,
            due_date=due_date
        )

        tool_calls.append({
            "service": "maintenance_service",
            "endpoint": "create_task",
            "params": {
                "locomotive_id": locomotive_id,
                "type": task_type,
                "due_date": due_date.isoformat()
            },
            "result": "success" if task_result.success else "error"
        })

        if not task_result.success:
            return HandlerResult(
                success=False,
                message=f"Fehler beim Anlegen der Wartungsmaßnahme: {task_result.error}",
                tool_calls=tool_calls
            )

        task_data = task_result.data

        message = f"✅ Wartungsmaßnahme angelegt:\n"
        message += f"  • Lok: {locomotive_id}\n"
        message += f"  • Typ: {task_type}\n"
        message += f"  • Fällig: {due_date.strftime('%d.%m.%Y')}\n"

        # Step 2: Create workshop order if workshop specified
        order_data = None
        if workshop_id:
            # Plan 7 days before due date
            due_datetime = datetime.combine(due_date, datetime.min.time())
            planned_from = due_datetime - timedelta(days=7)
            planned_to = planned_from + timedelta(hours=8)

            order_result = self.orchestrator.create_workshop_order(
                locomotive_id=locomotive_id,
                workshop_id=workshop_id,
                planned_from=planned_from,
                planned_to=planned_to,
                tasks=[task_type]
            )

            tool_calls.append({
                "service": "workshop_service",
                "endpoint": "create_order",
                "params": {"locomotive_id": locomotive_id, "workshop_id": workshop_id},
                "result": "success" if order_result.success else "error"
            })

            if order_result.success:
                order_data = order_result.data
                message += f"\n✅ Werkstattauftrag angelegt ({workshop_id})"

        return HandlerResult(
            success=True,
            message=message,
            tool_calls=tool_calls,
            data={"task": task_data, "order": order_data}
        )


# Singleton instance
_handlers: Optional[UseCaseHandlers] = None


def init_handlers(orchestrator: ToolOrchestrator) -> UseCaseHandlers:
    """Initialize global use case handlers"""
    global _handlers
    _handlers = UseCaseHandlers(orchestrator)
    return _handlers


def get_handlers() -> Optional[UseCaseHandlers]:
    """Get global use case handlers instance"""
    return _handlers
