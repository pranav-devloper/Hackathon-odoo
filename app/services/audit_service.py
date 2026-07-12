"""Audit cycle workflow (Screen 8).

Create a cycle scoped by department or location -> auto-generate one AuditItem per
matching asset -> auditors mark each Verified/Missing/Damaged -> discrepancy report ->
close locks the cycle and flips confirmed-missing assets to Lost.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_cycle import AuditCycle
from app.models.audit_item import AuditItem
from app.models.asset import Asset
from app.services import activity_service


MANAGER_ROLES = ("asset_manager", "department_head", "admin")
VALID_RESULTS = ("verified", "missing", "damaged")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _scope_query(db: Session, scope_type: str, scope_value: str):
    q = db.query(Asset)
    if scope_type == "department":
        try:
            dept_id = int(scope_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department scope must be a numeric id")
        return q.filter(Asset.department_id == dept_id)
    if scope_type == "location":
        return q.filter(Asset.location == scope_value)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope_type must be 'department' or 'location'")


def create_cycle(
    db: Session,
    name: str,
    scope_type: str,
    scope_value: str,
    created_by: int,
    auditors: Optional[list[int]] = None,
    start_date=None,
    end_date=None,
) -> AuditCycle:
    assets = _scope_query(db, scope_type, scope_value).all()
    cycle = AuditCycle(
        name=name, scope_type=scope_type, scope_value=scope_value,
        start_date=start_date, end_date=end_date,
        auditors=list(auditors or []), created_by=created_by, status="open",
    )
    db.add(cycle)
    db.flush()  # assign cycle.id before creating items
    for asset in assets:
        db.add(AuditItem(cycle_id=cycle.id, asset_id=asset.id))
    db.commit()
    db.refresh(cycle)
    activity_service.log_activity(db, created_by, "audit_cycle_created", "audit_cycle", cycle.id,
                                  f"{name} ({len(assets)} assets)")
    return cycle


def list_cycles(db: Session) -> list[AuditCycle]:
    return db.query(AuditCycle).order_by(AuditCycle.created_at.desc()).all()


def get_cycle(db: Session, cycle_id: int) -> AuditCycle:
    cycle = db.query(AuditCycle).filter(AuditCycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit cycle not found")
    return cycle


def update_auditors(db: Session, cycle_id: int, auditors: list[int], actor_id: int) -> AuditCycle:
    cycle = get_cycle(db, cycle_id)
    if cycle.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audit cycle is closed")
    cycle.auditors = list(auditors or [])
    db.commit()
    db.refresh(cycle)
    activity_service.log_activity(db, actor_id, "audit_cycle_updated", "audit_cycle", cycle.id, "auditors updated")
    return cycle


def mark_item(
    db: Session, cycle_id: int, item_id: int, result: str,
    audited_by: int, note: Optional[str] = None,
) -> AuditItem:
    cycle = get_cycle(db, cycle_id)
    if cycle.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audit cycle is closed")
    if result not in VALID_RESULTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"result must be one of {VALID_RESULTS}")
    item = db.query(AuditItem).filter(AuditItem.id == item_id, AuditItem.cycle_id == cycle_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit item not found")
    item.result = result
    item.note = note
    item.audited_by = audited_by
    item.audited_at = _utcnow()
    db.commit()
    db.refresh(item)
    return item


def discrepancies(db: Session, cycle_id: int) -> list[AuditItem]:
    get_cycle(db, cycle_id)
    return (
        db.query(AuditItem)
        .filter(AuditItem.cycle_id == cycle_id, AuditItem.result.in_(["missing", "damaged"]))
        .order_by(AuditItem.id)
        .all()
    )


def close_cycle(db: Session, cycle_id: int, actor_id: int) -> AuditCycle:
    cycle = get_cycle(db, cycle_id)
    if cycle.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audit cycle already closed")

    # Confirmed-missing assets become Lost; others keep their status.
    missing = db.query(AuditItem).filter(AuditItem.cycle_id == cycle_id, AuditItem.result == "missing").all()
    for item in missing:
        asset = db.query(Asset).filter(Asset.id == item.asset_id).first()
        if asset:
            asset.lifecycle_status = "lost"

    cycle.status = "closed"
    cycle.closed_at = _utcnow()
    db.commit()
    db.refresh(cycle)
    activity_service.log_activity(db, actor_id, "audit_cycle_closed", "audit_cycle", cycle.id,
                                  f"{len(missing)} asset(s) flagged lost")
    return cycle
