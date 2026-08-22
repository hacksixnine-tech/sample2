from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.anpr.normalize import normalize_plate_text
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import logger
from app.models.department import Department
from app.models.watchlist import Watchlist, WatchlistEntry
from app.repositories.audit import AuditRepository
from app.repositories.department import DepartmentRepository
from app.repositories.user import UserRepository
from app.repositories.watchlist import WatchlistEntryRepository, WatchlistRepository
from app.schemas.watchlist import (
    VALID_WATCHLIST_CATEGORIES,
    WatchlistCreate,
    WatchlistEntryCreate,
    WatchlistEntryResponse,
    WatchlistEntryUpdate,
    WatchlistResponse,
    WatchlistUpdate,
    normalize_watchlist_category,
)


class WatchlistService:
    def __init__(self):
        self.watchlists = WatchlistRepository()
        self.entries = WatchlistEntryRepository()
        self.departments = DepartmentRepository()
        self.users = UserRepository()
        self.audit = AuditRepository()

    async def create_watchlist(
        self,
        session: AsyncSession,
        data: WatchlistCreate,
        user_id: Optional[uuid.UUID] = None,
        user_department_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Watchlist:
        # Validate Category
        raw_cat = data.category.strip().upper()
        if raw_cat not in VALID_WATCHLIST_CATEGORIES:
            raise ValidationError(
                f"Invalid watchlist category '{data.category}'. Allowed categories: {sorted(list(VALID_WATCHLIST_CATEGORIES))}"
            )
        category = normalize_watchlist_category(raw_cat)

        # Department resolution
        dept_id = data.department_id or user_department_id
        if not dept_id and data.owner_department:
            dept = await self.departments.get_by_code(session, data.owner_department)
            if dept:
                dept_id = dept.id

        if not dept_id:
            # Fallback to first available department (e.g. Police)
            all_depts = await self.departments.get_all(session, limit=1)
            if all_depts:
                dept_id = all_depts[0].id
            else:
                raise ValidationError("Department ID or valid owner department is required.")

        code = data.code or f"WL-{uuid.uuid4().hex[:8].upper()}"
        existing = await self.watchlists.get_by_code(session, code)
        if existing:
            raise ConflictError(f"Watchlist with code '{code}' already exists.")

        valid_creator_id = None
        if user_id:
            user = await self.users.get_by_id(session, user_id)
            if user:
                valid_creator_id = user.id

        wl = Watchlist(
            name=data.name.strip(),
            code=code,
            category=category,
            department_id=dept_id,
            description=data.description,
            priority=data.priority.upper(),
            is_active=data.is_active if data.active is None else data.active,
            created_by_user_id=valid_creator_id,
            metadata_=data.metadata,
        )
        session.add(wl)
        await session.flush()
        await session.refresh(wl)

        await self.audit.log_action(
            session,
            action="CREATE_WATCHLIST",
            resource_type="WATCHLIST",
            resource_id=str(wl.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Created watchlist {wl.code} ({wl.name})",
        )
        return wl

    async def get_watchlist(self, session: AsyncSession, watchlist_id: uuid.UUID) -> Watchlist:
        wl = await self.watchlists.get_by_id(session, watchlist_id)
        if not wl:
            raise NotFoundError(f"Watchlist {watchlist_id} not found")
        return wl

    async def list_watchlists(
        self,
        session: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Watchlist], int]:
        norm_cat = normalize_watchlist_category(category) if category else None
        skip = (page - 1) * page_size
        return await self.watchlists.list_filtered(
            session,
            department_id=department_id,
            category=norm_cat,
            is_active=is_active,
            search=search,
            skip=skip,
            limit=page_size,
        )

    async def update_watchlist(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        data: WatchlistUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Watchlist:
        wl = await self.get_watchlist(session, watchlist_id)

        if data.name:
            wl.name = data.name.strip()
        if data.category:
            raw_cat = data.category.strip().upper()
            if raw_cat not in VALID_WATCHLIST_CATEGORIES:
                raise ValidationError(f"Invalid category {data.category}")
            wl.category = normalize_watchlist_category(raw_cat)
        if data.description is not None:
            wl.description = data.description
        if data.priority:
            wl.priority = data.priority.upper()
        if data.active is not None:
            wl.is_active = data.active
        elif data.is_active is not None:
            wl.is_active = data.is_active
        if data.metadata:
            wl.metadata_ = {**wl.metadata_, **data.metadata}

        await session.flush()
        await session.refresh(wl)

        await self.audit.log_action(
            session,
            action="UPDATE_WATCHLIST",
            resource_type="WATCHLIST",
            resource_id=str(wl.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Updated watchlist {wl.code}",
        )
        return wl

    async def delete_watchlist(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        wl = await self.get_watchlist(session, watchlist_id)
        # Soft delete / deactivate
        wl.is_active = False
        await session.flush()

        await self.audit.log_action(
            session,
            action="UPDATE_WATCHLIST",
            resource_type="WATCHLIST",
            resource_id=str(wl.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Deactivated watchlist {wl.code}",
        )
        return True

    # -------------------------------------------------------------------------
    # Watchlist Entries
    # -------------------------------------------------------------------------

    async def create_entry(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        data: WatchlistEntryCreate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> WatchlistEntry:
        wl = await self.get_watchlist(session, watchlist_id)

        ident = (data.normalized_plate or data.raw_plate or data.identifier).strip()
        norm_ident = normalize_plate_text(ident) if data.entity_type == "VEHICLE" else ident.upper().replace(" ", "")

        if data.valid_until and data.valid_from and data.valid_until < data.valid_from:
            raise ValidationError("valid_until must be greater than or equal to valid_from.")

        entry = WatchlistEntry(
            watchlist_id=wl.id,
            identifier=ident,
            normalized_identifier=norm_ident,
            entity_type=data.entity_type.upper(),
            case_reference_number=data.case_reference_number or data.external_reference,
            fir_station=data.fir_station,
            reason=data.reason or data.notes or "Added to watchlist",
            priority=data.priority.upper(),
            valid_from=data.valid_from or datetime.now(timezone.utc),
            valid_until=data.valid_until,
            is_active=data.is_active,
            metadata_=data.metadata,
        )
        session.add(entry)
        await session.flush()
        await session.refresh(entry)

        await self.audit.log_action(
            session,
            action="UPDATE_WATCHLIST",
            resource_type="WATCHLIST_ENTRY",
            resource_id=str(entry.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Created watchlist entry {entry.normalized_identifier} in watchlist {wl.code}",
        )
        return entry

    async def get_entry(
        self, session: AsyncSession, watchlist_id: uuid.UUID, entry_id: uuid.UUID
    ) -> WatchlistEntry:
        entry = await self.entries.get_by_id(session, entry_id)
        if not entry or entry.watchlist_id != watchlist_id:
            raise NotFoundError(f"Watchlist entry {entry_id} not found in watchlist {watchlist_id}")
        return entry

    async def list_entries(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[WatchlistEntry], int]:
        await self.get_watchlist(session, watchlist_id)
        skip = (page - 1) * page_size
        return await self.entries.list_by_watchlist(
            session, watchlist_id=watchlist_id, is_active=is_active, skip=skip, limit=page_size
        )

    async def update_entry(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        entry_id: uuid.UUID,
        data: WatchlistEntryUpdate,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> WatchlistEntry:
        entry = await self.get_entry(session, watchlist_id, entry_id)

        if data.identifier:
            entry.identifier = data.identifier.strip()
            entry.normalized_identifier = (
                normalize_plate_text(data.identifier)
                if entry.entity_type == "VEHICLE"
                else data.identifier.upper().replace(" ", "")
            )
        if data.case_reference_number is not None:
            entry.case_reference_number = data.case_reference_number
        if data.fir_station is not None:
            entry.fir_station = data.fir_station
        if data.reason:
            entry.reason = data.reason
        if data.priority:
            entry.priority = data.priority.upper()
        if data.valid_from is not None:
            entry.valid_from = data.valid_from
        if data.valid_until is not None:
            entry.valid_until = data.valid_until
        if data.is_active is not None:
            entry.is_active = data.is_active
        if data.metadata:
            entry.metadata_ = {**entry.metadata_, **data.metadata}

        if entry.valid_until and entry.valid_from and entry.valid_until < entry.valid_from:
            raise ValidationError("valid_until must be greater than or equal to valid_from.")

        await session.flush()
        await session.refresh(entry)

        await self.audit.log_action(
            session,
            action="UPDATE_WATCHLIST",
            resource_type="WATCHLIST_ENTRY",
            resource_id=str(entry.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Updated watchlist entry {entry.normalized_identifier}",
        )
        return entry

    async def delete_entry(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        entry_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        entry = await self.get_entry(session, watchlist_id, entry_id)
        entry.is_active = False
        await session.flush()

        await self.audit.log_action(
            session,
            action="UPDATE_WATCHLIST",
            resource_type="WATCHLIST_ENTRY",
            resource_id=str(entry.id),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Deactivated watchlist entry {entry.normalized_identifier}",
        )
        return True
