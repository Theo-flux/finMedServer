import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from src.db.models.roles import Role
from src.features.users.schemas import UserStatus

if TYPE_CHECKING:
    from src.db.models.budgets import Budget
    from src.db.models.departments import Department
    from src.db.models.expenses import Expenses
    from src.db.models.payments import Payment


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default_factory=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )
    staff_no: str = Field(nullable=False, index=True, unique=True)
    department_uid: uuid.UUID = Field(foreign_key="departments.uid")
    role_uid: uuid.UUID = Field(foreign_key="roles.uid")
    first_name: str = Field(...)
    last_name: str = Field(...)
    user_name: Optional[str] = Field(default="")
    email: EmailStr = Field(...)
    phone_number: Optional[str] = Field(default="")
    password: str = Field(...)
    avatar: Optional[str] = Field(default="")
    status: Optional[str] = Field(default=UserStatus.IN_ACTIVE.value)

    # relationship
    department: Optional["Department"] = Relationship(back_populates="users")
    role: "Role" = Relationship(back_populates="users")
    payments: List["Payment"] = Relationship(back_populates="user")
    created_budgets: List["Budget"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Budget.user_uid]"}
    )
    approved_budgets: List["Budget"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Budget.approver_uid]"}
    )
    created_expenses: List["Expenses"] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User: {self.model_dump()}>"
