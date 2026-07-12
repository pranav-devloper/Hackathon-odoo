"""Reports & analytics aggregation (Screen 9).

All values are derived from existing tables — no new storage. Designed to be cheap
to compute for a demo dataset and trivially CSV-exportable.
"""
from collections import Counter

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.allocation import Allocation
from app.models.maintenance_ticket import MaintenanceTicket
from app.models.booking import Booking
from app.models.asset_category import AssetCategory
from app.models.department import Department


def _asset_label(db: Session, asset: Asset):
    cat = db.query(AssetCategory).filter(AssetCategory.id == asset.category_id).first()
    return asset.asset_tag, asset.name, cat.name if cat else None


def summary(db: Session) -> dict:
    assets = db.query(Asset).all()
    allocations = db.query(Allocation).all()
    tickets = db.query(MaintenanceTicket).all()
    bookings = db.query(Booking).all()

    # --- Utilization: allocation counts per asset ---
    alloc_counts = Counter(a.asset_id for a in allocations)
    used_rows = []
    idle_rows = []
    for asset in assets:
        tag, name, cat = _asset_label(db, asset)
        n = alloc_counts.get(asset.id, 0)
        row = {"asset_tag": tag, "name": name, "category_name": cat, "allocations": n}
        if n > 0:
            used_rows.append(row)
        elif asset.lifecycle_status == "available":
            idle_rows.append({"asset_tag": tag, "name": name, "category_name": cat})
    used_rows.sort(key=lambda r: r["allocations"], reverse=True)

    # --- Maintenance frequency by category ---
    cat_counts: Counter = Counter()
    cat_name = {}
    for t in tickets:
        asset = db.query(Asset).filter(Asset.id == t.asset_id).first()
        if asset:
            c = db.query(AssetCategory).filter(AssetCategory.id == asset.category_id).first()
            key = c.name if c else "Uncategorized"
            cat_counts[key] += 1
            cat_name[key] = key
    maintenance_by_category = [
        {"category_name": k, "tickets": v} for k, v in cat_counts.most_common()
    ]

    # --- Department-wise active allocation summary ---
    dept_counts: Counter = Counter()
    for a in allocations:
        if a.status != "active":
            continue
        asset = db.query(Asset).filter(Asset.id == a.asset_id).first()
        if asset and asset.department_id:
            d = db.query(Department).filter(Department.id == asset.department_id).first()
            dept_counts[d.name if d else "Unknown"] += 1
    department_allocation = [
        {"department_name": k, "allocations": v}
        for k, v in sorted(dept_counts.items(), key=lambda x: -x[1])
    ]

    # --- Booking heatmap by hour-of-day ---
    hour_counts = Counter(b.start_time.hour for b in bookings if b.start_time)
    booking_heatmap = [
        {"hour": h, "bookings": hour_counts.get(h, 0)} for h in range(24)
    ]

    # --- Due for maintenance / nearing retirement ---
    due_for_maintenance = [
        {"asset_tag": tag, "name": name, "category_name": cat}
        for asset in assets if asset.lifecycle_status == "under_maintenance"
        for tag, name, cat in [_asset_label(db, asset)]
    ]
    near_retirement = [
        {"asset_tag": tag, "name": name, "condition": asset.condition}
        for asset in assets if asset.condition in ("poor", "fair")
        for tag, name, _ in [_asset_label(db, asset)]
    ]

    totals = {
        "assets": len(assets),
        "allocations_active": sum(1 for a in allocations if a.status == "active"),
        "bookings_upcoming": sum(1 for b in bookings if b.status == "upcoming"),
        "maintenance_open": sum(1 for t in tickets if t.status in ("pending", "approved", "in_progress")),
    }

    return {
        "utilization": {"most_used": used_rows[:10], "idle": idle_rows},
        "maintenance_by_category": maintenance_by_category,
        "department_allocation": department_allocation,
        "booking_heatmap": booking_heatmap,
        "due_for_maintenance": due_for_maintenance,
        "near_retirement": near_retirement,
        "totals": totals,
    }


def _csv(headers, rows) -> str:
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow([r.get(h, "") for h in headers])
    return buf.getvalue()


def export_csv(db: Session, section: str = "all") -> str:
    """Return a CSV string for one section or all sections concatenated."""
    s = summary(db)
    parts = []

    if section in ("all", "utilization"):
        parts.append("== Most Used Assets ==\n" + _csv(
            ["asset_tag", "name", "category_name", "allocations"], s["utilization"]["most_used"]))
        parts.append("== Idle Assets ==\n" + _csv(
            ["asset_tag", "name", "category_name"], s["utilization"]["idle"]))

    if section in ("all", "maintenance_by_category"):
        parts.append("== Maintenance by Category ==\n" + _csv(
            ["category_name", "tickets"], s["maintenance_by_category"]))

    if section in ("all", "department_allocation"):
        parts.append("== Department Allocation ==\n" + _csv(
            ["department_name", "allocations"], s["department_allocation"]))

    if section in ("all", "booking_heatmap"):
        parts.append("== Booking Heatmap (by hour) ==\n" + _csv(
            ["hour", "bookings"], s["booking_heatmap"]))

    if section in ("all", "due_for_maintenance"):
        parts.append("== Due for Maintenance ==\n" + _csv(
            ["asset_tag", "name", "category_name"], s["due_for_maintenance"]))

    if section in ("all", "near_retirement"):
        parts.append("== Near Retirement ==\n" + _csv(
            ["asset_tag", "name", "condition"], s["near_retirement"]))

    return "\n".join(parts)
