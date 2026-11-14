from datetime import datetime
from decimal import Decimal
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

WorkOrderStatus = Literal[
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "AWAITING_PARTS",
    "RESOLVED",
    "CLOSED",
]
WorkOrderSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
FailureCategory = Literal[
    "ELECTRICAL", "MECHANICAL", "OPTICAL", "SOFTWARE", "CONSUMABLE", "OTHER"
]
MaintenanceOutcome = Literal["OPERATIONAL", "REPAIRED_DEGRADED", "UNREPAIRABLE"]
T = TypeVar("T")


class MaintenancePage(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class CleanMaintenanceText(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def trim_text_fields(cls, value):
        if isinstance(value, dict):
            return {
                key: item.strip() if isinstance(item, str) else item
                for key, item in value.items()
            }
        return value


class FaultReportCreate(CleanMaintenanceText):
    asset_id: UUID
    severity: WorkOrderSeverity
    failure_category: FailureCategory
    fault_description: Annotated[str, Field(min_length=1)]


class TechnicianAssignment(CleanMaintenanceText):
    assigned_to: UUID


class WorkOrderStatusUpdate(BaseModel):
    status: Literal["IN_PROGRESS", "AWAITING_PARTS"]


class MaintenanceLogCreate(CleanMaintenanceText):
    actions_taken: Annotated[str, Field(min_length=1)]
    spare_parts_used: str | None = None
    labor_hours: Annotated[
        Decimal, Field(ge=Decimal("0"), max_digits=5, decimal_places=2)
    ] = Decimal("0.00")
    outcome_condition: MaintenanceOutcome


class MaintenanceVerification(CleanMaintenanceText):
    confirmed: bool
    verification_notes: Annotated[str, Field(min_length=1)]


class MaintenanceLogRead(BaseModel):
    id: UUID
    work_order_id: UUID
    technician_id: UUID
    technician_name: str
    actions_taken: str
    spare_parts_used: str | None
    labor_hours: Decimal
    outcome_condition: MaintenanceOutcome
    created_at: datetime


class WorkOrderStatusEvent(BaseModel):
    action: str
    actor_id: UUID | None
    actor_name: str | None
    old_status: WorkOrderStatus | None
    new_status: WorkOrderStatus
    old_assignee_id: UUID | None
    new_assignee_id: UUID | None
    notes: str | None
    occurred_at: datetime


class WorkOrderRead(BaseModel):
    id: UUID
    ticket_number: str
    asset_id: UUID
    asset_code: str
    asset_model_number: str
    asset_manufacturer_name: str
    laboratory_id: UUID
    laboratory_name: str
    reported_by: UUID
    reporter_name: str
    assigned_to: UUID | None
    assignee_name: str | None
    severity: WorkOrderSeverity
    failure_category: FailureCategory
    status: WorkOrderStatus
    fault_description: str
    verified_by: UUID | None
    verifier_name: str | None
    verification_notes: str | None
    created_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
    maintenance_logs: list[MaintenanceLogRead] = Field(default_factory=list)
    status_history: list[WorkOrderStatusEvent] = Field(default_factory=list)
