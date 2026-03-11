
import os
import logging
from typing import Callable
from functools import wraps

from fastapi import Request, HTTPException, status, Depends
from redis import asyncio as aioredis
import time

from app.utils.logger import setup_logging
from app.security.api_key_auth import get_api_key

setup_logging()
logger = logging.getLogger(__name__)

async def get_redis(request: Request) -> aioredis.Redis:
    """
    Dependency to get the Redis client from the FastAPI app state.
    """
    if not hasattr(request.app.state, 'redis') or not request.app.state.redis:
        logger.error("Redis client not found in app state.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not configured.")
    return request.app.state.redis

def rate_limit(max_requests: int, window_seconds: int):
    """
    Decorator for rate limiting API endpoints based on IP address.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if not request:
                logger.error(f"Rate limit decorator applied to a function without a Request object: {func.__name__}")
                raise RuntimeError("Request object not found for rate limiting.")

            # Extract client IP. Use X-Forwarded-For if behind a proxy, otherwise host
            client_ip = request.headers.get("X-Forwarded-For") or request.client.host
            key = f"rate_limit:{client_ip}:{func.__name__}"

            redis = await get_redis(request) # Get redis client using dependency

            current_time = int(time.time())
            # Remove timestamps older than the window
            await redis.zremrangebyscore(key, 0, current_time - window_seconds)
            # Add current request timestamp
            await redis.zadd(key, {str(current_time): current_time})
            # Get count of requests in the window
            request_count = await redis.zcard(key)

            if request_count > max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip} on endpoint: {func.__name__}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {window_seconds} seconds."
                )
            logger.debug(f"IP {client_ip} - requests in window: {request_count}/{max_requests}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
async def init_rate_limiter(app):
    """
    Initialize Redis connection and attach it to FastAPI app state.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    try:
        app.state.redis = await aioredis.from_url(redis_url, decode_responses=True)
        logger.info("Redis rate limiter initialized.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def close_rate_limiter(app):
    """
    Close Redis connection when shutting down the app.
    """
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed.")