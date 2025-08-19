import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.bills import Bill
    from src.db.models.users import User


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    serial_no: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
        ),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )
    received_at: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    bill_uid: uuid.UUID = Field(foreign_key="bills.uid")
    user_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid")
    payment_method: str = Field(...)
    amount_received: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    reference_number: str = Field(default="")
    Note: str = Field(default="")

    # relationships
    bill: "Bill" = Relationship(back_populates="payments")
    user: "User" = Relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment: {self.model_dump()}>"
