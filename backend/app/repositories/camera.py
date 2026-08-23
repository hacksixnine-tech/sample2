from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import selectinload
from app.models.camera import Camera
from app.models.department import Department
from app.models.location import Location
from app.models.stream import CameraStream
from app.models.health import CameraHealth
from app.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    def __init__(self):
        super().__init__(Camera)

    async def get_by_code(self, session: AsyncSession, camera_code: str) -> Optional[Camera]:
        stmt = (
            select(Camera)
            .where(Camera.camera_code == camera_code.strip().upper())
            .options(
                selectinload(Camera.department),
                selectinload(Camera.location),
                selectinload(Camera.streams),
                selectinload(Camera.health_logs),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_id_with_relations(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> Optional[Camera]:
        stmt = (
            select(Camera)
            .where(Camera.id == camera_id)
            .options(
                selectinload(Camera.department),
                selectinload(Camera.location),
                selectinload(Camera.streams),
                selectinload(Camera.health_logs),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        camera_type: Optional[str] = None,
        status: Optional[str] = None,
        connectivity_status: Optional[str] = None,
        manufacturer: Optional[str] = None,
        ownership: Optional[str] = None,
        search: Optional[str] = None,
        location_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Camera], int]:
        stmt = (
            select(Camera)
            .join(Camera.location)
            .join(Camera.department)
            .options(
                selectinload(Camera.department),
                selectinload(Camera.location),
                selectinload(Camera.streams),
            )
        )

        if department_id:
            stmt = stmt.where(Camera.department_id == department_id)

        if location_id:
            stmt = stmt.where(Camera.location_id == location_id)

        if district:
            stmt = stmt.where(Location.district.ilike(district.strip()))

        if city:
            stmt = stmt.where(Location.city.ilike(city.strip()))

        if camera_type:
            stmt = stmt.where(Camera.camera_type == camera_type.strip().upper())

        if status:
            stmt = stmt.where(Camera.status == status.strip().upper())

        if connectivity_status:
            stmt = stmt.where(Camera.connectivity_status == connectivity_status.strip().upper())

        if manufacturer:
            stmt = stmt.where(Camera.manufacturer.ilike(f"%{manufacturer.strip()}%"))

        if ownership:
            stmt = stmt.where(Camera.ownership.ilike(f"%{ownership.strip()}%"))

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Camera.camera_code.ilike(search_pattern),
                    Camera.name.ilike(search_pattern),
                    Location.name.ilike(search_pattern),
                    Location.city.ilike(search_pattern),
                    Location.district.ilike(search_pattern),
                    Department.name.ilike(search_pattern),
                    Department.code.ilike(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(
            stmt.with_only_columns(Camera.id).order_by(None).subquery()
        )
        total = (await session.execute(count_stmt)).scalar_one()

        # Paginate
        stmt = stmt.order_by(Camera.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_nearby_cameras(
        self,
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000.0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        PostGIS native spatial query retrieving all cameras within geodesic radius in meters.
        """
        sql = text("""
            SELECT 
                c.id as camera_id,
                c.camera_code,
                c.name,
                c.camera_type,
                c.status,
                c.connectivity_status,
                l.id as location_id,
                l.name as location_name,
                l.district,
                l.city,
                l.latitude::float as latitude,
                l.longitude::float as longitude,
                ROUND(ST_Distance(l.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 2)::float as distance_meters,
                (
                    SELECT cs.protocol 
                    FROM camera_streams cs 
                    WHERE cs.camera_id = c.id AND cs.is_primary = TRUE 
                    LIMIT 1
                ) as primary_stream_protocol
            FROM cameras c
            JOIN locations l ON c.location_id = l.id
            WHERE ST_DWithin(l.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
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
        return [dict(row) for row in result.mappings().all()]

    async def get_coverage_metrics(self, session: AsyncSession) -> Dict[str, Any]:
        """Compile statewide camera distribution statistics."""
        total_stmt = select(func.count(Camera.id))
        total = (await session.execute(total_stmt)).scalar_one()

        dept_stmt = (
            select(Department.name, func.count(Camera.id))
            .join(Camera, Camera.department_id == Department.id)
            .group_by(Department.name)
            .order_by(func.count(Camera.id).desc())
        )
        by_dept = {row[0]: row[1] for row in (await session.execute(dept_stmt)).all()}

        dist_stmt = (
            select(Location.district, func.count(Camera.id))
            .join(Camera, Camera.location_id == Location.id)
            .group_by(Location.district)
            .order_by(func.count(Camera.id).desc())
        )
        by_dist = {row[0]: row[1] for row in (await session.execute(dist_stmt)).all()}

        status_stmt = select(Camera.status, func.count(Camera.id)).group_by(Camera.status)
        by_status = {row[0]: row[1] for row in (await session.execute(status_stmt)).all()}

        type_stmt = select(Camera.camera_type, func.count(Camera.id)).group_by(Camera.camera_type)
        by_type = {row[0]: row[1] for row in (await session.execute(type_stmt)).all()}

        online_count_stmt = select(func.count(Camera.id)).where(Camera.connectivity_status == "ONLINE")
        online_count = (await session.execute(online_count_stmt)).scalar_one()
        online_pct = round((online_count / total * 100.0), 2) if total > 0 else 0.0

        return {
            "total_cameras": total,
            "cameras_by_department": by_dept,
            "cameras_by_district": by_dist,
            "cameras_by_status": by_status,
            "cameras_by_type": by_type,
            "online_percentage": online_pct,
        }

    async def get_department_camera_summary(
        self, session: AsyncSession, department_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Detailed breakdown of cameras belonging to a single department."""
        dept = await session.get(Department, department_id)
        if not dept:
            return None

        total_stmt = select(func.count(Camera.id)).where(Camera.department_id == department_id)
        total = (await session.execute(total_stmt)).scalar_one()

        online_stmt = select(func.count(Camera.id)).where(
            Camera.department_id == department_id, Camera.connectivity_status == "ONLINE"
        )
        online = (await session.execute(online_stmt)).scalar_one()

        offline_stmt = select(func.count(Camera.id)).where(
            Camera.department_id == department_id, Camera.connectivity_status == "OFFLINE"
        )
        offline = (await session.execute(offline_stmt)).scalar_one()

        degraded_stmt = select(func.count(Camera.id)).where(
            Camera.department_id == department_id, Camera.connectivity_status == "DEGRADED"
        )
        degraded = (await session.execute(degraded_stmt)).scalar_one()

        maintenance_stmt = select(func.count(Camera.id)).where(
            Camera.department_id == department_id, Camera.status == "MAINTENANCE"
        )
        maintenance = (await session.execute(maintenance_stmt)).scalar_one()

        types_stmt = (
            select(Camera.camera_type, func.count(Camera.id))
            .where(Camera.department_id == department_id)
            .group_by(Camera.camera_type)
        )
        types_map = {row[0]: row[1] for row in (await session.execute(types_stmt)).all()}

        return {
            "department_id": dept.id,
            "department_code": dept.code,
            "department_name": dept.name,
            "total_cameras": total,
            "online_cameras": online,
            "offline_cameras": offline,
            "degraded_cameras": degraded,
            "maintenance_cameras": maintenance,
            "by_camera_type": types_map,
        }

    async def find_cameras_in_bbox(
        self,
        session: AsyncSession,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        department_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """PostGIS Bounding Box Envelope query using spatial index."""
        sql = """
            SELECT 
                c.id as camera_id,
                c.camera_code,
                c.name,
                c.camera_type,
                c.status,
                c.connectivity_status,
                l.id as location_id,
                l.name as location_name,
                l.district,
                l.city,
                l.latitude::float as latitude,
                l.longitude::float as longitude,
                d.name as department_name,
                COALESCE(c.coverage_radius_meters, 150.0)::float as coverage_radius_meters,
                (
                    SELECT cs.protocol 
                    FROM camera_streams cs 
                    WHERE cs.camera_id = c.id AND cs.is_primary = TRUE 
                    LIMIT 1
                ) as primary_stream_protocol,
                (
                    SELECT cs.stream_url 
                    FROM camera_streams cs 
                    WHERE cs.camera_id = c.id AND cs.is_primary = TRUE 
                    LIMIT 1
                ) as primary_stream_url
            FROM cameras c
            JOIN locations l ON c.location_id = l.id
            JOIN departments d ON c.department_id = d.id
            WHERE l.latitude BETWEEN :min_lat AND :max_lat
              AND l.longitude BETWEEN :min_lon AND :max_lon
        """
        params: Dict[str, Any] = {
            "min_lat": min(min_lat, max_lat),
            "max_lat": max(min_lat, max_lat),
            "min_lon": min(min_lon, max_lon),
            "max_lon": max(min_lon, max_lon),
            "limit": limit,
        }

        if department_id:
            sql += " AND c.department_id = :department_id"
            params["department_id"] = department_id

        if district:
            sql += " AND l.district ILIKE :district"
            params["district"] = district.strip()

        if status:
            sql += " AND c.connectivity_status = :status"
            params["status"] = status.strip().upper()

        sql += " ORDER BY c.created_at DESC LIMIT :limit;"

        result = await session.execute(text(sql), params)
        return [dict(row) for row in result.mappings().all()]

    async def find_cameras_in_corridor(
        self,
        session: AsyncSession,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        buffer_meters: float = 1000.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """PostGIS Route Corridor query searching within buffer of the trajectory line."""
        sql = text("""
            WITH corridor AS (
                SELECT ST_Buffer(
                    ST_SetSRID(ST_MakeLine(ST_MakePoint(:start_lon, :start_lat), ST_MakePoint(:end_lon, :end_lat)), 4326)::geography,
                    :buffer_meters
                ) as geom
            )
            SELECT 
                c.id as camera_id,
                c.camera_code,
                c.name,
                c.camera_type,
                c.status,
                c.connectivity_status,
                l.id as location_id,
                l.name as location_name,
                l.district,
                l.city,
                l.latitude::float as latitude,
                l.longitude::float as longitude,
                d.name as department_name,
                ROUND(ST_Distance(l.geom, ST_SetSRID(ST_MakeLine(ST_MakePoint(:start_lon, :start_lat), ST_MakePoint(:end_lon, :end_lat)), 4326)::geography)::numeric, 2)::float as distance_from_corridor_meters
            FROM cameras c
            JOIN locations l ON c.location_id = l.id
            JOIN departments d ON c.department_id = d.id
            JOIN corridor cor ON ST_Intersects(l.geom, cor.geom)
            ORDER BY distance_from_corridor_meters ASC
            LIMIT :limit;
        """)

        result = await session.execute(
            sql,
            {
                "start_lat": start_lat,
                "start_lon": start_lon,
                "end_lat": end_lat,
                "end_lon": end_lon,
                "buffer_meters": buffer_meters,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings().all()]

    async def analyze_coverage_gaps(
        self,
        session: AsyncSession,
        district: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Calculates surveillance density, low coverage zones, and offline hotspots."""
        # 1. District density
        dist_sql = text("""
            SELECT 
                l.district,
                COUNT(c.id) as total_cameras,
                COUNT(CASE WHEN c.connectivity_status = 'ONLINE' THEN 1 END) as online_cameras,
                COUNT(CASE WHEN c.connectivity_status = 'OFFLINE' THEN 1 END) as offline_cameras,
                AVG(l.latitude)::float as avg_lat,
                AVG(l.longitude)::float as avg_lng,
                CASE 
                    WHEN COUNT(c.id) < 5 THEN 'LOW'
                    WHEN COUNT(c.id) BETWEEN 5 AND 15 THEN 'MEDIUM'
                    ELSE 'HIGH'
                END as coverage_density_level
            FROM locations l
            LEFT JOIN cameras c ON l.id = c.location_id
            GROUP BY l.district
            ORDER BY total_cameras DESC;
        """)
        dist_rows = [dict(row) for row in (await session.execute(dist_sql)).mappings().all()]

        # 2. Offline hotspots (locations with high concentration of offline/degraded cameras)
        offline_sql = text("""
            SELECT 
                l.district,
                l.city,
                l.name as location_name,
                l.latitude::float as latitude,
                l.longitude::float as longitude,
                COUNT(c.id) as offline_count
            FROM cameras c
            JOIN locations l ON c.location_id = l.id
            WHERE c.connectivity_status IN ('OFFLINE', 'DEGRADED')
            GROUP BY l.district, l.city, l.name, l.latitude, l.longitude
            HAVING COUNT(c.id) >= 1
            ORDER BY offline_count DESC
            LIMIT 10;
        """)
        offline_rows = [dict(row) for row in (await session.execute(offline_sql)).mappings().all()]

        # 3. Low coverage alert zones
        low_coverage_zones = [d for d in dist_rows if d.get("coverage_density_level") == "LOW"]

        metrics = await self.get_coverage_metrics(session)

        return {
            "statewide_summary": metrics,
            "district_density": dist_rows,
            "offline_hotspots": offline_rows,
            "low_coverage_zones": low_coverage_zones,
        }
