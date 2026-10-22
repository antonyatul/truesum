#!/usr/bin/env bash
# Apply replica/schema.sql to a scratch Postgres and run the row-level security test.
# Usage: PGHOST=... PGPORT=... PGUSER=postgres tests/db/run.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
db="truesum_rls_$$"
psql -qtA -c "create database $db" >/dev/null
trap 'psql -qtA -c "drop database if exists $db" >/dev/null' EXIT
psql -d "$db" -q -v ON_ERROR_STOP=1 \
  -f tests/db/supabase_stub.sql -f replica/schema.sql -f tests/db/rls_test.sql
