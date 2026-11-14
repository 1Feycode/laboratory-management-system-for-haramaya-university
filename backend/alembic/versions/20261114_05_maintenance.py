"""Add approved work order and maintenance log tables.

Revision ID: 20261114_05
Revises: 20261113_04
Create Date: 2026-11-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261114_05"
down_revision: Union[str, None] = "20261113_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "work_orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("ticket_number", sa.String(length=50), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reported_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("failure_category", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="OPEN",
            nullable=False,
        ),
        sa.Column("fault_description", sa.Text(), nullable=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_work_orders_severity",
        ),
        sa.CheckConstraint(
            "failure_category IN "
            "('ELECTRICAL', 'MECHANICAL', 'OPTICAL', 'SOFTWARE', 'CONSUMABLE', 'OTHER')",
            name="ck_work_orders_failure_category",
        ),
        sa.CheckConstraint(
            "status IN "
            "('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'AWAITING_PARTS', 'RESOLVED', 'CLOSED')",
            name="ck_work_orders_status",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["assets.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["reported_by"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["verified_by"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wo_asset", "work_orders", ["asset_id"])
    op.create_index("idx_wo_status", "work_orders", ["status"])
    op.create_index("idx_wo_assigned", "work_orders", ["assigned_to"])
    op.create_index("idx_wo_ticket", "work_orders", ["ticket_number"], unique=True)

    op.create_table(
        "maintenance_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technician_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actions_taken", sa.Text(), nullable=False),
        sa.Column("spare_parts_used", sa.Text(), nullable=True),
        sa.Column(
            "labor_hours",
            sa.Numeric(precision=5, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("outcome_condition", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "labor_hours >= 0",
            name="ck_maintenance_logs_labor_hours",
        ),
        sa.CheckConstraint(
            "outcome_condition IN ('OPERATIONAL', 'REPAIRED_DEGRADED', 'UNREPAIRABLE')",
            name="ck_maintenance_logs_outcome",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"], ["work_orders.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["technician_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_maint_wo", "maintenance_logs", ["work_order_id"])


def downgrade() -> None:
    op.drop_index("idx_maint_wo", table_name="maintenance_logs")
    op.drop_table("maintenance_logs")
    op.drop_index("idx_wo_ticket", table_name="work_orders")
    op.drop_index("idx_wo_assigned", table_name="work_orders")
    op.drop_index("idx_wo_status", table_name="work_orders")
    op.drop_index("idx_wo_asset", table_name="work_orders")
    op.drop_table("work_orders")
