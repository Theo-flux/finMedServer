import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.expenses import Expenses


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
    expenses: List["Expenses"] = Relationship(back_populates="expenses_category")

    def __repr__(self) -> str:
        return f"<Expenses category: {self.model_dump()}>"
