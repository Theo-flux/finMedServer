import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.bills import Bill
    from src.db.models.budgets import Budget
    from src.db.models.users import User


class Department(SQLModel, table=True):
    __tablename__ = "departments"

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

    # relationships
    users: List["User"] = Relationship(back_populates="department")
    earnings: List["Bill"] = Relationship(back_populates="department")
    budgets: List["Budget"] = Relationship(back_populates="department")

    def __repr__(self) -> str:
        return f"<Department: {self.model_dump()}>"
