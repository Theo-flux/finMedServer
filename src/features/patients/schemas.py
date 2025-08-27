from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from src.features.config import DBModel, Gender


class PatientType(StrEnum):
    IN_PATIENT = "IN_PATIENT"
    OUT_PATIENT = "OUT_PATIENT"


class BasePatientModel(BaseModel):
    first_name: str
    last_name: str
    other_name: Optional[str] = Field(default="")

    @field_validator("first_name", "last_name", "other_name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        if v is None:
            return v
        return v.lower().strip()


class CreatePatientModel(BasePatientModel):
    gender: Gender
    phone_number: Optional[str] = Field(default="")
    hospital_id: str
    patient_type: PatientType


class UpdatePatientModel(BasePatientModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    other_name: Optional[str] = None
    gender: Optional[Gender] = None
    phone_number: Optional[str] = None
    patient_type: Optional[PatientType] = None
    hospital_id: Optional[str] = None


class PatientResponseModel(DBModel):
    id: int
    first_name: str
    last_name: str
    other_name: str
    gender: str
    user_uid: UUID
    phone_number: str
    hospital_id: str
    patient_type: str

    @field_serializer("user_uid")
    def serialize_puuid(self, value: UUID, _info):
        return str(value)
