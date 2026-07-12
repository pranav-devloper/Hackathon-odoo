"""Audit routes (Screen 8)."""
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_roles
from app.models.user import User
from app.models.asset import Asset
from app.models.audit_item import AuditItem
from app.schemas.audit import (
    AuditCycleCreate, AuditCycleUpdate, AuditItemMark,
    AuditCycleOut, AuditItemOut, AuditCycleDetailOut,
)
from app.services import audit_service

router = APIRouter(prefix="/audits", tags=["audits"])

MANAGER_ROLES = ("asset_manager", "department_head", "admin")


def _is_manager(user: User) -> bool:
    return bool(user.role and user.role.name in MANAGER_ROLES)


def _asset_name(db: Session, asset_id: int):
    a = db.query(Asset).filter(Asset.id == asset_id).first()
    return (a.asset_tag if a else None), (a.name if a else None)


def serialize_item(db: Session, it) -> AuditItemOut:
    tag, name = _asset_name(db, it.asset_id)
    return AuditItemOut(
        id=it.id, cycle_id=it.cycle_id, asset_id=it.asset_id,
        asset_tag=tag, asset_name=name, result=it.result, note=it.note,
        audited_by=it.audited_by, audited_at=it.audited_at, created_at=it.created_at,
    )


def _counts(items):
    return (
        len(items),
        sum(1 for i in items if i.result == "verified"),
        sum(1 for i in items if i.result == "missing"),
        sum(1 for i in items if i.result == "damaged"),
    )


def serialize_cycle(db: Session, c) -> AuditCycleOut:
    items = db.query(AuditItem).filter_by(cycle_id=c.id).all()
    ic, vc, mc, dc = _counts(items)
    return AuditCycleOut(
        id=c.id, name=c.name, scope_type=c.scope_type, scope_value=c.scope_value,
        start_date=c.start_date, end_date=c.end_date, status=c.status,
        auditors=list(c.auditors or []), created_by=c.created_by,
        created_at=c.created_at, closed_at=c.closed_at,
        item_count=ic, verified_count=vc, missing_count=mc, damaged_count=dc,
    )


@router.post("/cycles", response_model=AuditCycleOut, status_code=status.HTTP_201_CREATED)
def post_cycle(data: AuditCycleCreate, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    c = audit_service.create_cycle(
        db, data.name, data.scope_type, data.scope_value, me.id,
        data.auditors, data.start_date, data.end_date,
    )
    return serialize_cycle(db, c)


@router.get("/cycles", response_model=list[AuditCycleOut])
def get_cycles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [serialize_cycle(db, c) for c in audit_service.list_cycles(db)]


@router.get("/cycles/{cycle_id}", response_model=AuditCycleDetailOut)
def get_cycle(cycle_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    c = audit_service.get_cycle(db, cycle_id)
    items = db.query(AuditItem).filter_by(cycle_id=cycle_id).all()
    disc = audit_service.discrepancies(db, cycle_id)
    return AuditCycleDetailOut(
        cycle=serialize_cycle(db, c),
        items=[serialize_item(db, it) for it in items],
        discrepancies=[serialize_item(db, it) for it in disc],
    )


@router.patch("/cycles/{cycle_id}", response_model=AuditCycleOut)
def patch_cycle(cycle_id: int, data: AuditCycleUpdate, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    c = audit_service.update_auditors(db, cycle_id, data.auditors, me.id)
    return serialize_cycle(db, c)


@router.patch("/cycles/{cycle_id}/items/{item_id}", response_model=AuditItemOut)
def mark_item(cycle_id: int, item_id: int, data: AuditItemMark, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    c = audit_service.get_cycle(db, cycle_id)
    if c.status == "closed":
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audit cycle is closed")
    # Only assigned auditors or managers may mark items.
    if not _is_manager(me) and me.id not in (c.auditors or []):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an assigned auditor for this cycle")
    it = audit_service.mark_item(db, cycle_id, item_id, data.result, me.id, data.note)
    return serialize_item(db, it)


@router.get("/cycles/{cycle_id}/discrepancies", response_model=list[AuditItemOut])
def get_discrepancies(cycle_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [serialize_item(db, it) for it in audit_service.discrepancies(db, cycle_id)]


@router.post("/cycles/{cycle_id}/close", response_model=AuditCycleOut)
def close_cycle(cycle_id: int, db: Session = Depends(get_db), me: User = Depends(require_roles(*MANAGER_ROLES))):
    c = audit_service.close_cycle(db, cycle_id, me.id)
    return serialize_cycle(db, c)
