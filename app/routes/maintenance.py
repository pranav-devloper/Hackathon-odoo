"""Maintenance routes (Screen 7)."""
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_roles
from app.models.asset import Asset
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceCreate, MaintenanceReject, MaintenanceAssign, MaintenanceOut,
)
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

MANAGER_ROLES = ("asset_manager", "department_head", "admin")


def _name(db: Session, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    u = db.query(User).filter(User.id == user_id).first()
    return u.full_name if u else None


def serialize(db: Session, t) -> MaintenanceOut:
    asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
    return MaintenanceOut(
        id=t.id, asset_id=t.asset_id,
        asset_tag=asset.asset_tag if asset else None,
        asset_name=asset.name if asset else None,
        reporter_id=t.reporter_id, reporter_name=_name(db, t.reporter_id),
        issue=t.issue, priority=t.priority, status=t.status,
        assigned_tech=t.assigned_tech, rejected_reason=t.rejected_reason,
        resolution=t.resolution, photo_path=t.photo_path, approved_by=t.approved_by,
        assigned_at=t.assigned_at, resolved_at=t.resolved_at,
        created_at=t.created_at,
    )


@router.post("", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
def post_maintenance(data: MaintenanceCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    """Any authenticated user may raise a maintenance request against an asset."""
    t = maintenance_service.raise_request(db, data.asset_id, me.id, data.issue, data.priority, data.photo_path)
    return serialize(db, t)


@router.get("", response_model=list[MaintenanceOut])
def get_maintenance(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return [serialize(db, t) for t in maintenance_service.list_tickets(db, me)]


@router.get("/{ticket_id}", response_model=MaintenanceOut)
def get_one(ticket_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return serialize(db, maintenance_service.get_ticket(db, ticket_id, me))


@router.post("/{ticket_id}/approve", response_model=MaintenanceOut)
def approve(ticket_id: int, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    return serialize(db, maintenance_service.approve(db, ticket_id, me))


@router.post("/{ticket_id}/reject", response_model=MaintenanceOut)
def reject(ticket_id: int, data: MaintenanceReject, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    return serialize(db, maintenance_service.reject(db, ticket_id, me, data.reason))


@router.post("/{ticket_id}/assign", response_model=MaintenanceOut)
def assign(ticket_id: int, data: MaintenanceAssign, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    return serialize(db, maintenance_service.assign_tech(db, ticket_id, me, data.tech))


@router.post("/{ticket_id}/resolve", response_model=MaintenanceOut)
def resolve(ticket_id: int, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    return serialize(db, maintenance_service.resolve(db, ticket_id, me))
