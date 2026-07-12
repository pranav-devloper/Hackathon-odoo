"""Asset + dashboard routes (Screens 2 & 4)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_roles
from app.models.user import User
from app.schemas.assets import (
    AssetCreate, AssetOut, AssetUpdate, AssetDetailOut,
    AllocationHistoryItem, MaintenanceHistoryItem, DashboardKPIs,
)
from app.services import asset_service, dashboard_service

router = APIRouter(prefix="/assets", tags=["assets"])
dashboard_router = APIRouter(tags=["dashboard"])


def serialize_asset(a) -> AssetOut:
    return AssetOut(
        id=a.id, asset_tag=a.asset_tag, name=a.name, category_id=a.category_id,
        category_name=a.category.name if a.category else None,
        serial_number=a.serial_number, acquisition_date=a.acquisition_date,
        acquisition_cost=float(a.acquisition_cost) if a.acquisition_cost is not None else None,
        condition=a.condition, location=a.location, department_id=a.department_id,
        holder_user_id=a.holder_user_id, lifecycle_status=a.lifecycle_status,
        is_bookable=a.is_bookable, image_path=a.image_path, created_at=a.created_at,
    )


@router.get("", response_model=list[AssetOut])
def get_assets(
    tag: Optional[str] = None,
    serial: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    department_id: Optional[int] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = {
        "tag": tag, "serial": serial, "category_id": category_id,
        "status": status, "department_id": department_id,
        "location": location, "search": search,
    }
    return [serialize_asset(a) for a in asset_service.list_assets(db, filters)]


@router.post("", response_model=AssetOut, status_code=201)
def post_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("asset_manager", "admin")),
):
    return serialize_asset(asset_service.register_asset(db, data))


@router.get("/{asset_id}", response_model=AssetDetailOut)
def get_asset_detail(asset_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    asset, allocations, tickets = asset_service.get_asset_detail(db, asset_id)
    holder_names = {}
    alloc_items = []
    for al in allocations:
        if al.holder_user_id not in holder_names:
            u = db.query(User).filter(User.id == al.holder_user_id).first()
            holder_names[al.holder_user_id] = u.full_name if u else None
        alloc_items.append(AllocationHistoryItem(
            id=al.id, holder_user_id=al.holder_user_id,
            holder_name=holder_names[al.holder_user_id],
            expected_return_date=al.expected_return_date,
            status=al.status, created_at=al.created_at,
        ))
    maint_items = [
        MaintenanceHistoryItem(
            id=t.id, issue=t.issue, priority=t.priority,
            status=t.status, assigned_tech=t.assigned_tech, created_at=t.created_at,
        )
        for t in tickets
    ]
    return AssetDetailOut(asset=serialize_asset(asset), allocation_history=alloc_items, maintenance_history=maint_items)


@router.patch("/{asset_id}", response_model=AssetOut)
def patch_asset(
    asset_id: int, data: AssetUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("asset_manager", "admin")),
):
    return serialize_asset(asset_service.update_asset(db, asset_id, data))


@dashboard_router.get("/dashboard", response_model=DashboardKPIs)
def get_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return DashboardKPIs(**dashboard_service.compute_kpis(db))
