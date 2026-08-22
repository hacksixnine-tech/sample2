from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.ai.anpr.normalize import normalize_plate_text
from app.core.exceptions import NotFoundError
from app.models.alert import Alert
from app.models.analytics import Detection, Entity, Evidence, Vehicle, VehicleObservation
from app.models.incident import Incident, IncidentAlert, IncidentEntity, IncidentEvidence
from app.models.match import Match
from app.repositories.alert import AlertRepository
from app.repositories.analytics import DetectionRepository, EvidenceRepository, ObservationRepository, VehicleRepository
from app.repositories.audit import AuditRepository
from app.repositories.incident import IncidentRepository
from app.repositories.match import MatchRepository
from app.schemas.investigation import (
    InvestigationSearchResult,
    InvestigationTimelineEvent,
    InvestigationTimelineResponse,
    VehicleInvestigationDossier,
)
from app.services.tracking_service import TrackingService


class InvestigationService:
    def __init__(self):
        self.vehicles = VehicleRepository()
        self.observations = ObservationRepository()
        self.detections = DetectionRepository()
        self.alerts = AlertRepository()
        self.incidents = IncidentRepository()
        self.matches = MatchRepository()
        self.evidence = EvidenceRepository()
        self.audit = AuditRepository()
        self.tracking = TrackingService()

    async def search(
        self,
        session: AsyncSession,
        *,
        plate: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        alert_code: Optional[str] = None,
        incident_code: Optional[str] = None,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        limit: int = 50,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> InvestigationSearchResult:
        norm_plate = normalize_plate_text(plate) if plate else None

        vehicles_found = []
        observations_found = []
        alerts_found = []
        incidents_found = []
        evidence_found = []

        # 1. Search Vehicles
        if norm_plate:
            veh = await self.vehicles.get_by_plate(session, norm_plate)
            if veh:
                vehicles_found.append({
                    "id": str(veh.id),
                    "normalized_plate": veh.normalized_plate,
                    "raw_plate": veh.raw_plate,
                    "vehicle_type": veh.vehicle_type,
                    "first_seen_at": veh.entity.first_seen_at.isoformat() if veh.entity else None,
                    "last_seen_at": veh.entity.last_seen_at.isoformat() if veh.entity else None,
                    "total_sightings": veh.entity.total_sightings if veh.entity else 1,
                })

        # 2. Search Observations
        obs_rows = await self.observations.search_observations(
            session,
            normalized_plate=norm_plate,
            camera_id=camera_id,
            district=district,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            skip=0,
            limit=limit,
        )
        for obs in obs_rows:
            observations_found.append({
                "id": str(obs.id),
                "vehicle_id": str(obs.vehicle_id) if obs.vehicle_id else None,
                "camera_id": str(obs.camera_id),
                "camera_name": obs.camera.name if obs.camera else None,
                "district": obs.location.district if obs.location else None,
                "normalized_plate": obs.normalized_plate,
                "raw_plate": obs.raw_plate,
                "observed_at": obs.observed_at.isoformat(),
                "plate_confidence": float(obs.plate_confidence) if obs.plate_confidence is not None else None,
            })

        # 3. Search Alerts
        alert_rows, _ = await self.alerts.list_filtered(
            session,
            camera_id=camera_id,
            limit=limit,
        )
        for alt in alert_rows:
            if norm_plate and norm_plate not in alt.title and norm_plate not in alt.message:
                continue
            if alert_code and alert_code.lower() not in alt.alert_code.lower():
                continue
            alerts_found.append({
                "id": str(alt.id),
                "alert_code": alt.alert_code,
                "alert_type": alt.alert_type,
                "severity": alt.severity,
                "title": alt.title,
                "message": alt.message,
                "status": alt.status,
                "camera_id": str(alt.camera_id),
                "created_at": alt.created_at.isoformat(),
            })

        # 4. Search Incidents
        incident_rows, _ = await self.incidents.list_filtered(
            session,
            search=incident_code or norm_plate,
            limit=limit,
        )
        for inc in incident_rows:
            incidents_found.append({
                "id": str(inc.id),
                "incident_code": inc.incident_code,
                "title": inc.title,
                "severity": inc.severity,
                "status": inc.status,
                "occurred_at": inc.occurred_at.isoformat(),
            })

        await self.audit.log_action(
            session,
            action="INVESTIGATION_SEARCH",
            resource_type="INVESTIGATION",
            resource_id=norm_plate,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Investigation search for plate: {norm_plate}, district: {district}",
            metadata={"plate": norm_plate, "camera_id": str(camera_id) if camera_id else None, "district": district},
        )

        return InvestigationSearchResult(
            query={
                "plate": plate,
                "normalized_plate": norm_plate,
                "camera_id": str(camera_id) if camera_id else None,
                "district": district,
                "alert_code": alert_code,
                "incident_code": incident_code,
            },
            total_vehicles=len(vehicles_found),
            total_observations=len(observations_found),
            total_alerts=len(alerts_found),
            total_incidents=len(incidents_found),
            vehicles=vehicles_found,
            observations=observations_found,
            alerts=alerts_found,
            incidents=incidents_found,
            evidence=evidence_found,
        )

    async def get_vehicle_dossier(
        self,
        session: AsyncSession,
        vehicle_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleInvestigationDossier:
        vehicle = await self.vehicles.get_with_entity(session, vehicle_id)
        if not vehicle or not vehicle.entity:
            raise NotFoundError(f"Vehicle {vehicle_id} not found")

        route_data = await self.tracking.get_vehicle_route(
            session, vehicle_id, user_id=user_id, ip_address=ip_address, user_agent=user_agent
        )

        # Observations
        obs_rows = await self.observations.history_for_vehicle(session, vehicle_id)
        obs_list = []
        districts_visited = set()
        cameras_visited = set()

        for o in obs_rows:
            dist = o.location.district if o.location else (o.camera.location.district if o.camera and o.camera.location else None)
            cam_name = o.camera.name if o.camera else str(o.camera_id)
            if dist:
                districts_visited.add(dist)
            if cam_name:
                cameras_visited.add(cam_name)

            obs_list.append({
                "observation_id": str(o.id),
                "camera_id": str(o.camera_id),
                "camera_name": cam_name,
                "district": dist,
                "observed_at": o.observed_at.isoformat(),
                "confidence": float(o.plate_confidence) if o.plate_confidence is not None else None,
                "evidence_id": str(o.evidence_id) if o.evidence_id else None,
            })

        # Alerts for this entity
        stmt_alerts = (
            select(Alert)
            .where(Alert.entity_id == vehicle.id)
            .options(selectinload(Alert.camera))
            .order_by(Alert.created_at.desc())
        )
        alerts_rows = (await session.execute(stmt_alerts)).scalars().all()
        alerts_list = [
            {
                "alert_id": str(a.id),
                "alert_code": a.alert_code,
                "title": a.title,
                "severity": a.severity,
                "status": a.status,
                "camera_name": a.camera.name if a.camera else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts_rows
        ]

        # Incidents referencing this entity
        stmt_incidents = (
            select(Incident)
            .join(IncidentEntity, Incident.id == IncidentEntity.incident_id)
            .where(IncidentEntity.entity_id == vehicle.id)
            .order_by(Incident.created_at.desc())
        )
        incidents_rows = (await session.execute(stmt_incidents)).scalars().all()
        incidents_list = [
            {
                "incident_id": str(i.id),
                "incident_code": i.incident_code,
                "title": i.title,
                "severity": i.severity,
                "status": i.status,
                "occurred_at": i.occurred_at.isoformat(),
            }
            for i in incidents_rows
        ]

        # Watchlist Matches
        matches_list = []
        for a in alerts_rows:
            if a.source_match_id:
                m = await self.matches.get_by_id(session, a.source_match_id)
                if m:
                    matches_list.append({
                        "match_id": str(m.id),
                        "matching_method": m.matching_method,
                        "match_score": float(m.match_score),
                        "status": m.status,
                        "matched_at": m.matched_at.isoformat(),
                    })

        await self.audit.log_action(
            session,
            action="VIEW_ENTITY",
            resource_type="VEHICLE_DOSSIER",
            resource_id=str(vehicle_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Viewed full investigation dossier for {vehicle.normalized_plate}",
        )

        return VehicleInvestigationDossier(
            identity=f"VEHICLE-{vehicle.normalized_plate}",
            vehicle_id=vehicle.id,
            plate=vehicle.normalized_plate,
            raw_plate=vehicle.raw_plate,
            vehicle_type=vehicle.vehicle_type,
            make=vehicle.make,
            model=vehicle.model,
            color=vehicle.color,
            owner_name=vehicle.owner_name,
            first_seen=vehicle.entity.first_seen_at,
            last_seen=vehicle.entity.last_seen_at,
            sighting_count=len(obs_list),
            camera_count=len(cameras_visited),
            district_count=len(districts_visited),
            districts_visited=sorted(list(districts_visited)),
            cameras_visited=sorted(list(cameras_visited)),
            observations=obs_list,
            alerts=alerts_list,
            watchlist_matches=matches_list,
            incidents=incidents_list,
            evidence=[],
            anomalies=route_data.anomalies_detected,
        )

    async def get_vehicle_timeline(
        self,
        session: AsyncSession,
        vehicle_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> InvestigationTimelineResponse:
        """
        Synthesizes a unified chronological forensic timeline combining:
        - Detections / ANPR
        - Observations
        - Watchlist Hits / Matches
        - Operational Alerts
        - Incident Dossier Associations
        """
        vehicle = await self.vehicles.get_with_entity(session, vehicle_id)
        if not vehicle or not vehicle.entity:
            raise NotFoundError(f"Vehicle {vehicle_id} not found")

        events: List[InvestigationTimelineEvent] = []

        # 1. Observations / ANPR
        obs_rows = await self.observations.history_for_vehicle(session, vehicle_id)
        for o in obs_rows:
            loc = o.location or (o.camera.location if o.camera else None)
            events.append(
                InvestigationTimelineEvent(
                    timestamp=o.observed_at,
                    event_type="OBSERVATION",
                    camera_id=o.camera_id,
                    camera_name=o.camera.name if o.camera else None,
                    location=loc.name if loc else None,
                    latitude=float(loc.latitude) if loc and loc.latitude is not None else None,
                    longitude=float(loc.longitude) if loc and loc.longitude is not None else None,
                    confidence=float(o.plate_confidence) if o.plate_confidence is not None else None,
                    reference_id=str(o.id),
                    title=f"Vehicle Sighting at {o.camera.name if o.camera else 'Camera'}",
                    description=f"Plate {o.normalized_plate} recognized with confidence {o.plate_confidence or 0:.2f}",
                    metadata={"frame_reference": o.frame_reference, "is_demo": o.is_demo},
                )
            )

        # 2. Alerts
        stmt_alerts = (
            select(Alert)
            .where(Alert.entity_id == vehicle.id)
            .options(selectinload(Alert.camera))
        )
        alert_rows = (await session.execute(stmt_alerts)).scalars().all()
        for a in alert_rows:
            cam_loc = a.camera.location if a.camera and a.camera.location else None
            events.append(
                InvestigationTimelineEvent(
                    timestamp=a.created_at,
                    event_type="ALERT",
                    camera_id=a.camera_id,
                    camera_name=a.camera.name if a.camera else None,
                    location=cam_loc.name if cam_loc else None,
                    latitude=float(cam_loc.latitude) if cam_loc and cam_loc.latitude is not None else None,
                    longitude=float(cam_loc.longitude) if cam_loc and cam_loc.longitude is not None else None,
                    reference_id=str(a.id),
                    severity=a.severity,
                    title=f"Alert: {a.title}",
                    description=a.message,
                    metadata={"alert_code": a.alert_code, "status": a.status},
                )
            )

        # 3. Incidents
        stmt_incidents = (
            select(Incident)
            .join(IncidentEntity, Incident.id == IncidentEntity.incident_id)
            .where(IncidentEntity.entity_id == vehicle.id)
        )
        incident_rows = (await session.execute(stmt_incidents)).scalars().all()
        for inc in incident_rows:
            events.append(
                InvestigationTimelineEvent(
                    timestamp=inc.occurred_at,
                    event_type="INCIDENT",
                    reference_id=str(inc.id),
                    severity=inc.severity,
                    title=f"Incident Dossier Linked: {inc.title}",
                    description=inc.description,
                    metadata={"incident_code": inc.incident_code, "status": inc.status},
                )
            )

        # Sort combined events chronologically
        events.sort(key=lambda e: e.timestamp)

        first_t = events[0].timestamp if events else None
        last_t = events[-1].timestamp if events else None

        await self.audit.log_action(
            session,
            action="VIEW_ENTITY",
            resource_type="INVESTIGATION_TIMELINE",
            resource_id=str(vehicle_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Generated unified investigation timeline for {vehicle.normalized_plate}",
        )

        return InvestigationTimelineResponse(
            vehicle_id=vehicle.id,
            normalized_plate=vehicle.normalized_plate,
            total_events=len(events),
            first_event_at=first_t,
            last_event_at=last_t,
            events=events,
        )
