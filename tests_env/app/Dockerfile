FROM python:3.12

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app .
COPY ./tests_env/.env ./

CMD ["uvicorn", "interfaces.fast_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
