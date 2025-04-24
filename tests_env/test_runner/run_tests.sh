#!/bin/sh

echo "Waiting for FastAPI and Kafka to start... 15 second"
sleep 5
echo "10 seconds"
sleep 5
echo "5 seconds"
sleep 5
echo "Running tests..."
pytest
# tests/t_interfaces/account/test_account_api.py --maxfail=1 --disable-warnings -q
