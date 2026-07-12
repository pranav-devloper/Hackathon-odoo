"""Schemas for bookings (Screen 6)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BookingCreate(BaseModel):
    asset_id: int
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None


class BookingReschedule(BaseModel):
    start_time: datetime
    end_time: datetime


class BookingOut(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
