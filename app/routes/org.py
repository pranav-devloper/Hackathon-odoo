"""Organization setup routes (Screen 3) — Admin only.

Departments, asset categories, and the employee directory. The employee directory
is the ONLY place roles are assigned (admin promotes employees here).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.roles import require_role
from app.models.user import User
from app.schemas.org import (
    DepartmentCreate, DepartmentOut, DepartmentUpdate,
    CategoryCreate, CategoryOut, CategoryUpdate,
    EmployeeOut, EmployeeUpdate,
)
from app.services import department_service, category_service, employee_service

router = APIRouter(prefix="/org", tags=["org"])


def serialize_department(d) -> DepartmentOut:
    return DepartmentOut(
        id=d.id, name=d.name, head_id=d.head_id,
        head_name=d.head.full_name if d.head else None,
        parent_id=d.parent_id, status=d.status, created_at=d.created_at,
    )


def serialize_employee(u) -> EmployeeOut:
    return EmployeeOut(
        id=u.id, full_name=u.full_name, email=u.email,
        department_id=u.department_id,
        department_name=u.department.name if u.department else None,
        role=u.role.name if u.role else "user",
        is_active=u.is_active,
    )


# ---------- Departments ----------
@router.get("/departments", response_model=list[DepartmentOut])
def get_departments(db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return [serialize_department(d) for d in department_service.list_departments(db)]


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def post_department(data: DepartmentCreate, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return serialize_department(department_service.create_department(db, data))


@router.patch("/departments/{dept_id}", response_model=DepartmentOut)
def patch_department(dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return serialize_department(department_service.update_department(db, dept_id, data))


# ---------- Asset categories ----------
@router.get("/asset-categories", response_model=list[CategoryOut])
def get_categories(db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return category_service.list_categories(db)


@router.post("/asset-categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def post_category(data: CategoryCreate, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return category_service.create_category(db, data)


@router.patch("/asset-categories/{cat_id}", response_model=CategoryOut)
def patch_category(cat_id: int, data: CategoryUpdate, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return category_service.update_category(db, cat_id, data)


# ---------- Employees (directory + role assignment) ----------
@router.get("/employees", response_model=list[EmployeeOut])
def get_employees(db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    return [serialize_employee(u) for u in employee_service.list_employees(db)]


@router.patch("/employees/{user_id}", response_model=EmployeeOut)
def patch_employee(user_id: int, data: EmployeeUpdate, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    user = employee_service.get_employee(db, user_id)
    if data.role is not None:
        user = employee_service.set_role(db, user_id, data.role)
    if data.department_id is not None:
        user = employee_service.set_department(db, user_id, data.department_id)
    if data.is_active is not None:
        user = employee_service.set_status(db, user_id, data.is_active)
    return serialize_employee(user)
