"""Role model for role-based access control (RBAC)."""
from sqlalchemy import Column, Integer, String, Text

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.name}>"
