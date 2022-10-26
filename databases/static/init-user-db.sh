#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER siance;
    ALTER USER siance WITH PASSWORD 'siance';
    CREATE DATABASE siancedb;
    GRANT ALL PRIVILEGES ON DATABASE siancedb TO siance;
EOSQL
