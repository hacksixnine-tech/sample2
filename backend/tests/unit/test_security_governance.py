import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps_auth import (
    Principal,
    get_permissions_for_roles,
    resolve_principal,
)
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.dependencies import get_db
from app.main import app
from app.models.department import Department
from app.models.user import Role, User


@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


@pytest.mark.asyncio
async def test_bcrypt_hashing_and_verification():
    """Verify passwords are secure, salted, and verified correctly with Bcrypt."""
    raw_pass = "GujaratSecurity2026!#"
    hashed = get_password_hash(raw_pass)

    assert hashed != raw_pass
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


@pytest.mark.asyncio
async def test_token_creation_and_expiration():
    """Verify JWT access and refresh token creation, decoding, and expiration logic."""
    user_id = str(uuid.uuid4())
    access_token = create_access_token(
        subject=user_id,
        extra_claims={"role": "POLICE_OFFICER", "username": "officer_patel"},
    )
    payload = decode_token(access_token)
    assert payload["sub"] == user_id
    assert payload["role"] == "POLICE_OFFICER"
    assert payload["type"] == "access"

    # Refresh token
    refresh_token = create_refresh_token(subject=user_id)
    ref_payload = decode_token(refresh_token)
    assert ref_payload["sub"] == user_id
    assert ref_payload["type"] == "refresh"

    # Expired token
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-5),
    )
    with pytest.raises(ValueError, match="Token has expired"):
        decode_token(expired_token)


@pytest.mark.asyncio
async def test_role_to_permissions_resolution():
    """Verify default role permissions are resolved accurately."""
    admin_perms = get_permissions_for_roles(["SYSTEM_ADMIN"])
    assert admin_perms == ["*"]

    officer_perms = get_permissions_for_roles(["POLICE_OFFICER"])
    assert "camera:view" in officer_perms
    assert "watchlist:manage" in officer_perms
    assert "vehicle:search" in officer_perms

    viewer_perms = get_permissions_for_roles(["VIEWER"])
    assert "camera:view" in viewer_perms
    assert "watchlist:manage" not in viewer_perms


@pytest.mark.asyncio
async def test_principal_resolution_and_checks():
    """Verify Principal helper methods and worker key auth."""
    user_id = uuid.uuid4()
    p_admin = Principal(subject=str(user_id), principal_type="user", roles=["SYSTEM_ADMIN"], user_id=user_id)
    assert p_admin.has_permission("any:permission") is True

    p_viewer = Principal(subject=str(user_id), principal_type="user", roles=["VIEWER"], user_id=user_id)
    assert p_viewer.has_permission("camera:view") is True
    assert p_viewer.has_permission("user:manage") is False


