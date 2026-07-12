"""Activity log routes (Screen 10 base).

Admins and managers see the full trail; employees see only their own actions.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_roles
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services import activity_service

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])

MANAGER_ROLES = ("asset_manager", "department_head", "admin")


def serialize(e) -> dict:
    return {
        "id": e.id,
        "actor_user_id": e.actor_user_id,
        "action": e.action,
        "entity_type": e.entity_type,
        "entity_id": e.entity_id,
        "detail": e.detail,
        "created_at": e.created_at,
    }


@router.get("")
def get_activity(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    q = db.query(ActivityLog)
    is_manager = bool(me.role and me.role.name in MANAGER_ROLES)
    if not is_manager:
        q = q.filter(ActivityLog.actor_user_id == me.id)
    if action:
        q = q.filter(ActivityLog.action == action)
    if entity_type:
        q = q.filter(ActivityLog.entity_type == entity_type)
    rows = q.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return [serialize(e) for e in rows]
