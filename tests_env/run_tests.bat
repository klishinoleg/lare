@echo off
setlocal

echo 🚀 Starting required Kafka workers...

set KAFKA_APP=interfaces.event_broker.kafka_chapter:app
docker compose up -d --no-recreate --scale kafka_worker=5

set KAFKA_APP=interfaces.event_broker.kafka_finance:app
docker compose up -d --no-recreate --scale kafka_worker=1

echo ✅ Kafka workers up

REM
timeout /t 5 > nul

echo 🧪 Running tests...
docker compose up test_runner --build

echo ✅ Tests finished

echo 🧹 Stopping test Kafka workers...
docker compose stop kafka_worker

endlocal
