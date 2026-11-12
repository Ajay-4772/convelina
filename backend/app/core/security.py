import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth

from app.config import settings
from app.core.firebase import is_firebase_configured, get_firebase_init_error
from app.core.security_monitoring import record_security_event

logger = logging.getLogger(__name__)

class AuthenticationError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

def verify_firebase_id_token(token: str, check_revoked: bool = True) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token using the official Firebase Admin SDK.
    Validates signature, issuer, audience, expiration, and session revocation by default.
    Returns decoded token payload containing 'uid', 'email', etc.
    """
    if not token or not token.strip():
        record_security_event("auth_failure_missing_token", component="auth")
        raise AuthenticationError("Authorization token is missing or empty.")

    # 1. Isolated test token verification (strictly limited to dev/test environments)
    if (
        settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
        and settings.ENVIRONMENT.lower() in ("development", "test")
    ):
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
            record_security_event("auth_failure_expired_token", component="auth")
            raise AuthenticationError("Firebase ID token has expired.")
        elif token == "test_token_invalid":
            record_security_event("auth_failure_invalid_token", component="auth")
            raise AuthenticationError("Invalid Firebase ID token.")

    # 2. Structural JWT pre-check (reject unsigned alg=none or empty-signature JWTs before network calls)
    if token.strip().startswith("eyJ"):
        jwt_segments = token.strip().split(".")
        if len(jwt_segments) != 3 or not jwt_segments[2].strip():
            record_security_event("auth_failure_invalid_token", component="auth")
            raise AuthenticationError("Invalid or unsigned Firebase ID token.")

    # 3. Production Firebase Admin SDK verification
    if not is_firebase_configured():
        err = get_firebase_init_error() or "Firebase Admin SDK is not configured on the server."
        logger.error(f"Authentication failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is currently unconfigured. Live Firebase integration: pending credential configuration."
        )

    try:
        # verify_id_token verifies signature, exp, iat, aud, iss, and token revocation
        decoded_token = firebase_auth.verify_id_token(token, check_revoked=check_revoked)
        return decoded_token
    except firebase_auth.ExpiredIdTokenError:
        record_security_event("auth_failure_expired_token", component="auth")
        raise AuthenticationError("Firebase ID token has expired.")
    except firebase_auth.RevokedIdTokenError:
        record_security_event("auth_failure_revoked_token", component="auth")
        raise AuthenticationError("Firebase ID token has been revoked.")
    except firebase_auth.InvalidIdTokenError as e:
        record_security_event("auth_failure_invalid_token", component="auth")
        logger.warning(f"Invalid ID token rejected: {e}")
        raise AuthenticationError("Invalid Firebase ID token.")
    except Exception as e:
        err_msg = str(e).lower()
        if "default credentials were not found" in err_msg or "failed to establish a new connection" in err_msg:
            logger.error(f"Backend Firebase Admin unavailable or uncredentialed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is currently unavailable. Live Firebase integration: pending credential configuration."
            )
        logger.error(f"Unexpected token verification error: {e}")
        raise AuthenticationError("Authentication failed.")
