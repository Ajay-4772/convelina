import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db, set_rls_context
from app.core.firebase import is_firebase_configured, get_firebase_init_error
from app.dependencies.auth import (
    get_token_claims,
    require_authenticated_user,
    require_citizen,
    require_officer,
    require_admin,
)
from app.models.user import User
from app.schemas.auth import (
    UserProvisionRequest,
    UserResponse,
    AuthHealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.get("/health", response_model=AuthHealthResponse)
def auth_health():
    """Returns the operational status of the Firebase authentication provider."""
    configured = is_firebase_configured()
    err = get_firebase_init_error()
    return AuthHealthResponse(
        status="operational" if configured else "unconfigured",
        firebase_configured=configured,
        details=None if configured else err
    )

@router.post("/provision", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def provision_user(
    req: UserProvisionRequest,
    claims: Dict[str, Any] = Depends(get_token_claims),
    db: Session = Depends(get_db)
):
    """
    Provisions or synchronizes a user account from a verified Firebase identity.
    Enforces that new users receive the 'citizen' role. Client-supplied roles are ignored.
    """
    firebase_uid = claims.get("uid")
    email = claims.get("email") or f"{firebase_uid}@firebase.user"
    full_name = req.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name cannot be empty."
        )

    try:
        row = db.execute(
            text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM provision_citizen_user(:fuid, :email, :name);"),
            {
                "fuid": firebase_uid,
                "email": email,
                "name": full_name
            }
        ).mappings().first()
        db.commit()

        # Set transaction-local RLS context
        set_rls_context(db, row["id"], row["role"])

        return UserResponse(
            id=row["id"],
            firebase_uid=row["firebase_uid"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error provisioning user {firebase_uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision user profile."
        )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(require_authenticated_user)):
    """Returns the authenticated user's profile and verified system role."""
    return UserResponse(
        id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

# Role-specific verification routes
@router.get("/citizen-only")
def citizen_only_endpoint(current_user: User = Depends(require_citizen)):
    """Protected endpoint accessible only to users with the 'citizen' role."""
    return {
        "message": f"Welcome citizen {current_user.full_name}",
        "user_id": str(current_user.id),
        "role": current_user.role
    }

@router.get("/officer-only")
def officer_only_endpoint(current_user: User = Depends(require_officer)):
    """Protected endpoint accessible only to verification officers."""
    return {
        "message": f"Welcome officer {current_user.full_name}",
        "user_id": str(current_user.id),
        "role": current_user.role
    }

@router.get("/admin-only")
def admin_only_endpoint(current_user: User = Depends(require_admin)):
    """Protected endpoint accessible only to system administrators."""
    return {
        "message": f"Welcome admin {current_user.full_name}",
        "user_id": str(current_user.id),
        "role": current_user.role
    }
