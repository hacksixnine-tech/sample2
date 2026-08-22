#!/bin/bash
set -e

echo "=== 1. Resetting Database ==="
sudo -u postgres psql -d phantom -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO phantom_app; GRANT ALL ON SCHEMA public TO public;"

echo "=== 2. Applying Migrations ==="
for f in /mnt/d/Phantom/database/migrations/*.sql; do
    echo "Applying migration: $(basename "$f")"
    sudo -u postgres psql -d phantom -v ON_ERROR_STOP=1 -f "$f"
done

echo "=== 3. Applying Seeds ==="
for f in /mnt/d/Phantom/database/seeds/*.sql; do
    echo "Applying seed: $(basename "$f")"
    sudo -u postgres psql -d phantom -v ON_ERROR_STOP=1 -f "$f"
done

echo "=== 4. Running Verification SQL Tests ==="
for f in /mnt/d/Phantom/database/tests/*.sql; do
    echo "Running test: $(basename "$f")"
    sudo -u postgres psql -d phantom -v ON_ERROR_STOP=1 -f "$f"
done

echo "=== ALL DATABASE MIGRATIONS, SEEDS, AND TESTS COMPLETED SUCCESSFULLY ==="
