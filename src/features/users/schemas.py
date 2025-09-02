from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator

from src.features.config import DBModel, EmailOrStaffNoModel
from src.features.departments.schemas import DeptResponseModel
from src.features.roles.schemas import RoleResponseModel
from src.utils.validators import email_validator


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"
    SUSPENDED = "SUSPENDED"


class CreateUserModel(BaseModel):
    first_name: str = Field(...)
    last_name: str = Field(...)
    email: EmailStr = Field(...)
    password: Optional[str] = Field(default="")
    department_uid: UUID = Field(...)
    role_uid: UUID = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return email_validator(value)


class LoginUserModel(EmailOrStaffNoModel):
    password: Optional[str] = None


class UserResponseModel(DBModel):
    id: int
    staff_no: str
    first_name: str
    last_name: str
    avatar: Optional[str]
    email: str
    status: str
    phone_number: Optional[str]
    last_login: Optional[datetime]
    role: RoleResponseModel
    department: DeptResponseModel

    @field_serializer("last_login")
    def serialize_dt(self, value: datetime, _info):
        if value:
            return value.isoformat()


class UpdateUserModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_uid: Optional[UUID] = None
    role_uid: Optional[UUID] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    last_login: Optional[datetime] = None
