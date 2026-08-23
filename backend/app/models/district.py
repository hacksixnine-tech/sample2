from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base, UUIDMixin, TimestampMixin


class District(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "districts"

    district_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), default="Gujarat", nullable=False)
    zone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    centroid_lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    centroid_lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
