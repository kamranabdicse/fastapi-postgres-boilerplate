from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from starlette import status

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app import crud, models, schemas, utils
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import APIResponseType, APIResponse
from app import exceptions as exc
from app.utils.user import (
    verify_password_reset_token,
)
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS


router = APIRouter()
namespace = "user"


@router.post("/token")
async def login(
    login_user_in: schemas.LoginUser,
    db: Session = Depends(deps.get_db_async),
) -> Any:
    """
    Get access and refresh token.
    """
    user = await crud.user.authenticate(
        db, email=login_user_in.email, password=login_user_in.password
    )
    if not user:
        raise exc.InternalServiceError(
            status_code=400,
            detail="Incorrect email or password",
            msg_code=utils.MessageCodes.incorrect_email_or_password
        )
    elif not crud.user.is_active(user):
        raise exc.InternalServiceError(
            status_code=400,
            detail="Inactive user",
            msg_code=utils.MessageCodes.inactive_user
        )
    
    access_token = security.create_access_token(data=user.id)
    refresh_token = security.create_refresh_token(data=user.id)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh-token")
async def refresh_token(
    token: schemas.RefreshToken
) -> Any:
    """
    Get access token.
    """
    token = token.refresh_token

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        user_id = payload.get("sub")
        token_type = payload.get("token_type")
        expire_time = payload.get("exp")

        if not user_id or token_type != "refresh":
            raise exc.InternalServiceError(
                status_code=401,
                detail="Your token is invalid",
                msg_code=utils.MessageCodes.invalid_token
            )
        
        if datetime.fromtimestamp(expire_time) < datetime.now():
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
        access_token = security.create_access_token(data=user_id)
        return {"access_token": access_token}
    
    except jwt.ExpiredSignatureError:
        raise exc.InternalServiceError(
            status_code=401,
            detail="Token has expired",
            msg_code=utils.MessageCodes.expired_token
        )


@router.post("/me")
async def me(
    current_user: models.User = Depends(deps.get_current_user),
) -> APIResponseType[schemas.User]:
    """
    Get authenticated user.
    """
    return APIResponse(current_user)

@router.post("/reset-password/")
@invalidate(namespace=namespace)
async def reset_password(
    token: str = Body(),
    new_password: str = Body(),
    db: Session = Depends(deps.get_db_async),
) -> schemas.Msg:
    """
    Reset password.
    """
    id_ = verify_password_reset_token(token)
    if not id_:
        raise exc.InternalServiceError(
            status_code=400,
            detail="Invalid token.",
            msg_code=utils.MessageCodes.bad_request
        )
    user = await crud.user.get(db, id=int(id_))
    if not user:
        raise exc.InternalServiceError(
            status_code=400,
            detail="The user with this username does not exist in the system.",
            msg_code=utils.MessageCodes.bad_request
        )
    elif not crud.user.is_active(user):
        raise exc.InternalServiceError(
            status_code=400,
            detail="Inactive user.",
            msg_code=utils.MessageCodes.bad_request
        )
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    await db.commit()
    return {"msg": "Password updated successfully"}


@router.get("/")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_users(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[list[schemas.User]]:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return APIResponse(users)


@router.post("/")
@invalidate(namespace=namespace)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.User]:
    """
    Create new user.
    """
    user = await crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise exc.InternalServiceError(
            status_code=400,
            detail="The user with this username already exists in the system.",
            msg_code=utils.MessageCodes.bad_request,
        )
    user = await crud.user.create(db, obj_in=user_in)
    return APIResponse(user)


@router.put("/update/me")
@invalidate(namespace=namespace)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    password: str | None = Body(),
    full_name: str | None = Body(),
    email: str | None = Body(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.User]:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.full_name = full_name
    if email is not None:
        user_in.email = email
    user = await crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return APIResponse(user)


@router.get("/{user_id}")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[schemas.User]:
    """
    Get a specific user by id.
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.InternalServiceError(
            status_code=404,
            detail="User not found",
            msg_code=utils.MessageCodes.not_found,
        )
    if user == current_user:
        return APIResponse(user)
    if not crud.user.is_superuser(current_user):
        raise exc.InternalServiceError(
            status_code=400,
            detail="The user doesn't have enough privileges",
            msg_code=utils.MessageCodes.bad_request,
        )
    return APIResponse(user)


@router.put("/{user_id}")
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.User]:
    """
    Update a user.
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.InternalServiceError(
            status_code=404,
            detail="The user with this username does not exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    user = await crud.user.update(db, db_obj=user, obj_in=user_in)
    return APIResponse(user)
