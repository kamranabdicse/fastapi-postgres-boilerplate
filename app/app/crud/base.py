from asyncio import iscoroutine
from datetime import datetime
from typing import Awaitable, Any, Generic, Type, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base_class import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def _commit_refresh_async(
        self, db: AsyncSession, db_obj: ModelType
    ) -> ModelType:
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    def _commit_refresh(
        self, db: Session | AsyncSession, db_obj: ModelType
    ) -> ModelType | Awaitable[ModelType]:
        if isinstance(db, AsyncSession):
            return self._commit_refresh_async(db, db_obj=db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def _first_async(self, scalars) -> ModelType | None:
        results = await scalars
        return results.first()

    def _first(self, scalars) -> ModelType | None | Awaitable[ModelType | None]:
        if iscoroutine(scalars):
            return self._first_async(scalars)
        return scalars.first()

    async def _last_async(self, scalars) -> ModelType | None:
        results = await scalars
        return results.last()

    def _last(self, scalars) -> ModelType | None | Awaitable[ModelType | None]:
        if iscoroutine(scalars):
            return self._last_async(scalars)
        return scalars.last()

    async def _all_async(self, scalars) -> list[ModelType]:
        results = await scalars
        return results.all()

    def _all(self, scalars) -> list[ModelType] | Awaitable[list[ModelType]]:
        if iscoroutine(scalars):
            return self._all_async(scalars)
        return scalars.all()

    def get(
        self, db: Session | AsyncSession, id: Any
    ) -> ModelType | Awaitable[ModelType] | None:
        query = select(self.model).filter(self.model.id == id)
        return self._first(db.scalars(query))

    def get_multi(
        self,
        db: Session | AsyncSession,
        *,
        skip: int = 0,
        limit: int | None = 100,
        asc: bool = False
    ) -> list[ModelType] | Awaitable[list[ModelType]]:
        query = (
            select(self.model)
            .order_by(self.model.id.asc() if asc else self.model.id.desc())
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    def create(
        self, db: Session | AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType | Awaitable[ModelType]:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        return self._commit_refresh(db=db, db_obj=db_obj)

    def update(
        self,
        db: Session | AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any] | None = None
    ) -> ModelType | Awaitable[ModelType]:
        if obj_in is not None:
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
        if hasattr(self.model, "modified"):
            setattr(db_obj, "modified", datetime.now())
        db.add(db_obj)
        return self._commit_refresh(db=db, db_obj=db_obj)

    async def _remove_async(self, db: AsyncSession, *, id: int) -> ModelType:
        db_obj = await self.get(db=db, id=id)
        db_obj.is_deleted = True

        if hasattr(self.model, "modified"):
            setattr(db_obj, "modified", datetime.now())

        return await self._commit_refresh_async(db, db_obj=db_obj)

    def remove(
        self, db: Session | AsyncSession, *, id: int
    ) -> ModelType | Awaitable[ModelType]:
        if isinstance(db, AsyncSession):
            return self._remove_async(db=db, id=id)

        db_obj = db.query(self.model).get(id)
        db_obj.is_deleted = True

        if hasattr(self.model, "modified"):
            setattr(db_obj, "modified", datetime.now())

        return self._commit_refresh(db, db_obj=db_obj)
