"""Pydantic schemas for maintenance tickets (Screen 7)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MaintenanceCreate(BaseModel):
    asset_id: int
    issue: str = Field(..., min_length=1)
    priority: str = "medium"  # low | medium | high | urgent
    photo_path: Optional[str] = None


class MaintenanceReject(BaseModel):
    reason: Optional[str] = None


class MaintenanceAssign(BaseModel):
    tech: str = Field(..., min_length=1)


class MaintenanceOut(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    reporter_id: int
    reporter_name: Optional[str] = None
    issue: str
    priority: str
    status: str
    assigned_tech: Optional[str] = None
    rejected_reason: Optional[str] = None
    photo_path: Optional[str] = None
    approved_by: Optional[int] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
