"""Maintenance ticket business logic (Screen 7).

Raising a ticket puts the asset Under Maintenance; resolving or rejecting it
restores the asset to its natural state (allocated if currently held, else
available). Managers (asset_manager / department_head / admin) update tickets;
any authenticated user may raise one.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.maintenance_ticket import MaintenanceTicket
from app.models.user import User
from app.schemas.maintenance import PRIORITIES, STATUSES
from app.services import allocation_service, notification_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _name(db: Session, user_id: int | None) -> str | None:
    if not user_id:
        return None
    u = db.query(User).filter(User.id == user_id).first()
    return u.full_name if u else None


def _asset(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


def create_ticket(db: Session, reporter_id: int, data) -> MaintenanceTicket:
    if data.priority not in PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be one of: {', '.join(PRIORITIES)}",
        )
    asset = _asset(db, data.asset_id)

    ticket = MaintenanceTicket(
        asset_id=asset.id,
        reporter_id=reporter_id,
        issue=data.issue,
        priority=data.priority,
        assigned_tech=data.assigned_tech,
        status="pending",
    )
    db.add(ticket)

    # Open ticket => asset is Under Maintenance (preserves any holder).
    asset.lifecycle_status = "under_maintenance"
    db.commit()
    db.refresh(ticket)

    notification_service.notify_managers(
        db, "maintenance_requested",
        f"Maintenance raised for {asset.asset_tag} ({asset.name}): {data.issue}",
    )
    return ticket


def list_tickets(
    db: Session,
    *,
    asset_id: int | None = None,
    status_filter: str | None = None,
    priority: str | None = None,
    reporter_id: int | None = None,
) -> list[MaintenanceTicket]:
    q = db.query(MaintenanceTicket)
    if asset_id is not None:
        q = q.filter(MaintenanceTicket.asset_id == asset_id)
    if status_filter:
        q = q.filter(MaintenanceTicket.status == status_filter)
    if priority:
        q = q.filter(MaintenanceTicket.priority == priority)
    if reporter_id is not None:
        q = q.filter(MaintenanceTicket.reporter_id == reporter_id)
    return q.order_by(MaintenanceTicket.created_at.desc()).all()


def get_ticket(db: Session, ticket_id: int) -> MaintenanceTicket:
    t = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return t


def _restore_asset_status(db: Session, asset: Asset) -> None:
    """Return an asset to its natural state once a ticket closes."""
    held = allocation_service.active_allocation_for_asset(db, asset.id) is not None
    asset.lifecycle_status = "allocated" if held else "available"


def update_ticket(db: Session, ticket_id: int, data, actor_id: int) -> MaintenanceTicket:
    t = get_ticket(db, ticket_id)

    if data.status is not None:
        if data.status not in STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(STATUSES)}",
            )
        t.status = data.status
    if data.priority is not None:
        if data.priority not in PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {', '.join(PRIORITIES)}",
            )
        t.priority = data.priority
    if data.assigned_tech is not None:
        t.assigned_tech = data.assigned_tech
    if data.resolution is not None:
        t.resolution = data.resolution

    # Closing a ticket frees the asset from Under Maintenance.
    if t.status in ("resolved", "rejected"):
        asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
        if asset:
            _restore_asset_status(db, asset)

    db.commit()
    db.refresh(t)

    asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
    tag = asset.asset_tag if asset else "the asset"
    notification_service.notify(
        db, t.reporter_id, "maintenance_updated",
        f"Maintenance for {tag} is now {t.status}.",
    )
    if t.status == "resolved":
        notification_service.notify(
            db, t.reporter_id, "maintenance_resolved",
            f"Maintenance for {tag} has been resolved{f': {t.resolution}' if t.resolution else ''}.",
        )
    return t


def count_open(db: Session) -> int:
    return (
        db.query(MaintenanceTicket)
        .filter(MaintenanceTicket.status.in_(["pending", "in_progress"]))
        .count()
    )
