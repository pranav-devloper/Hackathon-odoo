"""Transfer request model (Screen 5).

Workflow: requested -> approved (re-allocated automatically) | rejected.
Raised when someone wants an asset currently held by another user.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # current holder
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)    # requested new holder
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expected_return_date = Column(Date, nullable=True)
    status = Column(String(30), default="requested", nullable=False)  # requested|approved|rejected
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Transfer asset={self.asset_id} to={self.to_user_id} {self.status}>"
