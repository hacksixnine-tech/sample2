import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from app.core.config import settings


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class EvidenceStore:
    """Stores media outside PostgreSQL. DB keeps metadata + cryptographic hash only."""

    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or settings.EVIDENCE_LOCAL_ROOT)
        self.backend = settings.EVIDENCE_STORAGE_BACKEND

    def put(
        self,
        *,
        data: Optional[bytes],
        logical_name: str,
        camera_id: str,
        captured_at: datetime,
        file_format: str = "bin",
    ) -> Tuple[str, str, int, str]:
        """Returns (object_key, sha256, size_bytes, provider)."""
        payload = data if data is not None else logical_name.encode("utf-8")
        digest = sha256_bytes(payload)
        size = len(payload)
        stamp = captured_at.astimezone(timezone.utc).strftime("%Y/%m/%d")
        object_key = f"{stamp}/{camera_id}/{uuid4().hex}.{file_format}"

        if self.backend == "filesystem":
            dest = self.root / object_key
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
            return object_key, digest, size, "LOCAL_STORAGE"

        # S3-compatible path is a reference only until a client is configured.
        return object_key, digest, size, "S3_COMPATIBLE"


evidence_store = EvidenceStore()
