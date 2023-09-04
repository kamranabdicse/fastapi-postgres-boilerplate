from typing import Any
from typing import Generator

import pytest
from app.api.api_v1.api import api_router
from app.api.deps import get_db
from app.core.config import settings
from app.db.base_class import Base
from app.db.init_db import init_db
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker




def start_application():
    app = FastAPI()
    app.include_router(api_router)
    return app


engine = create_engine(settings.SQLALCHEMY_TEST_DATABASE_URI, pool_pre_ping=True)
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case.
    """
    Base.metadata.create_all(engine)
    _app = start_application()
    yield _app
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def db_session(app: FastAPI) -> Generator[SessionTesting, Any, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)

    yield session  # use the session in tests.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def client(
        app: FastAPI, db_session: SessionTesting
) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    init_db(db=db_session)

    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app) as client:
        yield client
