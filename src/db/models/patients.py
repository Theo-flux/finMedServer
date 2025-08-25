import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.db.models.invoices import Invoice
    from src.db.models.users import User


class Patient(SQLModel, table=True):
    __tablename__ = "patients"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, index=True, unique=True)
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
    hospital_id: str = Field(nullable=False, index=True, unique=True)
    user_uid: Optional[uuid.UUID] = Field(foreign_key="users.uid")
    first_name: str = Field(...)
    last_name: str = Field(...)
    other_name: Optional[str] = Field(default="")
    gender: str = Field(...)
    phone_number: Optional[str] = Field(default="")
    patient_type: str = Field(...)

    # relationships
    invoices: List["Invoice"] = Relationship(back_populates="patient")
    user: "User" = Relationship(back_populates="patients")

    def __repr__(self) -> str:
        return f"<Patient: {self.model_dump()}>"
