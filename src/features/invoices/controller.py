import uuid
from datetime import datetime
from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import delete, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.invoices import Invoice
from src.db.models.payments import Payment
from src.features.invoices.schemas import (
    CreateInvoiceModel,
    InvoiceResponseModel,
    InvoiceStatus,
    SingleInvoiceResponseModel,
    UpdateInvoiceModel,
)
from src.features.patients.controller import PatientController
from src.features.payments.schemas import PaymentMethod, PaymentResponseModel
from src.features.roles.controller import RoleController
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import build_serial_no, get_current_and_total_pages
from src.utils.exceptions import BadRequest, InsufficientPermissions, InvalidToken, NotFound

patient_controller = PatientController()
role_controller = RoleController()


class InvoiceController:
    async def generate_invoice_serial_no(self, invoice_uid: uuid.UUID, session: AsyncSession):
        invoice = await self.get_invoice_by_uid(invoice_uid, session)
        serial_no = build_serial_no("Invoice", invoice.id)
        statement = update(Invoice).where(Invoice.uid == invoice_uid).values(serial_no=serial_no)

        await session.exec(statement)

    async def get_invoice_by_uid(self, invoice_uid: uuid.UUID, session: AsyncSession):
        statement = (
            select(Invoice)
            .options(
                selectinload(Invoice.user),
                selectinload(Invoice.patient),
                selectinload(Invoice.service),
                selectinload(Invoice.department),
            )
            .where(Invoice.uid == invoice_uid)
        )
        result = await session.exec(statement=statement)

        return result.first()

    async def get_invoice_with_payments(self, invoice_uid: uuid.UUID, session: AsyncSession):
        statement = select(Invoice).options(selectinload(Invoice.payments)).where(Invoice.uid == invoice_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def single_invoice(self, invoice_uid: uuid.UUID, session: AsyncSession):
        invoice = await self.get_invoice_by_uid(invoice_uid=invoice_uid, session=session)

        if invoice is None:
            raise NotFound("Invoice not found")

        invoice_response = SingleInvoiceResponseModel.model_validate(invoice)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[SingleInvoiceResponseModel](
                data=invoice_response, message="Invoice retrieved!"
            ).model_dump(),
        )

    async def get_user_invoice(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        invoice_status: Optional[InvoiceStatus],
        q: Optional[str] = None,
        offset: Optional[int] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        role_uid = token_payload["user"]["role_uid"]

        if not user_uid or not role_uid:
            raise InvalidToken()

        query = select(Invoice)

        if not await role_controller.is_role_admin(role_uid=role_uid, session=session):
            query = query.where(Invoice.user_uid == user_uid)

        if q:
            search_term = f"%{q}%"
            query = query.where(Invoice.title.ilike(search_term) | Invoice.serial_no.ilike(search_term))

        if invoice_status:
            query = query.where(Invoice.status == invoice_status)

        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)

        results = await session.exec(query)
        budgets = results.all()
        budgets_response = [InvoiceResponseModel.model_validate(budget) for budget in budgets]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_budget = PaginatedResponseModel.model_validate(
            {
                "items": budgets_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[InvoiceResponseModel]](
                data=paginated_budget, message="Invoice retrieved successfully"
            ).model_dump(),
        )

    async def create_invoice(self, token_payload: dict, data: CreateInvoiceModel, session: AsyncSession):
        invoice = data.model_dump()
        invoice["user_uid"] = token_payload["user"]["uid"]

        try:
            if invoice.get("patient_uid"):
                patient = await patient_controller.get_patient_by_uid(
                    patient_uid=invoice.get("patient_uid"), session=session
                )

                if not patient:
                    raise NotFound("Patient doesn't exist!")

            print(invoice)
            new_invoice = Invoice(**invoice)
            new_invoice.net_amount_due = new_invoice.calculate_net_amount_due()
            session.add(new_invoice)

            await session.flush()
            await self.generate_invoice_serial_no(new_invoice.uid, session)
            await session.commit()

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=ServerRespModel[bool](data=True, message="Invoice created!").model_dump(),
            )
        except Exception as e:
            await session.rollback()
            raise e

    async def update_invoice(
        self, invoice_uid: uuid.UUID, token_payload: dict, data: UpdateInvoiceModel, session: AsyncSession
    ):
        invoice_to_update = await self.get_invoice_with_payments(invoice_uid, session)

        if invoice_to_update is None:
            raise NotFound("Invoice doesn't exist")

        if str(invoice_to_update.user_uid) != token_payload["user"]["uid"]:
            raise InsufficientPermissions("You don't have the permission to update this invoice!")

        existing_payments = await session.exec(select(Payment).where(Payment.invoice_uid == invoice_uid))
        payments = existing_payments.all()

        valid_attrs = data.model_dump(exclude_none=True)
        if valid_attrs:
            financial_fields = {"gross_amount", "tax_percent", "discount_percent"}
            print("Payments count: ", len(payments))
            if payments and any(field in valid_attrs for field in financial_fields):
                raise BadRequest("Cannot update financial details of an invoice with existing payments")

            if valid_attrs.get("patient_uid"):
                patient = await patient_controller.get_patient_by_uid(
                    patient_uid=valid_attrs.get("patient_uid"), session=session
                )
                if not patient:
                    raise NotFound("Patient doesn't exist!")

            valid_attrs["updated_at"] = datetime.now()

            for field, value in valid_attrs.items():
                setattr(invoice_to_update, field, value)

            if any(field in valid_attrs for field in financial_fields):
                invoice_to_update.net_amount_due = invoice_to_update.calculate_net_amount_due()

            await session.commit()
            await session.refresh(invoice_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Invoice updated!").model_dump(),
        )

    async def get_invoice_payments(
        self,
        invoice_uid: uuid.UUID,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        offset: int,
        payment_method: Optional[PaymentMethod] = None,
        reference_number: Optional[str] = None,
        q: Optional[str] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        query = select(Payment).where(Payment.invoice_uid == invoice_uid)

        if q:
            query = query.where(Payment.note.ilike(f"%{q}"))

        if payment_method:
            query = query.where(Payment.payment_method == payment_method)

        if reference_number:
            query = query.where(Payment.reference_number.ilike(f"%{reference_number}%"))

        count_query = select(func.count()).select_from(query.subquery())

        total = await session.scalar(count_query)

        query = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit)

        results = await session.exec(query)

        invoice_payments = results.all()
        invoice_payments_response = [PaymentResponseModel.model_validate(invoice) for invoice in invoice_payments]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_invoice_payments = PaginatedResponseModel.model_validate(
            {
                "items": invoice_payments_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[PaymentResponseModel]](
                data=paginated_invoice_payments, message="Invoice Payments retrieved successfully"
            ).model_dump(),
        )

    async def delete_invoice(
        self,
        invoice_uid: uuid.UUID,
        token_payload: dict,
        session: AsyncSession,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        budget_exists = await session.exec(
            select(Invoice).where(Invoice.user_uid == user_uid, Invoice.uid == invoice_uid)
        )

        if not budget_exists.first():
            raise NotFound("Invoice not found!")

        statement = delete(Invoice).where(Invoice.user_uid == user_uid, Invoice.uid == invoice_uid)
        await session.exec(statement)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](data=True, message="Invoice deleted successfully!").model_dump(),
        )
