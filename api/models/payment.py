from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SqlEnum, JSON, Numeric, String
from sqlalchemy.sql import func

from db.base import Base
class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"

class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(SqlEnum(Currency, name="currency"), nullable=False)
    description = Column(String)
    meta = Column(JSON)
    status = Column(SqlEnum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.pending)
    idempotency_key = Column(String, unique=True, nullable=False)
    webhook_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    def amount_as_decimal(self) -> Decimal:
        return Decimal(str(self.amount))