from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.invoices.schemas import InvoiceStatus, SingleInvoiceResponseModel
from src.features.patients.controller import patient_controller
from src.features.patients.schemas import (
    CreatePatientModel,
    PatientResponseModel,
    PatientType,
    SinglePatientResponseModel,
    UpdatePatientModel,
)
from src.misc.schemas import PaginatedResponseModel, ServerRespModel

patients_router = APIRouter()


@patients_router.post("", response_model=ServerRespModel[bool])
async def create_patient(
    data: CreatePatientModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await patient_controller.create_patient(token_payload=token_payload, data=data, session=session)


@patients_router.get("", response_model=ServerRespModel[PaginatedResponseModel[SinglePatientResponseModel]])
async def get_patient(
    q: Optional[str] = Query(default=None),
    patient_type: Optional[PatientType] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await patient_controller.get_patient(
        q=q, patient_type=patient_type, limit=limit, token_payload=token_payload, session=session, offset=offset
    )


@patients_router.get(
    "/{patient_uid}/invoices",
    status_code=200,
    response_model=ServerRespModel[PaginatedResponseModel[SingleInvoiceResponseModel]],
)
async def get_patient_invoices(
    patient_uid: UUID,
    invoice_status: InvoiceStatus = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await patient_controller.get_patient_invoices(
        patient_uid=patient_uid,
        invoice_status=invoice_status,
        limit=limit,
        q=q,
        offset=offset,
        token_payload=token_payload,
        session=session,
    )


@patients_router.get("/{patient_uid}", response_model=ServerRespModel[PatientResponseModel])
async def get_patient_by_uid(
    patient_uid: UUID,
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await patient_controller.single_patient(patient_uid=patient_uid, session=session)


@patients_router.patch("/{patient_uid}", response_model=ServerRespModel[bool])
async def update_patient(
    patient_uid: UUID,
    data: UpdatePatientModel = Body(...),
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await patient_controller.update_patient(patient_uid=patient_uid, data=data, session=session)
