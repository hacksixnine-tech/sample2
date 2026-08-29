import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.ai.anpr.normalize import normalize_plate_text
from app.ai.reid import get_global_reid_gallery
from app.models.analytics import Detection, Entity, Evidence, Vehicle, VehicleObservation
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.alert import Alert

logger = logging.getLogger(__name__)


class InvestigationTools:
    """Approved, controlled tool suite for the Law Enforcement Copilot Agent."""

    @staticmethod
    async def search_plate(session: AsyncSession, plate: str) -> Dict[str, Any]:
        """Search exact and normalized license plate in the ANPR sighting registry."""
        norm = normalize_plate_text(plate)
        stmt = (
            select(Vehicle)
            .where(or_(Vehicle.normalized_plate == norm, Vehicle.raw_plate.ilike(f"%{plate}%")))
        )
        res = await session.execute(stmt)
        veh = res.scalars().first()

        if not veh:
            return {"found": False, "query_plate": plate, "normalized": norm, "message": "No vehicle record matches plate"}

        # Fetch latest observations
        obs_stmt = (
            select(VehicleObservation)
            .where(VehicleObservation.vehicle_id == veh.id)
            .order_by(VehicleObservation.observed_at.desc())
            .limit(10)
        )
        obs_res = await session.execute(obs_stmt)
        observations = obs_res.scalars().all()

        return {
            "found": True,
            "vehicle_id": str(veh.id),
            "normalized_plate": veh.normalized_plate,
            "raw_plate": veh.raw_plate,
            "vehicle_type": veh.vehicle_type,
            "make": veh.make,
            "model": veh.model,
            "color": veh.color,
            "owner_name": veh.owner_name,
            "total_sightings": len(observations),
            "recent_observations": [
                {
                    "observation_id": str(o.id),
                    "camera_id": str(o.camera_id),
                    "observed_at": o.observed_at.isoformat(),
                    "speed_kmph": float(o.speed_kmph) if o.speed_kmph else None,
                    "direction": o.direction,
                    "confidence": float(o.plate_confidence),
                }
                for o in observations
            ],
        }

    @staticmethod
    async def search_vehicle(
        session: AsyncSession,
        color: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        district: Optional[str] = None,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search vehicles by physical attributes (color, make, model) and geo-temporal bounds."""
        stmt = select(Vehicle)
        if color:
            stmt = stmt.where(Vehicle.color.ilike(f"%{color}%"))
        if make:
            stmt = stmt.where(Vehicle.make.ilike(f"%{make}%"))
        if model:
            stmt = stmt.where(Vehicle.model.ilike(f"%{model}%"))

        stmt = stmt.limit(limit)
        res = await session.execute(stmt)
        vehicles = res.scalars().all()

        results = []
        for v in vehicles:
            results.append({
                "vehicle_id": str(v.id),
                "plate": v.normalized_plate,
                "color": v.color or "UNKNOWN",
                "make": v.make or "UNKNOWN",
                "model": v.model or "UNKNOWN",
                "type": v.vehicle_type or "CAR",
                "owner": v.owner_name,
            })
        return results

    @staticmethod
    async def get_gis_route(session: AsyncSession, vehicle_identifier: str) -> Dict[str, Any]:
        """Constructs the spatial-temporal GPS route of a vehicle from camera sightings."""
        norm = normalize_plate_text(vehicle_identifier)
        stmt = select(Vehicle).where(Vehicle.normalized_plate == norm)
        res = await session.execute(stmt)
        veh = res.scalars().first()

        if not veh:
            return {"route_found": False, "points": [], "message": f"Vehicle {vehicle_identifier} not found"}

        obs_stmt = (
            select(VehicleObservation, Camera)
            .join(Camera, VehicleObservation.camera_id == Camera.id)
            .where(VehicleObservation.vehicle_id == veh.id)
            .order_by(VehicleObservation.observed_at.asc())
        )
        obs_res = await session.execute(obs_stmt)
        rows = obs_res.all()

        waypoints = []
        for obs, cam in rows:
            waypoints.append({
                "camera_name": cam.name if cam else "Camera",
                "district": cam.district if cam else "Gujarat",
                "latitude": float(cam.latitude) if cam and cam.latitude else 23.0225,
                "longitude": float(cam.longitude) if cam and cam.longitude else 72.5714,
                "timestamp": obs.observed_at.isoformat(),
                "speed_kmph": float(obs.speed_kmph) if obs.speed_kmph else None,
                "direction": obs.direction or "UNKNOWN",
            })

        return {
            "route_found": True,
            "vehicle_plate": veh.normalized_plate,
            "total_waypoints": len(waypoints),
            "waypoints": waypoints,
        }

    @staticmethod
    def cross_camera_visual_match(
        query_crop: Optional[Any] = None,
        query_embedding: Optional[Any] = None,
        object_class: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Invokes the Re-ID visual appearance gallery to search for candidate sightings."""
        gallery = get_global_reid_gallery()
        candidates = gallery.search_candidates(
            query_crop=query_crop,
            query_embedding=query_embedding,
            object_class=object_class,
            top_k=top_k,
        )
        return [
            {
                "sighting_id": c.sighting_id,
                "camera_id": c.camera_id,
                "timestamp": c.timestamp.isoformat(),
                "object_class": c.object_class,
                "similarity_score": c.similarity_score,
                "crop_reference": c.crop_reference,
            }
            for c in candidates
        ]
