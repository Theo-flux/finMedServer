import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

from src.features.invoices.schemas import InvoiceStatus

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
    service_uid: Optional[uuid.UUID] = Field(foreign_key="services.uid", nullable=True)
    patient_uid: Optional[uuid.UUID] = Field(foreign_key="patients.uid", nullable=True)
    user_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid", nullable=True)
    department_uid: Optional[uuid.UUID] = Field(foreign_key="departments.uid", nullable=True)
    invoice_type: str = Field(...)
    title: str = Field(...)
    status: Optional[str] = Field(
        sa_column=Column(default=InvoiceStatus.UNPAID.value, server_default=InvoiceStatus.UNPAID.value)
    )
    gross_amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    tax_percent: Optional[Decimal] = Field(sa_column=Column(Numeric(12, 2)), default=0.0)
    discount_percent: Optional[Decimal] = Field(sa_column=Column(Numeric(12, 2)), default=0.0)
    net_amount_due: Decimal = Field(sa_column=Column(Numeric(12, 2)))

    # relationships
    user: "User" = Relationship(back_populates="invoices")
    service: "Service" = Relationship(back_populates="invoices")
    patient: "Patient" = Relationship(back_populates="invoices")
    department: "Department" = Relationship(back_populates="invoices")
    payments: List["Payment"] = Relationship(back_populates="invoice", cascade_delete=True)

    @property
    def tax_amount(self) -> Decimal:
        """Calculate the tax amount based on gross amount."""
        if self.gross_amount is None or self.tax_percent is None or self.tax_percent <= 0:
            return Decimal("0.0")
        return self.gross_amount * (self.tax_percent / 100)

    @property
    def discount_amount(self) -> Decimal:
        """Calculate the discount amount based on gross + tax."""
        if self.gross_amount is None or self.discount_percent is None or self.discount_percent <= 0:
            return Decimal("0.0")

        gross_with_tax = self.gross_amount + self.tax_amount
        return gross_with_tax * (self.discount_percent / 100)

    @property
    def total_invoice_amount(self) -> Decimal:
        """Calculate the total invoice amount (gross + tax - discount)."""
        if self.gross_amount is None:
            return Decimal("0.0")

        return self.gross_amount + self.tax_amount - self.discount_amount

    @property
    def total_payments(self) -> Decimal:
        """Calculate the total amount paid against this invoice."""
        if not self.payments:
            return Decimal("0.0")

        return sum(payment.amount_received for payment in self.payments if payment.amount_received)

    def calculate_net_amount_due(self) -> Decimal:
        """Calculate the net amount due (total invoice - payments made)."""
        return self.total_invoice_amount - self.total_payments

    @property
    def is_fully_paid(self) -> bool:
        """Check if the invoice is fully paid."""
        return self.calculate_net_amount_due() <= Decimal("0.0")

    @property
    def is_overpaid(self) -> bool:
        """Check if payments exceed the invoice total."""
        return self.calculate_net_amount_due() < Decimal("0.0")

    @property
    def payment_status(self) -> str:
        """Get the payment status of the invoice."""
        net_due = self.calculate_net_amount_due()
        total_payments = self.total_payments

        if total_payments == Decimal("0.0"):
            return InvoiceStatus.UNPAID
        elif net_due <= Decimal("0.0"):
            return InvoiceStatus.PAID if net_due == Decimal("0.0") else InvoiceStatus.OVER_PAID
        else:
            return InvoiceStatus.PARTIALLY_PAID

    def __repr__(self) -> str:
        return f"<Invoices: {self.model_dump()}>"
