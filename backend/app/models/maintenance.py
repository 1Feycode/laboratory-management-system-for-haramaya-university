import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_work_orders_severity",
        ),
        CheckConstraint(
            "failure_category IN "
            "('ELECTRICAL', 'MECHANICAL', 'OPTICAL', 'SOFTWARE', 'CONSUMABLE', 'OTHER')",
            name="ck_work_orders_failure_category",
        ),
        CheckConstraint(
            "status IN "
            "('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'AWAITING_PARTS', 'RESOLVED', 'CLOSED')",
            name="ck_work_orders_status",
        ),
        Index("idx_wo_asset", "asset_id"),
        Index("idx_wo_status", "status"),
        Index("idx_wo_assigned", "assigned_to"),
        Index("idx_wo_ticket", "ticket_number", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reported_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    failure_category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="OPEN"
    )
    fault_description: Mapped[str] = mapped_column(Text, nullable=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    asset: Mapped["Asset"] = relationship(back_populates="work_orders")
    reporter: Mapped["User"] = relationship(foreign_keys=[reported_by])
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assigned_to])
    verifier: Mapped["User | None"] = relationship(foreign_keys=[verified_by])
    logs: Mapped[list["MaintenanceLog"]] = relationship(
        back_populates="work_order", passive_deletes="all"
    )


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    __table_args__ = (
        CheckConstraint(
            "labor_hours >= 0",
            name="ck_maintenance_logs_labor_hours",
        ),
        CheckConstraint(
            "outcome_condition IN ('OPERATIONAL', 'REPAIRED_DEGRADED', 'UNREPAIRABLE')",
            name="ck_maintenance_logs_outcome",
        ),
        Index("idx_maint_wo", "work_order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    actions_taken: Mapped[str] = mapped_column(Text, nullable=False)
    spare_parts_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    labor_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    outcome_condition: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    work_order: Mapped[WorkOrder] = relationship(back_populates="logs")
    technician: Mapped["User"] = relationship()
