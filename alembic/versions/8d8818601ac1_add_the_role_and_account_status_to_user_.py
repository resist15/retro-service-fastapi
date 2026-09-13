"""Add the role and account status to user table

Revision ID: 8d8818601ac1
Revises: 9d3418ea8d27
Create Date: 2026-09-13 18:04:10.519633
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d8818601ac1"
down_revision: Union[str, Sequence[str], None] = "9d3418ea8d27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    user_role = sa.Enum(
        "USER",
        "SUPER_USER",
        name="userrole",
    )

    account_status = sa.Enum(
        "PENDING",
        "APPROVED",
        "REJECTED",
        "SUSPENDED",
        name="accountstatus",
    )

    # Create PostgreSQL enum types first.
    user_role.create(op.get_bind(), checkfirst=True)
    account_status.create(op.get_bind(), checkfirst=True)

    # Add columns.
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role,
            nullable=False,
            server_default="USER",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "acc_status",
            account_status,
            nullable=False,
            server_default="PENDING",
        ),
    )

    # Optional: remove defaults if they should only apply
    # during migration and not to future inserts.
    op.alter_column(
        "users",
        "role",
        server_default=None,
    )

    op.alter_column(
        "users",
        "acc_status",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "acc_status")
    op.drop_column("users", "role")

    sa.Enum(
        "PENDING",
        "APPROVED",
        "REJECTED",
        "SUSPENDED",
        name="accountstatus",
    ).drop(op.get_bind(), checkfirst=True)

    sa.Enum(
        "USER",
        "SUPER_USER",
        name="userrole",
    ).drop(op.get_bind(), checkfirst=True)
