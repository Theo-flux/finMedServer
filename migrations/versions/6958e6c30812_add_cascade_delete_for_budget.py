"""add cascade delete for budget

Revision ID: 6958e6c30812
Revises: 18335740a585
Create Date: 2025-08-24 15:34:51.757045

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6958e6c30812"
down_revision: Union[str, None] = "18335740a585"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Replace 'actual_constraint_name' with the name from the query above
    op.drop_constraint("actual_constraint_name", "expenses", type_="foreignkey")

    op.create_foreign_key(
        "fk_expenses_budget_cascade", "expenses", "budgets", ["budget_uid"], ["uid"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the CASCADE foreign key constraint
    op.drop_constraint("expenses_budget_uid_fkey", "expenses", type_="foreignkey")

    # Recreate the original foreign key constraint without CASCADE
    op.create_foreign_key("expenses_budget_uid_fkey", "expenses", "budgets", ["budget_uid"], ["uid"])
