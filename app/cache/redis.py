"""redis.py"""
import os
from typing import Tuple

import aioredis

from cache.enums import RedisStatus


async def redis_connect(host_url: str) -> Tuple[RedisStatus, aioredis.client.Redis]:
    """Attempt to connect to `host_url` and return a Redis client instance if successful."""
    return (
        await _connect(host_url)
        if os.environ.get("CACHE_ENV") != "TEST"
        else _connect_fake()
    )


async def _connect(
    host_url: str,
) -> tuple[RedisStatus, aioredis.client.Redis]:  # pragma: no cover
    try:
        redis_client = await aioredis.from_url(host_url)
        if await redis_client.ping():
            return (RedisStatus.CONNECTED, redis_client)
        return (RedisStatus.CONN_ERROR, None)
    except aioredis.AuthenticationError:
        return (RedisStatus.AUTH_ERROR, None)
    except aioredis.ConnectionError:
        return (RedisStatus.CONN_ERROR, None)


def _connect_fake() -> Tuple[RedisStatus, aioredis.client.Redis]:
    from fakeredis import FakeRedis

    return (RedisStatus.CONNECTED, FakeRedis())
