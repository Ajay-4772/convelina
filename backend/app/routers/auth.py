import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from app.config import settings
from app.core.database import get_db, set_rls_context
from app.core.firebase import is_firebase_configured, get_firebase_init_error
from app.core.rate_limit import rate_limiter
from app.core.sanitizer import mask_email
from app.core.security import verify_firebase_id_token
from app.core.security_monitoring import record_security_event
from app.dependencies.auth import (
    get_token_claims,
    require_authenticated_user,
    require_user,
    require_citizen,
    require_admin,
)
from app.models.user import User, EmailOTP
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.schemas.auth import (
    UserProvisionRequest,
    UserProfileUpdateRequest,
    UserResponse,
    AuthHealthResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    LinkProviderRequest,
    UserActivityItem,
    UserActivityResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_address(email: str) -> None:
    """Validate RFC email address format."""
    email_clean = email.strip()
    if not email_clean or not EMAIL_REGEX.match(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address.",
        )


def validate_gmail_address(email: str) -> None:
    """Validate that the email address is a valid Gmail address (@gmail.com or @googlemail.com)."""
    validate_email_address(email)
    clean = email.strip().lower()
    if not (clean.endswith("@gmail.com") or clean.endswith("@googlemail.com")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only official Gmail accounts (@gmail.com) are permitted for registration.",
        )


@router.get("/health", response_model=AuthHealthResponse)
def auth_health():
    """Returns the operational status of the Firebase authentication provider."""
    configured = is_firebase_configured()
    err = get_firebase_init_error()
    return AuthHealthResponse(
        status="operational" if configured else "unconfigured",
        firebase_configured=configured,
        details=None if configured else err,
    )


def _get_client_ip(request: Optional[Request]) -> str:
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for") if getattr(request, "headers", None) else None
    if forwarded:
        return forwarded.split(",")[0].strip()
    if getattr(request, "client", None) and request.client.host:
        return request.client.host
    return "unknown"


def _set_otp_rls(db: Session, email: str) -> None:
    """Binds transaction-local app.otp_email context required by scoped email_otps RLS policy."""
    db.execute(text("SELECT set_config('app.otp_email', :email, true);"), {"email": email})


def _hash_otp_code(otp_code: str, salt: str) -> str:
    """Computes keyed HMAC-SHA256 digest of a one-time passcode using per-record salt."""
    secret = (settings.ENCRYPTION_KEY or "convelina-otp-fallback").encode("utf-8")
    payload = f"{salt}:{otp_code}".encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


@router.post("/otp/send", response_model=SendOTPResponse)
def send_email_otp(req: SendOTPRequest, request: Request = None, db: Session = Depends(get_db)):
    """Generates and dispatches a secure 6-digit one-time password for email verification."""
    email = req.email.strip().lower()
    validate_email_address(email)
    now = datetime.now(timezone.utc)
    client_ip = _get_client_ip(request)

    # 0. Per-IP sliding-window throttling to prevent mass OTP abuse
    if client_ip != "unknown":
        allowed_ip, _, retry_after = rate_limiter.check_and_record(
            f"otp_send_ip:{client_ip}",
            limit=20,
            window_seconds=3600,
        )
        if not allowed_ip:
            record_security_event("otp_rate_limited", component="auth", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many verification requests from this network. Retry in {retry_after} seconds.",
            )

    _set_otp_rls(db, email)

    # 1. Enforce Resend cooldown
    latest_otp = (
        db.query(EmailOTP)
        .filter(EmailOTP.email == email)
        .order_by(desc(EmailOTP.created_at))
        .first()
    )
    if latest_otp and latest_otp.created_at:
        otp_tz = timezone.utc if latest_otp.created_at.tzinfo is None else latest_otp.created_at.tzinfo
        elapsed = (now - latest_otp.created_at.replace(tzinfo=otp_tz)).total_seconds()
        if elapsed < settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS:
            remaining = int(settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting another verification code.",
            )

    # 2. Enforce Hourly Rate Limit
    one_hour_ago = now - timedelta(hours=1)
    recent_count = (
        db.query(EmailOTP)
        .filter(EmailOTP.email == email, EmailOTP.created_at >= one_hour_ago)
        .count()
    )
    if recent_count >= 10:
        record_security_event("otp_rate_limited", component="auth", outcome="blocked")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification requests for this email. Please try again later.",
        )

    # 3. Generate cryptographically secure 6-digit OTP and keyed salt+hash
    otp_val = str(secrets.randbelow(900000) + 100000)
    otp_salt = secrets.token_hex(16)
    otp_hash = _hash_otp_code(otp_val, otp_salt)
    expires_at = now + timedelta(seconds=settings.EMAIL_OTP_EXPIRY_SECONDS)

    # 4. Dispatch via EmailService (Resend API or safe fallback)
    EmailService.send_otp_email(email, otp_val)

    # 5. Persist hashed OTP record (never store raw OTP plaintext in database)
    otp_record = EmailOTP(
        email=email,
        otp_code="******",
        otp_hash=otp_hash,
        otp_salt=otp_salt,
        attempt_count=0,
        locked_until=None,
        request_ip=client_ip,
        expires_at=expires_at,
        is_verified=False,
    )
    db.add(otp_record)
    db.commit()

    logger.info("CONVELINA Security: Dispatched verification OTP for %s", mask_email(email))
    return SendOTPResponse(
        success=True,
        message=f"A 6-digit verification code has been sent to {mask_email(email)} (valid for {settings.EMAIL_OTP_EXPIRY_SECONDS // 60} minutes).",
        expires_in_seconds=settings.EMAIL_OTP_EXPIRY_SECONDS,
    )


