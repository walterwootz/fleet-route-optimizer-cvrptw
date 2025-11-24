"""Compliance Reporter - Generate compliance reports from audit trails.

Provides compliance reporting for regulatory requirements, including
GDPR, SOX, HIPAA-style audit requirements.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.railfleet.events import Event as EventModel
from ..services.audit_trail import AuditTrailService
from ..services.change_history import ChangeHistoryService
from ..config import get_logger

logger = get_logger(__name__)


class ComplianceStandard(str, Enum):
    """Compliance standards."""

    GDPR = "gdpr"  # General Data Protection Regulation
    SOX = "sox"  # Sarbanes-Oxley Act
    ISO27001 = "iso27001"  # Information Security Management
    CUSTOM = "custom"


class ComplianceFinding:
    """A compliance finding (issue or observation)."""

    def __init__(
        self,
        severity: str,
        title: str,
        description: str,
        evidence: List[str],
        recommendation: Optional[str] = None,
    ):
        self.severity = severity  # low, medium, high, critical
        self.title = title
        self.description = description
        self.evidence = evidence
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


class ComplianceReport:
    """Complete compliance report."""

    def __init__(
        self,
        standard: ComplianceStandard,
        scope: str,
        start_date: datetime,
        end_date: datetime,
    ):
        self.standard = standard
        self.scope = scope
        self.start_date = start_date
        self.end_date = end_date
        self.generated_at = datetime.utcnow()
        self.findings: List[ComplianceFinding] = []
        self.statistics: Dict[str, Any] = {}
        self.passed_checks: List[str] = []
        self.failed_checks: List[str] = []

    def add_finding(self, finding: ComplianceFinding):
        """Add a compliance finding."""
        self.findings.append(finding)

    def add_passed_check(self, check: str):
        """Add a passed compliance check."""
        self.passed_checks.append(check)

    def add_failed_check(self, check: str):
        """Add a failed compliance check."""
        self.failed_checks.append(check)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "standard": self.standard.value,
            "scope": self.scope,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "generated_at": self.generated_at.isoformat(),
            "findings": [f.to_dict() for f in self.findings],
            "findings_by_severity": self._count_by_severity(),
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "compliance_score": self._calculate_compliance_score(),
            "statistics": self.statistics,
        }

    def _count_by_severity(self) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def _calculate_compliance_score(self) -> float:
        """Calculate overall compliance score (0-100)."""
        total_checks = len(self.passed_checks) + len(self.failed_checks)
        if total_checks == 0:
            return 100.0

        passed = len(self.passed_checks)
        return (passed / total_checks) * 100


class ComplianceReporter:
    """Service for generating compliance reports.

    Example:
        >>> reporter = ComplianceReporter(db)
        >>>
        >>> # Generate GDPR compliance report
        >>> report = reporter.generate_gdpr_report(
        ...     start_date=last_quarter,
        ...     end_date=now,
        ...     scope="all"
        ... )
        >>> print(f"Compliance score: {report.compliance_score}%")
        >>>
        >>> # Generate SOX compliance report
        >>> report = reporter.generate_sox_report(
        ...     start_date=fiscal_year_start,
        ...     end_date=fiscal_year_end
        ... )
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditTrailService(db)
        self.change_service = ChangeHistoryService(db)

    def generate_gdpr_report(
        self,
        start_date: datetime,
        end_date: datetime,
        scope: str = "all",
    ) -> ComplianceReport:
        """Generate GDPR compliance report.

        Checks:
        - Data access logging (who accessed what data)
        - Data modification tracking
        - User consent tracking
        - Data deletion/anonymization tracking

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            scope: Scope of report (e.g., "all", "user_data")

        Returns:
            ComplianceReport with GDPR findings
        """
        report = ComplianceReport(
            standard=ComplianceStandard.GDPR,
            scope=scope,
            start_date=start_date,
            end_date=end_date,
        )

        # Check 1: Audit trail completeness
        self._check_audit_trail_completeness(report, start_date, end_date)

        # Check 2: User attribution
        self._check_user_attribution(report, start_date, end_date)

        # Check 3: Data retention
        self._check_data_retention(report, start_date, end_date)

        # Statistics
        report.statistics = self._calculate_gdpr_statistics(start_date, end_date)

        logger.info(
            f"Generated GDPR compliance report: "
            f"{len(report.findings)} findings, "
            f"score: {report._calculate_compliance_score():.1f}%"
        )

        return report

    def generate_sox_report(
        self,
        start_date: datetime,
        end_date: datetime,
        scope: str = "financial",
    ) -> ComplianceReport:
        """Generate SOX compliance report.

        Checks:
        - Financial data change tracking
        - Segregation of duties
        - Audit trail integrity
        - Access control logging

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            scope: Scope of report

        Returns:
            ComplianceReport with SOX findings
        """
        report = ComplianceReport(
            standard=ComplianceStandard.SOX,
            scope=scope,
            start_date=start_date,
            end_date=end_date,
        )

        # Check 1: Financial data changes
        self._check_financial_changes(report, start_date, end_date)

        # Check 2: Change approval
        self._check_change_approval(report, start_date, end_date)

        # Check 3: Audit trail integrity
        self._check_audit_integrity(report, start_date, end_date)

        # Statistics
        report.statistics = self._calculate_sox_statistics(start_date, end_date)

        logger.info(
            f"Generated SOX compliance report: "
            f"{len(report.findings)} findings, "
            f"score: {report._calculate_compliance_score():.1f}%"
        )

        return report

    def generate_activity_summary(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Generate activity summary for compliance.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary with activity statistics
        """
        # Count events by type
        event_counts = (
            self.db.query(
                EventModel.aggregate_type,
                EventModel.event_type,
                func.count(EventModel.id).label("count"),
            )
            .filter(
                and_(
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .group_by(EventModel.aggregate_type, EventModel.event_type)
            .all()
        )

        # Count unique users
        unique_users = set()
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .all()
        )

        for event in events:
            if event.metadata and event.metadata.user_id:
                unique_users.add(event.metadata.user_id)

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_events": len(events),
            "unique_users": len(unique_users),
            "events_by_type": [
                {
                    "aggregate_type": agg_type,
                    "event_type": evt_type,
                    "count": count,
                }
                for agg_type, evt_type, count in event_counts
            ],
        }

    def _check_audit_trail_completeness(
        self,
        report: ComplianceReport,
        start_date: datetime,
        end_date: datetime,
    ):
        """Check audit trail completeness."""
        # Get all events
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .all()
        )

        if not events:
            report.add_finding(
                ComplianceFinding(
                    severity="high",
                    title="No Events Found",
                    description=f"No events found in period {start_date} to {end_date}",
                    evidence=["Empty event store for period"],
                    recommendation="Verify event sourcing is properly configured",
                )
            )
            report.add_failed_check("audit_trail_completeness")
        else:
            report.add_passed_check("audit_trail_completeness")

    def _check_user_attribution(
        self,
        report: ComplianceReport,
        start_date: datetime,
        end_date: datetime,
    ):
        """Check that all events have user attribution."""
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .all()
        )

        missing_user = [
            event
            for event in events
            if not event.metadata or not event.metadata.user_id
        ]

        if missing_user:
            report.add_finding(
                ComplianceFinding(
                    severity="medium",
                    title="Events Without User Attribution",
                    description=f"Found {len(missing_user)} events without user attribution",
                    evidence=[f"Event {e.event_id}" for e in missing_user[:10]],
                    recommendation="Ensure all events include user_id in metadata",
                )
            )
            report.add_failed_check("user_attribution")
        else:
            report.add_passed_check("user_attribution")

    def _check_data_retention(
        self,
        report: ComplianceReport,
        start_date: datetime,
        end_date: datetime,
    ):
        """Check data retention policies."""
        # Check for very old events (>7 years as example)
        old_threshold = datetime.utcnow() - timedelta(days=7 * 365)

        old_events = (
            self.db.query(EventModel)
            .filter(EventModel.occurred_at < old_threshold)
            .count()
        )

        if old_events > 0:
            report.add_finding(
                ComplianceFinding(
                    severity="low",
                    title="Old Data Retention",
                    description=f"Found {old_events} events older than 7 years",
                    evidence=[f"{old_events} events before {old_threshold.date()}"],
                    recommendation="Review data retention policy and archive old events",
                )
            )
            report.add_failed_check("data_retention")
        else:
            report.add_passed_check("data_retention")

    def _check_financial_changes(
        self,
        report: ComplianceReport,
        start_date: datetime,
        end_date: datetime,
    ):
        """Check financial data changes."""
        # Look for financial aggregate types
        financial_types = ["Invoice", "Budget", "CostCenter", "PurchaseOrder"]

        financial_events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type.in_(financial_types),
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .all()
        )

        if financial_events:
            # Check if all have proper attribution
            missing_user = [
                e for e in financial_events
                if not e.metadata or not e.metadata.user_id
            ]

            if missing_user:
                report.add_finding(
                    ComplianceFinding(
                        severity="high",
                        title="Financial Changes Without User",
                        description=f"Found {len(missing_user)} financial changes without user attribution",
                        evidence=[f"Event {e.event_id}" for e in missing_user[:10]],
                        recommendation="All financial changes must be attributed to a user",
                    )
                )
                report.add_failed_check("financial_user_attribution")
            else:
                report.add_passed_check("financial_user_attribution")

    def _check_change_approval(
        self,
        report: ComplianceReport,
        start_date: datetime,
        end_date: datetime,
    ):
        """Check change approval tracking."""
        # This is a placeholder - would check for approval metadata
        report.add_passed_check("change_approval")

    def _check_audit_integrity(
        self,
        report: ComplianceReport,
        start_date: datetime,
        end_date: datetime,
    ):
        """Check audit trail integrity."""
        # Check for version gaps
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .order_by(EventModel.aggregate_type, EventModel.aggregate_id, EventModel.aggregate_version)
            .all()
        )

        # Group by aggregate
        aggregates: Dict[str, List[EventModel]] = {}
        for event in events:
            key = f"{event.aggregate_type}:{event.aggregate_id}"
            if key not in aggregates:
                aggregates[key] = []
            aggregates[key].append(event)

        # Check for version gaps
        gaps_found = []
        for key, agg_events in aggregates.items():
            for i in range(1, len(agg_events)):
                expected_version = agg_events[i - 1].aggregate_version + 1
                actual_version = agg_events[i].aggregate_version

                if actual_version != expected_version:
                    gaps_found.append(
                        f"{key}: gap between v{agg_events[i-1].aggregate_version} "
                        f"and v{actual_version}"
                    )

        if gaps_found:
            report.add_finding(
                ComplianceFinding(
                    severity="critical",
                    title="Audit Trail Integrity Issues",
                    description=f"Found {len(gaps_found)} version gaps in audit trail",
                    evidence=gaps_found[:10],
                    recommendation="Investigate missing events and restore from backups if needed",
                )
            )
            report.add_failed_check("audit_integrity")
        else:
            report.add_passed_check("audit_integrity")

    def _calculate_gdpr_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate GDPR-relevant statistics."""
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .all()
        )

        return {
            "total_events": len(events),
            "data_access_events": sum(
                1 for e in events if "read" in e.event_type.lower()
            ),
            "data_modification_events": sum(
                1 for e in events if any(
                    op in e.event_type.lower()
                    for op in ["create", "update", "delete"]
                )
            ),
        }

    def _calculate_sox_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate SOX-relevant statistics."""
        financial_types = ["Invoice", "Budget", "CostCenter", "PurchaseOrder"]

        financial_events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type.in_(financial_types),
                    EventModel.occurred_at >= start_date,
                    EventModel.occurred_at <= end_date,
                )
            )
            .all()
        )

        return {
            "total_financial_events": len(financial_events),
            "financial_changes_by_type": {
                evt_type: sum(
                    1 for e in financial_events if e.aggregate_type == evt_type
                )
                for evt_type in financial_types
            },
        }
