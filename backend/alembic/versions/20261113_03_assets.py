"""Add approved asset category and asset tables.

Revision ID: 20261113_03
Revises: 20261113_02
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261113_03"
down_revision: Union[str, None] = "20261113_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_categories",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "requires_calibration",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "default_calibration_interval_days",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "default_calibration_interval_days >= 0",
            name="ck_asset_categories_calibration_interval",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_asset_categories_name"),
    )
    op.create_table(
        "assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("asset_code", sa.String(length=100), nullable=False),
        sa.Column("legacy_tag_number", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("model_number", sa.String(length=100), nullable=False),
        sa.Column("manufacturer_name", sa.String(length=150), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("laboratory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "operational_status",
            sa.String(length=50),
            server_default="OPERATIONAL",
            nullable=False,
        ),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("commissioning_date", sa.Date(), nullable=True),
        sa.Column("warranty_expiry_date", sa.Date(), nullable=True),
        sa.Column("last_calibrated_date", sa.Date(), nullable=True),
        sa.Column("next_calibration_due", sa.Date(), nullable=True),
        sa.Column("qr_code_path", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "operational_status IN "
            "('OPERATIONAL', 'UNDER_MAINTENANCE', 'DEFECTIVE', "
            "'TRANSFER_PENDING', 'DECOMMISSIONED')",
            name="ck_assets_operational_status",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["asset_categories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["laboratory_id"], ["laboratories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "manufacturer_name", "serial_number", name="uk_assets_serial_mfr"
        ),
    )
    op.create_index("idx_assets_code", "assets", ["asset_code"], unique=True)
    op.create_index(
        "idx_assets_legacy_tag",
        "assets",
        ["legacy_tag_number"],
        postgresql_where=sa.text("legacy_tag_number IS NOT NULL"),
    )
    op.create_index("idx_assets_status", "assets", ["operational_status"])
    op.create_index("idx_assets_next_cal", "assets", ["next_calibration_due"])
    op.create_index("idx_assets_lab", "assets", ["laboratory_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_audit_entity", "audit_logs", ["entity_type", "entity_id"]
    )
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_created", "audit_logs", ["created_at"])
    op.execute(
        """
        CREATE FUNCTION reject_audit_log_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only';
            RETURN OLD;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION reject_audit_log_mutation()")
    op.drop_index("idx_audit_created", table_name="audit_logs")
    op.drop_index("idx_audit_user", table_name="audit_logs")
    op.drop_index("idx_audit_entity", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("idx_assets_lab", table_name="assets")
    op.drop_index("idx_assets_next_cal", table_name="assets")
    op.drop_index("idx_assets_status", table_name="assets")
    op.drop_index("idx_assets_legacy_tag", table_name="assets")
    op.drop_index("idx_assets_code", table_name="assets")
    op.drop_table("assets")
    op.drop_table("asset_categories")
