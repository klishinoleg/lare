FROM python:3.12

WORKDIR /locust
COPY ../requirements.txt .


RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./tests_env/locust/locustfile.py .
COPY ./tests ./tests
COPY ./app .
#RUN ls -la /locust && ls -la /locust/tests
CMD ["locust", "-f", "locustfile.py", "--host=http://lare_test_app:8000"]
