#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is not set}"

echo "[firma_web] applying SQL migrations..."
for f in /app/infra/sql/*.sql; do
  [ -e "$f" ] || continue
  echo " -> running $f"
  psql "$DATABASE_URL" -f "$f"
done

echo "[firma_web] starting app..."
exec waitress-serve --host=0.0.0.0 --port=5000 run:app
