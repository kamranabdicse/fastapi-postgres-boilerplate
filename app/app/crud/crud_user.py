from typing import Any, Dict, Union, Awaitable

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(
        self, db: Session | AsyncSession, *, email: str
    ) -> User | None | Awaitable[User | None]:
        query = select(User).filter(User.email == email)
        return self._first(db.scalars(query))

    async def create(self, db: Session | AsyncSession, *, obj_in: UserCreate) -> User:
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data["hashed_password"] = get_password_hash(obj_in.password)
        del obj_in_data["password"]
        obj_in_data = {k: v for k, v in obj_in_data.items() if v is not None}
        return await super().create(db, obj_in=obj_in_data)

    def update(
        self,
        db: Session | AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User | Awaitable[User]:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate_async(
        self, db: AsyncSession, *, email: str, password: str
    ) -> User | None:
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def authenticate(
        self, db: Session | AsyncSession, *, email: str, password: str
    ) -> User | None | Awaitable[User | None]:
        if isinstance(db, AsyncSession):
            return self.authenticate_async(db=db, email=email, password=password)
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


user = CRUDUser(User)
