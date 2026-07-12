"""Notification routes (Screen 10 base)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.allocation import NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def get_notifications(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    # Refresh overdue alerts so the bell reflects the latest state.
    notification_service.scan_overdue(db)
    return notification_service.list_for_user(db, me.id)


@router.post("/{notif_id}/read", status_code=204)
def read_notification(notif_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    notification_service.mark_read(db, me.id, notif_id)


@router.post("/read-all", status_code=204)
def read_all(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    notification_service.mark_all_read(db, me.id)
