"""Dashboard KPI computation (Screen 2).

Phase 1 computed asset-based KPIs. Phase 2 adds real allocation/transfer/return
counts. Booking KPIs remain 0 until Phase 3.
"""
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.services import allocation_service, transfer_service, notification_service


def compute_kpis(db: Session) -> dict:
    # Refresh overdue notifications whenever the dashboard is viewed.
    notification_service.scan_overdue(db)

    assets = db.query(Asset).all()
    return {
        "assets_available": sum(1 for a in assets if a.lifecycle_status == "available"),
        "assets_allocated": sum(1 for a in assets if a.lifecycle_status == "allocated"),
        "under_maintenance": sum(1 for a in assets if a.lifecycle_status == "under_maintenance"),
        "active_bookings": 0,  # Phase 3
        "pending_transfers": transfer_service.count_pending(db),
        "upcoming_returns": allocation_service.count_upcoming(db),
        "overdue_returns": allocation_service.count_overdue(db),
    }
