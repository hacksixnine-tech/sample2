from app.core.exceptions import (
    PhantomException,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    PermissionDeniedError,
    ConflictError,
    DatabaseConnectionError,
)


def test_custom_exceptions_defaults():
    exc = NotFoundError("Camera not found", details={"camera_id": "CAM-01"})
    assert exc.status_code == 404
    assert exc.code == "NOT_FOUND"
    assert exc.message == "Camera not found"
    assert exc.details == {"camera_id": "CAM-01"}

    val_exc = ValidationError("Invalid plate format")
    assert val_exc.status_code == 422
    assert val_exc.code == "VALIDATION_ERROR"

    auth_exc = AuthenticationError()
    assert auth_exc.status_code == 401
    assert auth_exc.code == "AUTHENTICATION_FAILED"

    perm_exc = PermissionDeniedError()
    assert perm_exc.status_code == 403
    assert perm_exc.code == "PERMISSION_DENIED"

    conflict_exc = ConflictError()
    assert conflict_exc.status_code == 409
    assert conflict_exc.code == "CONFLICT"

    db_exc = DatabaseConnectionError()
    assert db_exc.status_code == 503
    assert db_exc.code == "DATABASE_UNAVAILABLE"
