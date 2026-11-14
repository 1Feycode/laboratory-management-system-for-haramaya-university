from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class CountByName(BaseModel):
    name: str
    count: int


class CalibrationDueItem(BaseModel):
    asset_id: UUID
    asset_code: str
    model_number: str
    category_name: str
    college_name: str
    department_name: str
    laboratory_name: str
    room_number: str
    next_calibration_due: date
    status: str


class CriticalWorkOrderItem(BaseModel):
    id: UUID
    ticket_number: str
    asset_code: str
    college_name: str
    department_name: str
    laboratory_name: str
    severity: str
    status: str
    created_at: datetime


class CollegeMaintenanceSummary(BaseModel):
    college_id: UUID
    college_name: str
    work_order_requests: int
    work_orders_completed: int
    active_work_orders: int


class DashboardReport(BaseModel):
    asset_total: int
    operational_assets: int
    assets_by_category: list[CountByName]
    assets_by_status: list[CountByName]
    work_order_total: int
    active_work_orders: int
    work_orders_completed: int
    work_orders_by_status: list[CountByName]
    calibration_records: int
    calibrations_passed: int
    calibrations_failed: int
    overdue_calibrations: int
    upcoming_calibrations: int
    upcoming_calibration_items: list[CalibrationDueItem]
    overdue_calibration_items: list[CalibrationDueItem]
    critical_work_orders: list[CriticalWorkOrderItem]
    availability_status: str
    uptime_percentage: float | None
    downtime_asset_hours: float | None


class DowntimeReport(BaseModel):
    date_from: date
    date_to: date
    availability_status: str
    asset_total: int
    uptime_percentage: float | None
    downtime_asset_hours: float | None
    work_order_requests: int
    work_orders_completed: int
    active_work_orders: int
    work_orders_by_status: list[CountByName]
    by_college: list[CollegeMaintenanceSummary]


class CalibrationComplianceReport(BaseModel):
    assets_requiring_calibration: int
    overdue_calibrations: int
    upcoming_calibrations: int
    calibration_records: int
    calibrations_passed: int
    calibrations_failed: int
    overdue_items: list[CalibrationDueItem]
    upcoming_items: list[CalibrationDueItem]
