@echo off
setlocal

echo Starting required Kafka workers...

docker compose up --scale kafka_worker_chapter=5 -d
docker compose up --scale kafka_worker_finance=1 -d

echo Kafka workers up

REM
timeout /t 5 > nul

echo Running tests...
docker compose up test_runner --build

echo Tests finished

echo Stopping test Kafka workers...
docker compose stop kafka_worker

endlocal
