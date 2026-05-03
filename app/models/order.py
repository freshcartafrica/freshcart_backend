from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    status: Mapped[OrderStatus] = mapped_column(SqlEnum(OrderStatus), default=OrderStatus.pending)
    delivery_address: Mapped[str] = mapped_column(Text)
    payment_method: Mapped[str] = mapped_column(String(60), default="pay_on_delivery")
    coupon_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    delivery_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    vendor = relationship("Vendor", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
