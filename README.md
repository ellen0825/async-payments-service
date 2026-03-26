# Async Payments Service

Asynchronous payment microservice with idempotent create, queue-based processing,
gateway simulation, and webhook notifications.

## Tech Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (Async Mode)
- PostgreSQL
- RabbitMQ (FastStream)
- Alembic (Migrations)
- Docker + Docker Compose

## Entities

- `payment_id` (UUID)
- `amount` (decimal, > 0)
- `currency` (`RUB`, `USD`, `EUR`)
- `description`
- `metadata` (JSON)
- `status` (`pending`, `success`, `failure`)
- `idempotency_key` (unique)
- `webhook_url`
- `created_at`, `processed_at`

## API functionality

- `POST /api/v1/payments` (requires `x-api-key` and `idempotency-key`)
  - Creates payment with status `pending`
  - Returns existing payment when same idempotency key is reused
  - Stores an outbox event in DB and publishes to `payments.new` via outbox worker
- `GET /api/v1/payments/{payment_id}` (requires `x-api-key`)
  - Returns payment details (`payment_id`, `amount`, `currency`, `description`, `metadata`, `status`, `idempotency_key`, `webhook_url`, `created_at`, `processed_at`)

## Processing flow

- Worker consumes `payments.new`
- Simulates external gateway (2-5s delay, 90% success / 10% failure)
- Updates payment status and `processed_at`
- Sends webhook with retry/backoff
- Failed message handling uses 3 retries with exponential backoff, then moves message to `payments.dlq`

## Reliability guarantees

4. **Outbound Message Pattern: Guaranteed Event Delivery**
   - On payment creation, API writes both payment row and outbox event in one DB transaction.
   - Consumer publishes outbox events to `payments.new` and marks them as published only after broker publish succeeds.

5. **Retries: 3 Retries with Exponential Backoff**
   - Queue processing retries use retry headers (`x-retry`) and delays of `1s`, `2s`, `4s`.
   - Webhook sending uses retry with exponential backoff as well.

6. **Dead Letter Queue: For Permanently Discarded Messages**
   - Messages failing after the configured retries are forwarded to `payments.dlq`.

7. **Docker: Compose File Including PostgreSQL, RabbitMQ, API, and Consumers**
   - `docker-compose.yml` includes `db` (PostgreSQL), `rabbitmq`, `api`, and `worker` (consumer).
   - API and worker both run Alembic migrations on startup.

8. **Documentation: README File Including Runtime Instructions and Examples**
   - This README includes setup, run instructions, and API request examples.

## Authentication

- All endpoints require a fixed API key in header `X-API-Key`
- Current fixed key: `supersecretapikey`

## Run

Add your API key to `docker-compose.yml` (`API_KEY`) and call API with `x-api-key`.

### Offline wheelhouse setup

From the host machine (outside Docker), pre-download dependency wheels:

```powershell
python -m pip install --upgrade pip
.\scripts\download_wheels.ps1
```

Then build/run with Docker Compose:

```bash
docker-compose up --build
```

## API examples

Create payment:

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecretapikey" \
  -H "Idempotency-Key: ord-1001" \
  -d '{
    "amount": "125.50",
    "currency": "USD",
    "description": "Invoice #1001",
    "metadata": {"customer_id": "cust-1"},
    "webhook_url": "http://host.docker.internal:9000/webhook"
  }'
```

Retrieve payment:

```bash
curl "http://localhost:8000/api/v1/payments/<payment_id>" \
  -H "X-API-Key: supersecretapikey"
```