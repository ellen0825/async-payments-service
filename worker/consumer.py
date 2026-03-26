import asyncio
import os
import random
from datetime import datetime, timezone
import logging

import httpx
from sqlalchemy import select

from api.models.outbox import OutboxEvent
from api.models.payment import Payment, PaymentStatus
from db.base import async_session
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "payments.new"
DLQ_NAME = "payments.dlq"
MAX_RETRIES = 3

logger = logging.getLogger("worker")

exchange = RabbitExchange("payments", durable=True)
payments_new_queue = RabbitQueue(QUEUE_NAME, durable=True)
payments_dlq_queue = RabbitQueue(DLQ_NAME, durable=True)

broker = RabbitBroker(RABBITMQ_URL)
app = FastStream(broker)


async def simulate_gateway() -> PaymentStatus:
    await asyncio.sleep(random.randint(2, 5))
    return PaymentStatus.succeeded if random.random() < 0.9 else PaymentStatus.failed


async def send_webhook(payment: Payment) -> None:
    if not payment.webhook_url:
        return

    payload = {
        "payment_id": payment.id,
        "status": payment.status.value,
        "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(payment.webhook_url, json=payload)
                if response.status_code < 500:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(2 ** attempt)


async def process_payment(payment_id: str) -> None:
    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            return

        if payment.status != PaymentStatus.pending:
            return

        payment.status = await simulate_gateway()
        payment.processed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(payment)
        await send_webhook(payment)


async def publish_outbox_events() -> None:
    backoff_s = 1
    while True:
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(OutboxEvent)
                    .where(OutboxEvent.published.is_(False))
                    .order_by(OutboxEvent.created_at)
                    .limit(100)
                )
                events = result.scalars().all()

                for event in events:
                    await broker.publish(
                        event.payload,
                        exchange=exchange,
                        routing_key=QUEUE_NAME,
                        headers={"x-retry": 0},
                    )
                    event.published = True
                    event.published_at = datetime.now(timezone.utc)

                if events:
                    await session.commit()
            backoff_s = 1
            await asyncio.sleep(1)
        except Exception:
            logger.exception("Outbox publisher loop crashed; retrying")
            await asyncio.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 30)


@broker.subscriber(queue=payments_new_queue, exchange=exchange)
async def consume_message(payload: dict, message) -> None:
    retry_count = int((getattr(message, "headers", {}) or {}).get("x-retry", 0))
    try:
        payment_id = payload["payment_id"]
        await process_payment(payment_id)
    except Exception:
        if retry_count >= MAX_RETRIES:
            headers = {"x-retry": retry_count}
            await broker.publish(payload, exchange=exchange, routing_key=DLQ_NAME, headers=headers)
        else:
            await asyncio.sleep(2 ** retry_count)
            headers = {"x-retry": retry_count + 1}
            await broker.publish(payload, exchange=exchange, routing_key=QUEUE_NAME, headers=headers)


@app.after_startup
async def _start_outbox_publisher() -> None:
    asyncio.create_task(publish_outbox_events())


if __name__ == "__main__":
    asyncio.run(app.run())