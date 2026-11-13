import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetTransfer(Base):
    __tablename__ = "asset_transfers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING_RECEIVER', 'PENDING_ULMD', 'COMPLETED', 'REJECTED')",
            name="ck_asset_transfers_status",
        ),
        Index("idx_transfers_asset", "asset_id"),
        Index("idx_transfers_status", "status"),
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
    origin_laboratory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laboratories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    origin_room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_laboratory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laboratories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    accepted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_by_ulmd: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="PENDING_RECEIVER"
    )
    transfer_reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    asset: Mapped["Asset"] = relationship(back_populates="transfers")
    origin_laboratory: Mapped["Laboratory"] = relationship(
        foreign_keys=[origin_laboratory_id]
    )
    origin_room: Mapped["Room"] = relationship(foreign_keys=[origin_room_id])
    target_laboratory: Mapped["Laboratory"] = relationship(
        foreign_keys=[target_laboratory_id]
    )
    target_room: Mapped["Room"] = relationship(foreign_keys=[target_room_id])
    initiator: Mapped["User"] = relationship(foreign_keys=[initiated_by])
    accepter: Mapped["User | None"] = relationship(foreign_keys=[accepted_by])
    ulmd_approver: Mapped["User | None"] = relationship(
        foreign_keys=[approved_by_ulmd]
    )
