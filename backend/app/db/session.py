from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import logger

# Initialize Async Engine with robust connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Automatic connection liveness validation
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def check_db_connection() -> dict:
    """
    Execute a real database query to verify connection health and return version/status.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version(), postgis_full_version();"))
            row = result.fetchone()
            if row:
                return {
                    "connected": True,
                    "postgres_version": row[0].split(",")[0] if row[0] else "PostgreSQL 16",
                    "postgis_version": row[1].split()[0] if row[1] else "PostGIS 3.4",
                }
            return {"connected": True}
    except Exception as e:
        logger.error(f"Database healthcheck ping failed: {str(e)}")
        return {"connected": False, "error": str(e)}


async def close_db_connection() -> None:
    """Cleanly dispose of all pooled database connections."""
    logger.info("Closing database connection pool...")
    await engine.dispose()
    logger.info("Database connection pool closed.")
