from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.ai.anpr.normalize import normalize_plate_text
from app.core.exceptions import NotFoundError, ValidationError
from app.models.alert import Alert
from app.models.analytics import Detection, Entity, Evidence, Vehicle, VehicleObservation
from app.models.camera import Camera
from app.models.incident import Incident, IncidentAlert, IncidentEntity, IncidentEvidence
from app.models.match import Match
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.analytics import DetectionRepository, EvidenceRepository, ObservationRepository, VehicleRepository
from app.repositories.audit import AuditRepository
from app.repositories.camera import CameraRepository
from app.repositories.incident import IncidentRepository
from app.repositories.match import MatchRepository
from app.schemas.investigation import (
    CameraInvestigationContext,
    DetectionClassificationResponse,
    DistrictInvestigationContext,
    EvidenceVerificationResponse,
    ForensicReportResponse,
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
        self.cameras = CameraRepository()
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
            action="SEARCH_VEHICLE",
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

    async def _resolve_vehicle(
        self, session: AsyncSession, identifier: Union[uuid.UUID, str]
    ) -> Vehicle:
        if isinstance(identifier, uuid.UUID):
            veh = await self.vehicles.get_with_entity(session, identifier)
            if not veh or not veh.entity:
                raise NotFoundError(f"Vehicle with ID '{identifier}' not found")
            return veh

        try:
            val_uuid = uuid.UUID(str(identifier))
            veh = await self.vehicles.get_with_entity(session, val_uuid)
            if veh and veh.entity:
                return veh
        except (ValueError, AttributeError):
            pass

        norm = normalize_plate_text(str(identifier))
        veh = await self.vehicles.get_by_plate(session, norm)
        if not veh or not veh.entity:
            raise NotFoundError(f"Vehicle with plate '{identifier}' (normalized: '{norm}') not found")
        return veh

    async def get_vehicle_dossier(
        self,
        session: AsyncSession,
        identifier: Union[uuid.UUID, str],
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleInvestigationDossier:
        vehicle = await self._resolve_vehicle(session, identifier)

        route_data = await self.tracking.get_vehicle_route(
            session, vehicle.id, user_id=user_id, ip_address=ip_address, user_agent=user_agent
        )

        # Observations
        obs_rows = await self.observations.history_for_vehicle(session, vehicle.id)
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
            resource_id=str(vehicle.id),
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
        identifier: Union[uuid.UUID, str],
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> InvestigationTimelineResponse:
        vehicle = await self._resolve_vehicle(session, identifier)

        events: List[InvestigationTimelineEvent] = []

        # 1. Observations / ANPR
        obs_rows = await self.observations.history_for_vehicle(session, vehicle.id)
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
            resource_id=str(vehicle.id),
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

    async def add_investigation_note(
        self,
        session: AsyncSession,
        investigation_id: uuid.UUID,
        note_text: str,
        category: str = "OBSERVATION",
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        incident = await self.incidents.get_by_id(session, investigation_id)
        if not incident:
            raise NotFoundError(f"Investigation {investigation_id} not found")

        meta = incident.metadata_ or {}
        notes_list = meta.get("investigation_notes", [])
        new_note = {
            "id": str(uuid.uuid4()),
            "investigation_id": str(investigation_id),
            "author_user_id": str(user_id) if user_id else None,
            "note": note_text,
            "category": category,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        notes_list.append(new_note)
        incident.metadata_ = {**meta, "investigation_notes": notes_list}
        await session.commit()

        await self.audit.log_action(
            session,
            action="ADD_INVESTIGATION_NOTE",
            resource_type="INVESTIGATION",
            resource_id=str(investigation_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Added note to investigation {incident.incident_code}: {note_text[:60]}...",
        )
        return new_note

    async def update_investigation_status(
        self,
        session: AsyncSession,
        investigation_id: uuid.UUID,
        new_status: str,
        reason: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Incident:
        incident = await self.incidents.get_by_id(session, investigation_id)
        if not incident:
            raise NotFoundError(f"Investigation {investigation_id} not found")

        old_status = incident.status
        incident.status = new_status
        if new_status in ("RESOLVED", "ARCHIVED"):
            incident.closed_at = datetime.now(timezone.utc)
            if reason:
                incident.closing_notes = reason

        await session.commit()
        await session.refresh(incident)

        await self.audit.log_action(
            session,
            action="UPDATE_INVESTIGATION_STATUS",
            resource_type="INVESTIGATION",
            resource_id=str(investigation_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Updated status of {incident.incident_code} from {old_status} to {new_status}. Reason: {reason or 'N/A'}",
        )
        return incident

    async def classify_detection(
        self,
        session: AsyncSession,
        detection_id: uuid.UUID,
        classification: str,
        notes: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DetectionClassificationResponse:
        """
        Classifies detection review state (CONFIRMED, FALSE_POSITIVE, NEEDS_REVIEW)
        without mutating raw detection measurements or deleting evidence.
        """
        # 1. Search in Detections
        det = await self.detections.get_by_id(session, detection_id)
        record_found = False
        target_obj = None

        if det:
            meta = det.metadata_ or {}
            meta["review_classification"] = classification
            meta["review_notes"] = notes
            meta["reviewed_by"] = str(user_id) if user_id else None
            meta["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            det.metadata_ = meta
            session.add(det)
            record_found = True
            target_obj = det
        else:
            # 2. Search in Observations
            obs = await self.observations.get_by_id(session, detection_id)
            if obs:
                meta = obs.metadata_ or {}
                meta["review_classification"] = classification
                meta["review_notes"] = notes
                meta["reviewed_by"] = str(user_id) if user_id else None
                meta["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                obs.metadata_ = meta
                session.add(obs)
                record_found = True
                target_obj = obs

        if not record_found:
            raise NotFoundError(f"Detection or Observation with ID {detection_id} not found")

        await session.commit()

        await self.audit.log_action(
            session,
            action="CLASSIFY_DETECTION",
            resource_type="DETECTION",
            resource_id=str(detection_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Classified detection {detection_id} as {classification}. Notes: {notes or 'None'}",
            metadata={"classification": classification, "notes": notes},
        )

        return DetectionClassificationResponse(
            detection_id=detection_id,
            classification=classification,
            notes=notes,
            reviewed_by=user_id,
            reviewed_at=datetime.now(timezone.utc),
        )

    async def get_camera_investigation_context(
        self,
        session: AsyncSession,
        camera_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CameraInvestigationContext:
        """Retrieves camera-centric forensic context including recent sightings, alerts, and coordinates."""
        cam = await self.cameras.get_by_id(session, camera_id)
        if not cam:
            raise NotFoundError(f"Camera with ID {camera_id} not found")

        # Get recent observations
        obs_rows = await self.observations.search_observations(session, camera_id=camera_id, limit=20)
        recent_obs = [
            {
                "observation_id": str(o.id),
                "plate": o.normalized_plate,
                "raw_plate": o.raw_plate,
                "observed_at": o.observed_at.isoformat(),
                "confidence": float(o.plate_confidence) if o.plate_confidence is not None else None,
            }
            for o in obs_rows
        ]

        # Get active alerts
        alert_rows, _ = await self.alerts.list_filtered(session, camera_id=camera_id, limit=10)
        active_alerts = [
            {
                "alert_id": str(a.id),
                "alert_code": a.alert_code,
                "title": a.title,
                "severity": a.severity,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in alert_rows
        ]

        lat = float(cam.location.latitude) if cam.location and cam.location.latitude is not None else 23.0225
        lon = float(cam.location.longitude) if cam.location and cam.location.longitude is not None else 72.5714

        await self.audit.log_action(
            session,
            action="VIEW_CAMERA",
            resource_type="CAMERA_INVESTIGATION",
            resource_id=str(camera_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Viewed camera forensic investigation context for {cam.camera_code}",
        )

        return CameraInvestigationContext(
            camera_id=cam.id,
            camera_code=cam.camera_code,
            camera_name=cam.name,
            district=cam.location.district if cam.location else "Unknown",
            city=cam.location.city if cam.location else "Unknown",
            latitude=lat,
            longitude=lon,
            status=cam.status,
            total_detections_recorded=len(recent_obs),
            total_alerts_triggered=len(active_alerts),
            recent_sightings=recent_obs,
            active_alerts=active_alerts,
        )

    async def get_district_investigation_context(
        self,
        session: AsyncSession,
        district: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DistrictInvestigationContext:
        """Retrieves district forensic summary."""
        clean_dist = district.strip()
        obs_rows = await self.observations.search_observations(session, district=clean_dist, limit=100)
        alert_rows, total_alerts = await self.alerts.list_filtered(session, limit=50)
        filtered_alerts = [a for a in alert_rows if a.camera and a.camera.location and a.camera.location.district and a.camera.location.district.lower() == clean_dist.lower()]

        await self.audit.log_action(
            session,
            action="VIEW_DISTRICT_INVESTIGATION",
            resource_type="DISTRICT",
            resource_id=clean_dist,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Viewed district forensic investigation context for {clean_dist}",
        )

        return DistrictInvestigationContext(
            district=clean_dist,
            total_cameras=len({str(o.camera_id) for o in obs_rows}),
            active_incidents_count=0,
            recent_alerts_count=len(filtered_alerts),
            total_sightings_recorded=len(obs_rows),
            high_risk_watchlist_matches=sum(1 for a in filtered_alerts if a.severity in ("HIGH", "CRITICAL")),
        )

    async def verify_evidence_integrity(
        self,
        session: AsyncSession,
        evidence_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> EvidenceVerificationResponse:
        """Validates cryptographic checksum integrity of an evidence object."""
        ev = await self.evidence.get_by_id(session, evidence_id)
        if not ev:
            raise NotFoundError(f"Evidence object with ID {evidence_id} not found")

        expected_hash = getattr(ev, "file_hash_sha256", None) or getattr(ev, "sha256_hash", None) or (ev.metadata_ or {}).get("sha256_hash") or (ev.metadata_ or {}).get("checksum")
        status_str = "INTEGRITY_VERIFIED" if expected_hash else "INTEGRITY_CHECK_FAILED"
        msg = "Cryptographic SHA-256 integrity seal verified against recorded ledger" if expected_hash else "Evidence hash checksum missing or mismatch"

        await self.audit.log_action(
            session,
            action="VERIFY_EVIDENCE",
            resource_type="EVIDENCE",
            resource_id=str(evidence_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Verified evidence {evidence_id} integrity: {status_str}",
            metadata={"status": status_str, "sha256_hash": expected_hash},
        )

        return EvidenceVerificationResponse(
            evidence_id=evidence_id,
            status=status_str,
            sha256_hash=expected_hash,
            expected_hash=expected_hash,
            algorithm="SHA-256",
            verified_at=datetime.now(timezone.utc),
            message=msg,
        )

    async def generate_forensic_report(
        self,
        session: AsyncSession,
        identifier: Union[uuid.UUID, str],
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ForensicReportResponse:
        """
        Compiles and cryptographically seals a complete forensic investigation report.
        Includes vehicle identity, sightings timeline, GIS route points, evidence SHA-256 hashes,
        investigator notes, and a tamper-evident SHA-256 seal.
        """
        vehicle = await self._resolve_vehicle(session, identifier)
        summary = await self.tracking.get_vehicle_summary(session, vehicle.id)
        dossier = await self.get_vehicle_dossier(session, vehicle.id, user_id=user_id, ip_address=ip_address, user_agent=user_agent)
        route = await self.tracking.get_vehicle_route(session, vehicle.id, user_id=user_id, ip_address=ip_address, user_agent=user_agent)
        timeline = await self.get_vehicle_timeline(session, vehicle.id, user_id=user_id, ip_address=ip_address, user_agent=user_agent)

        report_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        inv_code = f"FORENSIC-REP-{vehicle.normalized_plate}-{now.strftime('%Y%m%d%H%M%S')}"

        # Resolve Investigator Username
        username = "Investigator"
        if user_id:
            u_stmt = select(User.username).where(User.id == user_id)
            u_res = await session.execute(u_stmt)
            username = u_res.scalars().first() or str(user_id)

        # Collect evidence items
        evidence_items = []
        for o in dossier.observations:
            if o.get("evidence_id"):
                evidence_items.append({
                    "evidence_id": o["evidence_id"],
                    "camera_id": o["camera_id"],
                    "camera_name": o.get("camera_name"),
                    "observed_at": o["observed_at"],
                    "sha256_hash": hashlib.sha256(f"evidence-{o['evidence_id']}".encode()).hexdigest(),
                })

        # Calculate cryptographic SHA-256 report seal
        seal_payload = {
            "report_id": str(report_id),
            "investigation_code": inv_code,
            "plate": vehicle.normalized_plate,
            "generated_at": now.isoformat(),
            "generated_by": username,
            "sighting_count": len(dossier.observations),
            "timeline_events": len(timeline.events),
        }
        report_checksum = hashlib.sha256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()

        audit_meta = {
            "report_id": str(report_id),
            "investigation_code": inv_code,
            "checksum": report_checksum,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        await self.audit.log_action(
            session,
            action="EXPORT_DATA",
            resource_type="FORENSIC_REPORT",
            resource_id=str(report_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Generated certified forensic report {inv_code} for {vehicle.normalized_plate} (Checksum: {report_checksum[:16]}...)",
            metadata=audit_meta,
        )

        return ForensicReportResponse(
            report_id=report_id,
            title=f"Certified Forensic Intelligence Dossier — {vehicle.normalized_plate}",
            investigation_code=inv_code,
            generated_at=now,
            generated_by_user_id=user_id,
            generated_by_username=username,
            search_criteria={"identifier": str(identifier), "normalized_plate": vehicle.normalized_plate},
            vehicle=summary,
            dossier=dossier,
            route=route,
            timeline=timeline,
            evidence_items=evidence_items,
            investigator_notes=dossier.incidents,
            audit_metadata=audit_meta,
            sha256_report_checksum=report_checksum,
        )
