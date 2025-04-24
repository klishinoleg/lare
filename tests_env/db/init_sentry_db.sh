#!/bin/bash

DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:-postgres}
SENTRY_DB_NAME=${SENTRY_DB_NAME:-sentry}

check_db_exists() {
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$SENTRY_DB_NAME'" | grep -q 1
}

echo "host: ${DB_HOST} user: ${DB_USER} password: ${DB_PASSWORD} sentry db name: ${SENTRY_DB_NAME}"

echo "Checking if Sentry database '$SENTRY_DB_NAME' exists..."

if check_db_exists; then
  echo "Database '$SENTRY_DB_NAME' already exists."
else
  echo "Database '$SENTRY_DB_NAME' not found. Creating..."
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d postgres -c "CREATE DATABASE $SENTRY_DB_NAME;"
  echo "Database '$SENTRY_DB_NAME' created successfully."
fi
