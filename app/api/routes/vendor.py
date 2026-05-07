from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models import Order, Product, User, UserRole
from app.schemas.catalog import ProductResponse, ProductUpsert
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.user import VendorProfileResponse, VendorProfileUpdate
from app.models.user import Vendor
from app.services.notifications import admin_user_ids, notify_many

router = APIRouter(prefix="/vendor", tags=["vendor"])


def _get_vendor_profile(db: Session, user: User) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.user_id == user.id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    return vendor


def _ensure_verified_vendor(vendor: Vendor) -> None:
    if not vendor.is_verified:
        raise HTTPException(status_code=403, detail="Vendor registration is pending admin approval")


@router.get("/profile", response_model=VendorProfileResponse)
def get_vendor_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    return _get_vendor_profile(db, current_user)


@router.put("/profile", response_model=VendorProfileResponse)
def update_vendor_profile(
    payload: VendorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor)),
):
    vendor = _get_vendor_profile(db, current_user)
    if payload.business_name:
        vendor.business_name = payload.business_name.strip()
    if payload.city:
        vendor.city = payload.city.strip()
    db.commit()
    db.refresh(vendor)
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
    _ensure_verified_vendor(vendor)
    slug = payload.name.lower().replace(" ", "-")
    product = Product(vendor_id=vendor.id, slug=f"{slug}-{vendor.id}", is_active=False, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    notify_many(
        db,
        user_ids=[current_user.id],
        title="Product submitted",
        message=f"{product.name} has been submitted for admin approval.",
        kind="product_submitted",
        entity_type="product",
        entity_id=product.id,
    )
    notify_many(
        db,
        user_ids=admin_user_ids(db),
        title="Product awaiting approval",
        message=f"{current_user.full_name} submitted {product.name} for approval.",
        kind="admin_product_review",
        entity_type="product",
        entity_id=product.id,
    )
    db.commit()
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_vendor_product(
    product_id: int,
    payload: ProductUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    _ensure_verified_vendor(vendor)
    product = db.query(Product).filter(Product.id == product_id, Product.vendor_id == vendor.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    product.is_active = False
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
    _ensure_verified_vendor(vendor)
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
    _ensure_verified_vendor(vendor)
    return db.query(Order).filter(Order.vendor_id == vendor.id).order_by(Order.created_at.desc()).all()


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_vendor_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.vendor, UserRole.admin)),
):
    vendor = _get_vendor_profile(db, current_user)
    _ensure_verified_vendor(vendor)
    order = db.query(Order).filter(Order.id == order_id, Order.vendor_id == vendor.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    notify_many(
        db,
        user_ids=[order.user_id, current_user.id],
        title="Order status updated",
        message=f"Order #{order.id} is now {str(order.status).replace('_', ' ')}.",
        kind="order_status",
        entity_type="order",
        entity_id=order.id,
    )
    db.commit()
    return order
