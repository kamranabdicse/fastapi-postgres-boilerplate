from typing import Optional

from jose import jwt

from app.core.config import settings


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print("-----------", decoded_token)
        return decoded_token["sub"]
    except jwt.JWTError:
        return None
