import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.payments.controller import PaymentController
from src.features.payments.schemas import (
    CreatePaymentModel,
    PaymentMethod,
    PaymentResponseModel,
    SinglePaymentResponseModel,
    UpdatePaymentModel,
)
from src.misc.schemas import ServerRespModel

payment_router = APIRouter()
payment_controller = PaymentController()


@payment_router.post("", response_model=ServerRespModel[bool])
async def create_payment(
    data: CreatePaymentModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await payment_controller.create_payment(token_payload=token_payload, data=data, session=session)


@payment_router.get("", response_model=ServerRespModel[PaymentResponseModel])
async def get_payments(
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
    return await payment_controller.get_payments(
        q=q,
        limit=limit,
        offset=offset,
        reference_number=reference_number,
        payment_method=payment_method,
        token_payload=token_payload,
        session=session,
    )


@payment_router.get("/{payment_uid}", response_model=ServerRespModel[SinglePaymentResponseModel])
async def get_single_payment(
    payment_uid: uuid.UUID,
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await payment_controller.single_payment(payment_uid=payment_uid, session=session)


@payment_router.delete("/{payment_uid}", response_model=ServerRespModel[bool])
async def del_payment(
    payment_uid: uuid.UUID,
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await payment_controller.delete_payment(
        payment_uid=payment_uid, token_payload=token_payload, session=session
    )


@payment_router.patch("/{payment_uid}", response_model=ServerRespModel[bool])
async def update_payment(
    payment_uid: uuid.UUID,
    data: UpdatePaymentModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await payment_controller.update_payment(
        payment_uid=payment_uid, token_payload=token_payload, data=data, session=session
    )
