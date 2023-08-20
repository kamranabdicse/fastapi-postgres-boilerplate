from datetime import datetime
from typing import Generator, AsyncGenerator

from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app import crud, models, schemas, utils
from app.core.config import settings
from app.db.session import SessionLocal, async_session
from app import exceptions as exc


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def get_db_async() -> AsyncGenerator:
    async with async_session() as session:
        yield session


async def get_current_user(
    authorization: str = Depends(HTTPBearer()),
    db: Session | AsyncSession = Depends(get_db_async)
) -> models.User:
    try:
        token = authorization.credentials
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)

    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token prefix missing",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication Failed",
        )
    
    user = await crud.user.get(db, id=token_data.sub)
    if not user:
        raise exc.InternalServiceError(
            status_code=404,
            detail="User not found",
            msg_code=utils.MessageCodes.not_found,
        )
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise exc.InternalServiceError(
            status_code=400,
            detail="Inactive user",
            msg_code=utils.MessageCodes.inactive_user,
        )
    return current_user


async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise exc.InternalServiceError(
            status_code=403,
            detail="Permision Error",
            msg_code=utils.MessageCodes.permisionError,
        )
    return current_user
