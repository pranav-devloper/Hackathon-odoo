"""Role-based authorization dependencies."""
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User


def require_role(required_role: str):
    """Dependency factory: allow only users whose role matches `required_role`."""
    def checker(user: User = Depends(get_current_user)) -> User:
        role_name = user.role.name if user.role else None
        if role_name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{required_role}' role",
            )
        return user
    return checker


def require_roles(*required_roles: str):
    """Dependency factory: allow users whose role is in `required_roles`."""
    def checker(user: User = Depends(get_current_user)) -> User:
        role_name = user.role.name if user.role else None
        if role_name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}",
            )
        return user
    return checker
