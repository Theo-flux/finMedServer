import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.departments import Department
    from src.db.models.patients import Patient
    from src.db.models.payments import Payment
    from src.db.models.services import Service
    from src.db.models.users import User


class Invoice(SQLModel, table=True):
    __tablename__ = "invoices"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    serial_no: Optional[str] = Field(nullable=True, index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )
    invoiced_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    service_uid: uuid.UUID = Field(foreign_key="services.uid")
    patient_uid: Optional[uuid.UUID] = Field(foreign_key="patients.uid")
    user_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid")
    department_uid: uuid.UUID = Field(foreign_key="departments.uid")
    invoice_type: str = Field(...)
    name: str = Field(...)
    status: str = Field(...)
    gross_amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    tax_amount: Optional[Decimal] = Field(sa_column=Column(Numeric(12, 2)), default=0.0)
    net_amount_due: Decimal = Field(sa_column=Column(Numeric(12, 2)))

    # relationships
    user: "User" = Relationship(back_populates="invoices")
    service: "Service" = Relationship(back_populates="invoices")
    patient: "Patient" = Relationship(back_populates="invoices")
    department: "Department" = Relationship(back_populates="invoices")
    payments: "Payment" = Relationship(back_populates="invoice")

    def __repr__(self) -> str:
        return f"<Invoives: {self.model_dump()}>"
