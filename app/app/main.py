from fastapi import FastAPI, Request, Response

from starlette.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.models import User
from app.exceptions import (
    http_exceptions,
    internal_exceptions,
    internal_service_exceptions,
    validation_exceptions,
)
from cache import Cache


app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

app.add_exception_handler(*internal_exceptions)
app.add_exception_handler(*internal_service_exceptions)
app.add_exception_handler(*internal_service_exceptions)
app.add_exception_handler(*validation_exceptions)
app.add_exception_handler(*http_exceptions)


@app.on_event("startup")
async def startup():
    redis_cache = Cache()
    url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:{settings.REDIS_PORT}"
    await redis_cache.init(
        host_url=url,
        prefix="api-cache",
        response_header="X-API-Cache",
        ignore_arg_types=[Request, Response, Session, AsyncSession, User],
    )
