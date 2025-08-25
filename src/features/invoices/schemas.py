import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from src.features.config import AbridgedUserResponseModel, DBModel
from src.features.departments.schemas import DeptResponseModel
from src.features.patients.schemas import PatientResponseModel
from src.features.services.schemas import ServiceResponseModel


class InvoiceStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    OVER_PAID = "OVER_PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class InvoiceType(StrEnum):
    PATIENT = "PATIENT"
    INSURANCE = "INSURANCE"
    GOVERMENT_GRANT = "GOVERMENT_GRANT"
    DONATION = "DONATION"
    OTHERS = "OTHERS"


class CreateInvoiceModel(BaseModel):
    title: str
    gross_amount: int
    tax_percent: Optional[Decimal] = Field(default=Decimal("0.0"))
    discount_percent: Optional[Decimal] = Field(default=Decimal("0.0"))
    invoice_type: InvoiceType
    patient_uid: Optional[uuid.UUID]


class UpdateInvoiceModel(BaseModel):
    title: Optional[str] = None
    gross_amount: Optional[int] = None
    tax_percent: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    invoice_type: Optional[InvoiceType] = None
    patient_uid: Optional[uuid.UUID] = None


class InvoiceResponseModel(DBModel):
    id: int
    serial_no: str
    invoiced_at: Optional[datetime] = None
    invoice_type: InvoiceType
    status: InvoiceStatus
    title: str
    gross_amount: Decimal
    tax_percent: Decimal
    discount_percent: Decimal
    net_amount_due: Decimal
    department_uid: uuid.UUID
    service_uid: uuid.UUID
    patient_uuid: Optional[uuid.UUID] = None
    user_uid: uuid.UUID

    @field_serializer("department_uid", "user_uid", "service_uid", "patient_uuid")
    def serialize_uuids(self, value: uuid.UUID, _info):
        if value:
            return str(value)

    @field_serializer("gross_amount", "net_amount_due", "tax_percent", "discount_percent")
    def serialize_decimals(self, value: Decimal, _info):
        return float(value)


class SingleInvoiceResponseModel(InvoiceResponseModel):
    user: AbridgedUserResponseModel
    service: ServiceResponseModel
    department: DeptResponseModel
    patient: Optional[PatientResponseModel] = None
