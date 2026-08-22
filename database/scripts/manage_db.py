#!/usr/bin/env python3
"""
PHANTOM Database Management & Test Automation Script
Executes migrations, seed scripts, and verification test suites via Docker.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / "migrations"
SEEDS_DIR = BASE_DIR / "seeds"
TESTS_DIR = BASE_DIR / "tests"

CONTAINER_NAME = "phantom-postgres"
DB_USER = "postgres"
DB_NAME = "phantom"

def run_psql_command(sql_text: str) -> tuple[int, str]:
    """Execute raw SQL string inside the PostgreSQL container."""
    cmd = [
        "docker", "exec", "-i", CONTAINER_NAME,
        "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"
    ]
    proc = subprocess.run(cmd, input=sql_text, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def run_sql_file(file_path: Path) -> bool:
    """Execute a single SQL file inside the container."""
    print(f"  -> Executing: {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    code, output = run_psql_command(sql_content)
    if code != 0:
        print(f"     [ERROR] Failed to execute {file_path.name}:\n{output}")
        return False
    return True

def reset_database():
    """Drop and recreate public schema for a clean slate."""
    print("\n=======================================================")
    print(" 0. RESETTING DATABASE (CLEAN SLATE)")
    print("=======================================================")
    sql = "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
    code, output = run_psql_command(sql)
    if code != 0:
        print(f" [ERROR] Failed to reset database:\n{output}")
        return False
    print(" [OK] Database schema reset.")
    return True

def apply_migrations():
    """Apply all migration files in alphabetical/numeric order."""
    print("\n=======================================================")
    print(" 1. APPLYING DATABASE MIGRATIONS")
    print("=======================================================")
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        print("No migration files found in", MIGRATIONS_DIR)
        return False
    
    for f in sql_files:
        if not run_sql_file(f):
            return False
    print(" [OK] All migrations applied successfully.")
    return True

def apply_seeds():
    """Apply all seed files in alphabetical/numeric order."""
    print("\n=======================================================")
    print(" 2. SEEDING DEMO DATA")
    print("=======================================================")
    sql_files = sorted(SEEDS_DIR.glob("*.sql"))
    if not sql_files:
        print("No seed files found in", SEEDS_DIR)
        return False
    
    for f in sql_files:
        if not run_sql_file(f):
            return False
    print(" [OK] All seed data loaded successfully.")
    return True

def run_tests():
    """Run all verification tests and print outputs."""
    print("\n=======================================================")
    print(" 3. RUNNING VERIFICATION SUITES")
    print("=======================================================")
    sql_files = sorted(TESTS_DIR.glob("*.sql"))
    if not sql_files:
        print("No test files found in", TESTS_DIR)
        return False
    
    all_passed = True
    for f in sql_files:
        print(f"\n--- Running Test: {f.name} ---")
        with open(f, "r", encoding="utf-8") as tf:
            sql_content = tf.read()
        code, output = run_psql_command(sql_content)
        print(output.strip())
        if code != 0:
            print(f" [FAIL] Test {f.name} failed!")
            all_passed = False
        else:
            print(f" [PASS] Test {f.name} succeeded.")
    
    return all_passed

def wait_for_db(max_retries=15):
    """Wait for Postgres to be ready inside Docker."""
    print("Waiting for PostgreSQL database container to become healthy...")
    for i in range(max_retries):
        cmd = ["docker", "exec", "-i", CONTAINER_NAME, "pg_isready", "-U", DB_USER, "-d", DB_NAME]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(" [OK] PostgreSQL is healthy and accepting connections.")
            return True
        time.sleep(2)
    print(" [ERROR] Timed out waiting for PostgreSQL container.")
    return False

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if not wait_for_db():
        sys.exit(1)
        
    if action in ("reset", "fresh"):
        if not reset_database():
            sys.exit(1)

    if action in ("all", "fresh", "migrate"):
        if action == "all":
            # Reset before all to ensure completely deterministic test run
            if not reset_database():
                sys.exit(1)
        if not apply_migrations():
            sys.exit(1)
            
    if action in ("all", "fresh", "seed"):
        if not apply_seeds():
            sys.exit(1)
            
    if action in ("all", "fresh", "test"):
        if not run_tests():
            sys.exit(1)
            
    print("\n=======================================================")
    print(" [SUCCESS] PHANTOM Database Foundation Initialized & Verified!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
