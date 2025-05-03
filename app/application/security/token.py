from __future__ import annotations
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional
from core.config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def generate_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a JWT access token for the given user ID.

    Args:
        user_id (int): The ID of the authenticated user.
        expires_delta (Optional[timedelta]): Optional expiration override.

    Returns:
        str: Encoded JWT token.
    """
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> int | None:
    """
    Decode and verify a JWT access token.

    Args:
        token (str): JWT string to decode.

    Returns:
        int | None: User ID if token is valid, else None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, ValueError):
        return None
