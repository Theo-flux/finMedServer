import uuid

from pydantic import BaseModel, field_serializer, field_validator

from src.utils.validators import email_validator


class ForgotPwdModel(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return email_validator(value)


class ResetPwdModel(BaseModel):
    new_password: str


class ChangePwdModel(BaseModel):
    new_password: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return email_validator(value)


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str


class LoginResModel(TokenModel):
    is_email_verified: bool
    is_phone_number_verified: bool


class TokenUserModel(BaseModel):
    id: int
    uid: uuid.UUID
    staff_no: str
    first_name: str
    last_name: str
    email: str
    status: str
    role_uid: uuid.UUID
    department_uid: uuid.UUID

    @field_serializer("uid", "role_uid", "department_uid")
    def serialize_uuid(self, value: uuid.UUID, _info):
        return str(value)
