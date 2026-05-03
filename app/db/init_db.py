from app.core.database import Base, SessionLocal, engine
from app.models import *  # noqa: F403
from app.services.seed import seed_database


def init() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    init()
