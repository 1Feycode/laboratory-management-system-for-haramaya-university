"""Add approved asset transfer history.

Revision ID: 20261113_04
Revises: 20261113_03
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261113_04"
down_revision: Union[str, None] = "20261113_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_transfers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "origin_laboratory_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("origin_room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "target_laboratory_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("target_room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accepted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by_ulmd", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="PENDING_RECEIVER",
            nullable=False,
        ),
        sa.Column("transfer_reason", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING_RECEIVER', 'PENDING_ULMD', 'COMPLETED', 'REJECTED')",
            name="ck_asset_transfers_status",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["assets.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["origin_laboratory_id"], ["laboratories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["origin_room_id"], ["rooms.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["target_laboratory_id"], ["laboratories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["target_room_id"], ["rooms.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["accepted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by_ulmd"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_transfers_asset", "asset_transfers", ["asset_id"])
    op.create_index("idx_transfers_status", "asset_transfers", ["status"])


def downgrade() -> None:
    op.drop_index("idx_transfers_status", table_name="asset_transfers")
    op.drop_index("idx_transfers_asset", table_name="asset_transfers")
    op.drop_table("asset_transfers")
