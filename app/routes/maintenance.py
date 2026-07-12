"""Maintenance ticket routes (Screen 7)."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_roles
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceTicketCreate, MaintenanceTicketOut, MaintenanceTicketUpdate,
)
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

MANAGER_ROLES = ("asset_manager", "department_head", "admin")


def _name(db: Session, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    u = db.query(User).filter(User.id == user_id).first()
    return u.full_name if u else None


def serialize(db: Session, t) -> MaintenanceTicketOut:
    asset = t.asset
    return MaintenanceTicketOut(
        id=t.id, asset_id=t.asset_id,
        asset_tag=asset.asset_tag if asset else None,
        asset_name=asset.name if asset else None,
        reporter_id=t.reporter_id,
        reporter_name=_name(db, t.reporter_id),
        issue=t.issue, priority=t.priority, status=t.status,
        assigned_tech=t.assigned_tech, resolution=t.resolution,
        created_at=t.created_at,
    )


@router.post("", response_model=MaintenanceTicketOut, status_code=201)
def post_ticket(
    data: MaintenanceTicketCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """Any authenticated user may raise a maintenance request."""
    return serialize(db, maintenance_service.create_ticket(db, me.id, data))


@router.get("", response_model=list[MaintenanceTicketOut])
def get_tickets(
    asset_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    # Managers see everything; employees see only their own tickets by default
    # (pass mine=true to be explicit, or any filter is ignored for non-managers).
    is_manager = bool(me.role and me.role.name in MANAGER_ROLES)
    reporter_id = me.id if (mine or not is_manager) else None
    return [
        serialize(db, t)
        for t in maintenance_service.list_tickets(
            db, asset_id=asset_id, status_filter=status,
            priority=priority, reporter_id=reporter_id,
        )
    ]


@router.get("/{ticket_id}", response_model=MaintenanceTicketOut)
def get_one(ticket_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return serialize(db, maintenance_service.get_ticket(db, ticket_id))


@router.patch("/{ticket_id}", response_model=MaintenanceTicketOut)
def patch_ticket(
    ticket_id: int,
    data: MaintenanceTicketUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*MANAGER_ROLES)),
):
    """Managers update status / priority / tech / resolution."""
    return serialize(db, maintenance_service.update_ticket(db, ticket_id, data, _.id))
