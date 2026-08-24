import pytest
from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.services.investigation_service import InvestigationService
from app.models.analytics import Vehicle, VehicleObservation, Entity
from app.models.incident import Incident
from app.schemas.investigation import (
    InvestigationSearchResult,
    InvestigationTimelineResponse,
    VehicleInvestigationDossier,
)


@pytest.mark.asyncio
async def test_investigation_dossier_by_plate():
    service = InvestigationService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 8, 42, 0, tzinfo=timezone.utc)
    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t0, total_sightings=1)
    mock_vehicle = Vehicle(
        id=veh_id,
        normalized_plate="GJ05AB1234",
        raw_plate="GJ 05 AB 1234",
        vehicle_type="CAR",
        make="Hyundai",
        model="Creta",
        color="Silver",
    )
    mock_vehicle.entity = mock_entity

    service.vehicles.get_by_plate = AsyncMock(return_value=mock_vehicle)
    service.observations.history_for_vehicle = AsyncMock(return_value=[])
    service.tracking.get_vehicle_route = AsyncMock(return_value=MagicMock(anomalies_detected=[]))
    service.audit.log_action = AsyncMock()

    # Execute mock queries on session for alerts/incidents
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    dossier = await service.get_vehicle_dossier(session, "GJ05AB1234")
    assert isinstance(dossier, VehicleInvestigationDossier)
    assert dossier.plate == "GJ05AB1234"
    assert dossier.identity == "VEHICLE-GJ05AB1234"


@pytest.mark.asyncio
async def test_investigation_note_and_status_lifecycle():
    service = InvestigationService()
    session = AsyncMock()

    inc_id = uuid.uuid4()
    mock_incident = Incident(
        id=inc_id,
        incident_code="INC-2026-001",
        title="Suspect Vehicle Sighting",
        description="Observed at toll checkpoint",
        status="OPEN",
        metadata_={"investigation_notes": []},
    )
    service.incidents.get_by_id = AsyncMock(return_value=mock_incident)
    service.audit.log_action = AsyncMock()

    # 1. Add Note
    note = await service.add_investigation_note(
        session, inc_id, note_text="Vehicle sighted entering sector 4 at 08:42", category="TACTICAL"
    )
    assert note["note"] == "Vehicle sighted entering sector 4 at 08:42"
    assert note["category"] == "TACTICAL"
    assert len(mock_incident.metadata_["investigation_notes"]) == 1

    # 2. Update Status Lifecycle
    updated_inc = await service.update_investigation_status(
        session, inc_id, new_status="UNDER_REVIEW", reason="Officer assigned"
    )
    assert updated_inc.status == "UNDER_REVIEW"
