import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import logger
from app.models.analytics import Vehicle, VehicleObservation
from app.models.camera import Camera
from app.repositories.alert import AlertRepository
from app.repositories.analytics import EvidenceRepository, ObservationRepository, VehicleRepository
from app.repositories.audit import AuditRepository
from app.schemas.investigation import (
    RoutePoint,
    SightingDetail,
    VehicleMovementHistory,
    VehicleRouteResponse,
)


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


class TrackingService:
    def __init__(self):
        self.vehicles = VehicleRepository()
        self.observations = ObservationRepository()
        self.evidence = EvidenceRepository()
        self.alerts = AlertRepository()
        self.audit = AuditRepository()

    async def get_vehicle_history(
        self,
        session: AsyncSession,
        vehicle_id: uuid.UUID,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        district: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        limit: int = 200,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleMovementHistory:
        vehicle = await self.vehicles.get_with_entity(session, vehicle_id)
        if not vehicle or not vehicle.entity:
            raise NotFoundError(f"Vehicle {vehicle_id} not found")

        obs_list = await self.observations.history_for_vehicle(
            session, vehicle_id, timestamp_from, timestamp_to
        )

        sightings: List[SightingDetail] = []
        unique_cameras = set()
        unique_districts = set()

        for obs in obs_list:
            cam = obs.camera
            loc = obs.location or (cam.location if cam else None)
            cam_district = loc.district if loc else None

            # Filters
            if district and cam_district and district.lower() not in cam_district.lower():
                continue
            if camera_id and obs.camera_id != camera_id:
                continue

            unique_cameras.add(obs.camera_id)
            if cam_district:
                unique_districts.add(cam_district)

            evidence_ref = None
            if obs.evidence_id:
                ev = await self.evidence.get_by_id(session, obs.evidence_id)
                if ev:
                    evidence_ref = ev.public_reference or ev.evidence_code

            lat = float(loc.latitude) if loc and loc.latitude is not None else None
            lon = float(loc.longitude) if loc and loc.longitude is not None else None

            sightings.append(
                SightingDetail(
                    camera_id=obs.camera_id,
                    camera_name=cam.name if cam else None,
                    source_camera_id=cam.source_camera_id if cam else None,
                    district=cam_district,
                    location_name=loc.name if loc else None,
                    latitude=lat,
                    longitude=lon,
                    timestamp=obs.observed_at,
                    plate_confidence=float(obs.plate_confidence) if obs.plate_confidence is not None else None,
                    vehicle_confidence=float(obs.vehicle_confidence) if obs.vehicle_confidence is not None else None,
                    evidence_reference=evidence_ref,
                    frame_reference=obs.frame_reference,
                    is_demo=obs.is_demo,
                )
            )

        # Sort chronologically
        sightings.sort(key=lambda s: s.timestamp)
        if limit:
            sightings = sightings[:limit]

        await self.audit.log_action(
            session,
            action="VIEW_ENTITY",
            resource_type="VEHICLE_HISTORY",
            resource_id=str(vehicle_id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Viewed chronological history for vehicle {vehicle.normalized_plate}",
        )

        return VehicleMovementHistory(
            vehicle_id=vehicle.id,
            normalized_plate=vehicle.normalized_plate,
            raw_plate=vehicle.raw_plate,
            vehicle_type=vehicle.vehicle_type,
            first_seen=vehicle.entity.first_seen_at,
            last_seen=vehicle.entity.last_seen_at,
            sighting_count=len(sightings),
            unique_camera_count=len(unique_cameras),
            unique_district_count=len(unique_districts),
            sightings=sightings,
        )

    async def get_vehicle_route(
        self,
        session: AsyncSession,
        vehicle_id: uuid.UUID,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleRouteResponse:
        """
        Builds GIS-ready observed camera route sequence.
        Distinguishes OBSERVED MOVEMENT from INFERRED/ESTIMATED ROUTING.
        Calculates straight-line geographic distances and detects suspicious anomalies.
        """
        history = await self.get_vehicle_history(
            session, vehicle_id, timestamp_from, timestamp_to, user_id=user_id, ip_address=ip_address, user_agent=user_agent
        )

        valid_points: List[SightingDetail] = [
            s for s in history.sightings if s.latitude is not None and s.longitude is not None
        ]

        route_points: List[RoutePoint] = []
        anomalies: List[Dict[str, Any]] = []
        total_dist = 0.0

        prev_point: Optional[RoutePoint] = None

        for idx, s in enumerate(valid_points, start=1):
            dist_prev = None
            time_delta = None
            speed_kmph = None
            anomaly_flag = None

            if prev_point:
                dist_prev = haversine_distance_meters(
                    prev_point.latitude, prev_point.longitude, s.latitude, s.longitude
                )
                time_delta = (s.timestamp - prev_point.timestamp).total_seconds()
                total_dist += dist_prev

                if time_delta > 0:
                    speed_kmph = round((dist_prev / time_delta) * 3.6, 2)

                # Anomaly Checks (Non-accusatory behavioral telemetry)
                if time_delta <= 5 and dist_prev > 1000:
                    anomaly_flag = "SIMULTANEOUS_DISTANT_SIGHTING"
                    anomalies.append({
                        "anomaly_type": "SIMULTANEOUS_DISTANT_SIGHTING",
                        "severity": "HIGH",
                        "description": (
                            f"Vehicle observed at two distant cameras ({dist_prev}m apart) "
                            f"within {time_delta:.1f}s. Potential plate clone or GPS/timestamp desync."
                        ),
                        "camera_from": str(prev_point.camera_id),
                        "camera_to": str(s.camera_id),
                        "timestamp": s.timestamp.isoformat(),
                    })
                elif speed_kmph and speed_kmph > 200:
                    anomaly_flag = "IMPOSSIBLE_GEOGRAPHIC_SPEED"
                    anomalies.append({
                        "anomaly_type": "IMPOSSIBLE_GEOGRAPHIC_SPEED",
                        "severity": "MEDIUM",
                        "description": f"Calculated straight-line speed of {speed_kmph} km/h between sightings.",
                        "speed_kmph": speed_kmph,
                        "timestamp": s.timestamp.isoformat(),
                    })
                elif time_delta > 14400:  # 4 hours gap
                    anomaly_flag = "LARGE_TIME_GAP"

            curr_point = RoutePoint(
                sequence=idx,
                camera_id=s.camera_id,
                camera_name=s.camera_name,
                source_camera_id=s.source_camera_id,
                district=s.district,
                city=s.location_name,
                latitude=s.latitude,
                longitude=s.longitude,
                timestamp=s.timestamp,
                straight_line_distance_prev_meters=dist_prev,
                time_delta_prev_seconds=time_delta,
                geographic_speed_kmph=speed_kmph,
                anomaly_flag=anomaly_flag,
            )
            route_points.append(curr_point)
            prev_point = curr_point

        return VehicleRouteResponse(
            vehicle_id=history.vehicle_id,
            normalized_plate=history.normalized_plate,
            route_type="OBSERVED_CAMERA_SEQUENCE",
            point_count=len(route_points),
            first_seen=history.first_seen,
            last_seen=history.last_seen,
            total_geographic_distance_meters=round(total_dist, 2),
            unique_camera_count=history.unique_camera_count,
            unique_district_count=history.unique_district_count,
            points=route_points,
            anomalies_detected=anomalies,
        )
