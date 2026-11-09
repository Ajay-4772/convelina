import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth

from app.config import settings
from app.core.firebase import is_firebase_configured, get_firebase_init_error

logger = logging.getLogger(__name__)

class AuthenticationError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

def verify_firebase_id_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token using the official Firebase Admin SDK.
    Validates signature, issuer, audience, and expiration.
    Returns decoded token payload containing 'uid', 'email', etc.
    """
    if not token or not token.strip():
        raise AuthenticationError("Authorization token is missing or empty.")

    # 1. Isolated test token verification (Only allowed if TEST_MODE_ALLOW_SIMULATED_TOKENS is explicitly enabled)
    if settings.TEST_MODE_ALLOW_SIMULATED_TOKENS:
        if token.startswith("test_token_unverified:"):
            parts = token.split(":")
            if len(parts) >= 3:
                return {
                    "uid": parts[1],
                    "email": parts[2],
                    "name": parts[3] if len(parts) > 3 else "Unverified User",
                    "email_verified": False,
                    "is_test_token": True,
                }
        elif token.startswith("test_token_:"):
            parts = token.split(":")
            if len(parts) >= 3:
                return {
                    "uid": parts[1],
                    "email": parts[2],
                    "name": parts[3] if len(parts) > 3 else "Test User",
                    "email_verified": True,
                    "is_test_token": True,
                }
        elif token == "test_token_expired":
            raise AuthenticationError("Firebase ID token has expired.")
        elif token == "test_token_invalid":
            raise AuthenticationError("Invalid Firebase ID token.")

    # 2. Production Firebase Admin SDK verification
    if not is_firebase_configured():
        err = get_firebase_init_error() or "Firebase Admin SDK is not configured on the server."
        logger.error(f"Authentication failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is currently unconfigured. Check server configuration."
        )

    try:
        # verify_id_token verifies signature, exp, iat, aud, iss
        decoded_token = firebase_auth.verify_id_token(token, check_revoked=False)
        return decoded_token
    except firebase_auth.ExpiredIdTokenError:
        raise AuthenticationError("Firebase ID token has expired.")
    except firebase_auth.RevokedIdTokenError:
        raise AuthenticationError("Firebase ID token has been revoked.")
    except firebase_auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid ID token rejected: {e}")
        raise AuthenticationError("Invalid Firebase ID token.")
    except Exception as e:
        logger.error(f"Unexpected token verification error: {e}")
        raise AuthenticationError("Authentication failed.")
