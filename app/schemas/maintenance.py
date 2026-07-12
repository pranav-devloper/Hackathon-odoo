"""Schemas for maintenance tickets (Screen 7, history in Screen 4).

One ticket tracks a single reported fault against an asset. Tickets move through
pending -> in_progress -> resolved | rejected. Opening a ticket puts the asset
Under Maintenance; resolving/rejecting returns it to its prior state.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Allowed values — shared with the service so validation lives in one place.
PRIORITIES = ["low", "medium", "high", "urgent"]
STATUSES = ["pending", "in_progress", "resolved", "rejected"]


class MaintenanceTicketCreate(BaseModel):
    asset_id: int
    issue: str = Field(..., min_length=1, max_length=2000)
    priority: str = "medium"  # low | medium | high | urgent
    assigned_tech: Optional[str] = Field(None, max_length=255)


class MaintenanceTicketUpdate(BaseModel):
    # Manager-only. Partial update — only provided fields are applied.
    status: Optional[str] = None       # pending | in_progress | resolved | rejected
    priority: Optional[str] = None     # low | medium | high | urgent
    assigned_tech: Optional[str] = Field(None, max_length=255)
    resolution: Optional[str] = Field(None, max_length=2000)


class MaintenanceTicketOut(BaseModel):
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
    resolution: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
