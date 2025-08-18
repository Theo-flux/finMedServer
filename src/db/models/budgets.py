from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Column, DateTime, Field, SQLModel, Relationship

from src.db.models.departments import Department
from src.db.models.users import User


class Budget(SQLModel, table=True):
    __tablename__ = "budgets"

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
    gross_amount: int = Field(...)
    amount_remaining: int = Field(...)
    title: str = Field(...)
    short_description: str = Field(...)

    # relationships
    department: Department = Relationship(back_populates="budgets")
    user: User = Relationship(back_populates="created_budgets")
    approver: User = Relationship(back_populates="approved_budgets")

    def __repr__(self) -> str:
        return f"<Budget: {self.model_dump()}>"
