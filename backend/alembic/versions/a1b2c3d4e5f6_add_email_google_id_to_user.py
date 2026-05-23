"""add_email_google_id_to_user

Revision ID: a1b2c3d4e5f6
Revises: 369b1e6df71c
Create Date: 2026-05-23 19:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "369b1e6df71c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make username nullable — required to store partial OAuth users before
    # they complete registration via /auth/google/complete.
    op.alter_column(
        "users", "username", existing_type=sa.String(length=150), nullable=True
    )

    # Make hashed_password nullable — OAuth-only users have no password.
    op.alter_column(
        "users", "hashed_password", existing_type=sa.String(length=255), nullable=True
    )

    # Add email column — nullable, unique, indexed.
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Add google_id column — nullable, unique, indexed.
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_column("users", "google_id")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "email")

    # Restore NOT NULL constraints — will fail if any rows have NULL values.
    op.alter_column(
        "users", "hashed_password", existing_type=sa.String(length=255), nullable=False
    )
    op.alter_column(
        "users", "username", existing_type=sa.String(length=150), nullable=False
    )
