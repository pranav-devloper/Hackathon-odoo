"""Activity log model (Screen 10 base).

A full audit trail of "who did what, when" across the app — distinct from the
user-facing Notification table. One row per meaningful action.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(80), nullable=False)        # e.g. asset_allocated
    entity_type = Column(String(40), nullable=True)     # asset|user|transfer|...
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ActivityLog {self.action} by {self.actor_user_id}>"
