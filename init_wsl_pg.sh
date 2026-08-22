#!/bin/bash
set -e

# Update postgresql.conf to listen on all interfaces
CONF="/etc/postgresql/18/main/postgresql.conf"
HBA="/etc/postgresql/18/main/pg_hba.conf"

echo "listen_addresses = '*'" >> "$CONF"
echo "host all all 0.0.0.0/0 md5" >> "$HBA"
echo "host all all ::/0 md5" >> "$HBA"
echo "host all all 127.0.0.1/32 trust" >> "$HBA"
echo "host all all all trust" >> "$HBA"

service postgresql restart

# Setup users and database
sudo -u postgres psql -c "CREATE USER phantom_app WITH PASSWORD 'phantom_app_secure_password_2026' SUPERUSER;" || true
sudo -u postgres psql -c "ALTER USER phantom_app WITH PASSWORD 'phantom_app_secure_password_2026';" || true
sudo -u postgres psql -c "CREATE DATABASE phantom OWNER phantom_app;" || true
sudo -u postgres psql -d phantom -c "CREATE EXTENSION IF NOT EXISTS postgis;"
sudo -u postgres psql -d phantom -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
sudo -u postgres psql -d phantom -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

echo "PostgreSQL initialization completed successfully!"
