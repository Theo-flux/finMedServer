from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.features.config import DBModel
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


class LoginUserModel(BaseModel):
    email_or_staff_no: str = Field(...)
    password: Optional[str] = None

    @field_validator("email_or_staff_no")
    @classmethod
    def validate_email_or_staff_no(cls, value: str):
        if not value.strip():
            raise ValueError("Email or Staff Number cannot be empty")
        return value


class UserResponseModel(DBModel):
    id: int
    staff_no: str
    first_name: str
    last_name: str
    avatar: Optional[str]
    email: str
    status: str
    phone_number: Optional[str]
    role: RoleResponseModel
    department: DeptResponseModel


class UpdateUserModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_email_verified: Optional[bool] = None
    is_phone_number_verified: Optional[bool] = None
