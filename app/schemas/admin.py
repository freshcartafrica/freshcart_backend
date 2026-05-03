from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    active_users: int
    daily_active_users: int
    orders_today: int
    conversion_rate: float
