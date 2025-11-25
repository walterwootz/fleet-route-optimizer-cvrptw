"""
Reporting schemas for KPIs and analytics.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


# ===== Availability Report Schemas =====

class AvailabilityMetric(BaseModel):
    """Vehicle availability metric."""
    vehicle_type: str
    total_vehicles: int
    available_vehicles: int
    in_service_vehicles: int
    in_workshop_vehicles: int
    out_of_service_vehicles: int
    availability_pct: float  # (available + in_service) / total * 100


class AvailabilityReportResponse(BaseModel):
    """Availability report response."""
    period: str
    metrics: List[AvailabilityMetric]
    overall_availability_pct: float
    summary: str


# ===== On-Time Ratio Report Schemas =====

class OnTimeMetric(BaseModel):
    """On-time performance metric."""
    maintenance_type: Optional[str]
    total_work_orders: int
    on_time: int
    late: int
    on_time_ratio_pct: float  # (on_time / total) * 100
    avg_delay_hours: Optional[float]  # Average delay for late WOs


class OnTimeRatioReportResponse(BaseModel):
    """On-time ratio report response."""
    period: str
    metrics: List[OnTimeMetric]
    overall_on_time_ratio_pct: float
    summary: str


# ===== Parts Usage Report Schemas =====

class PartsUsageMetric(BaseModel):
    """Parts usage metric."""
    part_no: str
    part_name: str
    total_quantity_used: int
    total_work_orders: int
    avg_quantity_per_wo: float
    usage_per_1000km: Optional[float]  # If vehicle mileage available
    total_cost: Decimal


class PartsUsageReportResponse(BaseModel):
    """Parts usage report response."""
    period: str
    metrics: List[PartsUsageMetric]
    total_parts_cost: Decimal
    total_quantity: int
    summary: str


# ===== Cost Report Schemas =====

class CostMetric(BaseModel):
    """Cost vs budget metric."""
    cost_center: str
    category: Optional[str]
    planned_budget: Decimal
    actual_cost: Decimal
    variance: Decimal  # actual - planned
    variance_pct: float  # (variance / planned) * 100
    status: str  # "UNDER", "ON_TRACK", "OVER"


class CostReportResponse(BaseModel):
    """Cost report response."""
    period: str
    metrics: List[CostMetric]
    total_planned: Decimal
    total_actual: Decimal
    total_variance: Decimal
    warnings: List[str]
    summary: str


# ===== Dashboard Summary Schema =====

class DashboardSummary(BaseModel):
    """Overall dashboard summary."""
    period: str
    availability_pct: float
    on_time_ratio_pct: float
    budget_utilization_pct: float
    total_work_orders: int
    total_parts_cost: Decimal
    alerts: List[str]
