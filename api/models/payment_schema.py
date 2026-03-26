from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from api.models.payment import Currency, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Currency
    description: str | None = None
    metadata: dict[str, Any] | None = None
    webhook_url: AnyHttpUrl | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: str
    amount: Decimal
    currency: Currency
    description: str | None = None
    metadata: dict[str, Any] | None = None
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str | None = None
    created_at: datetime
    processed_at: datetime | None = None


class PaymentCreateResponse(BaseModel):
    payment_id: str
    status: PaymentStatus
    created_at: datetime