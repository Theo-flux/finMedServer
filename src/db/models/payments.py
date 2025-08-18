from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Column, DateTime, Field, SQLModel, Relationship

from src.db.models.bills import Bill
from src.db.models.patients import Patient
from src.db.models.departments import Department
from src.db.models.services import Service
from src.db.models.users import User


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

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
    received_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    bill_uid: uuid.UUID = Field(foreign_key="services.uid")
    user_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid")
    payment_method: str = Field(...)
    amount_recieived: int = Field(primary_key=True, default=None)
    reference_number: str = Field(default="")
    Note: str = Field(default="")

    # relationships
    bill: Bill = Relationship(back_populates="payments")
    user: User = Relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment: {self.model_dump()}>"
