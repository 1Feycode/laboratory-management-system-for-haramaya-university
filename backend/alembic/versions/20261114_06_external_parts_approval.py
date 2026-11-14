"""Add configurable external-parts approval tracking to work orders.

Revision ID: 20261114_06
Revises: 20261114_05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261114_06"
down_revision: Union[str, None] = "20261114_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_work_orders_status", "work_orders", type_="check")
    op.create_check_constraint(
        "ck_work_orders_status",
        "work_orders",
        "status IN "
        "('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'AWAITING_PARTS', "
        "'AWAITING_APPROVAL', 'RESOLVED', 'CLOSED')",
    )
    op.add_column(
        "work_orders",
        sa.Column("external_parts_request_details", sa.Text(), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("external_parts_requested_by", postgresql.UUID(as_uuid=True)),
    )
    op.add_column(
        "work_orders",
        sa.Column(
            "external_parts_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "work_orders",
        sa.Column("external_parts_previous_status", sa.String(length=50)),
    )
    op.add_column(
        "work_orders",
        sa.Column("external_parts_decision", sa.String(length=20)),
    )
    op.add_column(
        "work_orders",
        sa.Column("external_parts_decided_by", postgresql.UUID(as_uuid=True)),
    )
    op.add_column(
        "work_orders",
        sa.Column(
            "external_parts_decided_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "work_orders",
        sa.Column("external_parts_decision_notes", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_work_orders_external_parts_requester",
        "work_orders",
        "users",
        ["external_parts_requested_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_work_orders_external_parts_decider",
        "work_orders",
        "users",
        ["external_parts_decided_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_work_orders_external_parts_decision",
        "work_orders",
        "external_parts_decision IS NULL OR "
        "external_parts_decision IN ('PENDING', 'APPROVED', 'REJECTED')",
    )
    op.create_check_constraint(
        "ck_work_orders_external_parts_previous_status",
        "work_orders",
        "external_parts_previous_status IS NULL OR "
        "external_parts_previous_status IN ('IN_PROGRESS', 'AWAITING_PARTS')",
    )
    op.create_check_constraint(
        "ck_work_orders_external_parts_approval_state",
        "work_orders",
        "("
        "external_parts_request_details IS NULL AND "
        "external_parts_requested_by IS NULL AND "
        "external_parts_requested_at IS NULL AND "
        "external_parts_previous_status IS NULL AND "
        "external_parts_decision IS NULL AND "
        "external_parts_decided_by IS NULL AND "
        "external_parts_decided_at IS NULL AND "
        "external_parts_decision_notes IS NULL"
        ") OR ("
        "external_parts_request_details IS NOT NULL AND "
        "external_parts_requested_by IS NOT NULL AND "
        "external_parts_requested_at IS NOT NULL AND "
        "external_parts_previous_status IS NOT NULL AND "
        "("
        "("
        "external_parts_decision = 'PENDING' AND "
        "external_parts_decided_by IS NULL AND "
        "external_parts_decided_at IS NULL"
        ") OR ("
        "external_parts_decision IN ('APPROVED', 'REJECTED') AND "
        "external_parts_decided_by IS NOT NULL AND "
        "external_parts_decided_at IS NOT NULL"
        ")"
        ")"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_work_orders_external_parts_approval_state",
        "work_orders",
        type_="check",
    )
    op.drop_constraint(
        "ck_work_orders_external_parts_previous_status",
        "work_orders",
        type_="check",
    )
    op.drop_constraint(
        "ck_work_orders_external_parts_decision",
        "work_orders",
        type_="check",
    )
    op.drop_constraint(
        "fk_work_orders_external_parts_decider",
        "work_orders",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_work_orders_external_parts_requester",
        "work_orders",
        type_="foreignkey",
    )
    op.drop_column("work_orders", "external_parts_decision_notes")
    op.drop_column("work_orders", "external_parts_decided_at")
    op.drop_column("work_orders", "external_parts_decided_by")
    op.drop_column("work_orders", "external_parts_decision")
    op.drop_column("work_orders", "external_parts_previous_status")
    op.drop_column("work_orders", "external_parts_requested_at")
    op.drop_column("work_orders", "external_parts_requested_by")
    op.drop_column("work_orders", "external_parts_request_details")
    op.drop_constraint("ck_work_orders_status", "work_orders", type_="check")
    op.create_check_constraint(
        "ck_work_orders_status",
        "work_orders",
        "status IN "
        "('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'AWAITING_PARTS', 'RESOLVED', 'CLOSED')",
    )
