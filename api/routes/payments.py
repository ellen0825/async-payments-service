import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from api.models.payment import Payment, PaymentStatus
from api.models.outbox import OutboxEvent
from api.models.payment_schema import PaymentCreate, PaymentCreateResponse, PaymentResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.session import get_session
from api.dependencies.auth import verify_api_key

router = APIRouter(prefix="/api/v1/payments")


def to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        payment_id=payment.id,
        amount=payment.amount_as_decimal(),
        currency=payment.currency,
        description=payment.description,
        metadata=payment.meta,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )


def to_create_response(payment: Payment) -> PaymentCreateResponse:
    return PaymentCreateResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.post("", response_model=PaymentCreateResponse, status_code=202, dependencies=[Depends(verify_api_key)])
async def create_payment(
    payment: PaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
    existing = result.scalar_one_or_none()
    if existing:
        return to_create_response(existing)

    new_payment = Payment(
        id=str(uuid.uuid4()),
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        meta=payment.metadata,
        status=PaymentStatus.pending,
        idempotency_key=idempotency_key,
        webhook_url=str(payment.webhook_url) if payment.webhook_url else None,
    )
    outbox_event = OutboxEvent(
        aggregate_id=new_payment.id,
        event_type="payment.created",
        payload={"payment_id": new_payment.id},
        published=False,
    )
    session.add(new_payment)
    session.add(outbox_event)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
        existing = result.scalar_one()
        return to_create_response(existing)
    await session.refresh(new_payment)
    return to_create_response(new_payment)

@router.get("/{payment_id}", response_model=PaymentResponse, dependencies=[Depends(verify_api_key)])
async def get_payment(payment_id: str, session: AsyncSession = Depends(get_session)):
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return to_response(payment)