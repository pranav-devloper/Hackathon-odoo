"""Asset registration, directory, and history (Screen 4)."""
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.asset import Asset, LIFECYCLE_STATUSES
from app.models.asset_category import AssetCategory
from app.models.department import Department
from app.models.allocation import Allocation
from app.models.user import User
from app.models.maintenance_ticket import MaintenanceTicket

# Asset condition vocabulary (Screen 4).
ALLOWED_CONDITIONS = {"new", "good", "fair", "poor"}


def _next_tag(db: Session) -> str:
    """Auto-generate the next asset tag, e.g. AF-0001."""
    last = db.query(Asset).order_by(Asset.id.desc()).first()
    n = (last.id if last else 0) + 1
    return f"AF-{n:04d}"


def register_asset(db: Session, data) -> Asset:
    if not db.query(AssetCategory).filter(AssetCategory.id == data.category_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if data.department_id is not None:
        if not db.query(Department).filter(Department.id == data.department_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if data.condition not in ALLOWED_CONDITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid condition. Must be one of: {', '.join(sorted(ALLOWED_CONDITIONS))}",
        )
    asset = Asset(
        asset_tag=_next_tag(db),
        name=data.name,
        category_id=data.category_id,
        serial_number=data.serial_number,
        acquisition_date=data.acquisition_date,
        acquisition_cost=Decimal(str(data.acquisition_cost)) if data.acquisition_cost is not None else None,
        condition=data.condition,
        location=data.location,
        department_id=data.department_id,
        is_bookable=data.is_bookable,
        image_path=data.image_path,
        lifecycle_status="available",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def list_assets(db: Session, filters: dict) -> list[Asset]:
    q = db.query(Asset)
    if filters.get("tag"):
        q = q.filter(Asset.asset_tag.contains(filters["tag"]))
    if filters.get("serial"):
        q = q.filter(Asset.serial_number.contains(filters["serial"]))
    if filters.get("category_id") is not None:
        q = q.filter(Asset.category_id == filters["category_id"])
    if filters.get("status"):
        q = q.filter(Asset.lifecycle_status == filters["status"])
    if filters.get("department_id") is not None:
        q = q.filter(Asset.department_id == filters["department_id"])
    if filters.get("location"):
        q = q.filter(Asset.location.contains(filters["location"]))
    search = filters.get("search")
    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                Asset.name.contains(search),
                Asset.asset_tag.contains(search),
                Asset.serial_number.contains(search),
                Asset.location.contains(search),
            )
        )
    return q.order_by(Asset.asset_tag).all()


def get_asset(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


def update_asset(db: Session, asset_id: int, data) -> Asset:
    asset = get_asset(db, asset_id)
    # exclude_unset => only fields the client actually sent are present, so we
    # can apply each one directly (explicit nulls intentionally clear a value).
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "acquisition_cost" and value is not None:
            value = Decimal(str(value))
        if field == "condition" and value not in ALLOWED_CONDITIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid condition. Must be one of: {', '.join(sorted(ALLOWED_CONDITIONS))}",
            )
        if field == "lifecycle_status" and value not in LIFECYCLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid lifecycle status. Must be one of: {', '.join(LIFECYCLE_STATUSES)}",
            )
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


def get_asset_detail(db: Session, asset_id: int):
    """Asset + allocation history + maintenance history (Screen 4 history views)."""
    asset = get_asset(db, asset_id)
    allocations = (
        db.query(Allocation)
        .filter(Allocation.asset_id == asset_id)
        .order_by(Allocation.created_at.desc())
        .all()
    )
    tickets = (
        db.query(MaintenanceTicket)
        .filter(MaintenanceTicket.asset_id == asset_id)
        .order_by(MaintenanceTicket.created_at.desc())
        .all()
    )
    return asset, allocations, tickets
