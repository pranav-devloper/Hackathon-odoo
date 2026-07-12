"""Dashboard KPI computation (Screen 2).

Phase 1 computes asset-based KPIs from real data. Booking/transfer/return KPIs
are 0 until their phases (2–3) add the underlying records.
"""
from sqlalchemy.orm import Session

from app.models.asset import Asset


def compute_kpis(db: Session) -> dict:
    assets = db.query(Asset).all()
    return {
        "assets_available": sum(1 for a in assets if a.lifecycle_status == "available"),
        "assets_allocated": sum(1 for a in assets if a.lifecycle_status == "allocated"),
        "under_maintenance": sum(1 for a in assets if a.lifecycle_status == "under_maintenance"),
        "active_bookings": 0,       # Phase 3
        "pending_transfers": 0,     # Phase 2
        "upcoming_returns": 0,      # Phase 2
        "overdue_returns": 0,       # Phase 2
    }
