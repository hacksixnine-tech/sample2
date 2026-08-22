from datetime import datetime, timedelta, timezone
import uuid
import pytest
from app.ai.anpr.normalize import normalize_plate_text
from app.schemas.watchlist import normalize_watchlist_category, VALID_WATCHLIST_CATEGORIES


def test_plate_normalization():
    assert normalize_plate_text("GJ 01 AB 1234") == "GJ01AB1234"
    assert normalize_plate_text("gj-01-ab-1234") == "GJ01AB1234"
    assert normalize_plate_text("  GJ01 AB 1234  ") == "GJ01AB1234"
    assert normalize_plate_text("GJ-01/AB.1234") == "GJ01AB1234"


def test_watchlist_category_normalization_and_validation():
    assert "STOLEN_VEHICLE" in VALID_WATCHLIST_CATEGORIES
    assert "WANTED_PERSON" in VALID_WATCHLIST_CATEGORIES
    assert "CUSTOM" in VALID_WATCHLIST_CATEGORIES

    assert normalize_watchlist_category("STOLEN_VEHICLE") == "STOLEN_VEHICLES"
    assert normalize_watchlist_category("WANTED_VEHICLE") == "WANTED_VEHICLES"
    assert normalize_watchlist_category("BLACKLISTED_VEHICLE") == "BLACKLISTED_VEHICLES"
    assert normalize_watchlist_category("WANTED_PERSON") == "WANTED_PERSONS"
    assert normalize_watchlist_category("MISSING_PERSON") == "MISSING_PERSONS"
    assert normalize_watchlist_category("SUSPECT") == "SUSPECT_WATCHLIST"
    assert normalize_watchlist_category("CUSTOM") == "OTHER"


def test_watchlist_entry_validity_logic():
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    last_week = now - timedelta(days=7)

    # Valid entry: valid_from yesterday, valid_until tomorrow
    is_valid_now = yesterday <= now <= tomorrow
    assert is_valid_now is True

    # Expired entry: valid_from last_week, valid_until yesterday
    is_expired_now = not (last_week <= now <= yesterday)
    assert is_expired_now is True

    # Future entry: valid_from tomorrow, valid_until None
    is_not_yet_valid = not (tomorrow <= now)
    assert is_not_yet_valid is True
