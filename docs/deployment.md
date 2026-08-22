# PHANTOM — Production Deployment & Operational Guide

This document details the production deployment, containerization, environment configuration, and operational verification of the **PHANTOM** backend.

---

## 1. Prerequisites & System Requirements

- **Operating System**: Ubuntu 22.04 LTS / 24.04 LTS (or Windows with WSL2 Ubuntu)
- **Container Engine**: Docker Engine 24.0+ & Docker Compose v2.20+
- **Database Engine**: PostgreSQL 16+ or 18 with PostGIS 3.4+ (`postgis/postgis:16-3.4` or `postgis:18-3.6`)
- **Python Runtime**: Python 3.11, 3.12, or 3.14 with `pip` / `venv`
- **Memory & CPU**: Minimum 4 Cores, 8 GB RAM (16 GB recommended for live AI workloads).

---

## 2. Docker & Container Orchestration

PHANTOM provides a production-grade multi-stage `Dockerfile` and `docker-compose.yml` for unified deployment:

### Launching the Full Stack

```bash
# 1. Clone repository and enter project root
cd /path/to/Phantom

# 2. Configure environment file
cp backend/.env.example backend/.env

# 3. Build and launch database + backend API services
docker compose up --build -d

# 4. Inspect container health
docker compose ps
```

### Docker Compose Architecture (`docker-compose.yml`)

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4
    container_name: phantom_postgis
    environment:
      POSTGRES_DB: phantom
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./database/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d phantom"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: phantom_backend
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD:-postgres}@postgres:5432/phantom
      SECRET_KEY: ${SECRET_KEY:-phantom_super_secure_jwt_secret_key_gujarat_2026}
      AI_WORKER_API_KEY: ${AI_WORKER_API_KEY:-phantom_ai_worker_dev_key_2026}
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  pgdata:
```

---

## 3. Database Migration & Seeding Runbook

To manually initialize or reset the database with all 21 migrations and 9 demo seeds:

```bash
# Execute all SQL migrations and seed datasets
./run_db_migrations.sh
```

---

## 4. Healthcheck & Liveness Monitoring

PHANTOM implements Kubernetes-ready health probes:

| Endpoint | Method | Purpose | Typical Response |
|---|:---:|---|---|
| `/health/live` | `GET` | Container liveness check (process up) | `{"status": "alive", "timestamp": "..."}` (HTTP 200) |
| `/health/ready`| `GET` | Readiness probe (verifies database connectivity) | `{"status": "ready", "database": "connected"}` (HTTP 200) |
| `/api/v1/info` | `GET` | System version, features, and active config | `{"version": "1.0.0", "environment": "production"}` (HTTP 200) |

---

## 5. Security & Secret Management Best Practices

1. **JWT Secret Rotation**:
   - In production, ensure `SECRET_KEY` is set to a cryptographically random 256-bit string (`openssl rand -hex 32`).
2. **AI Worker Ingestion Key**:
   - `AI_WORKER_API_KEY` must be restricted to internal edge gateway containers.
3. **Database Network Isolation**:
   - The PostgreSQL container should not expose port 5432 to the public internet; bind strictly to private network bridges.
