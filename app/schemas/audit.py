"""Pydantic schemas for audit cycles & items (Screen 8)."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AuditCycleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scope_type: str = "department"  # department | location
    scope_value: str
    auditors: List[int] = []
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AuditCycleUpdate(BaseModel):
    auditors: List[int] = []


class AuditItemMark(BaseModel):
    result: str  # verified | missing | damaged
    note: Optional[str] = None


class AuditItemOut(BaseModel):
    id: int
    cycle_id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    result: Optional[str] = None
    note: Optional[str] = None
    audited_by: Optional[int] = None
    audited_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditCycleOut(BaseModel):
    id: int
    name: str
    scope_type: str
    scope_value: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    auditors: List[int] = []
    created_by: Optional[int] = None
    created_at: datetime
    closed_at: Optional[datetime] = None
    item_count: int = 0
    verified_count: int = 0
    missing_count: int = 0
    damaged_count: int = 0

    model_config = {"from_attributes": True}


class AuditCycleDetailOut(BaseModel):
    cycle: AuditCycleOut
    items: List[AuditItemOut] = []
    discrepancies: List[AuditItemOut] = []
