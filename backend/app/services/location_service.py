from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ValidationError
from app.models.location import Location
from app.repositories.location import LocationRepository
from app.repositories.audit import AuditRepository
from app.schemas.location import LocationCreate, LocationUpdate, NearbyLocationResponse


class LocationService:
    def __init__(
        self,
        location_repo: Optional[LocationRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.location_repo = location_repo or LocationRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def get_location(self, session: AsyncSession, location_id: uuid.UUID) -> Location:
        location = await self.location_repo.get_by_id(session, location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} was not found.")
        return location

    async def list_locations(
        self,
        session: AsyncSession,
        district: Optional[str] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Location], int]:
        skip = (page - 1) * page_size
        return await self.location_repo.list_filtered(
            session, district=district, city=city, search=search, skip=skip, limit=page_size
        )

    async def find_nearby_locations(
        self,
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000.0,
        limit: int = 50,
    ) -> List[NearbyLocationResponse]:
        if not (-90.0 <= latitude <= 90.0):
            raise ValidationError(f"Invalid latitude: {latitude}. Must be between -90 and +90.")
        if not (-180.0 <= longitude <= 180.0):
            raise ValidationError(f"Invalid longitude: {longitude}. Must be between -180 and +180.")
        if radius_meters <= 0:
            raise ValidationError("Radius in meters must be greater than zero.")

        raw_results = await self.location_repo.find_nearby(
            session, latitude=latitude, longitude=longitude, radius_meters=radius_meters, limit=limit
        )
        return [NearbyLocationResponse(**row) for row in raw_results]

    async def create_location(
        self, session: AsyncSession, data: LocationCreate, actor_id: Optional[uuid.UUID] = None
    ) -> Location:
        loc = Location(
            name=data.name,
            state=data.state,
            district=data.district,
            taluka=data.taluka,
            city=data.city,
            zone=data.zone,
            ward=data.ward,
            address=data.address,
            landmark=data.landmark,
            postal_code=data.postal_code,
            latitude=data.latitude,
            longitude=data.longitude,
            metadata_=data.metadata,
        )
        created = await self.location_repo.create(session, loc)

        await self.audit_repo.log_action(
            session,
            action="CREATE_LOCATION",
            resource_type="LOCATION",
            resource_id=str(created.id),
            user_id=actor_id,
            details=f"Created location '{created.name}' in {created.city}, {created.district}",
        )
        return created

    async def update_location(
        self,
        session: AsyncSession,
        location_id: uuid.UUID,
        data: LocationUpdate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> Location:
        loc = await self.get_location(session, location_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "metadata" in update_dict:
            loc.metadata_ = update_dict.pop("metadata")

        for key, value in update_dict.items():
            setattr(loc, key, value)

        await session.flush()
        await session.refresh(loc)

        await self.audit_repo.log_action(
            session,
            action="UPDATE_LOCATION",
            resource_type="LOCATION",
            resource_id=str(loc.id),
            user_id=actor_id,
            details=f"Updated location '{loc.name}' ({loc.id})",
        )
        return loc

    async def delete_location(
        self, session: AsyncSession, location_id: uuid.UUID, actor_id: Optional[uuid.UUID] = None
    ) -> bool:
        loc = await self.get_location(session, location_id)
        if loc.cameras:
            raise ValidationError(
                f"Cannot delete location '{loc.name}' because it has {len(loc.cameras)} cameras installed."
            )

        success = await self.location_repo.delete(session, location_id)
        if success:
            await self.audit_repo.log_action(
                session,
                action="DELETE_LOCATION",
                resource_type="LOCATION",
                resource_id=str(location_id),
                user_id=actor_id,
                details=f"Deleted location '{loc.name}'",
            )
        return success
