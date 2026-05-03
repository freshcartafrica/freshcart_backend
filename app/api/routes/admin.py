from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models import Order, User, UserRole
from app.schemas.admin import AnalyticsResponse
from app.schemas.order import OrderResponse
from app.schemas.user import UserResponse

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
