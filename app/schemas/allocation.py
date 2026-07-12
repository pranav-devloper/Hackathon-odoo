"""Schemas for allocation, transfer, and notifications (Screens 5 & 10)."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Allocation ----------
class AllocationCreate(BaseModel):
    asset_id: int
    holder_user_id: int
    expected_return_date: Optional[date] = None


class AllocationReturn(BaseModel):
    condition_notes: Optional[str] = None


class AllocationOut(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    holder_user_id: int
    holder_name: Optional[str] = None
    expected_return_date: Optional[date] = None
    status: str
    is_overdue: bool = False
    condition_notes: Optional[str] = None
    returned_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Transfer ----------
class TransferCreate(BaseModel):
    asset_id: int
    to_user_id: int
    expected_return_date: Optional[date] = None
    note: Optional[str] = None


class TransferOut(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    from_user_id: Optional[int] = None
    from_name: Optional[str] = None
    to_user_id: int
    to_name: Optional[str] = None
    requested_by: int
    status: str
    note: Optional[str] = None
    expected_return_date: Optional[date] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------- Notification ----------
class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Returned by the 409 conflict when allocating an already-held asset.
class AllocationConflict(BaseModel):
    detail: str
    holder_user_id: int
    holder_name: Optional[str] = None
