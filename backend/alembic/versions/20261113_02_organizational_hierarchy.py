"""Add laboratories and rooms to the approved hierarchy.

Revision ID: 20261113_02
Revises: 20261113_01
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261113_02"
down_revision: Union[str, None] = "20261113_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "laboratories",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("lab_type", sa.String(length=50), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "lab_type IN ('WET', 'DRY', 'COMPUTING', 'WORKSHOP')",
            name="ck_laboratories_lab_type",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_labs_dept", "laboratories", ["department_id"])
    op.create_table(
        "rooms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("laboratory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_number", sa.String(length=50), nullable=False),
        sa.Column("building_name", sa.String(length=150), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["laboratory_id"], ["laboratories.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "laboratory_id", "room_number", name="uk_room_lab_number"
        ),
    )


def downgrade() -> None:
    op.drop_table("rooms")
    op.drop_index("idx_labs_dept", table_name="laboratories")
    op.drop_table("laboratories")
