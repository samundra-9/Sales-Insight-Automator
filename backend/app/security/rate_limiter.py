import logging
import time
from typing import Callable
from functools import wraps

from fastapi import Request, HTTPException, status

from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# In-memory request tracking
request_store: dict[str, list[float]] = {}


def rate_limit(max_requests: int, window_seconds: int):
    """Simple in-memory rate limiter based on client IP."""

    def decorator(func: Callable):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request | None = kwargs.get("request")

            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                logger.error("Request object missing in rate limiter.")
                raise RuntimeError("Request object not found for rate limiting.")

            client_ip = request.headers.get("X-Forwarded-For") or request.client.host
            key = f"{client_ip}:{func.__name__}"

            current_time = time.time()

            if key not in request_store:
                request_store[key] = []

            # Remove timestamps outside window
            request_store[key] = [
                t for t in request_store[key] if current_time - t < window_seconds
            ]

            if len(request_store[key]) >= max_requests:
                logger.warning(f"Rate limit exceeded for IP {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )

            request_store[key].append(current_time)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def init_rate_limiter(app):
    """Dummy initializer to keep FastAPI startup compatible."""

    logger.info("In-memory rate limiter initialized.")


async def close_rate_limiter(app):
    """Dummy shutdown function."""

    logger.info("In-memory rate limiter shutdown.")
