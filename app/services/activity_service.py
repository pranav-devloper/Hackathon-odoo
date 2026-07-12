"""Activity logging (Screen 10): the full "who did what, when" audit trail.

Every meaningful mutation in the app calls `log_activity` so the Activity Log
screen can replay admin/manager/employee actions. Reads are intentionally not logged.
"""
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


def log_activity(
    db: Session,
    actor_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    detail: str | None = None,
    commit: bool = True,
) -> ActivityLog:
    """Append one activity-log row. `commit` lets callers batch with a bigger transaction."""
    entry = ActivityLog(
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
