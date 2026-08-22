import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing_and_verification():
    plain = "SuperSecurePassword2026!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = "30000000-0000-0000-0000-000000000001"
    token = create_access_token(
        subject=user_id,
        extra_claims={"role": "POLICE_OFFICER", "department": "GUJ-POLICE"}
    )
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == "POLICE_OFFICER"
    assert payload["department"] == "GUJ-POLICE"
    assert payload["type"] == "access"


def test_refresh_token_creation():
    user_id = "30000000-0000-0000-0000-000000000002"
    token = create_refresh_token(subject=user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_invalid_token_decode():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token("invalid.token.structure")
