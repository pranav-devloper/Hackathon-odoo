"""Pydantic schemas for assets (Screen 4) and the dashboard KPIs (Screen 2)."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Assets ----------
class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_id: int
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = None
    condition: str = "new"  # new | good | fair | poor
    location: Optional[str] = None
    department_id: Optional[int] = None
    is_bookable: bool = False
    image_path: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    is_bookable: Optional[bool] = None
    image_path: Optional[str] = None
    lifecycle_status: Optional[str] = None


class AssetOut(BaseModel):
    id: int
    asset_tag: str
    name: str
    category_id: int
    category_name: Optional[str] = None
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = None
    condition: str
    location: Optional[str] = None
    department_id: Optional[int] = None
    holder_user_id: Optional[int] = None
    lifecycle_status: str
    is_bookable: bool
    image_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AllocationHistoryItem(BaseModel):
    id: int
    holder_user_id: int
    holder_name: Optional[str] = None
    expected_return_date: Optional[date] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenanceHistoryItem(BaseModel):
    id: int
    issue: str
    priority: str
    status: str
    assigned_tech: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetDetailOut(BaseModel):
    asset: AssetOut
    allocation_history: List[AllocationHistoryItem] = []
    maintenance_history: List[MaintenanceHistoryItem] = []


# ---------- Dashboard KPIs ----------
class DashboardKPIs(BaseModel):
    assets_available: int = 0
    assets_allocated: int = 0
    under_maintenance: int = 0
    active_bookings: int = 0       # populated in Phase 3
    pending_transfers: int = 0     # populated in Phase 2
    upcoming_returns: int = 0      # populated in Phase 2
    overdue_returns: int = 0       # populated in Phase 2
