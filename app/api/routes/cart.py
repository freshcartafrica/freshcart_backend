from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.cart import CartMutation, CartResponse
from app.services.cart import add_item_to_cart, get_or_create_cart, remove_item_from_cart, serialize_cart

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
def get_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return serialize_cart(get_or_create_cart(db, current_user))


@router.post("/add", response_model=CartResponse)
def add_cart_item(
    payload: CartMutation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cart = add_item_to_cart(db, current_user, payload.product_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return serialize_cart(cart)


@router.post("/remove", response_model=CartResponse)
def remove_cart_item(
    payload: CartMutation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = remove_item_from_cart(db, current_user, payload.product_id)
    return serialize_cart(cart)
