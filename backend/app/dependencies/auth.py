import logging
import uuid
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db, set_rls_context
from app.core.security import verify_firebase_id_token, AuthenticationError
from app.models.user import User

logger = logging.getLogger(__name__)

def get_current_token(authorization: Optional[str] = Header(None)) -> str:
    """Extracts the Bearer token from the Authorization header."""
    if not authorization:
        raise AuthenticationError("Authorization header is missing.")
    
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'.")
    
    return parts[1]

def get_token_claims(token: str = Depends(get_current_token)) -> Dict[str, Any]:
    """Verifies Firebase token and extracts claims."""
    return verify_firebase_id_token(token)

def get_current_user(
    claims: Dict[str, Any] = Depends(get_token_claims),
    db: Session = Depends(get_db)
) -> User:
    """
    Resolves the internal User entity from the database using verified Firebase UID.
    Activates transaction-local RLS session parameters for the query.
    """
    firebase_uid = claims.get("uid")
    if not firebase_uid:
        raise AuthenticationError("Token does not contain a valid user identity.")

    # Secure resolution via resolve_user_by_firebase_uid
    row = db.execute(
        text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM resolve_user_by_firebase_uid(:fuid);"),
        {"fuid": firebase_uid}
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found. Please provision your profile via /api/v1/auth/provision."
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
    return user

def require_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensures caller is an authenticated user."""
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            logger.warning(
                f"Unauthorized access attempt by user {user.id} (role: {user.role}) "
                f"to endpoint requiring roles: {self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have the required role permissions."
            )
        return user

# Role-specific dependencies
require_citizen = RoleChecker(["citizen"])
require_officer = RoleChecker(["officer"])
require_admin = RoleChecker(["admin"])
require_officer_or_admin = RoleChecker(["officer", "admin"])
