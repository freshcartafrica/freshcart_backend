from fastapi import APIRouter

from app.api.routes import admin, auth, cart, catalog, orders, users, vendor

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(admin.router)
api_router.include_router(vendor.router)
