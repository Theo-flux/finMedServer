from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from src.features.services.schemas import ServiceStatus

if TYPE_CHECKING:
    from src.db.models.invoices import Invoice


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: Optional[int] = Field(primary_key=True, default=None)
    uid: UUID = Field(default_factory=uuid4, nullable=False, index=True, unique=True)
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
    name: str = Field(...)
    status: Optional[str] = Field(
        sa_column=Column(default=ServiceStatus.ACTIVE.value, server_default=ServiceStatus.ACTIVE.value)
    )

    # relationship
    invoices: List["Invoice"] = Relationship(back_populates="service")

    def __repr__(self) -> str:
        return f"<Service: {self.model_dump()}>"
