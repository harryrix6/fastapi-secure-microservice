#!/bin/sh
set -e

echo "Waiting for PostgreSQL database..."
while ! python -c "import socket; s = socket.socket(); s.connect(('db', 5432)); s.close()" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
alembic upgrade head

echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000