from sqlalchemy import or_
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import Category, Product
from app.schemas.catalog import CategoryResponse, ProductResponse

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
