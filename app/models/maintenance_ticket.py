"""Maintenance ticket model (Screen 7).

Workflow: pending -> approved / rejected -> in_progress -> resolved.
On approval the asset flips to under_maintenance; on resolution it returns to available.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    issue = Column(Text, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)  # low|medium|high|urgent
    status = Column(String(30), default="pending", nullable=False)
    # pending | approved | rejected | in_progress | resolved

    assigned_tech = Column(String(255), nullable=True)
    rejected_reason = Column(Text, nullable=True)
    photo_path = Column(String(512), nullable=True)  # optional attached photo (URL/path)

    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MaintenanceTicket asset={self.asset_id} {self.status}>"
