from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from src.db.models.budgets import Budget
from src.db.models.departments import Department
from src.db.models.expenses import Expenses
from src.db.models.payments import Payment


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
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

    users: List[User] = Relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Roles: {self.model_dump()}>"


class User(SQLModel, table=True):
    __tablename__ = "users"

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
    staff_id: str = Field(nullable=False, index=True, unique=True)
    department_uuid: uuid.UUID = Field(foreign_key="departments.uid")
    role_uid: uuid.UUID = Field(foreign_key="user_roles.uid")
    first_name: str = Field(...)
    last_name: str = Field(...)
    user_name: Optional[str] = Field(default="")
    email: EmailStr = Field(...)
    phone_number: Optional[str] = Field(default="")
    password: str = Field(...)
    avatar: Optional[str] = Field(default="")
    status: str = Field(...)

    # relationship
    department: Optional[Department] = Relationship(back_populates="users")
    role: UserRole = Relationship(back_populates="users")
    payments: List[Payment] = Relationship(back_populates="user")
    created_budgets: List[Budget] = Relationship(back_populates="user")
    approved_budgets: List[Budget] = Relationship(back_populates="user")
    created_expenses: List[Expenses] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User: {self.model_dump()}>"
