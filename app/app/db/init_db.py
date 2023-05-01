import logging

from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.core.security import get_password_hash
from app.db import base  # noqa: F401
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def create_super_admin(db: Session) -> None:
    user = (
        db.query(models.User)
        .filter(models.User.email == settings.FIRST_SUPERUSER)
        .first()
    )

    if not user:
        user = models.User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(
                settings.FIRST_SUPERUSER_PASSWORD
            ),
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)


def init_db(db: Session) -> None:
    create_super_admin(db)


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
