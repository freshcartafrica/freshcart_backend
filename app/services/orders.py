from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Cart, Order, OrderItem, OrderStatus, Product, User


def create_order_from_cart(
    db: Session,
    user: User,
    delivery_address: str,
    payment_method: str,
    coupon_code: Optional[str],
) -> Order:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise ValueError("Cart is empty")

    subtotal = 0.0
    vendor_id = cart.items[0].product.vendor_id
    for item in cart.items:
        subtotal += float(item.product.price) * item.quantity

    delivery_fee = 2.5 if subtotal < 25 else 1.0
    discount_amount = round(subtotal * 0.1, 2) if coupon_code and coupon_code.upper() == "SAVE10" else 0.0

    order = Order(
        user_id=user.id,
        vendor_id=vendor_id,
        status=OrderStatus.pending,
        delivery_address=delivery_address,
        payment_method=payment_method,
        coupon_code=coupon_code,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount_amount=discount_amount,
        total_amount=subtotal + delivery_fee - discount_amount,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.flush()

    for item in cart.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=float(item.product.price),
            )
        )

    for item in list(cart.items):
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order
