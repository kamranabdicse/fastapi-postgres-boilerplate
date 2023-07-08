from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, drop_database

from app.db.base import Base
from app.models.user import User
from app.core.config import settings


engine = create_engine(settings.SQLALCHEMY_TEST_DATABASE_URI, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_testing_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def test_create_user():
    user = User(
        full_name="test user",
        email="test@mail.com",
        hashed_password="password",
    )

    db = next(setup_test_db())
    db.add(user)
    db.commit()


    retrieved_user = db.query(User).filter(User.id == user.id).first()

    assert retrieved_user is not None
    assert retrieved_user.full_name == "test user"
    assert retrieved_user.email == "test@mail.com"
    assert not retrieved_user.is_superuser
    assert retrieved_user.is_active

    db.delete(user)
    db.commit()