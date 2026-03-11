import os
import logging
import time
from typing import Callable, Optional
from functools import wraps

from fastapi import Request, HTTPException, status
from redis import asyncio as aioredis

from app.utils.logger import setup_logging
from app.security.api_key_auth import get_api_key

setup_logging()
logger = logging.getLogger(__name__)

# fallback memory store if Redis is unavailable
memory_store: dict[str, list[int]] = {}


async def get_redis(request: Request) -> Optional[aioredis.Redis]:
    """Return the Redis client from app state if available."""

    if hasattr(request.app.state, "redis") and request.app.state.redis:
        return request.app.state.redis

    return None


def rate_limit(max_requests: int, window_seconds: int):
    """Rate limiter that uses Redis if available, otherwise falls back to in-memory store."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")

            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise RuntimeError("Request object not found for rate limiting.")

            client_ip = request.headers.get("X-Forwarded-For") or request.client.host
            key = f"rate_limit:{client_ip}:{func.__name__}"

            redis_client = await get_redis(request)
            current_time = int(time.time())

            # ----------------------------
            # Redis Rate Limiting
            # ----------------------------
            if redis_client:
                await redis_client.zremrangebyscore(key, 0, current_time - window_seconds)
                await redis_client.zadd(key, {str(current_time): current_time})

                request_count = await redis_client.zcard(key)
                if request_count > max_requests:
                    logger.warning(f"Redis rate limit exceeded: {client_ip}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded.",
                    )

            # ----------------------------
            # Memory Fallback Rate Limit
            # ----------------------------
            else:
                if key not in memory_store:
                    memory_store[key] = []

                memory_store[key] = [
                    t for t in memory_store[key] if current_time - t < window_seconds
                ]

                if len(memory_store[key]) >= max_requests:
                    logger.warning(f"Memory rate limit exceeded: {client_ip}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded.",
                    )

                memory_store[key].append(current_time)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def init_rate_limiter(app):
    """Initialize Redis if available."""

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("REDIS_URL not set. Using memory rate limiter.")
        app.state.redis = None
        return

    try:
        app.state.redis = await aioredis.from_url(redis_url, decode_responses=True)
        logger.info("Redis rate limiter initialized.")
    except Exception as e:
        logger.warning(f"Redis unavailable. Falling back to memory rate limiter: {e}")
        app.state.redis = None


async def close_rate_limiter(app):
    """Close Redis connection if it exists."""

    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed.")
