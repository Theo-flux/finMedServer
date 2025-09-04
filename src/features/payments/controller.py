from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.invoices import Invoice
from src.db.models.payments import Payment
from src.features.invoices.controller import InvoiceController
from src.features.payments.schemas import (
    CreatePaymentModel,
    PaymentMethod,
    PaymentResponseModel,
    SinglePaymentResponseModel,
    UpdatePaymentModel,
)
from src.features.roles.controller import RoleController
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import build_serial_no, get_current_and_total_pages
from src.utils.exceptions import InsufficientPermissions, InvalidToken, NotFound

invoice_controller = InvoiceController()
role_controller = RoleController()


class PaymentController:
    async def generate_payment_serial_no(self, payment_uid: UUID, session: AsyncSession):
        payment = await self.get_payment_by_uid(payment_uid, session)
        serial_no = build_serial_no("Payment", payment.id)
        statement = update(Payment).where(Payment.uid == payment_uid).values(serial_no=serial_no)

        await session.exec(statement)

    async def get_payment_by_uid(self, payment_invoice: UUID, session: AsyncSession):
        statement = (
            select(Payment)
            .options(selectinload(Payment.user), selectinload(Payment.invoice))
            .where(Payment.uid == payment_invoice)
        )
        result = await session.exec(statement=statement)

        return result.first()

    async def single_payment(self, payment_uid: UUID, session: AsyncSession):
        invoice = await self.get_payment_by_uid(payment_uid=payment_uid, session=session)

        if invoice is None:
            raise NotFound("Payment not found")

        invoice_response = SinglePaymentResponseModel.model_validate(invoice)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[SinglePaymentResponseModel](
                data=invoice_response, message="Payment retrieved!"
            ).model_dump(),
        )

    async def get_payments(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        offset: int,
        serial_no: Optional[str],
        payment_method: Optional[PaymentMethod] = None,
        reference_number: Optional[str] = None,
        q: Optional[str] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        role_uid = token_payload["user"]["role_uid"]

        if not user_uid or not role_uid:
            raise InvalidToken()

        query = select(Payment)

        if not await role_controller.is_role_admin(role_uid=role_uid, session=session):
            query = query.where(Payment.user_uid == user_uid)
        if q:
            search_term = f"%{q}"
            query = query.where(Payment.note.ilike(search_term) | Payment.serial_no.ilike(search_term))

        if payment_method:
            query = query.where(Payment.payment_method == payment_method)

        if reference_number:
            query = query.where(Payment.reference_number.ilike(f"%{reference_number}%"))

        if serial_no:
            query = query.where(Payment.serial_no == serial_no)

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
                data=paginated_invoice_payments, message="Payments retrieved successfully"
            ).model_dump(),
        )

    async def create_payment(
        self, invoice_uid: UUID, token_payload: dict, data: CreatePaymentModel, session: AsyncSession
    ):
        payment = data.model_dump()
        payment["user_uid"] = token_payload["user"]["uid"]

        try:
            invoice_to_update = await invoice_controller.get_invoice_with_payments(
                invoice_uid=invoice_uid, session=session
            )
            if not invoice_to_update:
                raise NotFound("Invoice not found")

            payment["invoice_uid"] = invoice_uid
            new_payment = Payment(**payment)
            session.add(new_payment)

            await session.flush()
            await self.generate_payment_serial_no(new_payment.uid, session)
            await session.refresh(invoice_to_update)

            invoice_to_update.status = invoice_to_update.payment_status
            session.add(invoice_to_update)

            await session.commit()
            await session.refresh(invoice_to_update)
            await session.refresh(invoice_to_update)

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=ServerRespModel[bool](data=True, message="Payment created!").model_dump(),
            )
        except Exception as e:
            await session.rollback()
            raise e

    async def update_payment(
        self, payment_uid: UUID, token_payload: dict, data: UpdatePaymentModel, session: AsyncSession
    ):
        payment_to_update = await self.get_payment_by_uid(payment_uid, session)

        if payment_to_update is None:
            raise NotFound("Payment doesn't exist")

        if str(payment_to_update.user_uid) != token_payload["user"]["uid"]:
            raise InsufficientPermissions("You don't have the permission to update this payment!")

        valid_attrs = data.model_dump(exclude_none=True)
        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()

            for field, value in valid_attrs.items():
                setattr(payment_to_update, field, value)

            invoice_to_update = await invoice_controller.get_invoice_with_payments(
                invoice_uid=payment_to_update.invoice_uid, session=session
            )

            if not invoice_to_update:
                raise NotFound("Invoice not found")

            await session.commit()
            await session.refresh(invoice_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Payment updated!").model_dump(),
        )

    async def delete_payment(
        self,
        payment_uid: UUID,
        token_payload: dict,
        session: AsyncSession,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        payment_result = await session.exec(
            select(Payment).where(Payment.user_uid == user_uid, Payment.uid == payment_uid)
        )
        payment_to_delete = payment_result.first()

        if not payment_to_delete:
            raise NotFound("Payment not found!")

        invoice_to_update = await session.get(Invoice, payment_to_delete.invoice_uid)
        if not invoice_to_update:
            raise NotFound("Invoice not found!")

        await session.delete(payment_to_delete)
        await session.flush()

        session.add(invoice_to_update)

        await session.commit()
        await session.refresh(invoice_to_update)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](data=True, message="Payment deleted successfully!").model_dump(),
        )
