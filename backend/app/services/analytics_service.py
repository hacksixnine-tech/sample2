from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anpr.normalize import normalize_plate_text
from app.ai.configuration import load_ai_config
from app.ai.evidence_store import evidence_store, sha256_text
from app.ai.metrics import metrics
from app.ai.postprocessing.classes import (
    event_type_for_class,
    phantom_class_to_detection_type,
    phantom_class_to_vehicle_type,
)
from app.ai.postprocessing.dedupe import temporary_observation_identity
from app.ai.postprocessing.validation import meets_ocr_threshold
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.analytics import (
    AIIngestEvent,
    Detection,
    Entity,
    Event,
    Evidence,
    Vehicle,
    VehicleObservation,
)
from app.models.camera import Camera
from app.repositories.analytics import (
    DetectionRepository,
    EntityRepository,
    EventRepository,
    EvidenceRepository,
    IngestEventRepository,
    ObservationRepository,
    VehicleRepository,
)
from app.repositories.audit import AuditRepository
from app.repositories.camera import CameraRepository
from app.services.alert_engine import AlertEngine
from app.services.watchlist_correlation import WatchlistCorrelationService
from app.schemas.analytics import (
    AIResultIngestRequest,
    AIResultIngestResponse,
    ANPRObservationCreate,
    DetectionCreate,
    EvidenceResponse,
    VehicleHistoryResponse,
    VehicleSearchHit,
    VehicleSighting,
)


