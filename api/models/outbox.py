from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, Column, DateTime, JSON, String
from db.base import Base
class OutboxEvent(Base):
    __tablename__ = "outbox"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_id = Column(String, nullable=False)  # Payment ID
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)