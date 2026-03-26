FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY wheelhouse/ /wheelhouse/

RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]