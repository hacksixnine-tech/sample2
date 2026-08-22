from typing import Optional
from app.adapters.base_source_adapter import BaseSourceAdapter
from app.adapters.corp8_source_adapter import Corp8SourceAdapter


class SourceAdapterFactory:
    """Factory to return the appropriate adapter based on source system type or URL."""

    @staticmethod
    def get_adapter(source_type: str, base_url: Optional[str] = None) -> BaseSourceAdapter:
        if "corp8" in (base_url or "").lower() or source_type == "EXTERNAL_PROVIDED_CCTV_SOURCE":
            return Corp8SourceAdapter()
        # Default fallback
        return Corp8SourceAdapter()
