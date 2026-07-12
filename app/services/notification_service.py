"""Notification creation + retrieval + lazy overdue scanning (Screen 10 base)."""
from datetime import date

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.role import Role
from app.models.user import User


def notify(db: Session, user_id: int, ntype: str, message: str, commit: bool = True) -> Notification:
    n = Notification(user_id=user_id, type=ntype, message=message)
    db.add(n)
    if commit:
        db.commit()
        db.refresh(n)
    return n


def notify_managers(db: Session, ntype: str, message: str, commit: bool = True) -> None:
    """Send a notification to every asset_manager / department_head / admin."""
    manager_roles = db.query(Role).filter(Role.name.in_(["asset_manager", "department_head", "admin"])).all()
    role_ids = [r.id for r in manager_roles]
    managers = db.query(User).filter(User.role_id.in_(role_ids)).all()
    for m in managers:
        db.add(Notification(user_id=m.id, type=ntype, message=message))
    if commit:
        db.commit()


def list_for_user(db: Session, user_id: int) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_read(db: Session, user_id: int, notif_id: int) -> None:
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user_id).first()
    if n and not n.is_read:
        n.is_read = True
        db.commit()


def mark_all_read(db: Session, user_id: int) -> None:
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update(  # noqa: E712
        {"is_read": True}
    )
    db.commit()


def scan_overdue(db: Session) -> int:
    """Create overdue-return notifications for allocations past their return date.

    Idempotent-ish: dedupes by an "[A<id>]" marker so each overdue allocation
    only generates one alert to its holder. Returns count of overdue allocations.
    """
    today = date.today()
    overdue = (
        db.query(Allocation)
        .filter(Allocation.status == "active", Allocation.expected_return_date < today)
        .all()
    )
    for al in overdue:
        marker = f"[A{al.id}]"
        exists = (
            db.query(Notification)
            .filter(Notification.type == "overdue_return", Notification.message.contains(marker))
            .first()
        )
        if exists:
            continue
        asset = db.query(Asset).filter(Asset.id == al.asset_id).first()
        tag = asset.asset_tag if asset else f"#{al.asset_id}"
        msg = f"{marker} Overdue return: {tag} was due {al.expected_return_date}."
        db.add(Notification(user_id=al.holder_user_id, type="overdue_return", message=msg))
    if overdue:
        db.commit()
    return len(overdue)
