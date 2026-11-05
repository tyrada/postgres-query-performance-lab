#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"

python -m performance_lab.generator --output-dir data --orders "${ORDER_COUNT:-100000}" --customers 10000 --seed 2025
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/01_schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/02_load.sql
python -m performance_lab.benchmark --database-url "$DATABASE_URL" --output-dir reports/generated --repeats "${REPEATS:-5}"

