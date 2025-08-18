import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.budgets import Budget
    from src.db.models.expenses_category import ExpensesCategory
    from src.db.models.users import User


class Expenses(SQLModel, table=True):
    __tablename__ = "expenses"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    serial_no: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    budget_uid: uuid.UUID = Field(foreign_key="budgets.uid")
    expenses_category_uid: uuid.UUID = Field(foreign_key="expenses_category.uid")
    user_uid: uuid.UUID = Field(foreign_key="users.uid")
    amount_spent: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    title: str = Field(...)
    short_description: str = Field(...)
    note: str = Field(...)

    # relationships
    user: "User" = Relationship(back_populates="created_expenses")
    expenses_category: "ExpensesCategory" = Relationship(back_populates="expenses")
    budget: "Budget" = Relationship(back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expenses: {self.model_dump()}>"
