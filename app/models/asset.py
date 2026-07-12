"""Asset model — the central tracked entity (Screen 4)."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, Boolean, DateTime, ForeignKey, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Lifecycle states per the spec.
LIFECYCLE_STATUSES = [
    "available",      # free to allocate/book
    "allocated",      # held by someone (allocation phase)
    "reserved",       # booked/reserved
    "under_maintenance",
    "lost",
    "retired",
    "disposed",
]


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(50), unique=True, index=True, nullable=False)  # AF-0001
    name = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey("asset_categories.id"), nullable=False)
    serial_number = Column(String(255), nullable=True)
    acquisition_date = Column(Date, nullable=True)
    acquisition_cost = Column(Numeric(14, 2), nullable=True)  # reports/ranking only
    condition = Column(String(50), default="new", nullable=False)  # new|good|fair|poor
    location = Column(String(255), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    holder_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    lifecycle_status = Column(String(30), default="available", nullable=False)
    is_bookable = Column(Boolean, default=False, nullable=False)  # shared/bookable flag
    image_path = Column(String(512), nullable=True)  # photo/document reference
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    category = relationship("AssetCategory")
    department = relationship("Department")
    holder = relationship("User", foreign_keys=[holder_user_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Asset {self.asset_tag} {self.name}>"
