"""Allocation model — who currently holds an asset (Screen 5, history in Screen 4).

The full allocation/transfer workflow (conflict rules, approvals, overdue flagging)
lands in Phase 2; the table and basic rows are created here so asset history exists.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    holder_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expected_return_date = Column(Date, nullable=True)
    status = Column(String(30), default="active", nullable=False)  # active | returned
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Allocation asset={self.asset_id} holder={self.holder_user_id}>"
