import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetCategory(Base):
    __tablename__ = "asset_categories"
    __table_args__ = (
        UniqueConstraint("name", name="uq_asset_categories_name"),
        CheckConstraint(
            "default_calibration_interval_days >= 0",
            name="ck_asset_categories_calibration_interval",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    requires_calibration: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    default_calibration_interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="category", passive_deletes="all"
    )


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint(
            "manufacturer_name", "serial_number", name="uk_assets_serial_mfr"
        ),
        CheckConstraint(
            "operational_status IN "
            "('OPERATIONAL', 'UNDER_MAINTENANCE', 'DEFECTIVE', "
            "'TRANSFER_PENDING', 'DECOMMISSIONED')",
            name="ck_assets_operational_status",
        ),
        Index("idx_assets_code", "asset_code", unique=True),
        Index(
            "idx_assets_legacy_tag",
            "legacy_tag_number",
            postgresql_where=text("legacy_tag_number IS NOT NULL"),
        ),
        Index("idx_assets_status", "operational_status"),
        Index("idx_assets_next_cal", "next_calibration_due"),
        Index("idx_assets_lab", "laboratory_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    asset_code: Mapped[str] = mapped_column(String(100), nullable=False)
    legacy_tag_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)
    model_number: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    laboratory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laboratories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    operational_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="OPERATIONAL"
    )
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    commissioning_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warranty_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_calibrated_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_calibration_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    qr_code_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped[AssetCategory] = relationship(back_populates="assets")
    laboratory: Mapped["Laboratory"] = relationship(back_populates="assets")
    room: Mapped["Room"] = relationship(back_populates="assets")
    transfers: Mapped[list["AssetTransfer"]] = relationship(
        back_populates="asset", passive_deletes="all"
    )
    work_orders: Mapped[list["WorkOrder"]] = relationship(
        back_populates="asset", passive_deletes="all"
    )
    calibration_logs: Mapped[list["CalibrationLog"]] = relationship(
        back_populates="asset", passive_deletes="all"
    )


class AssetAuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
