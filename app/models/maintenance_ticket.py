"""Maintenance ticket model (Screen 7, history in Screen 4).

The approval workflow (Pending → Approved/Rejected → In Progress → Resolved) and the
auto asset-status updates land in Phase 4; the table and basic rows are created here.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

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
    assigned_tech = Column(String(255), nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    asset = relationship("Asset")
    reporter = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MaintenanceTicket asset={self.asset_id}>"
