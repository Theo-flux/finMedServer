from typing import Generic, List, TypeVar

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ServerRespModel(BaseModel, Generic[T]):
    data: T
    message: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PaginationModel(BaseModel):
    total: int
    current_page: int
    limit: int
    total_pages: int


class PaginatedResponseModel(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationModel


class ServerErrorModel(BaseModel, Generic[T]):
    error_code: T
    message: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EmailType:
    def __init__(self, _subject: str, _template: str):
        self.subject = _subject
        self.template = _template


class EmailTypes:
    EMAIL_VERIFICATION = EmailType("Verify your account", "email_verification.html")
    PWD_RESET = EmailType("Password reset", "pwd_reset.html")


class EmailModel(BaseModel):
    subject: str
    reciepients: List[str]
    payload: dict
    template: str
    attachments: List[UploadFile] = ([],)
