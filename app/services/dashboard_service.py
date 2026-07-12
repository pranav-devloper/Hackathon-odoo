"""Dashboard KPI computation (Screen 2).

Real-time operational snapshot: asset states, open transfers, returns due soon
or overdue, and live booking counts. Booking statuses are refreshed from the
clock before counting, and stale notifications (overdue / reminders) are swept.
"""
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.services import (
    allocation_service,
    transfer_service,
    notification_service,
    booking_service,
)


def compute_kpis(db: Session) -> dict:
    # Refresh derived state before counting.
    booking_service.refresh_statuses(db)
    booking_service.scan_reminders(db)
    notification_service.scan_overdue(db)

    assets = db.query(Asset).all()
    return {
        "assets_available": sum(1 for a in assets if a.lifecycle_status == "available"),
        "assets_allocated": sum(1 for a in assets if a.lifecycle_status == "allocated"),
        "under_maintenance": sum(1 for a in assets if a.lifecycle_status == "under_maintenance"),
        "active_bookings": booking_service.count_active(db),
        "pending_transfers": transfer_service.count_pending(db),
        "upcoming_returns": allocation_service.count_upcoming(db),
        "overdue_returns": allocation_service.count_overdue(db),
    }