class AnalyticsIngestionService:
    def __init__(self):
        self.detections = DetectionRepository()
        self.vehicles = VehicleRepository()
        self.observations = ObservationRepository()
        self.evidence = EvidenceRepository()
        self.events = EventRepository()
        self.entities = EntityRepository()
        self.ingest_events = IngestEventRepository()
        self.cameras = CameraRepository()
        self.audit = AuditRepository()
        self.watchlist_correlation = WatchlistCorrelationService()
        self.alert_engine = AlertEngine()

    async def _require_camera(self, session: AsyncSession, camera_id: uuid.UUID) -> Camera:
        camera = await self.cameras.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Unknown camera: {camera_id}")
        return camera

    async def ingest_ai_results(
        self,
        session: AsyncSession,
        payload: AIResultIngestRequest,
        actor_subject: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> AIResultIngestResponse:
        cfg = load_ai_config()
        camera = await self._require_camera(session, payload.camera_id)
        is_demo = bool(payload.is_demo or cfg.demo_mode)
        inference_event_id = payload.inference_event_id or str(uuid.uuid4())

        existing = await self.ingest_events.get_by_inference_id(session, inference_event_id)
        if existing:
            summary = existing.result_summary or {}
            return AIResultIngestResponse(
                inference_event_id=inference_event_id,
                idempotent_replay=True,
                is_demo=bool(existing.is_demo),
                detections_created=int(summary.get("detections_created", 0)),
                observations_created=int(summary.get("observations_created", 0)),
                observations_deduplicated=int(summary.get("observations_deduplicated", 0)),
                vehicles_created=int(summary.get("vehicles_created", 0)),
                events_created=int(summary.get("events_created", 0)),
                evidence_ids=[uuid.UUID(x) for x in summary.get("evidence_ids", [])],
                detection_ids=[uuid.UUID(x) for x in summary.get("detection_ids", [])],
                vehicle_ids=[uuid.UUID(x) for x in summary.get("vehicle_ids", [])],
            )

        now = datetime.now(timezone.utc)
        response = AIResultIngestResponse(inference_event_id=inference_event_id, is_demo=is_demo)
        vehicle_conf = _best_vehicle_confidence(payload.detections)

        evidence_row = await self._store_frame_evidence(
            session,
            camera=camera,
            captured_at=payload.timestamp,
            frame_reference=payload.frame_reference,
            is_demo=is_demo,
        )
        if evidence_row:
            response.evidence_ids.append(evidence_row.id)

        created_vehicle_ids = set()
        has_plate_item = any(i.type == "LICENSE_PLATE" and i.plate for i in payload.detections)

        for item in payload.detections:
            object_class = item.type
            plate_raw = item.plate.raw if item.plate else None
            plate_norm = item.plate.normalized if item.plate else None
            plate_conf = item.plate.confidence if item.plate else None
            anpr_claimed = False
            if object_class == "LICENSE_PLATE":
                metrics.incr("anpr_attempts")
                if plate_conf is not None and plate_norm:
                    if meets_ocr_threshold(plate_conf, cfg.ocr_threshold):
                        anpr_claimed = True
                        metrics.incr("anpr_success")
                    else:
                        metrics.incr("low_confidence_ocr")
                        plate_raw, plate_norm = plate_raw, plate_norm

            detection = Detection(
                camera_id=camera.id,
                detection_type=phantom_class_to_detection_type(object_class),
                object_class=object_class,
                detected_at=payload.timestamp,
                confidence=item.confidence,
                bounding_box=item.bbox if isinstance(item.bbox, dict) else item.bbox,
                detected_plate_number=plate_raw,
                normalized_plate_number=plate_norm,
                frame_reference=payload.frame_reference,
                crop_image_url=item.plate_crop_reference,
                model_name=payload.model.name,
                model_version=payload.model.version,
                metadata_={
                    **(item.metadata or {}),
                    "raw_preserved": True,
                    "origin": "DEMO_AI_MODE" if is_demo else "AI_WORKER",
                    "not_live_cctv": is_demo,
                    "plate_bbox": item.plate_bbox,
                },
                created_at=now,
                inference_event_id=inference_event_id,
                source_camera_id=payload.source_camera_id,
                source_system_id=payload.source_system_id,
                inference_time_ms=payload.inference_time_ms,
                device=payload.device or cfg.device,
                is_demo=is_demo,
                anpr_claimed=anpr_claimed,
                evidence_id=evidence_row.id if evidence_row else None,
            )
            session.add(detection)
            await session.flush()
            response.detection_ids.append(detection.id)
            response.detections_created += 1
            metrics.incr("detections")

            vehicle = None
            if anpr_claimed and plate_norm:
                vehicle, created = await self._get_or_create_vehicle(
                    session,
                    normalized_plate=plate_norm,
                    raw_plate=plate_raw or plate_norm,
                    object_class=object_class,
                    seen_at=payload.timestamp,
                    is_demo=is_demo,
                )
                detection.entity_id = vehicle.id
                if created:
                    response.vehicles_created += 1
                    created_vehicle_ids.add(vehicle.id)
                else:
                    created_vehicle_ids.add(vehicle.id)
                response.vehicle_ids.append(vehicle.id)

            event_type = event_type_for_class(object_class)
            await self._create_event(
                session,
                event_type=event_type,
                camera_id=camera.id,
                entity_id=vehicle.id if vehicle else None,
                detection_id=detection.id,
                occurred_at=payload.timestamp,
                description=_event_description(event_type, plate_norm, is_demo),
                is_demo=is_demo,
                worker=actor_subject,
            )
            response.events_created += 1

            if anpr_claimed and plate_norm:
                await self._create_event(
                    session,
                    event_type="ANPR_RECOGNIZED",
                    camera_id=camera.id,
                    entity_id=vehicle.id if vehicle else None,
                    detection_id=detection.id,
                    occurred_at=payload.timestamp,
                    description=_event_description("ANPR_RECOGNIZED", plate_norm, is_demo),
                    is_demo=is_demo,
                    worker=actor_subject,
                )
                response.events_created += 1

            should_observe = object_class in {
                "CAR",
                "TRUCK",
                "BUS",
                "MOTORCYCLE",
                "OTHER_VEHICLE",
                "LICENSE_PLATE",
            }
            if should_observe and not (has_plate_item and object_class != "LICENSE_PLATE"):
                dup = None
                if plate_norm:
                    dup = await self.observations.find_recent_duplicate(
                        session,
                        camera.id,
                        plate_norm,
                        payload.timestamp,
                        cfg.dedupe_window_seconds,
                    )
                if dup:
                    response.observations_deduplicated += 1
                else:
                    obs = VehicleObservation(
                        vehicle_id=vehicle.id if vehicle else None,
                        camera_id=camera.id,
                        location_id=camera.location_id,
                        detection_id=detection.id,
                        evidence_id=evidence_row.id if evidence_row else None,
                        observed_at=payload.timestamp,
                        raw_plate=plate_raw,
                        normalized_plate=plate_norm,
                        plate_confidence=plate_conf,
                        vehicle_confidence=vehicle_conf,
                        frame_reference=payload.frame_reference,
                        detection_reference=str(detection.id),
                        observation_identity=(
                            None
                            if vehicle
                            else temporary_observation_identity(camera.id, payload.timestamp)
                        ),
                        inference_event_id=inference_event_id,
                        is_demo=is_demo,
                        anpr_claimed=anpr_claimed,
                        metadata_={"origin": "DEMO_AI_MODE" if is_demo else "AI_WORKER"},
                        created_at=now,
                    )
                    session.add(obs)
                    response.observations_created += 1

            # -----------------------------------------------------------------
            # Step 6: Watchlist Correlation & Operational Alert Generation
            # -----------------------------------------------------------------
            if plate_norm:
                matches = await self.watchlist_correlation.correlate_observation(
                    session,
                    detection=detection,
                    raw_plate=plate_raw,
                    normalized_plate=plate_norm,
                    plate_confidence=plate_conf,
                    observation_timestamp=payload.timestamp,
                )
                for match_res in matches:
                    await self.alert_engine.process_match(
                        session,
                        match_result=match_res,
                        detection=detection,
                        entity=vehicle.entity if vehicle else None,
                        camera=camera,
                        plate=plate_norm,
                        confidence=plate_conf,
                        timestamp=payload.timestamp,
                    )


        ledger = AIIngestEvent(
            inference_event_id=inference_event_id,
            camera_id=camera.id,
            payload_hash=sha256_text(f"{inference_event_id}:{payload.timestamp.isoformat()}"),
            is_demo=is_demo,
            result_summary={
                "detections_created": response.detections_created,
                "observations_created": response.observations_created,
                "observations_deduplicated": response.observations_deduplicated,
                "vehicles_created": response.vehicles_created,
                "events_created": response.events_created,
                "evidence_ids": [str(x) for x in response.evidence_ids],
                "detection_ids": [str(x) for x in response.detection_ids],
                "vehicle_ids": [str(x) for x in response.vehicle_ids],
            },
            created_at=now,
        )
        session.add(ledger)

        await self.audit.log_action(
            session,
            action="OTHER",
            resource_type="AI_RESULT",
            resource_id=inference_event_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="AI result ingested",
            metadata={
                "custom_action": "INGEST_AI_RESULT",
                "is_demo": is_demo,
                "camera_id": str(camera.id),
                "actor": actor_subject,
            },
        )
        return response

    async def ingest_detection(
        self, session: AsyncSession, body: DetectionCreate, actor: str, **audit_kwargs
    ) -> Detection:
        from app.schemas.analytics import DetectionIngestItem, ModelInfo

        item = DetectionIngestItem(
            type=body.type,
            confidence=body.confidence,
            bbox=body.bbox,
            plate=body.plate,
            metadata=body.metadata,
        )
        payload = AIResultIngestRequest(
            camera_id=body.camera_id,
            timestamp=body.timestamp,
            model=ModelInfo(
                name=body.model_name or settings.AI_MODEL_NAME,
                version=body.model_version or settings.AI_MODEL_VERSION,
            ),
            detections=[item],
            frame_reference=body.frame_reference,
            source_camera_id=body.source_camera_id,
            inference_event_id=body.inference_event_id,
            is_demo=body.is_demo,
            metadata=body.metadata,
        )
        result = await self.ingest_ai_results(session, payload, actor, **audit_kwargs)
        det = await self.detections.get_by_id(session, result.detection_ids[0])
        if not det:
            raise ValidationError("detection ingest failed")
        return det

    async def ingest_anpr_observation(
        self, session: AsyncSession, body: ANPRObservationCreate, actor: str, **audit_kwargs
    ) -> VehicleObservation:
        from app.schemas.analytics import DetectionIngestItem, ModelInfo, PlatePayload

        bbox = body.bbox or [0, 0, 1, 1]
        payload = AIResultIngestRequest(
            camera_id=body.camera_id,
            timestamp=body.timestamp,
            model=ModelInfo(
                name=body.model_name or settings.AI_MODEL_NAME,
                version=body.model_version or settings.AI_MODEL_VERSION,
            ),
            detections=[
                DetectionIngestItem(
                    type="LICENSE_PLATE",
                    confidence=body.plate_confidence,
                    bbox=bbox,
                    plate=PlatePayload(
                        raw=body.raw_plate,
                        normalized=body.normalized_plate,
                        confidence=body.plate_confidence,
                    ),
                    metadata=body.metadata,
                )
            ],
            frame_reference=body.frame_reference,
            inference_event_id=body.inference_event_id,
            is_demo=body.is_demo,
        )
        result = await self.ingest_ai_results(session, payload, actor, **audit_kwargs)
        if result.idempotent_replay:
            rows, _ = await self.observations.list_filtered(
                session, plate=normalize_plate_text(body.raw_plate), camera_id=body.camera_id, limit=1
            )
            if rows:
                return rows[0]
        # Fetch latest observation for this inference event
        from sqlalchemy import select

        stmt = (
            select(VehicleObservation)
            .where(VehicleObservation.inference_event_id == result.inference_event_id)
            .order_by(VehicleObservation.created_at.desc())
        )
        obs = (await session.execute(stmt)).scalars().first()
        if not obs:
            if result.observations_deduplicated > 0 or result.observations_created == 0:
                rows, _ = await self.observations.list_filtered(
                    session, plate=normalize_plate_text(body.raw_plate), camera_id=body.camera_id, limit=1
                )
                if rows:
                    return rows[0]
            raise ValidationError("ANPR observation was not persisted (below OCR threshold or deduped)")
        return obs

    async def search_vehicles(
        self,
        session: AsyncSession,
        *,
        plate: Optional[str],
        camera_id: Optional[uuid.UUID],
        district: Optional[str],
        timestamp_from: Optional[datetime],
        timestamp_to: Optional[datetime],
        user_id: Optional[uuid.UUID],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> List[VehicleSearchHit]:
        norm = normalize_plate_text(plate) if plate else None
        observations, _ = await self.observations.list_filtered(
            session,
            plate=norm,
            camera_id=camera_id,
            district=district,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            skip=0,
            limit=200,
        )
        hits: Dict[uuid.UUID, VehicleSearchHit] = {}
        for obs in observations:
            if not obs.vehicle_id:
                continue
            vehicle = await self.vehicles.get_with_entity(session, obs.vehicle_id)
            if not vehicle or not vehicle.entity:
                continue
            hits[vehicle.id] = VehicleSearchHit(
                vehicle_id=vehicle.id,
                normalized_plate=vehicle.normalized_plate,
                raw_plate=vehicle.raw_plate,
                first_seen_at=vehicle.entity.first_seen_at,
                last_seen_at=vehicle.entity.last_seen_at,
                total_sightings=vehicle.entity.total_sightings,
                is_demo=bool((vehicle.metadata_ or {}).get("is_demo")),
                metadata=vehicle.metadata_ or {},
            )

        if norm and not hits:
            vehicle = await self.vehicles.get_by_plate(session, norm)
            if vehicle and vehicle.entity:
                hits[vehicle.id] = VehicleSearchHit(
                    vehicle_id=vehicle.id,
                    normalized_plate=vehicle.normalized_plate,
                    raw_plate=vehicle.raw_plate,
                    first_seen_at=vehicle.entity.first_seen_at,
                    last_seen_at=vehicle.entity.last_seen_at,
                    total_sightings=vehicle.entity.total_sightings,
                    is_demo=bool((vehicle.metadata_ or {}).get("is_demo")),
                    metadata=vehicle.metadata_ or {},
                )

        await self.audit.log_action(
            session,
            action="SEARCH_VEHICLE",
            resource_type="VEHICLE",
            resource_id=norm,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="Vehicle search",
            metadata={"plate": norm, "camera_id": str(camera_id) if camera_id else None, "district": district},
        )
        return list(hits.values())

    async def vehicle_history(
        self,
        session: AsyncSession,
        vehicle_id: uuid.UUID,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleHistoryResponse:
        vehicle = await self.vehicles.get_with_entity(session, vehicle_id)
        if not vehicle or not vehicle.entity:
            raise NotFoundError(f"Vehicle {vehicle_id} was not found")
        rows = await self.observations.history_for_vehicle(
            session, vehicle_id, timestamp_from, timestamp_to
        )
        sightings = []
        for obs in rows:
            district = None
            if obs.location:
                district = obs.location.district
            elif obs.camera and obs.camera.location:
                district = obs.camera.location.district
            evidence_ref = None
            if obs.evidence_id:
                ev = await self.evidence.get_by_id(session, obs.evidence_id)
                if ev:
                    evidence_ref = ev.public_reference or ev.evidence_code
            sightings.append(
                VehicleSighting(
                    camera_id=obs.camera_id,
                    district=district,
                    timestamp=obs.observed_at,
                    confidence=float(obs.plate_confidence) if obs.plate_confidence is not None else (
                        float(obs.vehicle_confidence) if obs.vehicle_confidence is not None else None
                    ),
                    evidence_reference=evidence_ref,
                    is_demo=obs.is_demo,
                    plate_confidence=float(obs.plate_confidence) if obs.plate_confidence is not None else None,
                    vehicle_confidence=float(obs.vehicle_confidence) if obs.vehicle_confidence is not None else None,
                    frame_reference=obs.frame_reference,
                )
            )
        await self.audit.log_action(
            session,
            action="VIEW_ENTITY",
            resource_type="VEHICLE",
            resource_id=str(vehicle_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="Vehicle history viewed",
        )
        return VehicleHistoryResponse(
            vehicle_id=vehicle.id,
            plate=vehicle.normalized_plate,
            first_seen=vehicle.entity.first_seen_at,
            last_seen=vehicle.entity.last_seen_at,
            sightings=sightings,
        )

    async def get_evidence(
        self,
        session: AsyncSession,
        evidence_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> EvidenceResponse:
        ev = await self.evidence.get_by_id(session, evidence_id)
        if not ev:
            raise NotFoundError(f"Evidence {evidence_id} was not found")
        await self.audit.log_action(
            session,
            action="VIEW_EVIDENCE",
            resource_type="EVIDENCE",
            resource_id=str(evidence_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="Evidence metadata viewed",
        )
        return to_evidence_response(ev)

    async def _get_or_create_vehicle(
        self,
        session: AsyncSession,
        *,
        normalized_plate: str,
        raw_plate: str,
        object_class: str,
        seen_at: datetime,
        is_demo: bool,
    ) -> Tuple[Vehicle, bool]:
        existing = await self.vehicles.get_by_plate(session, normalized_plate)
        if existing:
            if existing.entity:
                existing.entity.last_seen_at = max(existing.entity.last_seen_at, seen_at)
                existing.entity.total_sightings = int(existing.entity.total_sightings or 0) + 1
            return existing, False

        now = datetime.now(timezone.utc)
        try:
            async with session.begin_nested():
                entity = Entity(
                    entity_type="VEHICLE",
                    primary_identifier=normalized_plate,
                    first_seen_at=seen_at,
                    last_seen_at=seen_at,
                    total_sightings=1,
                    metadata_={"is_demo": is_demo, "origin": "DEMO_AI_MODE" if is_demo else "ANPR"},
                )
                session.add(entity)
                await session.flush()
                vehicle = Vehicle(
                    id=entity.id,
                    normalized_plate=normalized_plate,
                    raw_plate=raw_plate,
                    plate_state_code=normalized_plate[:2] if len(normalized_plate) >= 2 else "GJ",
                    vehicle_type=phantom_class_to_vehicle_type("CAR" if object_class == "LICENSE_PLATE" else object_class),
                    metadata_={"is_demo": is_demo},
                )
                session.add(vehicle)
                await session.flush()
                vehicle.entity = entity
                return vehicle, True
        except Exception:
            existing = await self.vehicles.get_by_plate(session, normalized_plate)
            if existing:
                if existing.entity:
                    existing.entity.last_seen_at = max(existing.entity.last_seen_at, seen_at)
                    existing.entity.total_sightings = int(existing.entity.total_sightings or 0) + 1
                return existing, False
            raise

    async def _store_frame_evidence(
        self,
        session: AsyncSession,
        *,
        camera: Camera,
        captured_at: datetime,
        frame_reference: Optional[str],
        is_demo: bool,
    ) -> Optional[Evidence]:
        logical = frame_reference or f"frame-ref:{camera.id}:{captured_at.isoformat()}"
        object_key, digest, size, provider = evidence_store.put(
            data=None,
            logical_name=logical,
            camera_id=str(camera.id),
            captured_at=captured_at,
            file_format="ref",
        )
        code = f"EVD-{uuid.uuid4().hex[:12].upper()}"
        public_ref = f"evd:{code}"
        row = Evidence(
            evidence_code=code,
            evidence_type="FRAME_SNAPSHOT",
            storage_provider=provider,
            bucket_name=settings.S3_BUCKET_NAME,
            object_key=object_key,
            file_format="ref",
            file_size_bytes=size,
            file_hash_sha256=digest,
            captured_at=captured_at,
            camera_id=camera.id,
            metadata_={"logical_reference": frame_reference, "is_demo": is_demo},
            created_at=datetime.now(timezone.utc),
            hash_algorithm="SHA-256",
            is_demo=is_demo,
            retention_days=settings.EVIDENCE_RETENTION_DAYS,
            public_reference=public_ref,
        )
        session.add(row)
        await session.flush()
        return row

    async def _create_event(
        self,
        session: AsyncSession,
        *,
        event_type: str,
        camera_id: uuid.UUID,
        entity_id: Optional[uuid.UUID],
        detection_id: uuid.UUID,
        occurred_at: datetime,
        description: str,
        is_demo: bool,
        worker: str,
    ) -> Event:
        ev = Event(
            event_type=event_type,
            camera_id=camera_id,
            entity_id=entity_id,
            detection_id=detection_id,
            occurred_at=occurred_at,
            severity="INFO",
            description=description,
            processed_by_worker=worker[:100],
            metadata_={"is_demo": is_demo},
            created_at=datetime.now(timezone.utc),
            is_demo=is_demo,
        )
        session.add(ev)
        await session.flush()
        return ev


def _best_vehicle_confidence(items) -> Optional[float]:
    scores = [
        i.confidence
        for i in items
        if i.type in {"CAR", "TRUCK", "BUS", "MOTORCYCLE", "OTHER_VEHICLE", "BICYCLE"}
    ]
    return max(scores) if scores else None


def _event_description(event_type: str, plate: Optional[str], is_demo: bool) -> str:
    prefix = "[DEMO] " if is_demo else ""
    if plate:
        return f"{prefix}{event_type} for plate {plate}"
    return f"{prefix}{event_type}"


def to_evidence_response(ev: Evidence) -> EvidenceResponse:
    return EvidenceResponse(
        evidence_id=ev.id,
        type=ev.evidence_type,
        storage_reference=ev.public_reference or ev.evidence_code,
        created_at=ev.created_at,
        hash=ev.file_hash_sha256,
        algorithm=ev.hash_algorithm or "SHA-256",
        camera_id=ev.camera_id,
        timestamp=ev.captured_at,
        is_demo=ev.is_demo,
        retention_days=ev.retention_days,
        file_format=ev.file_format,
        file_size_bytes=ev.file_size_bytes,
    )


def detection_to_response(det: Detection) -> Dict[str, Any]:
    from app.schemas.analytics import DetectionResponse

    return DetectionResponse.model_validate(det)
