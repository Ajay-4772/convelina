"""
CONVELINA Cryptographic Service & Ed25519 PKI Primitives
Provides deterministic document fingerprinting, canonical JSON payload serialization,
Ed25519 keypair generation, digital signature creation, and mathematical verification.
"""

import base64
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class CanonicalJSONSerializer:
    """
    Serializes Python dictionaries into deterministic, canonical JSON byte strings
    following RFC 8785 principles: sorted keys, minimal separators (no whitespace),
    and UTF-8 encoding.
    """

    @staticmethod
    def serialize(payload: Dict[str, Any]) -> bytes:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")


class DocumentFingerprinter:
    """
    Generates SHA-256 fingerprints for document byte streams or canonical representations.
    Never logs raw document contents or sensitive personally identifiable information.
    """

    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Computes lowercase 64-character hex SHA-256 digest."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def validate_hash_format(hash_str: str) -> bool:
        """Validates that a string is a 64-character lowercase hex SHA-256 digest."""
        if not isinstance(hash_str, str) or len(hash_str) != 64:
            return False
        return all(c in "0123456789abcdefABCDEF" for c in hash_str)


class Ed25519CryptoManager:
    """
    Handles Ed25519 keypair generation, public key serialization, and
    digital signature generation and verification.
    """

    @staticmethod
    def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Generates a new secure random Ed25519 keypair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def public_key_to_base64(public_key: ed25519.Ed25519PublicKey) -> str:
        """Encodes an Ed25519 public key as base64 string."""
        raw_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw_bytes).decode("ascii")

    @staticmethod
    def public_key_from_base64(b64_str: str) -> ed25519.Ed25519PublicKey:
        """Decodes an Ed25519 public key from base64 string."""
        raw_bytes = base64.b64decode(b64_str.encode("ascii"))
        return ed25519.Ed25519PublicKey.from_public_bytes(raw_bytes)

    @staticmethod
    def compute_public_key_fingerprint(public_key: ed25519.Ed25519PublicKey) -> str:
        """Computes SHA-256 hex digest of the raw 32-byte public key."""
        raw_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return hashlib.sha256(raw_bytes).hexdigest()

    @staticmethod
    def private_key_to_base64(private_key: ed25519.Ed25519PrivateKey) -> str:
        """Encodes an Ed25519 private key as base64 string."""
        raw_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return base64.b64encode(raw_bytes).decode("ascii")

    @staticmethod
    def private_key_from_base64(b64_str: str) -> ed25519.Ed25519PrivateKey:
        """Decodes an Ed25519 private key from base64 string."""
        raw_bytes = base64.b64decode(b64_str.encode("ascii"))
        return ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)

    @classmethod
    def sign_payload(
        cls,
        private_key: ed25519.Ed25519PrivateKey,
        canonical_payload: Dict[str, Any],
    ) -> str:
        """
        Serializes the payload canonically and signs it using Ed25519.
        Returns base64-encoded signature.
        """
        payload_bytes = CanonicalJSONSerializer.serialize(canonical_payload)
        signature_bytes = private_key.sign(payload_bytes)
        return base64.b64encode(signature_bytes).decode("ascii")

    @classmethod
    def verify_signature(
        cls,
        public_key_b64: str,
        signature_b64: str,
        canonical_payload: Dict[str, Any],
    ) -> bool:
        """
        Verifies an Ed25519 digital signature against a canonicalized dictionary payload.
        Returns True if mathematically valid, False otherwise.
        """
        try:
            public_key = cls.public_key_from_base64(public_key_b64)
            signature_bytes = base64.b64decode(signature_b64.encode("ascii"))
            payload_bytes = CanonicalJSONSerializer.serialize(canonical_payload)
            public_key.verify(signature_bytes, payload_bytes)
            return True
        except (InvalidSignature, ValueError, Exception):
            return False


class DevSigningKeyProvider:
    """
    Manages private keys for local development and testing environments ONLY.
    In production/staging, signing keys must come from PKI_PRIVATE_KEY_PEM / HSM / Cloud KMS.
    """

    _dev_keys: Dict[str, ed25519.Ed25519PrivateKey] = {}

    @classmethod
    def register_dev_key(cls, key_id: str, private_key: ed25519.Ed25519PrivateKey) -> None:
        cls._dev_keys[key_id] = private_key

    @classmethod
    def get_dev_key(cls, key_id: str) -> Optional[ed25519.Ed25519PrivateKey]:
        return cls._dev_keys.get(key_id)

    @classmethod
    def create_or_get_default_dev_key(cls, key_id: str = "consolith-officer-key-2026-v1") -> Tuple[ed25519.Ed25519PrivateKey, str, str]:
        """
        Returns (private_key, public_key_b64, fingerprint).
        In restricted environments (`production`/`staging`), requires PKI_PRIVATE_KEY_PEM
        and refuses deterministic hardcoded fallback seeds.
        """
        from app.config import settings
        from cryptography.hazmat.primitives import serialization

        env_lower = settings.ENVIRONMENT.lower()
        if settings.PKI_PRIVATE_KEY_PEM and key_id not in cls._dev_keys:
            pem_bytes = settings.PKI_PRIVATE_KEY_PEM.replace("\\n", "\n").encode("utf-8")
            loaded = serialization.load_pem_private_key(pem_bytes, password=None)
            if not isinstance(loaded, ed25519.Ed25519PrivateKey):
                raise ValueError("PKI_PRIVATE_KEY_PEM must be a valid Ed25519 private key.")
            cls.register_dev_key(key_id, loaded)

        if key_id not in cls._dev_keys:
            if env_lower in ("production", "staging") or settings.PKI_SIGNING_BACKEND != "development":
                raise RuntimeError(
                    "Security violation: Deterministic development Ed25519 key derivation is forbidden in restricted environments. "
                    "Configure an HSM/KMS backend or PKI_PRIVATE_KEY_PEM."
                )
            seed = hashlib.sha256(f"consolith-dev-officer-seed-{key_id}".encode("utf-8")).digest()
            priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
            cls.register_dev_key(key_id, priv)

        priv = cls._dev_keys[key_id]
        pub = priv.public_key()
        pub_b64 = Ed25519CryptoManager.public_key_to_base64(pub)
        fingerprint = Ed25519CryptoManager.compute_public_key_fingerprint(pub)
        return priv, pub_b64, fingerprint
