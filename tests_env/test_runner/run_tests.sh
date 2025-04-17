#!/bin/sh

echo "Waiting for FastAPI to start..."
sleep 5

echo "Running tests..."
pytest
# tests/t_interfaces/account/test_account_api.py --maxfail=1 --disable-warnings -q