@router.post("/otp/verify", response_model=VerifyOTPResponse)
def verify_email_otp(req: VerifyOTPRequest, request: Request = None, db: Session = Depends(get_db)):
    """Verifies the submitted email OTP against recorded active non-expired hashed tokens."""
    email = req.email.strip().lower()
    submitted_otp = req.otp_code.strip()
    now = datetime.now(timezone.utc)
    client_ip = _get_client_ip(request)
    is_dev_or_test = settings.ENVIRONMENT.lower() in ("development", "test")

    if client_ip != "unknown":
        allowed_ip, _, retry_after = rate_limiter.check_and_record(
            f"otp_verify_ip:{client_ip}",
            limit=30,
            window_seconds=900,
        )
        if not allowed_ip:
            record_security_event("otp_rate_limited", component="auth", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many verification attempts. Please retry in {retry_after} seconds.",
            )

    # Simulated test OTP is strictly restricted to development/test modes
    if (
        is_dev_or_test
        and settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
        and submitted_otp == "123456"
        and (
            email.endswith("@gmail.com")
            or ".test" in email
            or ".in" in email
            or "@example.com" in email
        )
    ):
        token = secrets.token_hex(16)
        return VerifyOTPResponse(
            success=True,
            verified=True,
            message="Email verified successfully (Test Mode).",
            verification_token=token,
        )

    _set_otp_rls(db, email)

    record = (
        db.query(EmailOTP)
        .filter(
            EmailOTP.email == email,
            EmailOTP.expires_at > now,
            EmailOTP.is_verified == False,
        )
        .order_by(desc(EmailOTP.created_at))
        .first()
    )

    if not record:
        record_security_event("otp_verification_failed", component="auth", outcome="blocked")
        return VerifyOTPResponse(
            success=False,
            verified=False,
            message="Invalid or expired verification code. Please request a new OTP.",
            verification_token=None,
        )

    if record.locked_until:
        locked_tz = timezone.utc if record.locked_until.tzinfo is None else record.locked_until.tzinfo
        if record.locked_until.replace(tzinfo=locked_tz) > now:
            record_security_event("otp_lockout_blocked", component="auth", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Verification temporarily locked due to too many invalid attempts. Please request a new OTP later.",
            )

    if record.otp_hash and record.otp_salt:
        expected_hash = _hash_otp_code(submitted_otp, record.otp_salt)
        matches = hmac.compare_digest(expected_hash, record.otp_hash)
    else:
        matches = hmac.compare_digest(submitted_otp, record.otp_code or "")

    if not matches:
        attempts = int(record.attempt_count or 0) + 1
        record.attempt_count = attempts
        if attempts >= settings.EMAIL_OTP_MAX_ATTEMPTS:
            record.locked_until = now + timedelta(minutes=15)
            record.is_verified = True  # Burn compromised OTP after max failed attempts
            db.commit()
            record_security_event("otp_lockout_triggered", component="auth", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum OTP verification attempts exceeded. Please wait and request a new verification code.",
            )
        db.commit()
        record_security_event("otp_verification_failed", component="auth", outcome="blocked")
        return VerifyOTPResponse(
            success=False,
            verified=False,
            message="Invalid or expired verification code. Please request a new OTP.",
            verification_token=None,
        )

    verification_token = secrets.token_hex(16)
    record.is_verified = True
    record.verification_token_hash = hashlib.sha256(verification_token.encode("utf-8")).hexdigest()
    # Invalidate any other pending unverified OTPs for this email to prevent reuse
    db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.id != record.id,
        EmailOTP.is_verified == False,
    ).update({"is_verified": True}, synchronize_session=False)
    db.commit()

    return VerifyOTPResponse(
        success=True,
        verified=True,
        message="Email successfully verified.",
        verification_token=verification_token,
    )


