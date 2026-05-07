from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_role
from app.models import Order, Product, User, UserRole, Vendor
from app.schemas.admin import AnalyticsResponse
from app.schemas.auth import MessageResponse
from app.schemas.catalog import ProductResponse
from app.schemas.order import OrderResponse
from app.schemas.user import UserResponse, VendorProfileResponse
from app.services.notifications import notify_many

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/orders", response_model=list[OrderResponse])
def list_all_orders(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    today = date.today()
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0)
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    daily_active_users = active_users
    orders_today = (
        db.query(func.count(Order.id)).filter(func.date(Order.created_at) == today.isoformat()).scalar() or 0
    )
    conversion_rate = round((total_orders / active_users) * 100, 2) if active_users else 0
    return AnalyticsResponse(
        total_orders=total_orders,
        total_revenue=total_revenue,
        active_users=active_users,
        daily_active_users=daily_active_users,
        orders_today=orders_today,
        conversion_rate=conversion_rate,
    )


@router.get("/vendors", response_model=list[VendorProfileResponse])
def list_vendors(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return db.query(Vendor).options(joinedload(Vendor.user)).order_by(Vendor.id.desc()).all()


@router.put("/vendors/{vendor_id}/approve", response_model=VendorProfileResponse)
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    vendor = db.query(Vendor).options(joinedload(Vendor.user)).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.is_verified = True
    db.commit()
    db.refresh(vendor)
    notify_many(
        db,
        user_ids=[vendor.user_id],
        title="Vendor account approved",
        message="Your vendor profile has been approved. You can now receive orders and submit live inventory.",
        kind="vendor_approved",
        entity_type="vendor",
        entity_id=vendor.id,
    )
    db.commit()
    return vendor


@router.get("/products/pending", response_model=list[ProductResponse])
def list_pending_products(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.is_active.is_(False))
        .order_by(Product.id.desc())
        .all()
    )


@router.put("/products/{product_id}/approve", response_model=ProductResponse)
def approve_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    product = db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = True
    db.commit()
    db.refresh(product)
    notify_many(
        db,
        user_ids=[product.vendor.user_id],
        title="Product approved",
        message=f"{product.name} has been approved and is now visible to customers.",
        kind="product_approved",
        entity_type="product",
        entity_id=product.id,
    )
    db.commit()
    return product


@router.delete("/products/{product_id}", response_model=MessageResponse)
def reject_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    vendor_user_id = product.vendor.user_id
    product_name = product.name
    db.delete(product)
    db.commit()
    notify_many(
        db,
        user_ids=[vendor_user_id],
        title="Product rejected",
        message=f"{product_name} was rejected during admin review and has been removed from the catalog.",
        kind="product_rejected",
        entity_type="product",
        entity_id=product_id,
    )
    db.commit()
    return MessageResponse(message="Product rejected")
