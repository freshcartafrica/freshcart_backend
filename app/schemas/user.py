from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class VendorStatusResponse(BaseModel):
    id: int
    business_name: str
    city: str
    is_verified: bool

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    vendor_profile: Optional[VendorStatusResponse] = None

    model_config = {"from_attributes": True}


class VendorUserSummary(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class VendorProfileResponse(BaseModel):
    id: int
    user_id: int
    business_name: str
    city: str
    is_verified: bool
    user: Optional[VendorUserSummary] = None

    model_config = {"from_attributes": True}


class VendorProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    city: Optional[str] = None
