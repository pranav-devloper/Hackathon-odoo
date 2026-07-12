"""Department model for the organization hierarchy (Screen 3, Tab A)."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    head_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String(20), default="active", nullable=False)  # active | inactive
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    head = relationship("User", foreign_keys=[head_id])
    parent = relationship("Department", remote_side=[id], foreign_keys=[parent_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Department {self.name}>"
