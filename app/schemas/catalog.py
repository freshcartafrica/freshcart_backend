from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    vendor_id: int
    name: str
    slug: str
    description: str
    price: float
    unit: str
    stock_quantity: int
    image_url: Optional[str] = None
    is_active: bool
    featured: bool
    category: CategoryResponse

    model_config = {"from_attributes": True}


class CategoryUpsert(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    image_url: Optional[str] = None


class ProductUpsert(BaseModel):
    category_id: int
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    price: float = Field(gt=0)
    unit: str = Field(default="item", max_length=32)
    stock_quantity: int = Field(default=0, ge=0)
    image_url: Optional[str] = None
    featured: bool = False
