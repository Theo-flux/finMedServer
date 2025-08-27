from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

from src.features.budgets.schemas import BudgetAvailability, BudgetStatus

if TYPE_CHECKING:
    from src.db.models.departments import Department
    from src.db.models.expenses import Expenses
    from src.db.models.users import User


class Budget(SQLModel, table=True):
    __tablename__ = "budgets"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: UUID = Field(default_factory=uuid4, nullable=False, index=True, unique=True)
    serial_no: Optional[str] = Field(nullable=True, index=True, unique=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)))
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )
    received_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    approved_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    department_uid: UUID = Field(foreign_key="departments.uid")
    user_uid: UUID = Field(foreign_key="users.uid")
    approver_uid: Optional[UUID] = Field(foreign_key="users.uid")
    assignee_uid: Optional[UUID] = Field(foreign_key="users.uid")
    status: Optional[str] = Field(default=BudgetStatus.PENDING.value)
    availability: str = Field(default=BudgetAvailability.AVAILABLE.value)
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
    assignee: "User" = Relationship(
        back_populates="assigned_budgets", sa_relationship_kwargs={"foreign_keys": "[Budget.assignee_uid]"}
    )
    expenses: List["Expenses"] = Relationship(back_populates="budget", cascade_delete=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.amount_remaining is None and self.gross_amount is not None:
            self.amount_remaining = self.gross_amount

    def __repr__(self) -> str:
        return f"<Budget: {self.model_dump()}>"
