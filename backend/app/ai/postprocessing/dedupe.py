from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid


def should_dedupe(
    *,
    existing_camera_id: uuid.UUID,
    existing_plate: Optional[str],
    existing_at: datetime,
    camera_id: uuid.UUID,
    normalized_plate: Optional[str],
    observed_at: datetime,
    window_seconds: float,
) -> bool:
    """Same camera + same normalized plate within the configured window is a duplicate burst.

    Different cameras are never merged. Missing plates are not deduped by plate identity.
    """
    if window_seconds <= 0:
        return False
    if existing_camera_id != camera_id:
        return False
    if not existing_plate or not normalized_plate:
        return False
    if existing_plate != normalized_plate:
        return False
    left = existing_at if existing_at.tzinfo else existing_at.replace(tzinfo=timezone.utc)
    right = observed_at if observed_at.tzinfo else observed_at.replace(tzinfo=timezone.utc)
    delta = abs(right - left)
    return delta <= timedelta(seconds=window_seconds)


def temporary_observation_identity(camera_id: uuid.UUID, observed_at: datetime) -> str:
    """Identity for plate-unknown sightings. Not a permanent vehicle entity."""
    ts = observed_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"tmp:{camera_id}:{ts}"
