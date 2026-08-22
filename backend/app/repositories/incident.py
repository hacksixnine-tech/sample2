from datetime import datetime
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.models.incident import (
    Incident,
    IncidentAlert,
    IncidentEvent,
    IncidentEntity,
    IncidentEvidence,
)
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self):
        super().__init__(Incident)

    async def get_by_code(self, session: AsyncSession, incident_code: str) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .where(Incident.incident_code == incident_code.strip())
            .options(
                selectinload(Incident.assigned_department),
                selectinload(Incident.assigned_user),
                selectinload(Incident.alerts).selectinload(IncidentAlert.alert),
                selectinload(Incident.events).selectinload(IncidentEvent.event),
                selectinload(Incident.entities).selectinload(IncidentEntity.entity),
                selectinload(Incident.evidence_links).selectinload(IncidentEvidence.evidence),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_with_relations(self, session: AsyncSession, id: uuid.UUID) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .where(Incident.id == id)
            .options(
                selectinload(Incident.assigned_department),
                selectinload(Incident.assigned_user),
                selectinload(Incident.alerts).selectinload(IncidentAlert.alert),
                selectinload(Incident.events).selectinload(IncidentEvent.event),
                selectinload(Incident.entities).selectinload(IncidentEntity.entity),
                selectinload(Incident.evidence_links).selectinload(IncidentEvidence.evidence),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        assigned_user_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Incident], int]:
        stmt = select(Incident)

        if status:
            stmt = stmt.where(Incident.status == status.upper().strip())
        if severity:
            stmt = stmt.where(Incident.severity == severity.upper().strip())
        if department_id:
            stmt = stmt.where(Incident.assigned_department_id == department_id)
        if assigned_user_id:
            stmt = stmt.where(Incident.assigned_user_id == assigned_user_id)
        if search:
            pat = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Incident.title.ilike(pat),
                    Incident.incident_code.ilike(pat),
                    Incident.description.ilike(pat),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(
                selectinload(Incident.assigned_department),
                selectinload(Incident.assigned_user),
            )
            .order_by(Incident.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    async def link_alert(
        self, session: AsyncSession, incident_id: uuid.UUID, alert_id: uuid.UUID, notes: Optional[str] = None
    ) -> IncidentAlert:
        stmt = select(IncidentAlert).where(
            IncidentAlert.incident_id == incident_id, IncidentAlert.alert_id == alert_id
        )
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            if notes:
                existing.notes = notes
            return existing

        link = IncidentAlert(incident_id=incident_id, alert_id=alert_id, notes=notes)
        session.add(link)
        await session.flush()
        return link

    async def link_event(
        self, session: AsyncSession, incident_id: uuid.UUID, event_id: uuid.UUID, notes: Optional[str] = None
    ) -> IncidentEvent:
        stmt = select(IncidentEvent).where(
            IncidentEvent.incident_id == incident_id, IncidentEvent.event_id == event_id
        )
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            if notes:
                existing.notes = notes
            return existing

        link = IncidentEvent(incident_id=incident_id, event_id=event_id, notes=notes)
        session.add(link)
        await session.flush()
        return link

    async def link_entity(
        self,
        session: AsyncSession,
        incident_id: uuid.UUID,
        entity_id: uuid.UUID,
        involvement_role: str = "SUSPECT",
        notes: Optional[str] = None,
    ) -> IncidentEntity:
        stmt = select(IncidentEntity).where(
            IncidentEntity.incident_id == incident_id,
            IncidentEntity.entity_id == entity_id,
            IncidentEntity.involvement_role == involvement_role,
        )
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            if notes:
                existing.notes = notes
            return existing

        link = IncidentEntity(
            incident_id=incident_id,
            entity_id=entity_id,
            involvement_role=involvement_role,
            notes=notes,
        )
        session.add(link)
        await session.flush()
        return link

    async def link_evidence(
        self, session: AsyncSession, incident_id: uuid.UUID, evidence_id: uuid.UUID, notes: Optional[str] = None
    ) -> IncidentEvidence:
        stmt = select(IncidentEvidence).where(
            IncidentEvidence.incident_id == incident_id, IncidentEvidence.evidence_id == evidence_id
        )
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            if notes:
                existing.notes = notes
            return existing

        link = IncidentEvidence(incident_id=incident_id, evidence_id=evidence_id, notes=notes)
        session.add(link)
        await session.flush()
        return link
