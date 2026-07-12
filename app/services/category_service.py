"""Asset category CRUD (Screen 3, Tab B)."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset_category import AssetCategory
from app.schemas.org import CategoryCreate, CategoryUpdate
from app.services import activity_service


def list_categories(db: Session) -> list[AssetCategory]:
    return db.query(AssetCategory).order_by(AssetCategory.name).all()


def get_category(db: Session, cat_id: int) -> AssetCategory:
    cat = db.query(AssetCategory).filter(AssetCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


def create_category(db: Session, data: CategoryCreate, actor_id: int | None = None) -> AssetCategory:
    if db.query(AssetCategory).filter(AssetCategory.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
    cat = AssetCategory(
        name=data.name,
        description=data.description,
        warranty_period_days=data.warranty_period_days,
        status="active",
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    activity_service.log_activity(db, actor_id, "category_created", "category", cat.id, cat.name)
    return cat


def update_category(db: Session, cat_id: int, data: CategoryUpdate) -> AssetCategory:
    cat = get_category(db, cat_id)
    if data.name is not None:
        if db.query(AssetCategory).filter(AssetCategory.name == data.name, AssetCategory.id != cat_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
        cat.name = data.name
    if data.description is not None:
        cat.description = data.description
    if data.warranty_period_days is not None:
        cat.warranty_period_days = data.warranty_period_days
    if data.status is not None:
        cat.status = data.status
    db.commit()
    db.refresh(cat)
    return cat
