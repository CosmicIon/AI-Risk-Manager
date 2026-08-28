"""Authentication middleware for API endpoints."""

import os
import typing
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# In a real system, these would be in a proper config/settings file
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-for-mvp-only")
ALGORITHM = "HS256"

security = HTTPBearer()

class TokenData(BaseModel):
    user_id: UUID
    tenant_id: UUID
    role: str

def create_access_token(user_id: UUID, tenant_id: UUID, role: str, expires_delta: timedelta = timedelta(hours=8)) -> str:
    """Create a new JWT access token."""
    to_encode: dict[str, typing.Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role
    }
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenData:
    """Decode JWT and return token payload."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        tenant_id_str: str = payload.get("tenant_id")
        role: str = payload.get("role")

        if user_id_str is None or tenant_id_str is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(
            user_id=UUID(user_id_str),
            tenant_id=UUID(tenant_id_str),
            role=role
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

def require_role(*roles: str):
    """Dependency to check if current user has required role."""
    async def role_checker(token_data: TokenData = Depends(verify_token)) -> TokenData:
        if token_data.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return token_data
    return role_checker



async def verify_api_key(x_api_key: str = Header(None)) -> TokenData:
    """
    Verify API key for machine-to-machine endpoints.
    For MVP, we just check against a dummy hardcoded key.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing"
        )

    # Dummy logic for MVP:
    # M2M integrations always run under a system tenant
    if x_api_key == "test-api-key-123":
        return TokenData(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
            role="system"
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key"
    )
