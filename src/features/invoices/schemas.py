from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

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
    SERVICE = "SERVICE"
    PRODUCT = "PRODUCT"
    SUBSCRIPTION = "SUBSCRIPTION"
    MAINTENANCE = "MAINTENANCE"
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
    department_uid: Optional[UUID] = Field(default=None)
    service_uid: Optional[UUID] = Field(default=None)
    patient_uid: Optional[UUID] = Field(default=None)


class UpdateInvoiceModel(BaseModel):
    title: Optional[str] = None
    gross_amount: Optional[int] = None
    tax_percent: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    invoice_type: Optional[InvoiceType] = None
    department_uid: Optional[UUID] = None
    service_uid: Optional[UUID] = None
    patient_uid: Optional[UUID] = None


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
    department_uid: Optional[UUID] = None
    service_uid: Optional[UUID] = None
    patient_uid: Optional[UUID] = None
    user_uid: Optional[UUID] = None

    @field_serializer("department_uid", "user_uid", "service_uid", "patient_uid")
    def serialize_uuids(self, value: UUID, _info):
        if value:
            return str(value)

    @field_serializer("gross_amount", "net_amount_due", "tax_percent", "discount_percent")
    def serialize_decimals(self, value: Decimal, _info):
        return float(value)


class SingleInvoiceResponseModel(InvoiceResponseModel):
    user: Optional[AbridgedUserResponseModel] = None
    service: Optional[ServiceResponseModel] = None
    department: Optional[DeptResponseModel] = None
    patient: Optional[PatientResponseModel] = None
