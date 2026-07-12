"""Department CRUD (Screen 3, Tab A)."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.user import User
from app.schemas.org import DepartmentCreate, DepartmentUpdate
from app.services import activity_service


def list_departments(db: Session) -> list[Department]:
    return db.query(Department).order_by(Department.name).all()


def get_department(db: Session, dept_id: int) -> Department:
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept


def create_department(db: Session, data: DepartmentCreate, actor_id: int | None = None) -> Department:
    if db.query(Department).filter(Department.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name already exists")
    if data.head_id is not None:
        if not db.query(User).filter(User.id == data.head_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Head user not found")
    if data.parent_id is not None:
        if not db.query(Department).filter(Department.id == data.parent_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent department not found")
    dept = Department(name=data.name, head_id=data.head_id, parent_id=data.parent_id, status=data.status)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    activity_service.log_activity(db, actor_id, "department_created", "department", dept.id, dept.name)
    return dept


def update_department(db: Session, dept_id: int, data: DepartmentUpdate) -> Department:
    dept = get_department(db, dept_id)
    if data.name is not None:
        if db.query(Department).filter(Department.name == data.name, Department.id != dept_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name already exists")
        dept.name = data.name
    if data.head_id is not None:
        dept.head_id = data.head_id
    if data.parent_id is not None:
        dept.parent_id = data.parent_id
    if data.status is not None:
        dept.status = data.status
    db.commit()
    db.refresh(dept)
    return dept
