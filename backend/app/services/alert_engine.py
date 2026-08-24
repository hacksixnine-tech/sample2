from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import logger
from app.models.alert import Alert
from app.models.analytics import Detection, Entity
from app.models.camera import Camera
from app.models.match import Match
from app.models.watchlist import WatchlistEntry
from app.repositories.alert import AlertRepository
from app.repositories.audit import AuditRepository
from app.repositories.camera import CameraRepository
from app.repositories.user import UserRepository
from app.schemas.alert import (
    VALID_ALERT_STATES,
    VALID_SEVERITIES,
    VALID_STATE_TRANSITIONS,
    AlertCreate,
    AlertResponse,
    AlertUpdate,
)
from app.services.event_publisher import event_publisher
from app.services.notification import notification_service
from app.services.watchlist_correlation import MatchResult


class AlertPolicyEngine:
    """
    Evaluates matches and observations against configurable alerting policies.
    """

    @staticmethod
    def calculate_severity(
        watchlist_priority: str,
        match_score: float,
        detection_confidence: Optional[float] = None,
    ) -> str:
        prio = watchlist_priority.upper()
        if prio == "CRITICAL" and match_score >= 0.9:
            return "CRITICAL"
        if prio in ("CRITICAL", "HIGH"):
            return "HIGH"
        if prio == "MEDIUM":
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def build_alert_explanation(
        match_result: MatchResult,
        camera: Camera,
        plate: str,
        confidence: Optional[float],
        timestamp: datetime,
    ) -> Dict[str, Any]:
        entry = match_result.watchlist_entry
        wl_name = entry.watchlist.name if entry.watchlist else "Statewide Hotlist"
        return {
            "type": "WATCHLIST_MATCH",
            "match_type": match_result.match_type,
            "plate": plate,
            "confidence": confidence,
            "watchlist": wl_name,
            "watchlist_id": str(entry.watchlist_id),
            "watchlist_entry_id": str(entry.id),
            "case_reference": entry.case_reference_number,
            "fir_station": entry.fir_station,
            "camera": camera.name or camera.camera_code,
            "camera_id": str(camera.id),
            "district": camera.location.district if camera.location else None,
            "timestamp": timestamp.isoformat(),
            "explanation": match_result.explanation,
        }


