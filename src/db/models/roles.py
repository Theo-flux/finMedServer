from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from src.features.roles.schemas import RoleStatus

if TYPE_CHECKING:
    from src.db.models.users import User


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    id: Optional[int] = Field(
        primary_key=True,
        default=None,
    )
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
    status: Optional[str] = Field(default=RoleStatus.ACTIVE.value)

    users: Optional[List["User"]] = Relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Roles: {self.model_dump()}>"
