"""
Security Utilities
Authentication, authorization, and token management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import hashlib

from app.core.config import settings

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash password using SHA-256

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if passwords match
    """
    return hash_password(plain_password) == hashed_password


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token

    Args:
        data: Data to encode
        expires_delta: Optional expiration time

    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None


def hash_api_key(api_key: str) -> str:
    """
    Hash API key

    Args:
        api_key: Plain text API key

    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify API key against hash

    Args:
        plain_key: Plain text API key
        hashed_key: Hashed API key

    Returns:
        True if keys match
    """
    return hash_api_key(plain_key) == hashed_key
