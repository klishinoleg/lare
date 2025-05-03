FROM python:3.11-slim

WORKDIR /code

COPY celery_exporter/main.py .
COPY .env .

RUN pip install fastapi uvicorn prometheus_client celery redis python-dotenv

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9812"]
