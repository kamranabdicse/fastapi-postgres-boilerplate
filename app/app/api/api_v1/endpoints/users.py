from datetime import timedelta

from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

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


@router.post("/login/access-token")
async def login_access_token(
    request: Request,
    db: AsyncSession = Depends(deps.get_db_async),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise exc.InternalServiceError(
            status_code=400,
            detail="Incorrect email or password",
            msg_code=utils.MessageCodes.incorrect_email_or_password,
        )
    elif not crud.user.is_active(user):
        raise exc.InternalServiceError(
            status_code=400,
            detail="Inactive user",
            msg_code=utils.MessageCodes.inactive_user,
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return schemas.Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        token_type="bearer",
        # 'access_list' later used for user access control
        access_list=[route.name for route in request.app.routes],
    )


@router.post("/login/test-token")
async def test_token(
    current_user: models.User = Depends(deps.get_current_user),
) -> APIResponseType[schemas.User]:
    """
    Test access token
    """
    return APIResponse(current_user)


@router.post("/reset-password/")
@invalidate(namespace=namespace)
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db_async),
) -> schemas.Msg:
    """
    Reset password
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


@router.put("/me")
@invalidate(namespace=namespace)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    password: str = Body(None),
    full_name: str = Body(None),
    email: str = Body(None),
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
