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

    @property
    def total_expenses(self) -> Decimal:
        """Calculate the total amount spent from expenses."""
        if not self.expenses:
            return Decimal("0.0")

        return sum(expense.amount_spent for expense in self.expenses if expense.amount_spent)

    @property
    def amount_spent(self) -> Decimal:
        """Calculate the amount spent (gross_amount - amount_remaining)."""
        if self.gross_amount is None or self.amount_remaining is None:
            return Decimal("0.0")

        return self.gross_amount - self.amount_remaining

    def calculate_amount_remaining(self, new_gross_amount: int) -> Decimal:
        """Calculate the net amount remaining (gross amount - total expenses)."""
        return new_gross_amount - self.total_expenses

    @property
    def consumption_percentage(self) -> Decimal:
        """Calculate the percentage of budget consumed."""
        if self.gross_amount is None or self.gross_amount == Decimal("0.0"):
            return Decimal("0.0")

        return (self.amount_spent / self.gross_amount) * 100

    @property
    def remaining_percentage(self) -> Decimal:
        """Calculate the percentage of budget remaining."""
        return Decimal("100.0") - self.consumption_percentage

    @property
    def is_fully_consumed(self) -> bool:
        """Check if the budget is fully consumed."""
        return self.amount_remaining <= Decimal("0.0")

    @property
    def is_overbudget(self) -> bool:
        """Check if spending exceeds the allocated budget."""
        return self.amount_remaining < Decimal("0.0")

    @property
    def is_near_limit(self) -> bool:
        """Check if budget consumption is at or above 80%."""
        return self.consumption_percentage >= Decimal("80.0")

    @property
    def budget_health_status(self) -> str:
        """Get the health status of the budget based on consumption."""
        consumption = self.consumption_percentage

        if self.is_overbudget:
            return "OVER_BUDGET"
        elif consumption >= Decimal("80.0"):
            return "NEAR_LIMIT"
        elif consumption >= Decimal("50.0"):
            return "MODERATE"
        else:
            return "HEALTHY"

    @property
    def utilization_status(self) -> str:
        """Get detailed utilization status."""
        if self.is_overbudget:
            return "EXCEEDED"
        elif self.is_fully_consumed:
            return "FULLY_UTILIZED"
        elif self.consumption_percentage >= Decimal("80.0"):
            return "HIGH_UTILIZATION"
        elif self.consumption_percentage >= Decimal("50.0"):
            return "MODERATE_UTILIZATION"
        elif self.consumption_percentage > Decimal("0.0"):
            return "LOW_UTILIZATION"
        else:
            return "UNUSED"

    def __repr__(self) -> str:
        return f"<Budget: {self.model_dump()}>"
