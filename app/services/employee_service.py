"""Employee directory + role assignment (Screen 3, Tab C).

IMPORTANT: this is the ONLY place roles are assigned. Admins promote employees
to Department Head / Asset Manager here; signup never offers a role.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.models.department import Department

ALLOWED_ROLES = {"user", "department_head", "asset_manager", "admin"}


def list_employees(db: Session) -> list[User]:
    return db.query(User).order_by(User.full_name).all()


def get_employee(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return user


def set_role(db: Session, user_id: int, role_name: str) -> User:
    if role_name not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    user = get_employee(db, user_id)
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Role not seeded")
    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user


def set_department(db: Session, user_id: int, department_id: int | None) -> User:
    user = get_employee(db, user_id)
    if department_id is not None:
        if not db.query(Department).filter(Department.id == department_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    user.department_id = department_id
    db.commit()
    db.refresh(user)
    return user


def set_status(db: Session, user_id: int, is_active: bool) -> User:
    user = get_employee(db, user_id)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
