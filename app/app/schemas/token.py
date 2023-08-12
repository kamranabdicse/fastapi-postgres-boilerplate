from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: int | None = None


class RefreshToken(BaseModel):
    refresh_token: str
