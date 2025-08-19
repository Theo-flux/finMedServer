import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from src.features.services.schemas import ServiceStatus

if TYPE_CHECKING:
    from src.db.models.bills import Bill


class Service(SQLModel, table=True):
    __tablename__ = "services"

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
    status: Optional[str] = Field(
        sa_column=Column(default=ServiceStatus.ACTIVE.value, server_default=ServiceStatus.ACTIVE.value)
    )

    # relationship
    bills: List["Bill"] = Relationship(back_populates="service")

    def __repr__(self) -> str:
        return f"<Service: {self.model_dump()}>"
