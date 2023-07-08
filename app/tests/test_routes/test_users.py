import json

from app import models
from app.core.config import settings

def test_login_access_token(client, db_session):
    data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD
    }

    response = client.post("users/login/access-token", data=data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()