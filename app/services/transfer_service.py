"""Transfer workflow (Screen 5): request -> approve (re-allocate) | reject."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.transfer import Transfer
from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.user import User
from app.services import allocation_service, notification_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def request_transfer(db: Session, asset_id: int, to_user_id: int, expected_return_date, note, requested_by: int) -> Transfer:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    to_user = db.query(User).filter(User.id == to_user_id).first()
    if not to_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    current = allocation_service.active_allocation_for_asset(db, asset_id)
    from_user_id = current.holder_user_id if current else None

    # Avoid duplicate open requests for the same asset+target.
    dupe = (
        db.query(Transfer)
        .filter(Transfer.asset_id == asset_id, Transfer.to_user_id == to_user_id, Transfer.status == "requested")
        .first()
    )
    if dupe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A transfer request for this asset is already pending")

    tr = Transfer(
        asset_id=asset_id, from_user_id=from_user_id, to_user_id=to_user_id,
        requested_by=requested_by, expected_return_date=expected_return_date,
        note=note, status="requested",
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)

    # Notify current holder + approvers.
    if from_user_id:
        notification_service.notify(db, from_user_id, "transfer_requested",
                                    f"A transfer of {asset.asset_tag} ({asset.name}) to {to_user.full_name} has been requested.")
    notification_service.notify_managers(db, "transfer_requested",
                                         f"Transfer requested: {asset.asset_tag} -> {to_user.full_name}. Awaiting approval.")
    return tr


def _get_pending(db: Session, transfer_id: int) -> Transfer:
    tr = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not tr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    if tr.status != "requested":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Transfer already {tr.status}")
    return tr


def approve_transfer(db: Session, transfer_id: int, approver_id: int) -> Transfer:
    tr = _get_pending(db, transfer_id)
    asset = db.query(Asset).filter(Asset.id == tr.asset_id).first()

    # End the current active allocation (if any), then re-allocate to the target.
    current = allocation_service.active_allocation_for_asset(db, tr.asset_id)
    if current:
        current.status = "returned"
        current.returned_at = _utcnow()

    new_alloc = Allocation(
        asset_id=tr.asset_id, holder_user_id=tr.to_user_id,
        expected_return_date=tr.expected_return_date, allocated_by=approver_id, status="active",
    )
    db.add(new_alloc)
    if asset:
        asset.holder_user_id = tr.to_user_id
        asset.lifecycle_status = "allocated"

    tr.status = "approved"
    tr.resolved_at = _utcnow()
    db.commit()
    db.refresh(tr)

    to_user = db.query(User).filter(User.id == tr.to_user_id).first()
    notification_service.notify(db, tr.to_user_id, "transfer_approved",
                                f"Transfer approved: {asset.asset_tag if asset else 'asset'} is now allocated to you.")
    if tr.from_user_id:
        notification_service.notify(db, tr.from_user_id, "transfer_approved",
                                    f"{asset.asset_tag if asset else 'Asset'} has been transferred to {to_user.full_name if to_user else 'another user'}.")
    return tr


def reject_transfer(db: Session, transfer_id: int, approver_id: int) -> Transfer:
    tr = _get_pending(db, transfer_id)
    tr.status = "rejected"
    tr.resolved_at = _utcnow()
    db.commit()
    db.refresh(tr)

    asset = db.query(Asset).filter(Asset.id == tr.asset_id).first()
    notification_service.notify(db, tr.requested_by, "transfer_rejected",
                                f"Your transfer request for {asset.asset_tag if asset else 'the asset'} was rejected.")
    return tr


def list_transfers(db: Session, status_filter: str | None = None) -> list[Transfer]:
    q = db.query(Transfer)
    if status_filter:
        q = q.filter(Transfer.status == status_filter)
    return q.order_by(Transfer.created_at.desc()).all()


def count_pending(db: Session) -> int:
    return db.query(Transfer).filter(Transfer.status == "requested").count()
