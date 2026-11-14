import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CalibrationLog(Base):
    __tablename__ = "calibration_logs"
    __table_args__ = (
        Index("idx_calib_asset", "asset_id"),
        Index("idx_calib_next_due", "next_due_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calibration_date: Mapped[date] = mapped_column(Date, nullable=False)
    standard_used: Mapped[str] = mapped_column(String(150), nullable=False)
    certificate_reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    accreditation_body: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="calibration_logs")
    technician: Mapped["User"] = relationship()
