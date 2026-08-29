from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
import numpy as np

from app.ai.reid.extractor import AppearanceEmbeddingExtractor, get_global_reid_extractor


@dataclass
class VisualSightingCandidate:
    sighting_id: str
    camera_id: str
    timestamp: datetime
    object_class: str
    embedding: np.ndarray
    similarity_score: float = 0.0
    crop_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReIDGallery:
    """In-memory & fast vector indexing for cross-camera visual search candidates."""

    def __init__(self, extractor: Optional[AppearanceEmbeddingExtractor] = None):
        self.extractor = extractor or get_global_reid_extractor()
        self._sightings: List[VisualSightingCandidate] = []

    def register_sighting(
        self,
        camera_id: str,
        timestamp: datetime,
        object_class: str,
        image_crop: Optional[np.ndarray] = None,
        embedding: Optional[np.ndarray] = None,
        sighting_id: Optional[str] = None,
        crop_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VisualSightingCandidate:
        """Stores a visual appearance embedding into the cross-camera gallery."""
        if embedding is None and image_crop is not None:
            embedding = self.extractor.extract(image_crop)
        elif embedding is None:
            embedding = np.zeros(self.extractor.embedding_dim, dtype=np.float32)

        s_id = sighting_id or str(uuid.uuid4())
        candidate = VisualSightingCandidate(
            sighting_id=s_id,
            camera_id=str(camera_id),
            timestamp=timestamp,
            object_class=object_class,
            embedding=embedding,
            crop_reference=crop_reference,
            metadata=metadata or {},
        )
        self._sightings.append(candidate)
        return candidate

    def search_candidates(
        self,
        query_crop: Optional[np.ndarray] = None,
        query_embedding: Optional[np.ndarray] = None,
        object_class: Optional[str] = None,
        exclude_camera_id: Optional[str] = None,
        min_similarity: float = 0.60,
        top_k: int = 10,
    ) -> List[VisualSightingCandidate]:
        """Finds visually similar candidates across other cameras ranked by cosine similarity."""
        if query_embedding is None and query_crop is not None:
            query_embedding = self.extractor.extract(query_crop)
        if query_embedding is None:
            return []

        scored_candidates: List[VisualSightingCandidate] = []
        for cand in self._sightings:
            if object_class and cand.object_class != object_class:
                continue
            if exclude_camera_id and cand.camera_id == str(exclude_camera_id):
                continue

            sim = self.extractor.compute_similarity(query_embedding, cand.embedding)
            if sim >= min_similarity:
                cand_copy = VisualSightingCandidate(
                    sighting_id=cand.sighting_id,
                    camera_id=cand.camera_id,
                    timestamp=cand.timestamp,
                    object_class=cand.object_class,
                    embedding=cand.embedding,
                    similarity_score=round(sim, 4),
                    crop_reference=cand.crop_reference,
                    metadata=cand.metadata,
                )
                scored_candidates.append(cand_copy)

        scored_candidates.sort(key=lambda c: c.similarity_score, reverse=True)
        return scored_candidates[:top_k]

    def total_count(self) -> int:
        return len(self._sightings)


_global_reid_gallery: Optional[ReIDGallery] = None


def get_global_reid_gallery() -> ReIDGallery:
    global _global_reid_gallery
    if _global_reid_gallery is None:
        _global_reid_gallery = ReIDGallery()
    return _global_reid_gallery
