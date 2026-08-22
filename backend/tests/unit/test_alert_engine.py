import pytest
from app.services.alert_engine import AlertPolicyEngine, AlertEngine
from app.schemas.alert import VALID_STATE_TRANSITIONS
from app.core.exceptions import ValidationError


def test_severity_calculation_policy():
    # Critical watchlist priority + high score -> CRITICAL
    assert AlertPolicyEngine.calculate_severity("CRITICAL", 1.0, 0.95) == "CRITICAL"
    # High watchlist priority -> HIGH
    assert AlertPolicyEngine.calculate_severity("HIGH", 1.0, 0.90) == "HIGH"
    # Medium watchlist priority -> MEDIUM
    assert AlertPolicyEngine.calculate_severity("MEDIUM", 1.0, 0.85) == "MEDIUM"
    # Low watchlist priority -> LOW
    assert AlertPolicyEngine.calculate_severity("LOW", 1.0, 0.80) == "LOW"


def test_alert_state_machine_transitions():
    engine = AlertEngine()

    # Valid transitions
    engine._validate_transition("NEW", "ACKNOWLEDGED")
    engine._validate_transition("NEW", "INVESTIGATING")
    engine._validate_transition("NEW", "DISMISSED")
    engine._validate_transition("ACKNOWLEDGED", "INVESTIGATING")
    engine._validate_transition("ACKNOWLEDGED", "RESOLVED")
    engine._validate_transition("ACKNOWLEDGED", "DISMISSED")
    engine._validate_transition("INVESTIGATING", "RESOLVED")
    engine._validate_transition("INVESTIGATING", "DISMISSED")
    
    # Same state is a no-op
    engine._validate_transition("NEW", "NEW")
    engine._validate_transition("RESOLVED", "RESOLVED")

    # Invalid transitions
    with pytest.raises(ValidationError, match="Invalid alert state transition"):
        engine._validate_transition("DISMISSED", "RESOLVED")

    with pytest.raises(ValidationError, match="Invalid alert state transition"):
        engine._validate_transition("DISMISSED", "ACKNOWLEDGED")

    with pytest.raises(ValidationError, match="Invalid alert state transition"):
        engine._validate_transition("RESOLVED", "INVESTIGATING")

    with pytest.raises(ValidationError, match="Invalid alert state transition"):
        engine._validate_transition("RESOLVED", "DISMISSED")
