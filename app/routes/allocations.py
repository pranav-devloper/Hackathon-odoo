"""Allocation, return, and transfer routes (Screen 5)."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_roles
from app.models.user import User
from app.models.asset import Asset
from app.schemas.allocation import (
    AllocationCreate, AllocationReturn, AllocationOut,
    TransferCreate, TransferOut,
)
from app.services import allocation_service, transfer_service

router = APIRouter(tags=["allocations"])

MANAGER_ROLES = ("asset_manager", "department_head", "admin")


# ---------- helpers ----------
def _name(db: Session, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    u = db.query(User).filter(User.id == user_id).first()
    return u.full_name if u else None


def serialize_allocation(db: Session, a) -> AllocationOut:
    asset = db.query(Asset).filter(Asset.id == a.asset_id).first()
    return AllocationOut(
        id=a.id, asset_id=a.asset_id,
        asset_tag=asset.asset_tag if asset else None,
        asset_name=asset.name if asset else None,
        holder_user_id=a.holder_user_id, holder_name=_name(db, a.holder_user_id),
        expected_return_date=a.expected_return_date, status=a.status,
        is_overdue=allocation_service.is_overdue(a),
        condition_notes=a.condition_notes, returned_at=a.returned_at, created_at=a.created_at,
    )


def serialize_transfer(db: Session, t) -> TransferOut:
    asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
    return TransferOut(
        id=t.id, asset_id=t.asset_id,
        asset_tag=asset.asset_tag if asset else None,
        asset_name=asset.name if asset else None,
        from_user_id=t.from_user_id, from_name=_name(db, t.from_user_id),
        to_user_id=t.to_user_id, to_name=_name(db, t.to_user_id),
        requested_by=t.requested_by, status=t.status, note=t.note,
        expected_return_date=t.expected_return_date,
        created_at=t.created_at, resolved_at=t.resolved_at,
    )


# ---------- allocations ----------
@router.get("/allocations", response_model=list[AllocationOut])
def get_allocations(active: bool = False, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [serialize_allocation(db, a) for a in allocation_service.list_allocations(db, only_active=active)]


@router.post("/allocations", response_model=AllocationOut, status_code=201)
def post_allocation(data: AllocationCreate, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    alloc = allocation_service.allocate(db, data.asset_id, data.holder_user_id, data.expected_return_date, me.id)
    return serialize_allocation(db, alloc)


@router.post("/allocations/{allocation_id}/return", response_model=AllocationOut)
def return_allocation(allocation_id: int, data: AllocationReturn, db: Session = Depends(get_db), _: User = Depends(require_roles(*MANAGER_ROLES))):
    alloc = allocation_service.return_allocation(db, allocation_id, data.condition_notes)
    return serialize_allocation(db, alloc)


# ---------- transfers ----------
@router.get("/transfers", response_model=list[TransferOut])
def get_transfers(status: Optional[str] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [serialize_transfer(db, t) for t in transfer_service.list_transfers(db, status)]


@router.post("/transfers", response_model=TransferOut, status_code=201)
def post_transfer(data: TransferCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    # Any authenticated user may REQUEST a transfer (Employee included).
    tr = transfer_service.request_transfer(db, data.asset_id, data.to_user_id, data.expected_return_date, data.note, me.id)
    return serialize_transfer(db, tr)


@router.post("/transfers/{transfer_id}/approve", response_model=TransferOut)
def approve_transfer(transfer_id: int, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    return serialize_transfer(db, transfer_service.approve_transfer(db, transfer_id, me.id))


@router.post("/transfers/{transfer_id}/reject", response_model=TransferOut)
def reject_transfer(transfer_id: int, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    return serialize_transfer(db, transfer_service.reject_transfer(db, transfer_id, me.id))
