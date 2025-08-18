from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Column, DateTime, Field, SQLModel, Relationship


from src.db.models.users import User


class ExpensesCategory(SQLModel, table=True):
    __tablename__ = "expenses_category"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    name: str = Field(...)
    status: str = Field(...)

    # relationship
    expenses: List[Expenses] = Relationship(back_populates="expense_category")

    def __repr__(self) -> str:
        return f"<Expenses category: {self.model_dump()}>"


class Expenses(SQLModel, table=True):
    __tablename__ = "expenses"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    budget_no: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    expenses_category_uid: uuid.UUID = Field(foreign_key="expenses_category.uid")
    user_uid: uuid.UUID = Field(foreign_key="users.uid")
    amount_spent: int = Field(...)
    title: str = Field(...)
    short_description: str = Field(...)
    note: str = Field(...)

    # relationships
    user: User = Relationship(back_populates="created_expenses")
    expenses_category: ExpensesCategory = Relationship(back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expenses: {self.model_dump()}>"
