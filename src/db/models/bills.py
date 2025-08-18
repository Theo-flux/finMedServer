from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Column, DateTime, Field, SQLModel, Relationship

from src.db.models.patients import Patient
from src.db.models.departments import Department
from src.db.models.payments import Payment
from src.db.models.services import Service


class Bill(SQLModel, table=True):
    __tablename__ = "bills"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
    bill_no: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    billed_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    service_uid: uuid.UUID = Field(foreign_key="services.uid")
    patient_uid: Optional[uuid.UUID] = Field(foreign_key="patients.uid")
    department_uid: uuid.UUID = Field(foreign_key="departments.uid")
    bill_type: str = Field(...)
    name: str = Field(...)
    status: str = Field(...)
    gross_amount: int = Field(primary_key=True, default=None)
    tax_amount: Optional[int] = Field(primary_key=True, default=0)
    net_amount_due: int = Field(primary_key=True, default=None)

    # relationships
    service: Service = Relationship(back_populates="bills")
    patient: Patient = Relationship(back_populates="bills")
    department: Department = Relationship(back_populates="earnings")
    payments: Payment = Relationship(back_populates="bill")

    def __repr__(self) -> str:
        return f"<Bills: {self.model_dump()}>"
