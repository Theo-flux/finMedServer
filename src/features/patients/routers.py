from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.patients.controller import PatientController
from src.features.patients.schemas import CreatePatientModel, PatientResponseModel, PatientType, UpdatePatientModel
from src.misc.schemas import PaginatedResponseModel, ServerRespModel

patients_router = APIRouter()
patient_controller = PatientController()


@patients_router.post("", response_model=ServerRespModel[bool])
async def create_patient(
    data: CreatePatientModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await patient_controller.create_patient(token_payload=token_payload, data=data, session=session)


@patients_router.get("", response_model=ServerRespModel[PaginatedResponseModel[PatientResponseModel]])
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
