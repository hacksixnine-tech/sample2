from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.models.location import Location
from app.repositories.base import BaseRepository


class DetectionRepository(BaseRepository[Detection]):
    def __init__(self):
        super().__init__(Detection)

    async def list_filtered(
        self,
        session: AsyncSession,
        *,
        camera_id: Optional[uuid.UUID] = None,
        detection_type: Optional[str] = None,
        confidence_min: Optional[float] = None,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        vehicle_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Detection], int]:
        filters = []
        if camera_id:
            filters.append(Detection.camera_id == camera_id)
        if detection_type:
            filters.append(Detection.detection_type == detection_type.upper())
        if confidence_min is not None:
            filters.append(Detection.confidence >= confidence_min)
        if timestamp_from:
            filters.append(Detection.detected_at >= timestamp_from)
        if timestamp_to:
            filters.append(Detection.detected_at <= timestamp_to)
        if vehicle_id:
            filters.append(Detection.entity_id == vehicle_id)

        stmt: Select = select(Detection)
        count_stmt = select(func.count()).select_from(Detection)
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        total = (await session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Detection.detected_at.desc()).offset(skip).limit(limit)
        rows = list((await session.execute(stmt)).scalars().all())
        return rows, total


class VehicleRepository(BaseRepository[Vehicle]):
    def __init__(self):
        super().__init__(Vehicle)

    async def get_by_plate(self, session: AsyncSession, normalized_plate: str) -> Optional[Vehicle]:
        result = await session.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.entity))
            .where(Vehicle.normalized_plate == normalized_plate)
        )
        return result.scalars().first()

    async def get_with_entity(self, session: AsyncSession, vehicle_id: uuid.UUID) -> Optional[Vehicle]:
        result = await session.execute(
            select(Vehicle).options(selectinload(Vehicle.entity)).where(Vehicle.id == vehicle_id)
        )
        return result.scalars().first()


class ObservationRepository(BaseRepository[VehicleObservation]):
    def __init__(self):
        super().__init__(VehicleObservation)

    async def find_recent_duplicate(
        self,
        session: AsyncSession,
        camera_id: uuid.UUID,
        normalized_plate: str,
        observed_at: datetime,
        window_seconds: float,
    ) -> Optional[VehicleObservation]:
        delta = timedelta(seconds=window_seconds)
        stmt = (
            select(VehicleObservation)
            .where(
                VehicleObservation.camera_id == camera_id,
                VehicleObservation.normalized_plate == normalized_plate,
                VehicleObservation.observed_at >= observed_at - delta,
                VehicleObservation.observed_at <= observed_at + delta,
            )
            .order_by(VehicleObservation.observed_at.desc())
            .limit(1)
        )
        return (await session.execute(stmt)).scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        *,
        plate: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        confidence_min: Optional[float] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[VehicleObservation], int]:
        stmt = (
            select(VehicleObservation)
            .options(
                selectinload(VehicleObservation.camera).selectinload(Camera.location),
                selectinload(VehicleObservation.location),
            )
        )
        count_stmt = select(func.count()).select_from(VehicleObservation)
        filters = []
        if plate:
            filters.append(VehicleObservation.normalized_plate == plate.upper())
        if camera_id:
            filters.append(VehicleObservation.camera_id == camera_id)
        if timestamp_from:
            filters.append(VehicleObservation.observed_at >= timestamp_from)
        if timestamp_to:
            filters.append(VehicleObservation.observed_at <= timestamp_to)
        if confidence_min is not None:
            filters.append(VehicleObservation.plate_confidence >= confidence_min)
        if district:
            stmt = stmt.join(Location, VehicleObservation.location_id == Location.id)
            count_stmt = count_stmt.join(Location, VehicleObservation.location_id == Location.id)
            filters.append(func.lower(Location.district) == district.lower())
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        total = (await session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(VehicleObservation.observed_at.desc()).offset(skip).limit(limit)
        rows = list((await session.execute(stmt)).scalars().all())
        return rows, total

    async def search_observations(
        self,
        session: AsyncSession,
        *,
        normalized_plate: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        confidence_min: Optional[float] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[VehicleObservation]:
        rows, _ = await self.list_filtered(
            session,
            plate=normalized_plate,
            camera_id=camera_id,
            district=district,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            confidence_min=confidence_min,
            skip=skip,
            limit=limit,
        )
        return rows

    async def history_for_vehicle(
        self,
        session: AsyncSession,
        vehicle_id: uuid.UUID,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
    ) -> List[VehicleObservation]:
        filters = [VehicleObservation.vehicle_id == vehicle_id]
        if timestamp_from:
            filters.append(VehicleObservation.observed_at >= timestamp_from)
        if timestamp_to:
            filters.append(VehicleObservation.observed_at <= timestamp_to)
        stmt = (
            select(VehicleObservation)
            .options(
                selectinload(VehicleObservation.camera).selectinload(Camera.location),
                selectinload(VehicleObservation.location),
            )
            .where(and_(*filters))
            .order_by(VehicleObservation.observed_at.asc())
        )
        return list((await session.execute(stmt)).scalars().all())


class EvidenceRepository(BaseRepository[Evidence]):
    def __init__(self):
        super().__init__(Evidence)


class EventRepository(BaseRepository[Event]):
    def __init__(self):
        super().__init__(Event)


class EntityRepository(BaseRepository[Entity]):
    def __init__(self):
        super().__init__(Entity)


class IngestEventRepository(BaseRepository[AIIngestEvent]):
    def __init__(self):
        super().__init__(AIIngestEvent)

    async def get_by_inference_id(
        self, session: AsyncSession, inference_event_id: str
    ) -> Optional[AIIngestEvent]:
        result = await session.execute(
            select(AIIngestEvent).where(AIIngestEvent.inference_event_id == inference_event_id)
        )
        return result.scalars().first()
