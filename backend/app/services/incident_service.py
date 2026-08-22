from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import logger
from app.models.incident import Incident
from app.repositories.audit import AuditRepository
from app.repositories.department import DepartmentRepository
from app.repositories.incident import IncidentRepository
from app.repositories.user import UserRepository
from app.schemas.incident import (
    VALID_INCIDENT_STATES,
    VALID_INCIDENT_TRANSITIONS,
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    LinkedAlertResponse,
    LinkedEntityResponse,
    LinkedEventResponse,
    LinkedEvidenceResponse,
)


class IncidentService:
    def __init__(self):
        self.incidents = IncidentRepository()
        self.users = UserRepository()
        self.departments = DepartmentRepository()
        self.audit = AuditRepository()

    async def create_incident(
        self,
        session: AsyncSession,
        data: IncidentCreate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Incident:
        now = datetime.now(timezone.utc)
        code_suffix = uuid.uuid4().hex[:8].upper()
        incident_code = data.incident_code or f"INC-{now.strftime('%Y%m%d')}-{code_suffix}"

        valid_uid = None
        if user_id:
            u = await self.users.get_by_id(session, user_id)
            if u:
                valid_uid = u.id

        valid_assigned_uid = None
        if data.assigned_user_id:
            u = await self.users.get_by_id(session, data.assigned_user_id)
            if u:
                valid_assigned_uid = u.id

        valid_dept_id = None
        if data.assigned_department_id:
            d = await self.departments.get_by_id(session, data.assigned_department_id)
            if d:
                valid_dept_id = d.id

        incident = Incident(
            incident_code=incident_code,
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=data.status or "OPEN",
            assigned_department_id=valid_dept_id,
            assigned_user_id=valid_assigned_uid or valid_uid,
            occurred_at=data.occurred_at or now,
            metadata_=data.metadata,
        )
        session.add(incident)
        await session.flush()

        # Link initial relations if provided
        if data.alert_ids:
            for aid in data.alert_ids:
                await self.incidents.link_alert(session, incident.id, aid)
        if data.event_ids:
            for eid in data.event_ids:
                await self.incidents.link_event(session, incident.id, eid)
        if data.evidence_ids:
            for evid in data.evidence_ids:
                await self.incidents.link_evidence(session, incident.id, evid)
        if data.entity_ids:
            for entid in data.entity_ids:
                await self.incidents.link_entity(session, incident.id, entid, involvement_role="SUSPECT")

        await session.flush()
        await session.refresh(incident)

        await self.audit.log_action(
            session,
            action="CREATE_INCIDENT",
            resource_type="INCIDENT",
            resource_id=str(incident.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Created incident dossier {incident.incident_code}: {incident.title}",
        )
        return incident

    async def get_incident(self, session: AsyncSession, incident_id: uuid.UUID) -> Incident:
        inc = await self.incidents.get_with_relations(session, incident_id)
        if not inc:
            raise NotFoundError(f"Incident {incident_id} not found")
        return inc

    async def list_incidents(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        assigned_user_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Incident], int]:
        skip = (page - 1) * page_size
        return await self.incidents.list_filtered(
            session,
            status=status,
            severity=severity,
            department_id=department_id,
            assigned_user_id=assigned_user_id,
            search=search,
            skip=skip,
            limit=page_size,
        )

    async def update_incident(
        self,
        session: AsyncSession,
        incident_id: uuid.UUID,
        data: IncidentUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Incident:
        inc = await self.get_incident(session, incident_id)

        if data.status and data.status != inc.status:
            self._validate_transition(inc.status, data.status)
            inc.status = data.status
            if data.status in ("CLOSED", "ARCHIVED") and not inc.closed_at:
                inc.closed_at = datetime.now(timezone.utc)
                if data.closing_notes:
                    inc.closing_notes = data.closing_notes

        if data.title:
            inc.title = data.title
        if data.description:
            inc.description = data.description
        if data.severity:
            inc.severity = data.severity
        if data.assigned_department_id:
            inc.assigned_department_id = data.assigned_department_id
        if data.assigned_user_id:
            inc.assigned_user_id = data.assigned_user_id
        if data.closing_notes:
            inc.closing_notes = data.closing_notes
        if data.metadata:
            inc.metadata_ = {**inc.metadata_, **data.metadata}

        await session.flush()
        await session.refresh(inc)

        await self.audit.log_action(
            session,
            action="UPDATE_INCIDENT",
            resource_type="INCIDENT",
            resource_id=str(inc.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Updated incident {inc.incident_code}",
        )
        return inc

    async def link_alert(
        self,
        session: AsyncSession,
        incident_id: uuid.UUID,
        alert_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Incident:
        inc = await self.get_incident(session, incident_id)
        await self.incidents.link_alert(session, incident_id, alert_id, notes)
        return await self.get_incident(session, incident_id)

    async def link_event(
        self,
        session: AsyncSession,
        incident_id: uuid.UUID,
        event_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Incident:
        inc = await self.get_incident(session, incident_id)
        await self.incidents.link_event(session, incident_id, event_id, notes)
        return await self.get_incident(session, incident_id)

    async def link_entity(
        self,
        session: AsyncSession,
        incident_id: uuid.UUID,
        entity_id: uuid.UUID,
        involvement_role: str = "SUSPECT",
        notes: Optional[str] = None,
    ) -> Incident:
        inc = await self.get_incident(session, incident_id)
        await self.incidents.link_entity(session, incident_id, entity_id, involvement_role, notes)
        return await self.get_incident(session, incident_id)

    async def link_evidence(
        self,
        session: AsyncSession,
        incident_id: uuid.UUID,
        evidence_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Incident:
        inc = await self.get_incident(session, incident_id)
        await self.incidents.link_evidence(session, incident_id, evidence_id, notes)
        return await self.get_incident(session, incident_id)

    def _validate_transition(self, current: str, next_state: str) -> None:
        if current == next_state:
            return
        allowed = VALID_INCIDENT_TRANSITIONS.get(current, set())
        if next_state not in allowed:
            raise ValidationError(
                f"Invalid incident state transition from '{current}' to '{next_state}'. Allowed: {sorted(list(allowed))}"
            )
