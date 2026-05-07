from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.cache import get_redis_client
from app.core.config import get_settings
from app.db.init_db import init

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init()


@app.get("/health")
def health():
    return {"status": "ok", "redis": bool(get_redis_client())}


app.include_router(api_router)
