import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class College(Base):
    __tablename__ = "colleges"
    __table_args__ = (
        UniqueConstraint("name", name="uq_colleges_name"),
        UniqueConstraint("code", name="uq_colleges_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    departments: Mapped[list["Department"]] = relationship(back_populates="college")


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("college_id", "code", name="uk_dept_college_code"),
        Index("idx_dept_college", "college_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    college_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("colleges.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    college: Mapped[College] = relationship(back_populates="departments")
    laboratories: Mapped[list["Laboratory"]] = relationship(back_populates="department")


class Laboratory(Base):
    __tablename__ = "laboratories"
    __table_args__ = (
        CheckConstraint(
            "lab_type IN ('WET', 'DRY', 'COMPUTING', 'WORKSHOP')",
            name="ck_laboratories_lab_type",
        ),
        Index("idx_labs_dept", "department_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    lab_type: Mapped[str] = mapped_column(String(50), nullable=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    department: Mapped[Department] = relationship(back_populates="laboratories")
    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id])
    rooms: Mapped[list["Room"]] = relationship(back_populates="laboratory")


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("laboratory_id", "room_number", name="uk_room_lab_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    laboratory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laboratories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    room_number: Mapped[str] = mapped_column(String(50), nullable=False)
    building_name: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    laboratory: Mapped[Laboratory] = relationship(back_populates="rooms")
