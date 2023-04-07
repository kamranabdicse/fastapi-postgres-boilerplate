from datetime import timedelta
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils.user import (
    verify_password_reset_token,
)
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS


router = APIRouter()
namespace = 'user'


@router.post("/login/access-token", response_model=schemas.Token)
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db_async), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/reset-password/", response_model=schemas.Msg)
@invalidate(namespace=namespace)
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db_async),
) -> Any:
    """
    Reset password
    """
    id_ = verify_password_reset_token(token)
    if not id_:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await crud.user.get(db, id=int(id_))
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    await db.commit()
    return {"msg": "Password updated successfully"}


@router.get("/", response_model=List[schemas.User])
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_users(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=schemas.User)
@invalidate(namespace=namespace)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = await crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    user = await crud.user.create(db, obj_in=user_in)
    return user


@router.put("/me", response_model=schemas.User)
@invalidate(namespace=namespace)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    password: str = Body(None),
    full_name: str = Body(None),
    email: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
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
    return user


@router.get("/me", response_model=schemas.User)
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_user_me(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.post("/open", response_model=schemas.User)
@invalidate(namespace=namespace)
async def create_user_open(
    *,
    db: read_user_me = Depends(deps.get_db_async),
    password: str = Body(...),
    email: str = Body(...),
    full_name: str = Body(None),
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = await crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user_in = schemas.UserCreate(password=password, email=email, full_name=full_name)
    user = await crud.user.create(db, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=schemas.User)
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_async),
) -> Any:
    """
    Get a specific user by id.
    """
    user = await crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=schemas.User)
@invalidate(namespace=namespace)
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    
    if await crud.user.get_by_email(db, email=user_in.email) and not user:
        raise HTTPException(
            status_code=400,
            detail="The email exists in the system",
        )
    user = await crud.user.update(db, db_obj=user, obj_in=user_in)
    return user
