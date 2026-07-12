"""Pydantic schemas for organization setup (Screen 3): departments, categories, employees."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Departments ----------
class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    head_id: Optional[int] = None
    parent_id: Optional[int] = None
    status: str = "active"  # active | inactive


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    head_id: Optional[int] = None
    parent_id: Optional[int] = None
    status: Optional[str] = None  # active | inactive


class DepartmentOut(BaseModel):
    id: int
    name: str
    head_id: Optional[int] = None
    head_name: Optional[str] = None
    parent_id: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Asset categories ----------
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    warranty_period_days: Optional[int] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    warranty_period_days: Optional[int] = None
    status: Optional[str] = None  # active | inactive


class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    warranty_period_days: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Employees (directory / role assignment) ----------
class EmployeeOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class EmployeeUpdate(BaseModel):
    # The ONLY place roles are assigned. Admins promote employees here.
    role: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