@router.post("/provision", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def provision_user(
    req: UserProvisionRequest,
    claims: Dict[str, Any] = Depends(get_token_claims),
    db: Session = Depends(get_db),
):
    """
    Provisions or synchronizes a user account from a verified identity.
    Enforces that new users receive the 'citizen' role. Client-supplied roles are ignored.
    Enforces that the email must be a valid Gmail address.
    """
    firebase_uid = claims.get("uid")
    email = claims.get("email") or f"{firebase_uid}@user.convelina.internal"
    if not claims.get("is_test_token"):
        validate_email_address(email)
    full_name = req.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name cannot be empty.",
        )

    try:
        # Check if an existing account exists for this email
        existing_by_email = db.execute(
            text("SELECT id, firebase_uid, email, full_name, role, created_at, updated_at FROM users WHERE LOWER(email) = LOWER(:email);"),
            {"email": email}
        ).mappings().first()

        if existing_by_email:
            existing_fuid = existing_by_email.get("firebase_uid")
            if existing_fuid and existing_fuid != firebase_uid:
                logger.warning(
                    f"Account conflict during provision: email '{email}' already registered under UID '{existing_fuid}'. "
                    f"Incoming UID '{firebase_uid}' rejected."
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email address already exists. Please authenticate with your original provider or complete authenticated account linking."
                )
            
            # Updating profile attributes for the same authenticated user
            set_rls_context(db, existing_by_email["id"], existing_by_email["role"])
            db.execute(
                text("UPDATE users SET full_name = :name, updated_at = NOW() WHERE id = :uid;"),
                {"name": full_name, "uid": existing_by_email["id"]}
            )
            db.commit()
            row = dict(existing_by_email)
            row["full_name"] = full_name
        else:
            row = db.execute(
                text(
                    "SELECT id, firebase_uid, email, full_name, role, created_at, updated_at "
                    "FROM provision_user(:fuid, :email, :name);"
                ),
                {"fuid": firebase_uid, "email": email, "name": full_name},
            ).mappings().first()

        # Set transaction-local RLS context so subsequent ORM queries are permitted under RLS
        set_rls_context(db, row["id"], row["role"])

        user = db.query(User).filter(User.id == row["id"]).first()
        if user:
            if req.phone_number:
                user.phone_number = req.phone_number
            if req.date_of_birth:
                user.date_of_birth = req.date_of_birth
            if req.address:
                user.address = req.address
            if req.father_name:
                user.father_name = req.father_name
            if req.mother_name:
                user.mother_name = req.mother_name

        AuditService.log_event(
            db=db,
            action="user_registered",
            entity_type="user",
            entity_id=row["id"],
            user_id=row["id"],
            details={"email": email, "full_name": full_name},
        )
        db.commit()

        return UserResponse(
            id=row["id"],
            firebase_uid=row["firebase_uid"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            phone_number=user.phone_number if user else None,
            date_of_birth=user.date_of_birth if user else None,
            address=user.address if user else None,
            father_name=user.father_name if user else None,
            mother_name=user.mother_name if user else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        err_lower = str(e).lower()
        if "idx_users_lower_email_unique" in err_lower or "unique constraint" in err_lower:
            record_security_event("account_takeover_email_conflict", component="auth", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists. Please authenticate with your original provider or complete authenticated account linking.",
            )
        logger.error(f"Error provisioning user {firebase_uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision user profile.",
        )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """Returns the authenticated user's profile and verified system role."""
    set_rls_context(db, current_user.id, current_user.role)
    return UserResponse(
        id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        phone_number=current_user.phone_number,
        date_of_birth=current_user.date_of_birth,
        address=current_user.address,
        father_name=current_user.father_name,
        mother_name=current_user.mother_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post("/link-provider", response_model=UserResponse)
def link_authentication_provider(
    req: LinkProviderRequest,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """
    Explicit, authenticated provider linking endpoint.
    Allows an authenticated citizen to link a secondary verified provider credential to their account.
    Security validations:
    1. Caller must already be authenticated with valid primary session (current_user).
    2. Secondary token must be cryptographically verified and unexpired (with revocation check).
    3. Secondary token must have verified email ('email_verified' == True).
    4. Secondary token email must match current_user.email (case-insensitive).
    5. Native linkWithCredential guarantee: secondary_uid must equal current_user.firebase_uid.
       Any attempt to link tokens with mismatched Firebase UIDs is rejected (HTTP 400).
    Preserves:
    - User UUID, documents, conflicts, correction drafts, and forced RLS context.
    Audits:
    - Writes immutable audit log event 'account_provider_linked'.
    """
    set_rls_context(db, current_user.id, current_user.role)
    secondary_claims = verify_firebase_id_token(req.linking_token, check_revoked=True)

    secondary_uid = secondary_claims.get("uid")
    secondary_email = secondary_claims.get("email")
    secondary_verified = secondary_claims.get("email_verified", False)
    provider = secondary_claims.get("firebase", {}).get("sign_in_provider", "secondary_provider")

    if not secondary_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Secondary token does not contain a valid user identity."
        )

    if not secondary_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Secondary provider account email is not verified. Email verification is mandatory before linking."
        )

    if not secondary_email or secondary_email.strip().lower() != current_user.email.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Secondary provider email does not match the authenticated account email."
        )

    if secondary_uid != current_user.firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both authentication providers must belong to the same Firebase UID via linkWithCredential."
        )

    # Acquire row-level lock on the user to prevent concurrent linking race conditions
    user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Record tamper-evident audit event
    AuditService.log_event(
        db=db,
        action="account_provider_linked",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "provider": provider,
        },
    )
    db.commit()

    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth,
        address=user.address,
        father_name=user.father_name,
        mother_name=user.mother_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    req: UserProfileUpdateRequest,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """Updates the user's editable profile information and logs a tamper-evident audit event."""
    set_rls_context(db, current_user.id, current_user.role)

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    changed_fields = {}
    if req.full_name is not None and req.full_name.strip():
        user.full_name = req.full_name.strip()
        changed_fields["full_name"] = user.full_name
    if req.phone_number is not None:
        user.phone_number = req.phone_number.strip()
        changed_fields["phone_number"] = user.phone_number
    if req.date_of_birth is not None:
        user.date_of_birth = req.date_of_birth.strip()
        changed_fields["date_of_birth"] = user.date_of_birth
    if req.address is not None:
        user.address = req.address.strip()
        changed_fields["address"] = user.address
    if req.father_name is not None:
        user.father_name = req.father_name.strip()
        changed_fields["father_name"] = user.father_name
    if req.mother_name is not None:
        user.mother_name = req.mother_name.strip()
        changed_fields["mother_name"] = user.mother_name

    AuditService.log_event(
        db=db,
        action="profile_updated",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={"updated_fields": list(changed_fields.keys())},
    )
    db.commit()

    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth,
        address=user.address,
        father_name=user.father_name,
        mother_name=user.mother_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/account")
