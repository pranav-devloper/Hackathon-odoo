"""Audit item model (Screen 8): one asset row inside an audit cycle."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# result values: None (pending) | verified | missing | damaged
class AuditItem(Base):
    __tablename__ = "audit_items"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("audit_cycles.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    result = Column(String(20), nullable=True)  # verified | missing | damaged
    note = Column(Text, nullable=True)
    audited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    audited_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditItem cycle={self.cycle_id} asset={self.asset_id} {self.result}>"
