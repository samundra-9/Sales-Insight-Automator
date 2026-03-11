
import os
import logging
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Authenticates requests using an API key provided in the X-API-KEY header.
    """
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        logger.critical("API_KEY environment variable is not set. Security is compromised.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security misconfiguration."
        )

    if api_key == expected_api_key:
        logger.debug("API Key authentication successful.")
        return api_key
    else:
        logger.warning("Unauthorized access attempt with invalid API Key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
