"""Maintenance workflow (Screen 7): raise -> approve/reject -> assign -> resolve.

Auto status flips on the asset:
  approved  -> asset.lifecycle_status = under_maintenance
  resolved  -> asset.lifecycle_status = available
Every transition is also written to the Activity Log.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.maintenance_ticket import MaintenanceTicket
from app.models.asset import Asset
from app.models.user import User
from app.services import notification_service, activity_service


MANAGER_ROLES = ("asset_manager", "department_head", "admin")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get(db: Session, ticket_id: int) -> MaintenanceTicket:
    t = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance ticket not found")
    return t


def _is_manager(user: User) -> bool:
    return bool(user.role and user.role.name in MANAGER_ROLES)


def raise_request(
    db: Session,
    asset_id: int,
    reporter_id: int,
    issue: str,
    priority: str = "medium",
    photo_path: str | None = None,
) -> MaintenanceTicket:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    ticket = MaintenanceTicket(
        asset_id=asset_id,
        reporter_id=reporter_id,
        issue=issue,
        priority=priority,
        photo_path=photo_path,
        status="pending",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    notification_service.notify_managers(
        db, "maintenance_requested",
        f"Maintenance requested for {asset.asset_tag} ({asset.name}): {issue[:60]}",
    )
    activity_service.log_activity(db, reporter_id, "maintenance_raised", "maintenance", ticket.id,
                                  f"{asset.asset_tag}: {issue[:80]}")
    return ticket


def list_tickets(db: Session, user: User) -> list[MaintenanceTicket]:
    q = db.query(MaintenanceTicket)
    if not _is_manager(user):
        q = q.filter(MaintenanceTicket.reporter_id == user.id)
    return q.order_by(MaintenanceTicket.created_at.desc()).all()


def get_ticket(db: Session, ticket_id: int, user: User) -> MaintenanceTicket:
    t = _get(db, ticket_id)
    if not _is_manager(user) and t.reporter_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this ticket")
    return t


def approve(db: Session, ticket_id: int, approver: User) -> MaintenanceTicket:
    t = _get(db, ticket_id)
    if t.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ticket already {t.status}")
    t.status = "approved"
    t.approved_by = approver.id

    asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
    if asset:
        asset.lifecycle_status = "under_maintenance"

    db.commit()
    db.refresh(t)

    notification_service.notify(db, t.reporter_id, "maintenance_approved",
                                f"Maintenance for {asset.asset_tag if asset else 'asset'} approved. Asset is now Under Maintenance.")
    activity_service.log_activity(db, approver.id, "maintenance_approved", "maintenance", t.id,
                                  asset.asset_tag if asset else None)
    return t


def reject(db: Session, ticket_id: int, approver: User, reason: str | None = None) -> MaintenanceTicket:
    t = _get(db, ticket_id)
    if t.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ticket already {t.status}")
    t.status = "rejected"
    t.rejected_reason = reason
    db.commit()
    db.refresh(t)

    notification_service.notify(db, t.reporter_id, "maintenance_rejected",
                                f"Maintenance request rejected{f': {reason}' if reason else '.'}")
    activity_service.log_activity(db, approver.id, "maintenance_rejected", "maintenance", t.id,
                                  reason or "no reason given")
    return t


def assign_tech(db: Session, ticket_id: int, approver: User, tech: str) -> MaintenanceTicket:
    t = _get(db, ticket_id)
    if t.status not in ("approved", "in_progress"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ticket must be approved before assigning a technician")
    t.assigned_tech = tech
    t.assigned_at = _utcnow()
    t.status = "in_progress"
    db.commit()
    db.refresh(t)

    asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
    notification_service.notify(db, t.reporter_id, "maintenance_in_progress",
                                f"Technician {tech} assigned to {asset.asset_tag if asset else 'asset'}.")
    activity_service.log_activity(db, approver.id, "maintenance_assigned", "maintenance", t.id,
                                  f"tech={tech}")
    return t


def resolve(db: Session, ticket_id: int, approver: User) -> MaintenanceTicket:
    t = _get(db, ticket_id)
    if t.status not in ("approved", "in_progress"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ticket must be in progress before resolving")
    t.status = "resolved"
    t.resolved_at = _utcnow()

    asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
    if asset:
        asset.lifecycle_status = "available"

    db.commit()
    db.refresh(t)

    notification_service.notify(db, t.reporter_id, "maintenance_resolved",
                                f"Maintenance for {asset.asset_tag if asset else 'asset'} resolved. Asset is now Available.")
    activity_service.log_activity(db, approver.id, "maintenance_resolved", "maintenance", t.id,
                                  asset.asset_tag if asset else None)
    return t
