"""
CONVELINA Server-Side PII Sanitizer & Redaction Service.
Implements pre-persistence masking for Aadhaar, PAN, phone numbers,
and sensitive identity identifiers to guarantee compliance with the
Aadhaar Act (2016) Section 29, DPDPA (2023), and IT Act (2000).
"""

import re
from typing import Tuple, Dict, Any

# 1. Aadhaar: 12 digits, formatted as 1234 5678 9012, 1234-5678-9012, or 123456789012
AADHAAR_REGEX = re.compile(
    r"\b([0-9]{4})[\s\-]?([0-9]{4})[\s\-]?([0-9]{4})\b"
)

# 2. PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_REGEX = re.compile(
    r"\b([a-zA-Z]{5})([0-9]{4})([a-zA-Z]{1})\b"
)

# 3. Indian Mobile Numbers: 10 digits starting with 6, 7, 8, 9 (optionally with +91 or 0)
PHONE_REGEX = re.compile(
    r"(?:\+91[\s\-]?)?(?:\b0)?([6-9][0-9]{5})([0-9]{4})\b"
)

def redact_aadhaar(text: str) -> Tuple[str, int]:
    """
    Detects 12-digit Aadhaar numbers and redacts them to XXXX-XXXX-<last4>.
    Returns the redacted text and count of redacted occurrences.
    """
    count = 0

    def _replace_aadhaar(match: re.Match) -> str:
        nonlocal count
        count += 1
        last4 = match.group(3)
        return f"XXXX-XXXX-{last4}"

    redacted = AADHAAR_REGEX.sub(_replace_aadhaar, text)
    return redacted, count


def redact_pan(text: str) -> Tuple[str, int]:
    """
    Detects 10-character PAN identifiers and redacts them to XXXXX<last4><last1>.
    Example: ABCDE1234F -> XXXXX1234F
    """
    count = 0

    def _replace_pan(match: re.Match) -> str:
        nonlocal count
        count += 1
        digits = match.group(2)
        last_char = match.group(3).upper()
        return f"XXXXX{digits}{last_char}"

    redacted = PAN_REGEX.sub(_replace_pan, text)
    return redacted, count


def redact_phone(text: str) -> Tuple[str, int]:
    """
    Detects Indian mobile phone numbers and redacts them to XXXXXX<last4>.
    """
    count = 0

    def _replace_phone(match: re.Match) -> str:
        nonlocal count
        count += 1
        last4 = match.group(2)
        return f"XXXXXX{last4}"

    redacted = PHONE_REGEX.sub(_replace_phone, text)
    return redacted, count


def sanitize_pii(text: str) -> Tuple[str, bool, Dict[str, Any]]:
    """
    Pre-persistence sanitization pass covering all sensitive identity categories.
    Guarantees that raw 12-digit Aadhaar numbers, PANs, and phone numbers are never
    stored in plaintext in database messages, session contexts, or error logs.

    Returns:
        (sanitized_text, was_redacted, audit_summary)
    """
    if not text:
        return text, False, {}

    sanitized, aadhaar_count = redact_aadhaar(text)
    sanitized, pan_count = redact_pan(sanitized)
    sanitized, phone_count = redact_phone(sanitized)

    total_redactions = aadhaar_count + pan_count + phone_count
    was_redacted = total_redactions > 0

    summary = {
        "redacted": was_redacted,
        "total_redactions": total_redactions,
        "aadhaar_redactions": aadhaar_count,
        "pan_redactions": pan_count,
        "phone_redactions": phone_count,
    }

    return sanitized, was_redacted, summary

