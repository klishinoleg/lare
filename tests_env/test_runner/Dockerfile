FROM python:3.12

WORKDIR /tests

COPY ./pyproject.toml .
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./tests ./tests
COPY ./app ./app
COPY ./tests_env/.env ./app/
COPY ./tests_env/test_runner/run_tests.sh ./

RUN chmod +x run_tests.sh
