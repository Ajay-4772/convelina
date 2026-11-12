"""
CONVELINA Privacy & Redaction Service.

Detects and redacts sensitive Indian identity and personal identifiers
before chat persistence, LLM prompt assembly, OCR text caching, error tracking,
Caches, and application logs:
- Aadhaar (12-digit formatted/unformatted -> XXXX-XXXX-<last4>)
- PAN (ABCDE1234F -> XXXXX1234F)
- Indian Passport numbers (A1234567 -> XXXXXX67)
- Phone numbers (+91/0 10-digit -> XXXXXX<last4>)
- Bank account numbers & IFSC codes
- Labeled physical addresses & PIN codes
- Bearer/API secrets and emails in server logs
"""

import logging
import re
from typing import Any, Dict, Tuple

# 1. Aadhaar: 12 digits, formatted as 1234 5678 9012, 1234-5678-9012, or 123456789012
AADHAAR_REGEX = re.compile(
    r"\b([0-9]{4})[\s\-]?([0-9]{4})[\s\-]?([0-9]{4})\b"
)

# 2. PAN: 5 letters, 4 digits, 1 letter
PAN_REGEX = re.compile(
    r"\b([a-zA-Z]{5})([0-9]{4})([a-zA-Z]{1})\b"
)

# 3. Indian Passport: 1 uppercase letter (excluding Q, X, Z) followed by 7 digits
PASSPORT_REGEX = re.compile(
    r"\b([A-PR-WY][0-9]{5})([0-9]{2})\b"
)

# 4. Indian Mobile Numbers: 10 digits starting with 6, 7, 8, 9 (optionally with +91 or 0)
PHONE_REGEX = re.compile(
    r"(?:\+91[\s\-]?)?(?:\b0)?([6-9][0-9]{5})([0-9]{4})\b"
)

# 5. IFSC codes (4 uppercase letters + 0 + 6 alphanumeric) & labeled Bank Account numbers
IFSC_REGEX = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
BANK_ACCOUNT_REGEX = re.compile(
    r"(?i)\b(a/c|acct|account)\s*(?:no\.?|number|#)?\s*[:\-]?\s*([0-9]{5,14})([0-9]{4})\b"
)

# 6. Labeled Residential Addresses & PIN Codes
LABELED_ADDRESS_REGEX = re.compile(
    r"(?im)\b(address|residential\s+address|residence|addr)\s*[:\-]\s*([^\n]{8,180})"
)
LABELED_PIN_REGEX = re.compile(
    r"(?i)\b(pin(?:\s*code)?|postal\s*code)\s*[:\-]?\s*([1-9][0-9]{2})([0-9]{3})\b"
)

# Log-specific sensitive patterns (Bearer tokens, email addresses)
BEARER_TOKEN_REGEX = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-:=]+")
EMAIL_REGEX = re.compile(r"\b([a-zA-Z0-9._%+\-])[a-zA-Z0-9._%+\-]*@([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b")


def redact_aadhaar(text: str) -> Tuple[str, int]:
    """Masks 12-digit Aadhaar numbers to XXXX-XXXX-<last4>."""
    count = 0

    def _replace_aadhaar(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"XXXX-XXXX-{match.group(3)}"

    return AADHAAR_REGEX.sub(_replace_aadhaar, text), count


def redact_pan(text: str) -> Tuple[str, int]:
    """Masks 10-char PAN identifiers to XXXXX<digits><last_char> (e.g. XXXXX1234F)."""
    count = 0

    def _replace_pan(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"XXXXX{match.group(2)}{match.group(3).upper()}"

    return PAN_REGEX.sub(_replace_pan, text), count


def redact_passport(text: str) -> Tuple[str, int]:
    """Masks Indian passport numbers (e.g. A1234567 -> XXXXXX67)."""
    count = 0

    def _replace_passport(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"XXXXXX{match.group(2)}"

    return PASSPORT_REGEX.sub(_replace_passport, text), count


def redact_phone(text: str) -> Tuple[str, int]:
    """Masks Indian mobile numbers to XXXXXX<last4>."""
    count = 0

    def _replace_phone(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"XXXXXX{match.group(2)}"

    return PHONE_REGEX.sub(_replace_phone, text), count


def redact_bank_details(text: str) -> Tuple[str, int]:
    """Masks IFSC codes and labeled bank account numbers."""
    count = 0

    def _replace_ifsc(_: re.Match) -> str:
        nonlocal count
        count += 1
        return "XXXX0XXXXXX"

    def _replace_account(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}: XXXXX{match.group(3)}"

    sanitized = IFSC_REGEX.sub(_replace_ifsc, text)
    sanitized = BANK_ACCOUNT_REGEX.sub(_replace_account, sanitized)
    return sanitized, count


def redact_address(text: str) -> Tuple[str, int]:
    """Masks explicitly labeled residential address lines and PIN codes."""
    count = 0

    def _replace_addr(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}: [REDACTED_ADDRESS]"

    def _replace_pin(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}: XXX{match.group(3)}"

    sanitized = LABELED_ADDRESS_REGEX.sub(_replace_addr, text)
    sanitized = LABELED_PIN_REGEX.sub(_replace_pin, sanitized)
    return sanitized, count


def mask_email(email: str) -> str:
    """Masks email address for safe telemetry/logging (e.g. a***@gmail.com)."""
    if not email or "@" not in email:
        return "[REDACTED_EMAIL]"
    return EMAIL_REGEX.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", email)


def sanitize_pii(text: str, include_address: bool = False) -> Tuple[str, bool, Dict[str, Any]]:
    """
    Pre-persistence sanitization pass covering sensitive identity categories:
    Aadhaar, PAN, Passport, Phone, Bank/IFSC, and optionally labeled physical addresses.
    """
    if not text:
        return text, False, {}

    sanitized, aadhaar_count = redact_aadhaar(text)
    sanitized, pan_count = redact_pan(sanitized)
    sanitized, passport_count = redact_passport(sanitized)
    sanitized, phone_count = redact_phone(sanitized)
    sanitized, bank_count = redact_bank_details(sanitized)
    addr_count = 0
    if include_address:
        sanitized, addr_count = redact_address(sanitized)

    total_redactions = aadhaar_count + pan_count + passport_count + phone_count + bank_count + addr_count
    was_redacted = total_redactions > 0

    summary = {
        "redacted": was_redacted,
        "total_redactions": total_redactions,
        "aadhaar_redactions": aadhaar_count,
        "pan_redactions": pan_count,
        "passport_redactions": passport_count,
        "phone_redactions": phone_count,
        "bank_redactions": bank_count,
        "address_redactions": addr_count,
    }

    return sanitized, was_redacted, summary


def scrub_for_logging(text: str) -> str:
    """Applies full PII, address, email, and bearer token redaction for log safety."""
    if not text:
        return text
    cleaned, _, _ = sanitize_pii(str(text), include_address=True)
    cleaned = BEARER_TOKEN_REGEX.sub("Bearer [REDACTED]", cleaned)
    cleaned = EMAIL_REGEX.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", cleaned)
    return cleaned


class PrivacyRedactingLogFilter(logging.Filter):
    """Logging filter that strips raw PII and credentials from server log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage()
            scrubbed = scrub_for_logging(rendered)
            if scrubbed != rendered:
                record.msg = scrubbed
                record.args = ()
        except Exception:
            pass
        return True
