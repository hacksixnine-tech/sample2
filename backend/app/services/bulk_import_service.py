import csv
import io
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.camera import Camera
from app.models.location import Location
from app.models.stream import CameraStream
from app.repositories.camera import CameraRepository
from app.repositories.department import DepartmentRepository
from app.repositories.location import LocationRepository
from app.repositories.stream import StreamRepository
from app.repositories.audit import AuditRepository
from app.schemas.camera import (
    BulkImportErrorDetail,
    CameraBulkImportResponse,
    CameraBulkImportRow,
    VALID_CAMERA_TYPES,
)


class BulkCameraImportService:
    def __init__(
        self,
        camera_repo: Optional[CameraRepository] = None,
        dept_repo: Optional[DepartmentRepository] = None,
        location_repo: Optional[LocationRepository] = None,
        stream_repo: Optional[StreamRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.camera_repo = camera_repo or CameraRepository()
        self.dept_repo = dept_repo or DepartmentRepository()
        self.location_repo = location_repo or LocationRepository()
        self.stream_repo = stream_repo or StreamRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def import_from_csv_content(
        self, session: AsyncSession, csv_text: str, actor_id: Optional[uuid.UUID] = None
    ) -> CameraBulkImportResponse:
        f = io.StringIO(csv_text.strip())
        reader = csv.DictReader(f)

        rows: List[Dict[str, Any]] = []
        for row in reader:
            rows.append(row)

        return await self.import_rows(session, rows, actor_id=actor_id)

    async def import_rows(
        self,
        session: AsyncSession,
        raw_rows: List[Dict[str, Any]],
        actor_id: Optional[uuid.UUID] = None,
    ) -> CameraBulkImportResponse:
        total_rows = len(raw_rows)
        successful_codes: List[str] = []
        errors: List[BulkImportErrorDetail] = []

        seen_codes_in_batch = set()

        for idx, row in enumerate(raw_rows, start=1):
            try:
                # 1. Parse row with Pydantic
                camera_code = str(row.get("camera_code", "")).strip().upper()
                if not camera_code:
                    errors.append(BulkImportErrorDetail(row=idx, field="camera_code", error="Missing camera code"))
                    continue

                if camera_code in seen_codes_in_batch:
                    errors.append(
                        BulkImportErrorDetail(
                            row=idx, field="camera_code", error=f"Duplicate camera code '{camera_code}' in this batch"
                        )
                    )
                    continue

                # 2. Check duplicate in database
                existing_cam = await self.camera_repo.get_by_code(session, camera_code)
                if existing_cam:
                    errors.append(
                        BulkImportErrorDetail(
                            row=idx, field="camera_code", error=f"Camera code '{camera_code}' already exists in database"
                        )
                    )
                    continue

                # 3. Validate Department
                dept_code = str(row.get("department_code", "")).strip().upper()
                dept = await self.dept_repo.get_by_code(session, dept_code)
                if not dept:
                    errors.append(
                        BulkImportErrorDetail(
                            row=idx, field="department_code", error=f"Department with code '{dept_code}' does not exist"
                        )
                    )
                    continue

                # 4. Validate Coordinates
                try:
                    lat = float(row.get("latitude"))
                    lon = float(row.get("longitude"))
                except (ValueError, TypeError):
                    errors.append(
                        BulkImportErrorDetail(
                            row=idx, field="coordinates", error="Invalid numeric format for latitude or longitude"
                        )
                    )
                    continue

                if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
                    errors.append(
                        BulkImportErrorDetail(
                            row=idx, field="coordinates", error=f"Coordinates ({lat}, {lon}) out of global WGS84 range"
                        )
                    )
                    continue

                # 5. Resolve or Create Location
                loc_name = str(row.get("location_name", "")).strip() or f"Junction {camera_code}"
                city = str(row.get("city", "Ahmedabad")).strip()
                district = str(row.get("district", "Ahmedabad")).strip()

                loc = await self.location_repo.get_by_name_and_city(session, loc_name, city)
                if not loc:
                    loc = Location(
                        name=loc_name,
                        state="Gujarat",
                        district=district,
                        city=city,
                        latitude=lat,
                        longitude=lon,
                        metadata_={"imported": True},
                    )
                    loc = await self.location_repo.create(session, loc)

                # 6. Validate camera type
                camera_type = str(row.get("camera_type", "ANPR")).strip().upper()
                if camera_type not in VALID_CAMERA_TYPES:
                    camera_type = "OTHER"

                # 7. Create Camera
                name = str(row.get("name", "")).strip() or f"Camera {camera_code}"
                cam = Camera(
                    camera_code=camera_code,
                    name=name,
                    department_id=dept.id,
                    location_id=loc.id,
                    camera_type=camera_type,
                    manufacturer=str(row.get("manufacturer", "")).strip() or None,
                    model=str(row.get("model", "")).strip() or None,
                    ownership=str(row.get("ownership", "Gujarat Government")).strip(),
                    status="ACTIVE",
                    connectivity_status="ONLINE",
                    storage_type="EDGE_AND_CENTRAL",
                    retention_days=30,
                    metadata_={"imported": True, "import_batch": True},
                )
                created_cam = await self.camera_repo.create(session, cam)

                # 8. Create Primary Stream if provided
                stream_url = str(row.get("stream_url", "")).strip()
                protocol = str(row.get("protocol", "RTSP")).strip().upper()
                if stream_url:
                    stream = CameraStream(
                        camera_id=created_cam.id,
                        protocol=protocol if protocol in {"RTSP", "HLS", "WEBRTC", "HTTP", "ONVIF", "VENDOR_API"} else "RTSP",
                        stream_url=stream_url,
                        resolution="1080p",
                        fps=25.0,
                        codec="H264",
                        is_primary=True,
                        is_active=True,
                    )
                    await self.stream_repo.create(session, stream)

                seen_codes_in_batch.add(camera_code)
                successful_codes.append(camera_code)

            except Exception as ex:
                errors.append(
                    BulkImportErrorDetail(
                        row=idx,
                        error=f"Unexpected error processing row: {str(ex)}",
                        data=row,
                    )
                )

        # Audit log for bulk import
        if successful_codes:
            await self.audit_repo.log_action(
                session,
                action="BULK_CAMERA_IMPORT",
                resource_type="CAMERA",
                user_id=actor_id,
                details=f"Bulk imported {len(successful_codes)} cameras. Failed: {len(errors)}",
                metadata={"successful": len(successful_codes), "failed": len(errors)},
            )

        return CameraBulkImportResponse(
            total_rows=total_rows,
            successful=len(successful_codes),
            failed=len(errors),
            errors=errors,
            imported_camera_codes=successful_codes,
        )
