"""
CONVELINA Encryption & Key Management Service.

Supports:
- Direct url-safe base64 32-byte Fernet master keys (consistent with production validator)
- HKDF-SHA256 purpose/tenant context key derivation for key separation
- Key versioning prefixing (e.g. `v1:<fernet_token>`)
- Zero-downtime key rotation via `MultiFernet` (`ENCRYPTION_PREVIOUS_KEYS`)
- Backward-compatible decryption of legacy unversioned tokens
"""

import base64
import hashlib
from typing import List, Optional
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import settings


def _normalize_master_secret(raw_key: str) -> bytes:
    """Normalizes configured key material to a 32-byte master key."""
    encoded = raw_key.encode("utf-8")
    try:
        # Validate whether raw_key is already a 44-char urlsafe base64 Fernet key
        Fernet(encoded)
        return base64.urlsafe_b64decode(encoded)
    except Exception:
        # Development fallback for arbitrary human-readable strings
        if settings.ENVIRONMENT.lower() in ("production", "staging"):
            raise ValueError("Invalid Fernet master key in restricted environment.")
        return hashlib.sha256(encoded).digest()


def _derive_fernet_key(raw_key: str, context: Optional[str] = None) -> bytes:
    """
    Derives a 32-byte url-safe base64 Fernet key. When `context` is supplied,
    uses HKDF-SHA256 for domain/tenant key separation.
    """
    master_bytes = _normalize_master_secret(raw_key)
    if not context:
        return base64.urlsafe_b64encode(master_bytes)

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"convelina-fernet-v1",
        info=context.encode("utf-8"),
    )
    return base64.urlsafe_b64encode(hkdf.derive(master_bytes))


def _get_legacy_sha256_fernet_key(raw_key: str) -> bytes:
    """Legacy pre-hardening derivation (sha256(raw_key)) kept solely for decrypt compatibility."""
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_multi_fernet(context: Optional[str] = None) -> MultiFernet:
    primary_raw = settings.ENCRYPTION_KEY or "consolith_default_secret_key_dev"
    keys: List[Fernet] = [Fernet(_derive_fernet_key(primary_raw, context=context))]

    prev_raw = getattr(settings, "ENCRYPTION_PREVIOUS_KEYS", None)
    if prev_raw:
        for candidate in prev_raw.split(","):
            trimmed = candidate.strip()
            if trimmed:
                keys.append(Fernet(_derive_fernet_key(trimmed, context=context)))

    # Keep legacy uncontextualized key in decrypt chain for seamless migration of old rows
    legacy_key = Fernet(_get_legacy_sha256_fernet_key(primary_raw))
    keys.append(legacy_key)
    return MultiFernet(keys)


def encrypt_data(plaintext: str, context: Optional[str] = None) -> str:
    """
    Encrypts sensitive text with version tracking (`v1:...`) using active Fernet key.
    """
    if not plaintext:
        return ""
    version = getattr(settings, "ENCRYPTION_KEY_VERSION", "v1") or "v1"
    mf = _get_multi_fernet(context=context)
    token = mf.encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{version}:{token}"


def decrypt_data(ciphertext: str, context: Optional[str] = None) -> str:
    """
    Decrypts versioned (`v1:...`) or legacy unversioned Fernet ciphertext back to plaintext.
    """
    if not ciphertext:
        return ""
    token = ciphertext
    if ":" in ciphertext and ciphertext.split(":", 1)[0].startswith("v"):
        _, token = ciphertext.split(":", 1)

    mf = _get_multi_fernet(context=context)
    return mf.decrypt(token.encode("utf-8")).decode("utf-8")


def rotate_ciphertext(ciphertext: str, context: Optional[str] = None) -> str:
    """Re-encrypts an existing ciphertext under the current primary key & version."""
    if not ciphertext:
        return ""
    plaintext = decrypt_data(ciphertext, context=context)
    return encrypt_data(plaintext, context=context)
