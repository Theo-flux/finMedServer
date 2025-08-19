import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.features.roles.schemas import UserRoles
from src.utils.validators import email_validator


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"
    SUSPENDED = "SUSPENDED"


class CreateUserModel(BaseModel):
    first_name: str = Field(...)
    last_name: str = Field(...)
    email: EmailStr = Field(...)
    role_uid: uuid.UUID = Field(...)
    password: str = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return email_validator(value)


class LoginUserModel(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if not value.strip():
            raise ValueError("Email can't not be empty")
        return email_validator(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not value.strip():
            raise ValueError("Password can't not be empty")
        return value


class UserResponseModel(BaseModel):
    id: int
    uid: uuid.UUID
    created_at: datetime
    updated_at: datetime
    staff_no: str
    first_name: str
    last_name: str
    avatar: Optional[str]
    email: str
    phone_number: Optional[str]
    role: UserRoles
    is_phone_number_verified: bool

    model_config = ConfigDict(from_attributes=True)


class UpdateUserModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_email_verified: Optional[bool] = None
    is_phone_number_verified: Optional[bool] = None
