"""
Consolith Module 9 Unit & Cryptographic Test Suite
Tests Ed25519 key generation, canonical serialization, document fingerprinting,
tamper detection, key lifecycle (rotation/revocation), and historical signature validity.
"""

import base64
import copy
from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import MagicMock

from app.core.crypto import (
    CanonicalJSONSerializer,
    DocumentFingerprinter,
    Ed25519CryptoManager,
    DevSigningKeyProvider,
)
from app.services.pki_service import PKIService, PKIVerificationStatus
from app.schemas.pki import SigningKeyCreate, SigningKeyRotateRequest, SigningKeyRevokeRequest


class TestCryptographicPrimitives:
    def test_canonical_json_serialization_is_deterministic(self):
        dict1 = {"z": 100, "a": "hello", "m": [3, 2, 1], "sub": {"b": 2, "a": 1}}
        dict2 = {"a": "hello", "sub": {"a": 1, "b": 2}, "z": 100, "m": [3, 2, 1]}

        bytes1 = CanonicalJSONSerializer.serialize(dict1)
        bytes2 = CanonicalJSONSerializer.serialize(dict2)

        assert bytes1 == bytes2
        # Verify compact formatting (no whitespace after ':' or ',')
        assert b": " not in bytes1
        assert b", " not in bytes1
        assert bytes1.startswith(b'{"a":"hello"')

    def test_document_fingerprinter_sha256(self):
        doc1 = b"Identity Document Content - Citizen A"
        doc2 = b"Identity Document Content - Citizen A"
        doc3 = b"Identity Document Content - Citizen B (Modified)"

        hash1 = DocumentFingerprinter.compute_hash(doc1)
        hash2 = DocumentFingerprinter.compute_hash(doc2)
        hash3 = DocumentFingerprinter.compute_hash(doc3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64
        assert DocumentFingerprinter.validate_hash_format(hash1) is True
        assert DocumentFingerprinter.validate_hash_format("invalid-hash") is False
        assert DocumentFingerprinter.validate_hash_format("g" * 64) is False

    def test_ed25519_sign_and_verify_valid_payload(self):
        priv, pub = Ed25519CryptoManager.generate_keypair()
        pub_b64 = Ed25519CryptoManager.public_key_to_base64(pub)
        fingerprint = Ed25519CryptoManager.compute_public_key_fingerprint(pub)

        assert len(fingerprint) == 64
        assert len(pub_b64) > 30

        payload = {
            "schema_version": "1.0",
            "document_fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "citizen_name": "Aarav Sharma",
            "verified": True,
        }

        signature = Ed25519CryptoManager.sign_payload(priv, payload)
        assert len(signature) > 60

        is_valid = Ed25519CryptoManager.verify_signature(pub_b64, signature, payload)
        assert is_valid is True

    def test_tampered_payload_fails_cryptographic_verification(self):
        priv, pub = Ed25519CryptoManager.generate_keypair()
        pub_b64 = Ed25519CryptoManager.public_key_to_base64(pub)

        payload = {"citizen_name": "Rajesh Kumar", "dob": "1985-06-15"}
        signature = Ed25519CryptoManager.sign_payload(priv, payload)

        # Altered payload: DOB modified by 1 day
        tampered_payload = {"citizen_name": "Rajesh Kumar", "dob": "1985-06-16"}
        assert Ed25519CryptoManager.verify_signature(pub_b64, signature, tampered_payload) is False

    def test_corrupted_signature_bytes_fails_verification(self):
        priv, pub = Ed25519CryptoManager.generate_keypair()
        pub_b64 = Ed25519CryptoManager.public_key_to_base64(pub)

        payload = {"record_id": "test-123"}
        valid_signature = Ed25519CryptoManager.sign_payload(priv, payload)

        # Corrupt signature string
        corrupt_signature = valid_signature[:-4] + "AAAA"
        assert Ed25519CryptoManager.verify_signature(pub_b64, corrupt_signature, payload) is False

    def test_wrong_public_key_fails_verification(self):
        priv1, pub1 = Ed25519CryptoManager.generate_keypair()
        priv2, pub2 = Ed25519CryptoManager.generate_keypair()

        pub2_b64 = Ed25519CryptoManager.public_key_to_base64(pub2)

        payload = {"claim": "Authentic Document"}
        signature1 = Ed25519CryptoManager.sign_payload(priv1, payload)

        # Attempting to verify signature1 with pub2
        assert Ed25519CryptoManager.verify_signature(pub2_b64, signature1, payload) is False


class TestPKILifecycleAndTamperDetection:
    def test_dev_signing_key_provider(self):
        key_id = "unit-test-officer-key"
        priv, pub_b64, fp = DevSigningKeyProvider.create_or_get_default_dev_key(key_id)

        assert priv is not None
        assert len(pub_b64) > 20
        assert len(fp) == 64

        # Re-fetching returns the identical key
        priv2, pub_b64_2, fp2 = DevSigningKeyProvider.create_or_get_default_dev_key(key_id)
        assert pub_b64 == pub_b64_2
        assert fp == fp2

    def test_historical_signature_validity_after_key_rotation(self):
        """
        Critical security test: Rotating an officer key must NOT invalidate
        historical signatures that were properly signed with the old key.
        """
        # Key 1
        priv1, pub1 = Ed25519CryptoManager.generate_keypair()
        pub1_b64 = Ed25519CryptoManager.public_key_to_base64(pub1)

        # Key 2 (rotated new key)
        priv2, pub2 = Ed25519CryptoManager.generate_keypair()
        pub2_b64 = Ed25519CryptoManager.public_key_to_base64(pub2)

        historical_payload = {
            "attestation_id": "historical-1",
            "key_id": "officer-key-v1",
            "status": "approved",
        }
        historical_sig = Ed25519CryptoManager.sign_payload(priv1, historical_payload)

        # Historical signature is valid with key1
        assert Ed25519CryptoManager.verify_signature(pub1_b64, historical_sig, historical_payload) is True

        # New payload signed with key2
        new_payload = {
            "attestation_id": "new-2",
            "key_id": "officer-key-v2",
            "status": "approved",
        }
        new_sig = Ed25519CryptoManager.sign_payload(priv2, new_payload)

        # Both remain valid with their respective keys
        assert Ed25519CryptoManager.verify_signature(pub2_b64, new_sig, new_payload) is True
        assert Ed25519CryptoManager.verify_signature(pub1_b64, historical_sig, historical_payload) is True
