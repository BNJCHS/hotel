#!/bin/sh
set -e

HOST="${DB_HOST:-db}"
PORT="${DB_PORT:-3306}"

echo "Waiting for database at $HOST:$PORT..."
until nc -z "$HOST" "$PORT"; do
  echo "DB not ready, sleeping..."
  sleep 2
done

echo "Database is up! Running migrations and collectstatic..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

echo "Starting application..."
exec "$@"
