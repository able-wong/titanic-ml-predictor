"""
JWT Authentication middleware and utilities for FastAPI ML Service.

This module provides JWT token verification, user authentication dependencies,
and related security functionality using RS256 asymmetric encryption.
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import config_manager
from app.core.logging_config import get_logger, StructuredLogger


class TokenData(BaseModel):
    """Token data model for JWT payload."""

    user_id: str
    username: Optional[str] = None
    exp: datetime
    iat: datetime


class AuthService:
    """Handles JWT authentication operations."""

    def __init__(self):
        """Initialize auth service with configuration."""
        self.config = None
        self.algorithm = None
        self.private_key = None
        self.public_key = None
        self.expire_minutes = None
        self._initialized = False
        self.logger = get_logger("auth")
        self.structured_logger = StructuredLogger("auth")

    def _ensure_initialized(self):
        """Ensure auth service is initialized with configuration."""
        if not self._initialized:
            self.config = config_manager.config
            self.algorithm = self.config.jwt.algorithm
            self.private_key = self.config.jwt.private_key
            self.public_key = self.config.jwt.public_key
            self.expire_minutes = self.config.jwt.access_token_expire_minutes
            self._initialized = True

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new JWT access token.

        Args:
            data (Dict): Token payload data
            expires_delta (timedelta, optional): Custom expiration time

        Returns:
            str: Encoded JWT token
        """
        self._ensure_initialized()
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

        try:
            # Encode token with private key
            encoded_jwt = jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)

            self.logger.debug(
                "Access token created successfully",
                user_id=data.get("user_id"),
                algorithm=self.algorithm,
                expires_at=expire.isoformat(),
            )

            return encoded_jwt
        except (TypeError, ValueError) as e:
            # Handle serialization errors or invalid data
            self.logger.error(
                "Failed to create access token due to invalid payload",
                error_type=type(e).__name__,
                error_message=str(e),
                user_id=data.get("user_id"),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token: invalid payload data",
            )
        except jwt.InvalidKeyError as e:
            # Handle JWT key errors
            self.logger.error(
                "Failed to create access token due to invalid key",
                error_type=type(e).__name__,
                error_message=str(e),
                user_id=data.get("user_id"),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token: invalid signing key",
            )

    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode a JWT token.

        Args:
            token (str): JWT token to verify

        Returns:
            TokenData: Decoded token data

        Raises:
            HTTPException: If token is invalid or expired
        """
        self._ensure_initialized()
        try:
            # Decode token with public key
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])

            # Extract user information
            user_id = payload.get("user_id")
            if user_id is None:
                self.structured_logger.authentication_event(
                    event_type="token_verification", success=False, error_reason="missing_user_id"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create token data
            token_data = TokenData(
                user_id=user_id,
                username=payload.get("username"),
                exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc),
                iat=datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc),
            )

            self.structured_logger.authentication_event(
                event_type="token_verification",
                user_id=user_id,
                success=True,
                username=payload.get("username"),
            )

            return token_data

        except jwt.ExpiredSignatureError:
            self.structured_logger.authentication_event(
                event_type="token_verification", success=False, error_reason="token_expired"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            self.structured_logger.authentication_event(
                event_type="token_verification",
                success=False,
                error_reason="invalid_token",
                error_details=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            self.logger.error(
                "Token verification failed with unexpected error",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token verification failed: {str(e)}",
            )


# Global auth service instance
auth_service = AuthService()

# HTTP Bearer token security scheme
security = HTTPBearer()


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    FastAPI dependency to verify JWT tokens.

    This dependency can be used to protect endpoints that require authentication.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        TokenData: Verified token data with user information

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify the token
        token_data = auth_service.verify_token(credentials.credentials)

        # Check if token is still valid (additional safety check)
        if token_data.exp < datetime.now(timezone.utc):
            auth_service.structured_logger.authentication_event(
                event_type="token_validation",
                user_id=token_data.user_id,
                success=False,
                error_reason="token_expired_on_validation",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return token_data

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        auth_service.logger.error(
            "Authentication failed with unexpected error",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_current_user(token_data: TokenData = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user information.

    Args:
        token_data: Verified token data from verify_jwt_token dependency

    Returns:
        Dict: User information extracted from token
    """
    return {
        "user_id": token_data.user_id,
        "username": token_data.username,
        "token_issued_at": token_data.iat,
        "token_expires_at": token_data.exp,
    }
