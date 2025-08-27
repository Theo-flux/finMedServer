from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.features.config import AbridgedUserResponseModel, DBModel
from src.features.invoices.schemas import InvoiceResponseModel


class PaymentMethod(StrEnum):
    CASH = "CASH"
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    INSURANCE = "INSURANCE"
    OTHERS = "OTHERS"


class CreatePaymentModel(BaseModel):
    amount_received: int
    note: str
    payment_method: PaymentMethod
    reference_number: Optional[str] = Field(default="")


class UpdatePaymentModel(BaseModel):
    note: Optional[str] = None
    amount_received: Optional[int] = None
    payment_method: Optional[str] = None


class PaymentResponseModel(DBModel):
    id: int
    serial_no: str
    received_at: Optional[datetime] = None
    invoice_uid: UUID
    user_uid: UUID
    payment_method: str
    amount_received: Decimal
    reference_number: str
    note: str

    @field_serializer("invoice_uid", "user_uid")
    def serialize_uuids(self, value: UUID, _info):
        if value:
            return str(value)

    @field_serializer("amount_received")
    def serialize_decimals(self, value: Decimal, _info):
        return float(value)


class SinglePaymentResponseModel(PaymentResponseModel):
    user: AbridgedUserResponseModel
    invoice: Optional[InvoiceResponseModel] = None