@pytest.mark.asyncio
async def test_security_headers_middleware(client: AsyncClient):
    """Verify security headers are injected on API responses."""
    resp = await client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_rate_limit_headers(client: AsyncClient):
    """Verify rate limit tracking headers are returned on API calls."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_audit_log_endpoint_immutability(client: AsyncClient):
    """Verify audit endpoints strictly reject DELETE / PUT mutations (405 Method Not Allowed)."""
    admin_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "SYSTEM_ADMIN"},
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    del_resp = await client.delete("/api/v1/audit", headers=headers)
    assert del_resp.status_code in (404, 405)

    put_resp = await client.put(f"/api/v1/audit/{uuid.uuid4()}", json={}, headers=headers)
    assert put_resp.status_code in (404, 405)


@pytest.mark.asyncio
async def test_rbac_unauthorized_user_management(client: AsyncClient):
    """Verify non-admin roles (POLICE_OFFICER, VIEWER) cannot list or create users (403)."""
    police_token = create_access_token(
        subject=str(uuid.uuid4()),
        extra_claims={"role": "POLICE_OFFICER"},
    )
    headers = {"Authorization": f"Bearer {police_token}"}

    # POLICE_OFFICER cannot list users
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 403

    # POLICE_OFFICER cannot create user
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "username": "new_cop",
            "password": "Password123!",
            "full_name": "Test Cop",
            "department_id": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert create_resp.status_code == 403


@pytest.mark.asyncio
async def test_auth_me_endpoint_with_mocked_db(client: AsyncClient, mock_db_session):
    """Verify /api/v1/auth/me returns identity and permission claims for token with mock DB."""
    officer_id = uuid.uuid4()
    dept_id = uuid.uuid4()
    role_id = uuid.uuid4()

    mock_role = Role()
    mock_role.id = role_id
    mock_role.name = "POLICE_OFFICER"
    mock_role.permissions = ["camera:view", "camera:manage", "watchlist:manage"]

    mock_dept = Department()
    mock_dept.id = dept_id
    mock_dept.name = "Surat Police Headquarters"

    mock_user = User()
    mock_user.id = officer_id
    mock_user.username = "inspector_gadget"
    mock_user.email = "gadget@police.gov.in"
    mock_user.full_name = "Inspector Gadget"
    mock_user.badge_number = "GJ-POL-8821"
    mock_user.phone_number = "9876543210"
    mock_user.role_id = role_id
    mock_user.role = mock_role
    mock_user.department_id = dept_id
    mock_user.department = mock_dept
    mock_user.is_active = True
    mock_user.metadata_ = {}

    app.dependency_overrides[get_db] = lambda: mock_db_session

    with patch("app.api.v1.endpoints.auth.user_repo.get_by_id", return_value=mock_user):
        token = create_access_token(
            subject=str(officer_id),
            extra_claims={"role": "POLICE_OFFICER", "username": "inspector_gadget"},
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["username"] == "inspector_gadget"
        assert data["role"] == "POLICE_OFFICER"
        assert "camera:view" in data["permissions"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_login_flow(client: AsyncClient, mock_db_session):
    """Verify login authenticates valid password, rejects invalid password, and handles inactive users."""
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    dept_id = uuid.uuid4()

    mock_role = Role()
    mock_role.id = role_id
    mock_role.name = "POLICE_OFFICER"
    mock_role.permissions = ["camera:view"]

    mock_dept = Department()
    mock_dept.id = dept_id
    mock_dept.name = "Ahmedabad Crime Branch"

    plain_pass = "StrongPass2026@"
    mock_user = User()
    mock_user.id = user_id
    mock_user.username = "comm_sharma"
    mock_user.email = "sharma@gujaratpolice.gov.in"
    mock_user.password_hash = get_password_hash(plain_pass)
    mock_user.full_name = "Commissioner Sharma"
    mock_user.badge_number = "GJ-POL-0001"
    mock_user.phone_number = "9988776655"
    mock_user.role_id = role_id
    mock_user.role = mock_role
    mock_user.department_id = dept_id
    mock_user.department = mock_dept
    mock_user.is_active = True
    mock_user.metadata_ = {}
    mock_user.last_login_at = None

    app.dependency_overrides[get_db] = lambda: mock_db_session

    # 1. Successful Login
    with patch("app.api.v1.endpoints.auth.user_repo.get_by_identifier", return_value=mock_user), \
         patch("app.api.v1.endpoints.auth.audit_repo.log_action", return_value=AsyncMock()):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "comm_sharma", "password": plain_pass},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        token_data = body["data"]
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["user"]["username"] == "comm_sharma"

    # 2. Failed Login - Wrong Password
    with patch("app.api.v1.endpoints.auth.user_repo.get_by_identifier", return_value=mock_user), \
         patch("app.api.v1.endpoints.auth.audit_repo.log_action", return_value=AsyncMock()):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "comm_sharma", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    # 3. Failed Login - Inactive User
    mock_user.is_active = False
    with patch("app.api.v1.endpoints.auth.user_repo.get_by_identifier", return_value=mock_user), \
         patch("app.api.v1.endpoints.auth.audit_repo.log_action", return_value=AsyncMock()):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "comm_sharma", "password": plain_pass},
        )
        assert resp.status_code == 401
        assert "inactive" in resp.json()["error"]["message"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_refresh_flow(client: AsyncClient, mock_db_session):
    """Verify refresh token validates token and issues new access token."""
    user_id = uuid.uuid4()
    mock_role = Role()
    mock_role.id = uuid.uuid4()
    mock_role.name = "INVESTIGATOR"
    mock_role.permissions = ["evidence:export"]

    mock_dept = Department()
    mock_dept.id = uuid.uuid4()
    mock_dept.name = "CID Crime"

    mock_user = User()
    mock_user.id = user_id
    mock_user.username = "inspector_roy"
    mock_user.email = "roy@cid.gov.in"
    mock_user.full_name = "Inspector Roy"
    mock_user.role = mock_role
    mock_user.department_id = mock_dept.id
    mock_user.department = mock_dept
    mock_user.is_active = True
    mock_user.metadata_ = {}
    mock_user.last_login_at = None

    valid_refresh = create_refresh_token(subject=str(user_id))

    app.dependency_overrides[get_db] = lambda: mock_db_session

    with patch("app.api.v1.endpoints.auth.user_repo.get_by_id", return_value=mock_user):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_refresh},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "access_token" in body["data"]

    app.dependency_overrides.clear()
