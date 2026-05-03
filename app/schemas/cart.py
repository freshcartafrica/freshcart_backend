from typing import Optional

from pydantic import BaseModel, Field


class CartMutation(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product_name: str
    unit_price: float
    image_url: Optional[str] = None


class CartResponse(BaseModel):
    id: int
    items: list[CartItemResponse]
    subtotal: float
