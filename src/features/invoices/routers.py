from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.invoices.controller import InvoiceController
from src.features.invoices.schemas import (
    CreateInvoiceModel,
    InvoiceStatus,
    SingleInvoiceResponseModel,
    UpdateInvoiceModel,
)
from src.features.payments.schemas import PaymentMethod, PaymentResponseModel
from src.misc.schemas import PaginatedResponseModel, ServerRespModel

invoice_router = APIRouter()
invoice_controller = InvoiceController()


@invoice_router.post("", response_model=ServerRespModel[bool])
async def create_invoice(
    data: CreateInvoiceModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await invoice_controller.create_invoice(token_payload=token_payload, data=data, session=session)


@invoice_router.get("")
async def get_invoices(
    invoice_status: InvoiceStatus = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await invoice_controller.get_user_invoice(
        invoice_status=invoice_status, limit=limit, q=q, offset=offset, token_payload=token_payload, session=session
    )


@invoice_router.get("/{invoice_uid}", response_model=ServerRespModel[SingleInvoiceResponseModel])
async def get_single_invoice(
    invoice_uid: UUID,
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await invoice_controller.single_invoice(invoice_uid=invoice_uid, session=session)


@invoice_router.get(
    "/{invoice_uid}/payments", response_model=ServerRespModel[PaginatedResponseModel[PaymentResponseModel]]
)
async def get_invoice_payments(
    invoice_uid: UUID,
    payment_method: PaymentMethod = Query(default=None),
    reference_number: str = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await invoice_controller.get_invoice_payments(
        invoice_uid=invoice_uid,
        q=q,
        limit=limit,
        offset=offset,
        payment_method=payment_method,
        reference_number=reference_number,
        token_payload=token_payload,
        session=session,
    )


@invoice_router.delete("/{invoice_uid}", response_model=ServerRespModel[bool])
async def del_invoice(
    invoice_uid: UUID,
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await invoice_controller.delete_invoice(
        invoice_uid=invoice_uid, token_payload=token_payload, session=session
    )


@invoice_router.patch("/{invoice_uid}", response_model=ServerRespModel[bool])
async def update_invoice(
    invoice_uid: UUID,
    data: UpdateInvoiceModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await invoice_controller.update_invoice(
        invoice_uid=invoice_uid, token_payload=token_payload, data=data, session=session
    )
