import pytest
from app.core.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.APP_NAME == "PHANTOM Video Intelligence Platform"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.POSTGRES_DB == "phantom"
    assert settings.POSTGRES_PORT == 5432
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert isinstance(settings.CORS_ORIGINS, list)
    assert isinstance(settings.ALLOWED_HOSTS, list)


def test_settings_cors_parsing():
    settings = Settings(CORS_ORIGINS="http://test.com, http://example.com")
    assert "http://test.com" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS


def test_settings_environment_flags():
    dev_settings = Settings(APP_ENV="development")
    assert dev_settings.is_development is True
    assert dev_settings.is_production is False

    prod_settings = Settings(APP_ENV="production")
    assert prod_settings.is_production is True
    assert prod_settings.is_development is False
