from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from app.models.location import Location
from app.repositories.base import BaseRepository


class LocationRepository(BaseRepository[Location]):
    def __init__(self):
        super().__init__(Location)

    async def get_by_name_and_city(
        self, session: AsyncSession, name: str, city: str
    ) -> Optional[Location]:
        stmt = select(Location).where(
            Location.name.ilike(name.strip()),
            Location.city.ilike(city.strip()),
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        district: Optional[str] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Location], int]:
        stmt = select(Location)

        if district:
            stmt = stmt.where(Location.district.ilike(district.strip()))

        if city:
            stmt = stmt.where(Location.city.ilike(city.strip()))

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Location.name.ilike(search_pattern),
                    Location.address.ilike(search_pattern),
                    Location.landmark.ilike(search_pattern),
                    Location.city.ilike(search_pattern),
                    Location.district.ilike(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        # Paginate
        stmt = stmt.order_by(Location.district.asc(), Location.city.asc(), Location.name.asc())
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_nearby(
        self,
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000.0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Execute native PostGIS ST_DWithin and ST_Distance query on WGS 84 (4326) geography.
        """
        sql = text("""
            SELECT 
                l.id as location_id,
                l.name,
                l.district,
                l.city,
                l.latitude::float as latitude,
                l.longitude::float as longitude,
                ROUND(ST_Distance(l.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 2)::float as distance_meters,
                COUNT(c.id)::int as camera_count
            FROM locations l
            LEFT JOIN cameras c ON l.id = c.location_id
            WHERE ST_DWithin(l.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
            GROUP BY l.id, l.name, l.district, l.city, l.latitude, l.longitude, l.geom
            ORDER BY distance_meters ASC
            LIMIT :limit;
        """)

        result = await session.execute(
            sql,
            {
                "lat": latitude,
                "lon": longitude,
                "radius": radius_meters,
                "limit": limit,
            },
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]
