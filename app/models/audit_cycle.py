"""Audit cycle model (Screen 8).

A cycle scopes a verification sweep over assets in a department or location,
assigns one or more auditors, and locks when closed.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, JSON

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditCycle(Base):
    __tablename__ = "audit_cycles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scope_type = Column(String(20), default="department", nullable=False)  # department | location
    scope_value = Column(String(255), nullable=False)  # department id (str) or location text
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), default="open", nullable=False)  # open | closed
    auditors = Column(JSON, default=list, nullable=False)  # list[int] user ids
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditCycle {self.name} {self.status}>"
