from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, field_serializer, field_validator

from src.features.config import EmailOrStaffNoModel
from src.utils.validators import email_validator


class UserType(StrEnum):
    NEW_USER = "new_user"
    OLD_USER = "old_user"


class ForgotPwdModel(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return email_validator(value)


class ResetPwdModel(BaseModel):
    new_password: str


class ChangePwdModel(EmailOrStaffNoModel):
    new_password: str


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    user_type: UserType


class TokenUserModel(BaseModel):
    id: int
    uid: UUID
    staff_no: str
    first_name: str
    last_name: str
    email: str
    status: str
    role_uid: UUID
    department_uid: UUID

    @field_serializer("uid", "role_uid", "department_uid")
    def serialize_uuid(self, value: UUID, _info):
        return str(value)