class AlertEngine:
    def __init__(self, deduplication_cooldown_seconds: int = 300):
        self.alerts = AlertRepository()
        self.cameras = CameraRepository()
        self.users = UserRepository()
        self.audit = AuditRepository()
        self.deduplication_cooldown_seconds = deduplication_cooldown_seconds
        self.policy = AlertPolicyEngine()

    async def process_match(
        self,
        session: AsyncSession,
        *,
        match_result: MatchResult,
        detection: Detection,
        entity: Optional[Entity] = None,
        camera: Camera,
        plate: str,
        confidence: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Alert]:
        """
        Process a match result:
        1. Apply Alert Policy
        2. Deduplicate: Suppress if identical vehicle/camera/alert created within cooldown window
        3. Persist Alert
        4. Publish Real-time Event
        5. Trigger In-App Notification
        """
        now = timestamp or detection.detected_at or datetime.now(timezone.utc)
        cooldown_since = now - timedelta(seconds=self.deduplication_cooldown_seconds)

        # 1. Deduplication check
        entity_id = entity.id if entity else detection.entity_id
        duplicate = await self.alerts.find_recent_duplicate(
            session,
            camera_id=camera.id,
            entity_id=entity_id,
            alert_type="WATCHLIST_HIT",
            since_time=cooldown_since,
        )

        if duplicate:
            logger.info(
                f"[Alert Deduplication] Suppressed alert for entity {entity_id} at camera {camera.id} (within {self.deduplication_cooldown_seconds}s cooldown)"
            )
            return None

        # 2. Compute severity and structured explanation
        entry = match_result.watchlist_entry
        severity = self.policy.calculate_severity(
            entry.priority, match_result.score, confidence
        )
        explanation_dict = self.policy.build_alert_explanation(
            match_result, camera, plate, confidence, now
        )

        code_suffix = uuid.uuid4().hex[:8].upper()
        alert_code = f"ALT-{now.strftime('%Y%m%d')}-{code_suffix}"
        title = f"Watchlist Hit: {plate} [{entry.priority}]"
        message = (
            f"Vehicle with plate {plate} matched '{entry.watchlist.name if entry.watchlist else 'Watchlist'}' "
            f"at camera {camera.name or camera.camera_code} in {camera.location.district if camera.location else 'Gujarat'}."
        )

        # 3. Create persistent Alert record
        alert = Alert(
            alert_code=alert_code,
            alert_type="WATCHLIST_HIT",
            severity=severity,
            title=title,
            message=message,
            status="NEW",
            camera_id=camera.id,
            entity_id=entity_id,
            source_match_id=match_result.match.id,
            metadata_={
                "reason": explanation_dict,
                "plate": plate,
                "match_score": match_result.score,
                "watchlist_category": entry.watchlist.category if entry.watchlist else None,
                "case_reference": entry.case_reference_number,
            },
        )
        session.add(alert)
        await session.flush()
        await session.refresh(alert)

        # 4. Audit Log
        await self.audit.log_action(
            session,
            action="CREATE_ALERT",
            resource_type="ALERT",
            resource_id=str(alert.id),
            details=f"Generated {severity} alert {alert.alert_code} for plate {plate}",
            metadata={"alert_code": alert.alert_code, "severity": severity, "plate": plate},
        )

        # 5. Publish Real-Time Domain Event
        event_payload = {
            "alert_id": str(alert.id),
            "alert_code": alert.alert_code,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "camera_id": str(camera.id),
            "camera_name": camera.name,
            "district": camera.location.district if camera.location else None,
            "plate": plate,
            "created_at": (alert.created_at or now).isoformat(),
            "reason": explanation_dict,
        }
        await event_publisher.publish("AlertCreatedEvent", event_payload)

        # 6. In-App Notification
        await notification_service.notify(
            title=f"🚨 {alert.title}",
            message=alert.message,
            recipient="police_control_room",
            channels=["IN_APP"],
            payload=event_payload,
        )

        return alert

    async def create_alert(
        self,
        session: AsyncSession,
        data: AlertCreate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Alert:
        code_suffix = uuid.uuid4().hex[:8].upper()
        now = datetime.now(timezone.utc)
        alert_code = data.alert_code or f"ALT-{now.strftime('%Y%m%d')}-{code_suffix}"

        alert = Alert(
            alert_code=alert_code,
            alert_type=data.alert_type,
            severity=data.severity,
            title=data.title,
            message=data.message,
            status=data.status or "NEW",
            camera_id=data.camera_id,
            entity_id=data.entity_id,
            source_match_id=data.source_match_id,
            source_event_id=data.source_event_id,
            metadata_={
                **data.metadata,
                "reason": data.reason.model_dump() if data.reason else data.metadata.get("reason", {}),
            },
        )
        session.add(alert)
        await session.flush()
        await session.refresh(alert)

        await self.audit.log_action(
            session,
            action="CREATE_ALERT",
            resource_type="ALERT",
            resource_id=str(alert.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Manual/API alert {alert.alert_code} created",
        )

        await event_publisher.publish(
            "AlertCreatedEvent",
            {
                "alert_id": str(alert.id),
                "alert_code": alert.alert_code,
                "title": alert.title,
                "severity": alert.severity,
                "status": alert.status,
            },
        )
        return alert

    async def get_alert(self, session: AsyncSession, alert_id: uuid.UUID) -> Alert:
        alert = await self.alerts.get_by_id(session, alert_id)
        if not alert:
            raise NotFoundError(f"Alert {alert_id} not found")
        return alert

    async def list_alerts(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        entity_id: Optional[uuid.UUID] = None,
        alert_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Alert], int]:
        skip = (page - 1) * page_size
        return await self.alerts.list_filtered(
            session,
            status=status,
            severity=severity,
            camera_id=camera_id,
            entity_id=entity_id,
            alert_type=alert_type,
            skip=skip,
            limit=page_size,
        )

    async def update_alert(
        self,
        session: AsyncSession,
        alert_id: uuid.UUID,
        data: AlertUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Alert:
        alert = await self.get_alert(session, alert_id)

        if data.status and data.status != alert.status:
            self._validate_transition(alert.status, data.status)
            alert.status = data.status

        if data.severity:
            alert.severity = data.severity
        if data.title:
            alert.title = data.title
        if data.message:
            alert.message = data.message
        if data.metadata:
            alert.metadata_ = {**alert.metadata_, **data.metadata}

        await session.flush()
        await session.refresh(alert)
        return alert

    async def acknowledge_alert(
        self,
        session: AsyncSession,
        alert_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Alert:
        alert = await self.get_alert(session, alert_id)
        self._validate_transition(alert.status, "ACKNOWLEDGED")

        valid_uid = None
        if user_id:
            u = await self.users.get_by_id(session, user_id)
            if u:
                valid_uid = u.id

        now = datetime.now(timezone.utc)
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by_user_id = valid_uid
        alert.acknowledged_at = now
        if notes:
            alert.metadata_ = {**alert.metadata_, "ack_notes": notes}

        await session.flush()
        await session.refresh(alert)

        await self.audit.log_action(
            session,
            action="ACKNOWLEDGE_ALERT",
            resource_type="ALERT",
            resource_id=str(alert.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Alert {alert.alert_code} acknowledged by user {user_id}",
        )

        await event_publisher.publish(
            "ALERT_ACKNOWLEDGED",
            {
                "alert_id": str(alert.id),
                "alert_code": alert.alert_code,
                "status": "ACKNOWLEDGED",
                "acknowledged_at": now.isoformat(),
                "acknowledged_by": str(valid_uid) if valid_uid else None,
                "severity": alert.severity,
                "title": alert.title,
                "camera_id": str(alert.camera_id) if alert.camera_id else None,
            },
            camera_id=str(alert.camera_id) if alert.camera_id else None,
            severity=alert.severity,
            source="alert-engine",
        )
        return alert

    async def resolve_alert(
        self,
        session: AsyncSession,
        alert_id: uuid.UUID,
        resolution_notes: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Alert:
        alert = await self.get_alert(session, alert_id)
        self._validate_transition(alert.status, "RESOLVED")

        valid_uid = None
        if user_id:
            u = await self.users.get_by_id(session, user_id)
            if u:
                valid_uid = u.id

        now = datetime.now(timezone.utc)
        alert.status = "RESOLVED"
        alert.resolved_by_user_id = valid_uid
        alert.resolved_at = now
        alert.resolution_notes = resolution_notes

        await session.flush()
        await session.refresh(alert)

        await self.audit.log_action(
            session,
            action="RESOLVE_ALERT",
            resource_type="ALERT",
            resource_id=str(alert.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Alert {alert.alert_code} resolved: {resolution_notes}",
        )

        await event_publisher.publish(
            "ALERT_RESOLVED",
            {
                "alert_id": str(alert.id),
                "alert_code": alert.alert_code,
                "status": "RESOLVED",
                "resolved_at": now.isoformat(),
                "resolved_by": str(valid_uid) if valid_uid else None,
                "resolution_notes": resolution_notes,
                "severity": alert.severity,
                "title": alert.title,
                "camera_id": str(alert.camera_id) if alert.camera_id else None,
            },
            camera_id=str(alert.camera_id) if alert.camera_id else None,
            severity=alert.severity,
            source="alert-engine",
        )
        return alert

    async def dismiss_alert(
        self,
        session: AsyncSession,
        alert_id: uuid.UUID,
        dismissal_reason: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Alert:
        alert = await self.get_alert(session, alert_id)
        self._validate_transition(alert.status, "DISMISSED")

        alert.status = "DISMISSED"
        alert.resolution_notes = f"DISMISSED: {dismissal_reason}"

        await session.flush()
        await session.refresh(alert)

        await self.audit.log_action(
            session,
            action="RESOLVE_ALERT",
            resource_type="ALERT",
            resource_id=str(alert.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Alert {alert.alert_code} dismissed: {dismissal_reason}",
        )

        await event_publisher.publish(
            "ALERT_DISMISSED",
            {
                "alert_id": str(alert.id),
                "alert_code": alert.alert_code,
                "status": "DISMISSED",
                "dismissal_reason": dismissal_reason,
                "severity": alert.severity,
                "title": alert.title,
                "camera_id": str(alert.camera_id) if alert.camera_id else None,
            },
            camera_id=str(alert.camera_id) if alert.camera_id else None,
            severity=alert.severity,
            source="alert-engine",
        )
        return alert

    def _validate_transition(self, current_status: str, next_status: str) -> None:
        if current_status == next_status:
            return
        allowed = VALID_STATE_TRANSITIONS.get(current_status, set())
        if next_status not in allowed:
            raise ValidationError(
                f"Invalid alert state transition from '{current_status}' to '{next_status}'. "
                f"Allowed target states: {sorted(list(allowed)) or 'None (Terminal state)'}"
            )
