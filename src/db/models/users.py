from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from src.features.users.schemas import UserStatus

if TYPE_CHECKING:
    from src.db.models.budgets import Budget
    from src.db.models.departments import Department
    from src.db.models.expenses import Expenses
    from src.db.models.invoices import Invoice
    from src.db.models.patients import Patient
    from src.db.models.payments import Payment
    from src.db.models.roles import Role


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: UUID = Field(default_factory=uuid4, nullable=False, index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )
    staff_no: Optional[str] = Field(nullable=True, index=True, unique=True)
    created_by_uid: Optional[UUID] = Field(foreign_key="users.uid", default=None)
    department_uid: UUID = Field(foreign_key="departments.uid")
    role_uid: UUID = Field(foreign_key="roles.uid")
    first_name: str = Field(...)
    last_name: str = Field(...)
    user_name: Optional[str] = Field(default="")
    email: EmailStr = Field(...)
    phone_number: Optional[str] = Field(default="")
    password: Optional[str] = Field(default="")
    avatar: Optional[str] = Field(default="")
    status: Optional[str] = Field(default=UserStatus.IN_ACTIVE.value)
    last_login: Optional[datetime] = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=None,
        )
    )

    # relationship
    created_by_user: Optional["User"] = Relationship(
        back_populates="created_users",
        sa_relationship_kwargs={"remote_side": "[User.uid]", "foreign_keys": "[User.created_by_uid]"},
    )
    created_users: List["User"] = Relationship(back_populates="created_by_user")
    department: Optional["Department"] = Relationship(back_populates="users")
    role: "Role" = Relationship(back_populates="users")
    invoices: List["Invoice"] = Relationship(back_populates="user")
    payments: List["Payment"] = Relationship(back_populates="user")
    patients: List["Patient"] = Relationship(back_populates="user")
    created_budgets: List["Budget"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Budget.user_uid]"}
    )
    approved_budgets: List["Budget"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Budget.approver_uid]"}
    )
    assigned_budgets: List["Budget"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Budget.assignee_uid]"}
    )
    created_expenses: List["Expenses"] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User: {self.model_dump()}>"
