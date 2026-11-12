import logging
import uuid
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.core.database import get_db, set_rls_context
from app.core.security import verify_firebase_id_token, AuthenticationError
from app.core.security_monitoring import record_security_event
from app.models.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

def get_current_token(authorization: Optional[str] = Header(None)) -> str:
    """Extracts the Bearer token from the Authorization header."""
    if not authorization:
        record_security_event("auth_failure_missing_header", component="auth")
        raise AuthenticationError("Authorization header is missing.")
    
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        record_security_event("auth_failure_malformed_header", component="auth")
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'.")
    
    return parts[1]

def get_token_claims(token: str = Depends(get_current_token)) -> Dict[str, Any]:
    """Verifies Firebase token (including revocation check) and extracts claims."""
    return verify_firebase_id_token(token, check_revoked=True)

def get_current_user(
    claims: Dict[str, Any] = Depends(get_token_claims),
    db: Session = Depends(get_db)
) -> User:
    """
    Resolves the internal User entity from the database using verified Firebase UID.
    Activates transaction-local RLS session parameters for the query.
    Automatically provisions new users or synchronizes linked accounts (Email + Google)
    without duplicating user records.
    """
    firebase_uid = claims.get("uid")
    if not firebase_uid:
        raise AuthenticationError("Token does not contain a valid user identity.")

    # 1. Primary lookup by verified Firebase UID
    row = db.execute(
        text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM resolve_user_by_firebase_uid(:fuid);"),
        {"fuid": firebase_uid}
    ).mappings().first()

    if not row:
        email = claims.get("email") or f"{firebase_uid}@user.convelina.internal"
        display_name = claims.get("name") or claims.get("display_name") or email.split("@")[0] or "User"
        email_verified = bool(claims.get("email_verified", False))

        # 2. Check if a user with the same email already exists
        existing_by_email = db.execute(
            text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM users WHERE LOWER(email) = LOWER(:email);"),
            {"email": email}
        ).mappings().first()

        if existing_by_email:
            existing_fuid = existing_by_email.get("firebase_uid")
            if existing_fuid and existing_fuid != firebase_uid:
                # SECURITY ENFORCEMENT: Prevent Unauthorized Account Takeover (ATO)
                # An account exists with this email under a DIFFERENT Firebase UID.
                # We strictly refuse to overwrite firebase_uid solely based on email match.
                # The user must sign in with their original provider or perform authenticated provider linking.
                logger.warning(
                    f"Authentication rejected: email '{email}' is already bound to Firebase UID '{existing_fuid}'. "
                    f"Incoming unlinked UID '{firebase_uid}' cannot claim this account without explicit authenticated linking."
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email address already exists under a different authentication identity. Please sign in with your original provider or complete authenticated account linking."
                )
            elif not existing_fuid:
                # Legacy unlinked account without a registered Firebase UID
                if not email_verified:
                    logger.warning(f"Unverified identity '{firebase_uid}' attempted to claim unlinked user '{email}'.")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Email address must be verified before associating with an existing user account."
                    )
                # Safely associate verified Firebase UID to legacy account
                try:
                    set_rls_context(db, existing_by_email["id"], existing_by_email["role"])
                    db.execute(
                        text("UPDATE users SET firebase_uid = :fuid, updated_at = NOW() WHERE id = :uid;"),
                        {"fuid": firebase_uid, "uid": existing_by_email["id"]}
                    )
                    AuditService.log_event(
                        db=db,
                        action="account_firebase_uid_bound",
                        entity_type="user",
                        entity_id=existing_by_email["id"],
                        user_id=existing_by_email["id"],
                        details={"email": email, "bound_firebase_uid": firebase_uid}
                    )
                    db.commit()
                    row = db.execute(
                        text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM resolve_user_by_firebase_uid(:fuid);"),
                        {"fuid": firebase_uid}
                    ).mappings().first()
                except Exception as bind_err:
                    db.rollback()
                    logger.error(f"Failed to bind verified UID to legacy account for {email}: {bind_err}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to associate authentication identity."
                    )

        if not row:
            # 3. Auto-provision brand new user record on first authenticated request
            # CRITICAL SECURITY RULE: Every new user strictly receives role 'user'.
            # Automatic role escalation based on ADMIN_GMAIL is completely eliminated.
            # Client-supplied role claims are strictly ignored.
            # Administrator access MUST be provisioned via explicit DB CLI script or authenticated admin endpoint.
            try:
                row = db.execute(
                    text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM provision_user(:fuid, :email, :name);"),
                    {"fuid": firebase_uid, "email": email, "name": display_name}
                ).mappings().first()
                db.commit()
            except Exception as e:
                db.rollback()
                err_lower = str(e).lower()
                if "idx_users_lower_email_unique" in err_lower or "unique constraint" in err_lower:
                    record_security_event("account_takeover_email_conflict", component="auth", outcome="blocked")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="An account with this email address already exists under a different authentication identity. Please sign in with your original provider or complete authenticated account linking."
                    )
                logger.error(f"Auto-provisioning failed for {firebase_uid}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to auto-provision user account."
                )

    # Establish transaction-local RLS context for subsequent operations
    user_id = row["id"]
    user_role = row["role"]
    set_rls_context(db, user_id, user_role)

    # Fetch complete User entity from DB under active RLS session context
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            firebase_uid=row["firebase_uid"],
            email=row["email"],
            full_name=row["full_name"],
            role=user_role,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    # Bind verified token claims transiently for downstream MFA checks
    setattr(user, "_auth_claims", claims)
    return user

def require_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensures caller is an authenticated user."""
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        user_role = "user" if user.role == "citizen" else user.role
        allowed = [("user" if r == "citizen" else r) for r in self.allowed_roles]
        if user_role not in allowed and user.role not in self.allowed_roles:
            record_security_event("unauthorized_role_access", component="rbac")
            logger.warning(
                f"Unauthorized access attempt by user {user.id} (role: {user.role}) "
                f"to endpoint requiring roles: {self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have the required role permissions."
            )

        # Enforce MFA for ADMIN accounts when configured or strictly in production
        require_mfa = (
            bool(getattr(settings, "ADMIN_REQUIRE_MFA", False))
            or settings.ENVIRONMENT.lower() == "production"
        )
        if "admin" in allowed and user_role == "admin" and require_mfa:
            claims = getattr(user, "_auth_claims", None) or {}
            firebase_meta = claims.get("firebase") if isinstance(claims.get("firebase"), dict) else {}
            mfa_satisfied = bool(
                claims.get("mfa_verified")
                or firebase_meta.get("sign_in_second_factor")
            )
            if not mfa_satisfied:
                record_security_event("admin_mfa_required_rejected", component="rbac")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Multi-factor authentication (MFA) is required for administrative access."
                )

        return user

# Two-Role RBAC model: USER and ADMIN
# 'user' is the primary platform role; 'citizen' is accepted for transitional backward compatibility
require_user = RoleChecker(["user", "citizen"])
require_admin = RoleChecker(["admin"])

# Backward-compatibility alias during role migration
require_citizen = require_user
