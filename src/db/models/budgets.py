import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.departments import Department
    from src.db.models.expenses import Expenses
    from src.db.models.users import User


class Budget(SQLModel, table=True):
    __tablename__ = "budgets"

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
    received_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    approved_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    department_uid: uuid.UUID = Field(foreign_key="departments.uid")
    user_uid: uuid.UUID = Field(foreign_key="users.uid")
    approver_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid")
    status: str = Field(...)
    availability: str = Field(...)
    gross_amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    amount_remaining: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    title: str = Field(...)
    short_description: str = Field(...)

    # relationships
    department: "Department" = Relationship(back_populates="budgets")
    user: "User" = Relationship(
        back_populates="created_budgets", sa_relationship_kwargs={"foreign_keys": "[Budget.user_uid]"}
    )
    approver: "User" = Relationship(
        back_populates="approved_budgets", sa_relationship_kwargs={"foreign_keys": "[Budget.approver_uid]"}
    )
    expenses: List["Expenses"] = Relationship(back_populates="budget")

    def __repr__(self) -> str:
        return f"<Budget: {self.model_dump()}>"
