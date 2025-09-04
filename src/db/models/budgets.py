from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import column_property
from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

from src.features.budgets.schemas import BudgetAvailability, BudgetStatus

if TYPE_CHECKING:
    from src.db.models.departments import Department
    from src.db.models.expenses import Expenses
    from src.db.models.users import User


class BaseBudget(SQLModel):
    """Abstract base with computed SQL + Python props."""

    __abstract__ = True

    # placeholder so Pydantic ignores it as a model field
    amount_remaining: ClassVar[Decimal]

    @property
    def total_expenses(self) -> Decimal:
        if not self.expenses:
            return Decimal("0.0")
        return sum(expense.amount_spent for expense in self.expenses if expense.amount_spent)

    @property
    def amount_spent(self) -> Decimal:
        if self.gross_amount is None or self.amount_remaining is None:
            return Decimal("0.0")
        return self.gross_amount - self.amount_remaining

    def calculate_amount_remaining(self, new_gross_amount: int) -> Decimal:
        return new_gross_amount - self.total_expenses

    @property
    def consumption_percentage(self) -> Decimal:
        if self.gross_amount in (None, Decimal("0.0")):
            return Decimal("0.0")
        return (self.amount_spent / self.gross_amount) * 100

    @property
    def remaining_percentage(self) -> Decimal:
        return Decimal("100.0") - self.consumption_percentage

    @property
    def is_fully_consumed(self) -> bool:
        return self.amount_remaining <= Decimal("0.0")

    @property
    def is_overbudget(self) -> bool:
        return self.amount_remaining < Decimal("0.0")

    @property
    def is_near_limit(self) -> bool:
        return self.consumption_percentage >= Decimal("80.0")

    @property
    def budget_health_status(self) -> str:
        if self.is_overbudget:
            return "OVER_BUDGET"
        elif self.is_near_limit:
            return "NEAR_LIMIT"
        elif self.consumption_percentage >= Decimal("50.0"):
            return "MODERATE"
        return "HEALTHY"

    @property
    def utilization_status(self) -> str:
        if self.is_overbudget:
            return "EXCEEDED"
        elif self.is_fully_consumed:
            return "FULLY_UTILIZED"
        elif self.is_near_limit:
            return "HIGH_UTILIZATION"
        elif self.consumption_percentage >= Decimal("50.0"):
            return "MODERATE_UTILIZATION"
        elif self.consumption_percentage > Decimal("0.0"):
            return "LOW_UTILIZATION"
        return "UNUSED"


class Budget(BaseBudget, table=True):
    __tablename__ = "budgets"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: UUID = Field(default_factory=uuid4, index=True, unique=True, nullable=False)
    serial_no: Optional[str] = Field(index=True, unique=True, nullable=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)))
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        )
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
    title: str
    short_description: str

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

    def __repr__(self) -> str:
        return f"<Budget: {self.model_dump()}>"


from src.db.models.expenses import Expenses  # noqa

Budget.amount_remaining = column_property(
    Budget.gross_amount
    - (
        select(func.coalesce(func.sum(Expenses.amount_spent), 0))
        .where(Expenses.budget_uid == Budget.uid)
        .correlate_except(Expenses)
        .scalar_subquery()
    )
)
