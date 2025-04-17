FROM python:3.11

WORKDIR /tests

COPY ./pytest.ini .
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./tests ./tests
COPY ./app ./app
COPY ../tests_env/test_runner/run_tests.sh ./run_tests.sh

RUN chmod +x run_tests.sh
