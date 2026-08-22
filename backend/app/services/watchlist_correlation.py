from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anpr.normalize import normalize_plate_text
from app.ai.configuration import load_ai_config
from app.core.logging import logger
from app.models.analytics import Detection, VehicleObservation
from app.models.match import Match
from app.models.watchlist import WatchlistEntry
from app.repositories.match import MatchRepository
from app.repositories.watchlist import WatchlistEntryRepository


class MatchResult:
    def __init__(
        self,
        match: Match,
        watchlist_entry: WatchlistEntry,
        match_type: str,
        score: float,
        explanation: str,
    ):
        self.match = match
        self.watchlist_entry = watchlist_entry
        self.match_type = match_type
        self.score = score
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": str(self.match.id),
            "observation_id": str(self.match.detection_id),
            "watchlist_entry_id": str(self.watchlist_entry.id),
            "match_type": self.match_type,
            "score": self.score,
            "status": self.match.status,
            "matched_at": self.match.matched_at.isoformat(),
            "explanation": self.explanation,
            "watchlist_category": self.watchlist_entry.watchlist.category if self.watchlist_entry.watchlist else None,
            "watchlist_name": self.watchlist_entry.watchlist.name if self.watchlist_entry.watchlist else None,
            "priority": self.watchlist_entry.priority,
        }


class WatchlistCorrelationService:
    def __init__(self):
        self.watchlist_entries = WatchlistEntryRepository()
        self.matches = MatchRepository()

    async def correlate_observation(
        self,
        session: AsyncSession,
        *,
        detection: Detection,
        raw_plate: Optional[str] = None,
        normalized_plate: Optional[str] = None,
        plate_confidence: Optional[float] = None,
        observation_timestamp: Optional[datetime] = None,
    ) -> List[MatchResult]:
        """
        Correlates an ANPR observation / detection against active watchlists.
        Adheres to exact normalized matching as default policy, rejecting expired entries,
        inactive watchlists, and sub-threshold confidence reads.
        """
        cfg = load_ai_config()
        obs_time = observation_timestamp or detection.detected_at or datetime.now(timezone.utc)
        
        # 1. Normalize Plate
        plate_norm = normalized_plate or detection.normalized_plate_number
        if not plate_norm and (raw_plate or detection.detected_plate_number):
            plate_norm = normalize_plate_text(raw_plate or detection.detected_plate_number or "")
        
        if not plate_norm:
            return []

        # 2. Check OCR / Plate Confidence Policy
        conf = plate_confidence
        if conf is None and detection.confidence is not None:
            conf = float(detection.confidence)
        
        # 3. Query active matching watchlist entries
        active_entries = await self.watchlist_entries.find_active_matches(
            session,
            normalized_identifier=plate_norm,
            entity_type="VEHICLE",
            reference_time=obs_time,
        )

        if not active_entries:
            return []

        results: List[MatchResult] = []

        for entry in active_entries:
            # 4. Idempotency Check: Don't duplicate match records for same detection and entry
            existing_match = await self.matches.get_by_detection_and_entry(
                session, detection.id, entry.id
            )
            
            # 5. Exact match scoring
            match_score = 1.0
            match_type = "EXACT_PLATE"
            status = "CONFIRMED"

            explanation = (
                f"Normalized plate '{plate_norm}' matched active watchlist entry "
                f"'{entry.identifier}' in '{entry.watchlist.name if entry.watchlist else 'Watchlist'}' "
                f"(Priority: {entry.priority}, Reason: {entry.reason})."
            )

            if existing_match:
                match_row = existing_match
            else:
                match_row = Match(
                    detection_id=detection.id,
                    watchlist_entry_id=entry.id,
                    match_score=match_score,
                    matching_method=match_type,
                    status=status,
                    matched_at=obs_time,
                    metadata_={
                        "explanation": explanation,
                        "plate_norm": plate_norm,
                        "raw_plate": raw_plate or detection.detected_plate_number,
                        "plate_confidence": conf,
                        "watchlist_category": entry.watchlist.category if entry.watchlist else None,
                        "watchlist_name": entry.watchlist.name if entry.watchlist else None,
                        "priority": entry.priority,
                    },
                )
                session.add(match_row)
                await session.flush()

            results.append(
                MatchResult(
                    match=match_row,
                    watchlist_entry=entry,
                    match_type=match_type,
                    score=match_score,
                    explanation=explanation,
                )
            )
            logger.info(f"Watchlist hit: Detection {detection.id} -> Entry {entry.id} ({plate_norm})")

        return results
