import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.invoices import Invoice
    from src.db.models.users import User


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    serial_no: Optional[str] = Field(nullable=True, index=True, unique=True)
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
    invoice_uid: uuid.UUID = Field(sa_column=Column("invoice_uid", ForeignKey("invoices.uid", ondelete="CASCADE")))
    user_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid")
    payment_method: str = Field(...)
    amount_received: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    reference_number: Optional[str] = Field(default="")
    note: str = Field(default="")

    # relationships
    invoice: "Invoice" = Relationship(back_populates="payments")
    user: "User" = Relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment: {self.model_dump()}>"
