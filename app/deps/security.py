"""
Security utilities for API key validation.
"""

import os
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(
    api_key_header: str = Depends(api_key_header)
) -> Optional[str]:
    """
    Validate API key from header against environment variable.

    Args:
        api_key_header: API key from X-API-Key header

    Returns:
        str: Valid API key if validation passes

    Raises:
        HTTPException: If API key is invalid or missing when required
    """
    # Get expected API key from environment
    expected_key = os.getenv("API_KEY")

    # If no expected key is set, allow any key (or no key)
    if not expected_key:
        return api_key_header

    # If expected key is set, validate provided key
    if api_key_header == expected_key:
        return api_key_header
    else:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key",
        )
