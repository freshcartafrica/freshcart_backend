from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models import Order, Product, User, UserRole
from app.schemas.catalog import ProductResponse, ProductUpsert
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.models.user import Vendor

router = APIRouter(prefix="/vendor", tags=["vendor"])


def _get_vendor_profile(db: Session, user: User) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.user_id == user.id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    return vendor


@router.get("/products", response_model=list[ProductResponse])
def list_vendor_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    return db.query(Product).filter(Product.vendor_id == vendor.id).order_by(Product.id.desc()).all()


@router.post("/products", response_model=ProductResponse)
def create_vendor_product(
    payload: ProductUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    slug = payload.name.lower().replace(" ", "-")
    product = Product(vendor_id=vendor.id, slug=f"{slug}-{vendor.id}", **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_vendor_product(
    product_id: int,
    payload: ProductUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    product = db.query(Product).filter(Product.id == product_id, Product.vendor_id == vendor.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_vendor_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    product = db.query(Product).filter(Product.id == product_id, Product.vendor_id == vendor.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Deleted"}


@router.get("/orders", response_model=list[OrderResponse])
def list_vendor_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    return db.query(Order).filter(Order.vendor_id == vendor.id).order_by(Order.created_at.desc()).all()


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_vendor_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    order = db.query(Order).filter(Order.id == order_id, Order.vendor_id == vendor.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
