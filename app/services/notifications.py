from __future__ import annotations

from typing import Iterable

from sqlalchemy.orm import Session

from app.models import Notification, User, UserRole


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    kind: str = "general",
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> Notification:
    notification = Notification(
      user_id=user_id,
      title=title,
      message=message,
      kind=kind,
      entity_type=entity_type,
      entity_id=entity_id,
    )
    db.add(notification)
    return notification


def notify_many(
    db: Session,
    *,
    user_ids: Iterable[int],
    title: str,
    message: str,
    kind: str = "general",
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> None:
    for user_id in set(user_ids):
        create_notification(
            db,
            user_id=user_id,
            title=title,
            message=message,
            kind=kind,
            entity_type=entity_type,
            entity_id=entity_id,
        )


def admin_user_ids(db: Session) -> list[int]:
    return [
        user_id
        for (user_id,) in db.query(User.id).filter(User.role == UserRole.admin, User.is_active.is_(True)).all()
    ]
