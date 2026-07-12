"""Asset category model (Screen 3, Tab B) — e.g. Electronics, Furniture, Vehicles."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # Category-specific field, e.g. warranty period for Electronics.
    warranty_period_days = Column(Integer, nullable=True)
    status = Column(String(20), default="active", nullable=False)  # active | inactive
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AssetCategory {self.name}>"
