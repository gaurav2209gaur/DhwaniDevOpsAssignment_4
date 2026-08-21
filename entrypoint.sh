#!/bin/sh
set -e
echo "Waiting for database..."
python wait_for_db.py
echo "Starting application server..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - app:app
