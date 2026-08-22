from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.schemas.source_system import SourceDiscoveryCamera


class BaseSourceAdapter(ABC):
    """Abstract interface for external CCTV control room source adapters."""

    @abstractmethod
    async def probe(self, base_url: str, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check live reachability and probe telemetry of external source."""
        pass

    @abstractmethod
    async def discover_cameras(
        self, base_url: str, auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Discover live cameras and stream metadata from external source."""
        pass
