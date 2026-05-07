from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Order, User
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.services.notifications import admin_user_ids, notify_many
from app.services.orders import create_order_from_cart

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/create", response_model=OrderResponse)
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        order = create_order_from_cart(
            db,
            current_user,
            delivery_address=payload.delivery_address,
            payment_method=payload.payment_method,
            coupon_code=payload.coupon_code,
        )
        notify_many(
            db,
            user_ids=[current_user.id],
            title="Order placed successfully",
            message=f"Your order #{order.id} has been created and is waiting for vendor confirmation.",
            kind="order_created",
            entity_type="order",
            entity_id=order.id,
        )
        notify_many(
            db,
            user_ids=[order.vendor.user_id],
            title="New customer order",
            message=f"A new order #{order.id} is ready for fulfillment.",
            kind="vendor_order",
            entity_type="order",
            entity_id=order.id,
        )
        notify_many(
            db,
            user_ids=admin_user_ids(db),
            title="Marketplace order placed",
            message=f"Order #{order.id} was placed by {current_user.full_name}.",
            kind="admin_order",
            entity_type="order",
            entity_id=order.id,
        )
        db.commit()
        db.refresh(order)
        return order
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