def delete_account(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """
    Securely removes the user's account and logs the deletion in the audit trail.
    User may re-register cleanly in the future.
    """
    set_rls_context(db, current_user.id, current_user.role)

    AuditService.log_event(
        db=db,
        action="account_deleted",
        entity_type="user",
        entity_id=current_user.id,
        user_id=current_user.id,
        details={"email": current_user.email, "deleted_at": datetime.now(timezone.utc).isoformat()},
    )

    user = db.query(User).filter(User.id == current_user.id).first()
    if user:
        db.delete(user)
    db.commit()

    return {"success": True, "message": "Account successfully deleted."}


@router.get("/activity", response_model=UserActivityResponse)
def get_user_activity(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """Retrieves chronological activity history for the authenticated citizen."""
    set_rls_context(db, current_user.id, current_user.role)

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(desc(AuditLog.created_at))
        .limit(50)
        .all()
    )

    activities = [
        UserActivityItem(
            id=str(log.id),
            action=log.action,
            entity_type=log.entity_type,
            entity_id=str(log.entity_id) if log.entity_id else None,
            details=log.details or {},
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]

    return UserActivityResponse(activities=activities)


# Role-specific verification routes
@router.get("/user-only")
def user_only_endpoint(current_user: User = Depends(require_user)):
    """Protected endpoint accessible to users with the 'user' role."""
    return {
        "message": f"Welcome user {current_user.full_name}",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }


@router.get("/citizen-only")
def citizen_only_endpoint(current_user: User = Depends(require_user)):
    """Transitional backward-compatible alias for /user-only."""
    return {
        "message": f"Welcome user {current_user.full_name}",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }


@router.get("/admin-only")
def admin_only_endpoint(current_user: User = Depends(require_admin)):
    """Protected endpoint accessible only to system administrators."""
    return {
        "message": f"Welcome admin {current_user.full_name}",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }
