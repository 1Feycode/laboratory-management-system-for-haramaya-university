"""Add approved calibration history records.

Revision ID: 20261114_07
Revises: 20261114_06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261114_07"
down_revision: Union[str, None] = "20261114_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calibration_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technician_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calibration_date", sa.Date(), nullable=False),
        sa.Column("standard_used", sa.String(length=150), nullable=False),
        sa.Column("certificate_reference", sa.String(length=100), nullable=True),
        sa.Column("accreditation_body", sa.String(length=150), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            name="fk_calibration_logs_asset_id_assets",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["technician_id"],
            ["users.id"],
            name="fk_calibration_logs_technician_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_calibration_logs"),
    )
    op.create_index("idx_calib_asset", "calibration_logs", ["asset_id"])
    op.create_index("idx_calib_next_due", "calibration_logs", ["next_due_date"])


def downgrade() -> None:
    op.drop_index("idx_calib_next_due", table_name="calibration_logs")
    op.drop_index("idx_calib_asset", table_name="calibration_logs")
    op.drop_table("calibration_logs")
