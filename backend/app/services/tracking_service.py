import csv
import io
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.anpr.normalize import normalize_plate_text
from app.core.exceptions import NotFoundError
from app.core.logging import logger
from app.models.alert import Alert
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
    VehicleSummaryResponse,
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

    async def _resolve_vehicle(
        self, session: AsyncSession, identifier: Union[uuid.UUID, str]
    ) -> Vehicle:
        """Resolve vehicle by UUID or license plate string."""
        if isinstance(identifier, uuid.UUID):
            veh = await self.vehicles.get_with_entity(session, identifier)
            if not veh or not veh.entity:
                raise NotFoundError(f"Vehicle with ID '{identifier}' not found")
            return veh

        # Try parsing as UUID string
        try:
            val_uuid = uuid.UUID(str(identifier))
            veh = await self.vehicles.get_with_entity(session, val_uuid)
            if veh and veh.entity:
                return veh
        except (ValueError, AttributeError):
            pass

        # Parse as License Plate Number
        norm = normalize_plate_text(str(identifier))
        veh = await self.vehicles.get_by_plate(session, norm)
        if not veh or not veh.entity:
            raise NotFoundError(f"Vehicle with plate '{identifier}' (normalized: '{norm}') not found")
        return veh

    async def get_vehicle_history(
        self,
        session: AsyncSession,
        identifier: Union[uuid.UUID, str],
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        district: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        watchlist_only: Optional[bool] = False,
        sort_order: str = "desc",
        limit: int = 200,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleMovementHistory:
        vehicle = await self._resolve_vehicle(session, identifier)

        obs_list = await self.observations.history_for_vehicle(
            session, vehicle.id, timestamp_from, timestamp_to
        )

        # 1. Sort strictly chronologically (ascending) for transition calculations
        obs_list.sort(key=lambda s: s.observed_at)

        sightings: List[SightingDetail] = []
        unique_cameras = set()
        unique_districts = set()
        prev_sighting: Optional[SightingDetail] = None

        for obs in obs_list:
            cam = obs.camera
            loc = obs.location or (cam.location if cam else None)
            cam_district = loc.district if loc else None

            # Filters
            if district and cam_district and district.lower() not in cam_district.lower():
                continue
            if camera_id and obs.camera_id != camera_id:
                continue

            meta = obs.metadata_ or {}
            matched_wl = bool(meta.get("matched_watchlist") or meta.get("watchlist_hit"))
            wl_type = meta.get("watchlist_category") or meta.get("watchlist_type")

            if watchlist_only and not matched_wl:
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

            # Calculate transition telemetry relative to previous chronological observation
            dist_prev = None
            time_delta = None
            speed_kmph = None
            anomaly_flag = None

            if prev_sighting and prev_sighting.latitude is not None and prev_sighting.longitude is not None and lat is not None and lon is not None:
                dist_prev = haversine_distance_meters(
                    prev_sighting.latitude, prev_sighting.longitude, lat, lon
                )
                time_delta = (obs.observed_at - prev_sighting.timestamp).total_seconds()
                if time_delta > 0:
                    speed_kmph = round((dist_prev / time_delta) * 3.6, 1)

                # Anomaly classification (non-accusatory forensic telemetry)
                if time_delta <= 10 and dist_prev > 1000:
                    anomaly_flag = "SIMULTANEOUS_DISTANT_SIGHTING"
                elif speed_kmph and speed_kmph > 200:
                    anomaly_flag = "IMPOSSIBLE_GEOGRAPHIC_SPEED"
                elif time_delta > 14400:
                    anomaly_flag = "LARGE_TIME_GAP"

            sighting = SightingDetail(
                sighting_id=obs.id,
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
                is_demo=bool(getattr(obs, "is_demo", False)),
                transition_distance_meters=dist_prev,
                transition_time_seconds=time_delta,
                estimated_speed_kmph=speed_kmph,
                speed_label="ESTIMATED AVERAGE SPEED",
                anomaly_flag=anomaly_flag,
                matched_watchlist=matched_wl,
                watchlist_type=wl_type,
            )
            sightings.append(sighting)
            prev_sighting = sighting

        # Determine First & Last Seen from actual sightings
        first_seen = sightings[0].timestamp if sightings else vehicle.entity.first_seen_at
        last_seen = sightings[-1].timestamp if sightings else vehicle.entity.last_seen_at

        # Apply requested sort order: 'desc' (default for UI investigation feed) or 'asc' (route reconstruction)
        if sort_order.lower() == "desc":
            sightings.reverse()

        if limit:
            sightings = sightings[:limit]

        await self.audit.log_action(
            session,
            action="VIEW_ENTITY",
            resource_type="VEHICLE_HISTORY",
            resource_id=str(vehicle.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Viewed chronological history for vehicle {vehicle.normalized_plate} (order: {sort_order})",
        )

        return VehicleMovementHistory(
            vehicle_id=vehicle.id,
            normalized_plate=vehicle.normalized_plate,
            raw_plate=vehicle.raw_plate,
            vehicle_type=vehicle.vehicle_type,
            first_seen=first_seen,
            last_seen=last_seen,
            sighting_count=len(sightings),
            unique_camera_count=len(unique_cameras),
            unique_district_count=len(unique_districts),
            sort_order=sort_order,
            sightings=sightings,
        )

    async def get_vehicle_summary(
        self,
        session: AsyncSession,
        identifier: Union[uuid.UUID, str],
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleSummaryResponse:
        vehicle = await self._resolve_vehicle(session, identifier)
        history = await self.get_vehicle_history(
            session,
            vehicle.id,
            sort_order="asc",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Count watchlist matches and alerts
        stmt_alerts = (
            select(Alert)
            .where(Alert.entity_id == vehicle.id)
            .order_by(Alert.created_at.desc())
        )
        alerts_rows = list((await session.execute(stmt_alerts)).scalars().all())
        highest_prio = None
        for a in alerts_rows:
            if a.severity == "CRITICAL":
                highest_prio = "CRITICAL"
                break
            elif a.severity == "HIGH" and highest_prio != "CRITICAL":
                highest_prio = "HIGH"
            elif not highest_prio:
                highest_prio = a.severity

        matched_wl_count = sum(1 for s in history.sightings if s.matched_watchlist)
        speeds = [s.estimated_speed_kmph for s in history.sightings if s.estimated_speed_kmph is not None]
        avg_speed = round(sum(speeds) / len(speeds), 1) if speeds else None

        return VehicleSummaryResponse(
            vehicle_id=vehicle.id,
            normalized_plate=vehicle.normalized_plate,
            raw_plate=vehicle.raw_plate,
            vehicle_type=vehicle.vehicle_type,
            make=vehicle.make,
            model=vehicle.model,
            color=vehicle.color,
            owner_name=vehicle.owner_name,
            first_seen=history.first_seen,
            last_seen=history.last_seen,
            total_sightings=history.sighting_count,
            unique_cameras=history.unique_camera_count,
            unique_districts=history.unique_district_count,
            watchlist_matches_count=matched_wl_count,
            alerts_count=len(alerts_rows),
            watchlist_status="MATCH" if (matched_wl_count > 0 or alerts_rows) else "CLEAR",
            highest_risk_level=highest_prio,
            investigation_status="UNDER_REVIEW" if alerts_rows else "OPEN",
            average_transition_speed_kmph=avg_speed,
            speed_disclaimer="ESTIMATED AVERAGE SPEED BETWEEN CAMERAS",
            is_demo=bool(vehicle.metadata_.get("is_demo") if vehicle.metadata_ else False),
        )

    async def get_vehicle_route(
        self,
        session: AsyncSession,
        identifier: Union[uuid.UUID, str],
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VehicleRouteResponse:
        """Builds GIS-ready observed camera route sequence."""
        history = await self.get_vehicle_history(
            session,
            identifier,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            sort_order="asc",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        valid_points = [
            s for s in history.sightings if s.latitude is not None and s.longitude is not None
        ]

        route_points: List[RoutePoint] = []
        anomalies: List[Dict[str, Any]] = []
        total_dist = 0.0

        for idx, s in enumerate(valid_points, start=1):
            if s.transition_distance_meters:
                total_dist += s.transition_distance_meters

            if s.anomaly_flag:
                anomalies.append({
                    "anomaly_type": s.anomaly_flag,
                    "severity": "HIGH" if s.anomaly_flag == "SIMULTANEOUS_DISTANT_SIGHTING" else "MEDIUM",
                    "description": (
                        f"Unusual transition to camera {s.camera_name or str(s.camera_id)}: "
                        f"Distance {s.transition_distance_meters or 0:.0f}m in {s.transition_time_seconds or 0:.1f}s."
                    ),
                    "camera_id": str(s.camera_id),
                    "timestamp": s.timestamp.isoformat(),
                    "speed_kmph": s.estimated_speed_kmph,
                })

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
                straight_line_distance_prev_meters=s.transition_distance_meters,
                time_delta_prev_seconds=s.transition_time_seconds,
                geographic_speed_kmph=s.estimated_speed_kmph,
                speed_label="ESTIMATED AVERAGE SPEED",
                anomaly_flag=s.anomaly_flag,
            )
            route_points.append(curr_point)

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

    async def export_vehicle_history_csv(
        self,
        session: AsyncSession,
        identifier: Union[uuid.UUID, str],
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        district: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        watchlist_only: Optional[bool] = False,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Generates formatted CSV report for the vehicle movement dataset."""
        history = await self.get_vehicle_history(
            session,
            identifier,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            district=district,
            camera_id=camera_id,
            watchlist_only=watchlist_only,
            sort_order="asc",
            limit=5000,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Sighting_ID",
            "Normalized_Plate",
            "Raw_Plate",
            "Timestamp_UTC",
            "Camera_ID",
            "Camera_Name",
            "District",
            "City",
            "Latitude",
            "Longitude",
            "Plate_Confidence",
            "Transition_Distance_Meters",
            "Transition_Elapsed_Seconds",
            "Estimated_Average_Speed_Kmph",
            "Speed_Label",
            "Anomaly_Flag",
            "Watchlist_Matched",
            "Watchlist_Type",
            "Evidence_Reference",
        ])

        for s in history.sightings:
            writer.writerow([
                str(s.sighting_id or ""),
                history.normalized_plate,
                history.raw_plate,
                s.timestamp.isoformat(),
                str(s.camera_id),
                s.camera_name or "",
                s.district or "",
                s.location_name or "",
                s.latitude if s.latitude is not None else "",
                s.longitude if s.longitude is not None else "",
                f"{s.plate_confidence:.4f}" if s.plate_confidence is not None else "",
                f"{s.transition_distance_meters:.2f}" if s.transition_distance_meters is not None else "",
                f"{s.transition_time_seconds:.1f}" if s.transition_time_seconds is not None else "",
                f"{s.estimated_speed_kmph:.1f}" if s.estimated_speed_kmph is not None else "",
                s.speed_label,
                s.anomaly_flag or "NONE",
                "YES" if s.matched_watchlist else "NO",
                s.watchlist_type or "",
                s.evidence_reference or "",
            ])

        await self.audit.log_action(
            session,
            action="EXPORT_REPORT",
            resource_type="VEHICLE_REPORT_CSV",
            resource_id=history.normalized_plate,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Exported {len(history.sightings)} sighting records to CSV for {history.normalized_plate}",
        )

        return output.getvalue()
