"""Allocation business logic (Screen 5): allocate with conflict rule, return, overdue."""
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.user import User
from app.services import notification_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def active_allocation_for_asset(db: Session, asset_id: int) -> Allocation | None:
    return (
        db.query(Allocation)
        .filter(Allocation.asset_id == asset_id, Allocation.status == "active")
        .first()
    )


def allocate(db: Session, asset_id: int, holder_user_id: int, expected_return_date, allocated_by: int) -> Allocation:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    holder = db.query(User).filter(User.id == holder_user_id).first()
    if not holder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holder user not found")

    # Conflict rule: can't allocate an asset that's already held.
    existing = active_allocation_for_asset(db, asset_id)
    if existing:
        current = db.query(User).filter(User.id == existing.holder_user_id).first()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": f"Asset {asset.asset_tag} is currently held by {current.full_name if current else 'another user'}. Raise a Transfer Request instead.",
                "holder_user_id": existing.holder_user_id,
                "holder_name": current.full_name if current else None,
            },
        )
    if asset.lifecycle_status not in ("available",):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": f"Asset {asset.asset_tag} is {asset.lifecycle_status}, not available for allocation.",
                    "holder_user_id": asset.holder_user_id or 0, "holder_name": None},
        )

    alloc = Allocation(
        asset_id=asset_id,
        holder_user_id=holder_user_id,
        expected_return_date=expected_return_date,
        allocated_by=allocated_by,
        status="active",
    )
    db.add(alloc)
    asset.holder_user_id = holder_user_id
    asset.lifecycle_status = "allocated"
    db.commit()
    db.refresh(alloc)

    due = f" (due {expected_return_date})" if expected_return_date else ""
    notification_service.notify(db, holder_user_id, "asset_assigned",
                                f"Asset {asset.asset_tag} ({asset.name}) has been assigned to you{due}.")
    return alloc


def return_allocation(db: Session, allocation_id: int, condition_notes: str | None) -> Allocation:
    alloc = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if not alloc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    if alloc.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Allocation is not active")

    alloc.status = "returned"
    alloc.condition_notes = condition_notes
    alloc.returned_at = _utcnow()

    asset = db.query(Asset).filter(Asset.id == alloc.asset_id).first()
    if asset:
        asset.holder_user_id = None
        asset.lifecycle_status = "available"
    db.commit()
    db.refresh(alloc)

    if asset:
        notification_service.notify(db, alloc.holder_user_id, "asset_returned",
                                    f"Return recorded for {asset.asset_tag} ({asset.name}). Status is now Available.")
    return alloc


def list_allocations(db: Session, only_active: bool = False) -> list[Allocation]:
    q = db.query(Allocation)
    if only_active:
        q = q.filter(Allocation.status == "active")
    return q.order_by(Allocation.created_at.desc()).all()


def is_overdue(alloc: Allocation) -> bool:
    return (
        alloc.status == "active"
        and alloc.expected_return_date is not None
        and alloc.expected_return_date < date.today()
    )


def count_overdue(db: Session) -> int:
    return sum(1 for a in db.query(Allocation).filter(Allocation.status == "active").all() if is_overdue(a))


def count_upcoming(db: Session, days: int = 7) -> int:
    today = date.today()
    horizon = today + timedelta(days=days)
    return (
        db.query(Allocation)
        .filter(
            Allocation.status == "active",
            Allocation.expected_return_date != None,  # noqa: E711
            Allocation.expected_return_date >= today,
            Allocation.expected_return_date <= horizon,
        )
        .count()
    )
