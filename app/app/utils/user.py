from typing import Optional

import jwt

from app.core.config import settings


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
        )
        print("-----------", decoded_token)
        return decoded_token["sub"]
    except jwt.JWTError:
        return None
