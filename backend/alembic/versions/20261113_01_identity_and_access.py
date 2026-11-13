"""Add approved identity and role tables.

Revision ID: 20261113_01
Revises:
Create Date: 2026-11-13
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261113_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_ROWS = [
    {
        "id": uuid.UUID("00000000-0000-4000-8000-000000000001"),
        "name": "ULMD_ADMIN",
        "description": "University-wide application administrator",
    },
    {
        "id": uuid.UUID("00000000-0000-4000-8000-000000000002"),
        "name": "MAINTENANCE_TECH",
        "description": "Laboratory Technology Unit specialist",
    },
    {
        "id": uuid.UUID("00000000-0000-4000-8000-000000000003"),
        "name": "LAB_MANAGER",
        "description": "Laboratory custodian and manager",
    },
    {
        "id": uuid.UUID("00000000-0000-4000-8000-000000000004"),
        "name": "LAB_TECH",
        "description": "Laboratory technician or technical assistant",
    },
    {
        "id": uuid.UUID("00000000-0000-4000-8000-000000000005"),
        "name": "AUDITOR",
        "description": "Read-only inventory and compliance auditor",
    },
]


def upgrade() -> None:
    op.create_table(
        "colleges",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_colleges_code"),
        sa.UniqueConstraint("name", name="uq_colleges_name"),
    )
    op.create_table(
        "departments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("college_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["college_id"], ["colleges.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "college_id", "code", name="uk_dept_college_code"
        ),
    )
    op.create_index("idx_dept_college", "departments", ["college_id"])
    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    role_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String(length=50)),
        sa.column("description", sa.String(length=255)),
    )
    op.bulk_insert(role_table, ROLE_ROWS)
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_role", "users", ["role_id"])


def downgrade() -> None:
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_index("idx_dept_college", table_name="departments")
    op.drop_table("departments")
    op.drop_table("colleges")
