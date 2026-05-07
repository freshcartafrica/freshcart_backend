from sqlalchemy import or_
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import require_role
from app.core.database import get_db
from app.models import Category, Product, User, UserRole
from app.schemas.catalog import CategoryResponse, CategoryUpsert, ProductResponse
from app.schemas.auth import MessageResponse

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name.asc()).all()


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    featured: Optional[bool] = Query(default=None),
):
    query = db.query(Product).options(joinedload(Product.category)).filter(Product.is_active.is_(True))
    if category:
        query = query.join(Category).filter(Category.slug == category)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Product.name.ilike(term), Product.description.ilike(term)))
    if featured is not None:
        query = query.filter(Product.featured.is_(featured))
    return query.order_by(Product.id.desc()).all()


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryUpsert,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    slug = payload.name.strip().lower().replace("&", "and").replace(" ", "-")
    existing = db.query(Category).filter((Category.name == payload.name.strip()) | (Category.slug == slug)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category = Category(name=payload.name.strip(), slug=slug, image_url=payload.image_url)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpsert,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    slug = payload.name.strip().lower().replace("&", "and").replace(" ", "-")
    existing = db.query(Category).filter(Category.id != category_id, ((Category.name == payload.name.strip()) | (Category.slug == slug))).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category.name = payload.name.strip()
    category.slug = slug
    category.image_url = payload.image_url
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", response_model=MessageResponse)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.products:
        raise HTTPException(status_code=400, detail="Remove products from this category before deleting it")

    db.delete(category)
    db.commit()
    return MessageResponse(message="Category deleted")
