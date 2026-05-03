from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Order, User
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.services.orders import create_order_from_cart

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/create", response_model=OrderResponse)
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_order_from_cart(
            db,
            current_user,
            delivery_address=payload.delivery_address,
            payment_method=payload.payment_method,
            coupon_code=payload.coupon_code,
        )
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
