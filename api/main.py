from fastapi import FastAPI
from api.routes import payments

app = FastAPI(title="Async Payment Service")

app.include_router(payments.router)