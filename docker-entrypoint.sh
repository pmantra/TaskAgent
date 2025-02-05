#!/bin/bash
set -e

# Wait for database to be ready
if [ "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."
    python << END
import sys
import time
import psycopg2
while True:
    try:
        psycopg2.connect(
            dbname="${DB_NAME}",
            user="${DB_USER}",
            password="${DB_PASSWORD}",
            host="${DB_HOST}",
            port="${DB_PORT}"
        )
        break
    except psycopg2.OperationalError:
        sys.stderr.write("Database not ready. Waiting...\n")
        time.sleep(1)
END
fi

# Run database migrations if APPLY_MIGRATIONS is set
if [ "$APPLY_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Execute the main command
exec "$@"