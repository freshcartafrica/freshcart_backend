from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class OrderCreateRequest(BaseModel):
    delivery_address: str = Field(min_length=5)
    payment_method: str = "pay_on_delivery"
    coupon_code: Optional[str] = None


class OrderItemResponse(BaseModel):
    product_name: str
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    delivery_address: str
    payment_method: str
    coupon_code: Optional[str]
    subtotal: float
    delivery_fee: float
    discount_amount: float
    total_amount: float
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
