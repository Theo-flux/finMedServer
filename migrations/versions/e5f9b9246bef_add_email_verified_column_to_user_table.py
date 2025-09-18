"""add email verified column to user table.

Revision ID: e5f9b9246bef
Revises: 438ff77c9ff8
Create Date: 2025-09-18 02:54:36.376868

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f9b9246bef"
down_revision: Union[str, None] = "438ff77c9ff8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # First add the column as nullable
    op.add_column("users", sa.Column("is_email_verified", sa.Boolean(), nullable=True))

    # Update existing rows
    op.execute("UPDATE users SET is_email_verified = FALSE WHERE is_email_verified IS NULL")

    # Then alter the column to be non-nullable
    op.alter_column("users", "is_email_verified", nullable=False)

    # Update user status if needed
    op.execute("UPDATE users SET status = 'ACTIVE' WHERE status = 'IN_ACTIVE'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_email_verified")
