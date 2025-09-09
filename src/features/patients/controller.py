from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import delete, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.invoices import Invoice
from src.db.models.patients import Patient
from src.features.invoices.schemas import InvoiceStatus, SingleInvoiceResponseModel
from src.features.patients.schemas import (
    CreatePatientModel,
    PatientResponseModel,
    PatientType,
    SinglePatientResponseModel,
    UpdatePatientModel,
)
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import get_current_and_total_pages
from src.utils.exceptions import InvalidToken, NotFound, ResourceExists


class PatientController:
    async def get_patient_by_uid(self, patient_uid: UUID, session: AsyncSession):
        statement = select(Patient).where(Patient.uid == patient_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def get_patient_by_hopsital_id(self, hospital_id: str, session: AsyncSession):
        statement = select(Patient).where(Patient.hospital_id == hospital_id)
        result = await session.exec(statement=statement)

        return result.first()

    async def single_patient(self, patient_uid: UUID, session: AsyncSession):
        exp = await self.get_patient_by_uid(patient_uid=patient_uid, session=session)

        if exp is None:
            raise NotFound("Patient not found")

        exp_response = PatientResponseModel.model_validate(exp)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PatientResponseModel](data=exp_response, message="Patient retrieved!").model_dump(),
        )

    async def get_patient(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        offset: int,
        patient_type: Optional[PatientType] = None,
        q: Optional[str] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        query = select(Patient).options(selectinload(Patient.user))

        if patient_type:
            query = query.where(Patient.patient_type == patient_type)

        if q:
            search_term = f"%{q}%"
            query = query.where(
                Patient.first_name.ilike(search_term)
                | Patient.last_name.ilike(search_term)
                | Patient.other_name.ilike(search_term)
                | Patient.hospital_id.ilike(search_term)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        query = query.order_by(Patient.created_at.desc()).offset(offset).limit(limit)
        results = await session.exec(query)
        patients = results.all()
        patients_response = [SinglePatientResponseModel.model_validate(patient) for patient in patients]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_patients = PaginatedResponseModel.model_validate(
            {
                "items": patients_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[SinglePatientResponseModel]](
                data=paginated_patients, message="Patients retrieved successfully"
            ).model_dump(),
        )

    async def create_patient(self, token_payload: dict, data: CreatePatientModel, session: AsyncSession):
        patient = data.model_dump()

        old_patient = await self.get_patient_by_hopsital_id(hospital_id=patient.get("hospital_id"), session=session)

        if old_patient is not None:
            raise ResourceExists("Patient with similar patient number already exists!")

        try:
            patient["user_uid"] = token_payload["user"]["uid"]
            new_patient = Patient(**patient)

            session.add(new_patient)
            await session.commit()

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=ServerRespModel[bool](data=True, message="Patient created!").model_dump(),
            )
        except Exception as e:
            await session.rollback()
            raise e

    async def get_patient_invoices(
        self,
        patient_uid: UUID,
        limit: int,
        token_payload: dict,
        invoice_status: Optional[InvoiceStatus],
        session: AsyncSession,
        q: Optional[str] = None,
        offset: Optional[int] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        role_uid = token_payload["user"]["role_uid"]

        if not user_uid or not role_uid:
            raise InvalidToken()

        query = (
            select(Invoice)
            .options(
                selectinload(Invoice.user),
                selectinload(Invoice.service),
                selectinload(Invoice.department),
                selectinload(Invoice.patient).selectinload(Patient.user),
            )
            .where(Invoice.patient_uid == patient_uid)
        )

        if q:
            search_term = f"%{q}%"
            query = query.where(Invoice.title.ilike(search_term) | Invoice.serial_no.ilike(search_term))

        if invoice_status:
            query = query.where(Invoice.status == invoice_status)

        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)

        results = await session.exec(query)
        invoices = results.all()
        invoices_response = [SingleInvoiceResponseModel.model_validate(invoice) for invoice in invoices]

        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_invoice = PaginatedResponseModel.model_validate(
            {
                "items": invoices_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[SingleInvoiceResponseModel]](
                data=paginated_invoice, message="Patient invoices retrieved successfully"
            ).model_dump(),
        )

    async def update_patient(self, patient_uid: UUID, data: UpdatePatientModel, session: AsyncSession):
        patient_to_update = await self.get_patient_by_uid(patient_uid=patient_uid, session=session)

        if patient_to_update is None:
            raise NotFound("Patient doesn't exist")

        valid_attrs = data.model_dump(exclude_none=True)
        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(Patient).where(Patient.uid == patient_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(patient_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Patient updated!").model_dump(),
        )

    async def delete_patient(
        self,
        patient_uid: UUID,
        token_payload: dict,
        session: AsyncSession,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        patient_exists = await session.exec(select(Patient).where(Patient.uid == patient_uid))

        if not patient_exists.first():
            raise NotFound("Patient not found!")

        statement = delete(Patient).where(Patient.user_uid == user_uid, Patient.uid == patient_uid)
        await session.exec(statement)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](data=True, message="Patient deleted successfully!").model_dump(),
        )
