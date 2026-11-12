import io
import os
import re
import socket
import struct
from typing import Optional, Tuple
from fastapi import HTTPException, status
from PIL import Image
import pypdf

from app.config import settings
from app.core.security_monitoring import record_security_event

# Enforce global Pillow decompression-bomb guard
Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS

EICAR_TEST_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
SUSPICIOUS_POLYGLOT_RE = re.compile(
    rb"(<script[\s>]|<\?php|<svg[\s>]|<!DOCTYPE\s+html|<html[\s>])",
    re.IGNORECASE,
)
PDF_ACTIVE_CONTENT_RE = re.compile(
    rb"/(?:JavaScript|Launch|OpenAction|RichMedia|EmbeddedFiles|SubmitForm)\b"
)

# Magic byte signatures
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "jpeg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
}

SUPPORTED_DOC_TYPES = {
    "aadhaar",
    "pan",
    "passport",
    "education_10th",
    "education_12th",
    "epf_record",
    "other",
}

# Verhoeff Algorithm Tables for Official Aadhaar Checksum Validation
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 6, 7, 8, 9, 0, 1, 2, 3, 4],
    [6, 7, 8, 9, 5, 1, 2, 3, 4, 0],
    [7, 8, 9, 5, 6, 2, 3, 4, 0, 1],
    [8, 9, 5, 6, 7, 3, 4, 0, 1, 2],
    [9, 5, 6, 7, 8, 4, 0, 1, 2, 3],
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def validate_verhoeff(num_str: str) -> bool:
    """
    Validates a numeric string using the Verhoeff checksum algorithm (UIDAI Aadhaar standard).
    """
    cleaned = "".join(c for c in num_str if c.isdigit())
    if not cleaned:
        return False
    c = 0
    for i, char in enumerate(reversed(cleaned)):
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][int(char)]]
    return c == 0


def sanitize_filename(filename: str) -> str:
    """
    Prevents path traversal, null byte injections, and preserves safe basenames.
    """
    if not filename:
        return "unnamed_document"
    # Disallow null bytes
    if "\x00" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed filename containing null bytes."
        )
    # Normalize Windows backslashes to forward slashes so basename works on all platforms
    normalized = filename.replace("\\", "/")
    base_name = os.path.basename(normalized)
    # Remove any non-alphanumeric characters except safe punctuation
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    if not safe_name or safe_name in (".", ".."):
        return "unnamed_document"
    return safe_name


def validate_document_type(doc_type: str) -> str:
    """
    Ensures document type is one of the supported types.
    """
    normalized = doc_type.strip().lower()
    if normalized not in SUPPORTED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document type '{doc_type}'. Allowed types: {sorted(list(SUPPORTED_DOC_TYPES))}"
        )
    return normalized

def _scan_malware_and_polyglots(content: bytes, detected_format: str) -> None:
    """Performs signature checks for EICAR test files, polyglot scripts, and optional ClamAV INSTREAM scan."""
    if EICAR_TEST_SIGNATURE in content:
        record_security_event("upload_malware_detected", component="upload", outcome="blocked")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload rejected: malware signature detected.",
        )

    if detected_format in ("jpeg", "png") and SUSPICIOUS_POLYGLOT_RE.search(content):
        record_security_event("upload_polyglot_detected", component="upload", outcome="blocked")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload rejected: embedded active script markup detected in image payload.",
        )

    clamav_host = getattr(settings, "CLAMAV_HOST", "")
    if clamav_host:
        clamav_port = int(getattr(settings, "CLAMAV_PORT", 3310))
        try:
            with socket.create_connection((clamav_host, clamav_port), timeout=5.0) as sock:
                sock.sendall(b"zINSTREAM\0")
                chunk_size = 65536
                for idx in range(0, len(content), chunk_size):
                    chunk = content[idx : idx + chunk_size]
                    sock.sendall(struct.pack(">I", len(chunk)) + chunk)
                sock.sendall(struct.pack(">I", 0))
                scan_reply = sock.recv(1024).decode("utf-8", errors="ignore").strip("\x00\r\n ")
                if "FOUND" in scan_reply:
                    record_security_event("upload_malware_detected", component="upload", outcome="blocked")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Upload rejected: file failed antivirus inspection.",
                    )
        except HTTPException:
            raise
        except Exception:
            if settings.ENVIRONMENT.lower() in ("production", "staging"):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Antivirus verification service temporarily unavailable.",
                )


def validate_file_content(
    content: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Validates file content: size, MIME header, magic bytes, malware/polyglot signatures,
    PDF active-content/page limits, and image dimension/pixel decompression-bomb caps.
    Returns (detected_format, sanitized_extension).
    """
    # 1. Size checks
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB."
        )

    # 2. Extension check
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed extensions: {settings.ALLOWED_EXTENSIONS}"
        )

    # 3. HTTP Content-Type allowlist check (normalize image/jpg alias)
    normalized_mime = None
    if content_type:
        normalized_mime = content_type.split(";", 1)[0].strip().lower()
        if normalized_mime == "image/jpg":
            normalized_mime = "image/jpeg"
        if normalized_mime not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MIME content type '{normalized_mime}'."
            )

    # 4. Magic bytes inspection
    detected_format = None
    if content.startswith(MAGIC_BYTES["pdf"]):
        detected_format = "pdf"
    elif content.startswith(MAGIC_BYTES["jpeg"]):
        detected_format = "jpeg"
    elif content.startswith(MAGIC_BYTES["png"]):
        detected_format = "png"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match allowed signatures (PDF, JPEG, PNG)."
        )

    expected_mime = {
        "pdf": "application/pdf",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }[detected_format]
    if normalized_mime and normalized_mime != expected_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Declared Content-Type does not match actual file signature."
        )

    # Cross-verify extension matches detected magic bytes
    if detected_format == "pdf" and ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mismatched file extension for PDF content."
        )
    if detected_format in ("jpeg", "png") and ext not in (".jpg", ".jpeg", ".png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mismatched file extension for image content."
        )

    # 5. Malware & polyglot inspection
    _scan_malware_and_polyglots(content, detected_format)

    # 6. Deep decoding, active content, & bomb validation
    if detected_format == "pdf":
        if PDF_ACTIVE_CONTENT_RE.search(content):
            record_security_event("upload_active_pdf_rejected", component="upload", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF contains unsupported active scripting or launch actions."
            )
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            if len(reader.pages) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF file contains no valid pages."
                )
            if len(reader.pages) > settings.MAX_UPLOAD_PDF_PAGES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PDF exceeds maximum allowed page limit ({settings.MAX_UPLOAD_PDF_PAGES} pages)."
                )
            root_obj = (reader.trailer or {}).get("/Root")
            if root_obj is not None and hasattr(root_obj, "get_object"):
                root_dict = root_obj.get_object()
                if any(key in root_dict for key in ("/OpenAction", "/AA")):
                    record_security_event("upload_active_pdf_rejected", component="upload", outcome="blocked")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="PDF contains disallowed automatic execution actions."
                    )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or malformed PDF file."
            )
    else:
        # Image validation with explicit decompression-bomb caps
        try:
            with Image.open(io.BytesIO(content)) as img:
                width, height = img.size
                if width <= 0 or height <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image has invalid dimensions."
                    )
                if width > settings.MAX_IMAGE_DIMENSION or height > settings.MAX_IMAGE_DIMENSION:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Image dimensions exceed maximum allowed {settings.MAX_IMAGE_DIMENSION}px limit."
                    )
                if (width * height) > settings.MAX_IMAGE_PIXELS:
                    record_security_event("upload_decompression_bomb_rejected", component="upload", outcome="blocked")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image exceeds maximum safe pixel count (decompression bomb protection)."
                    )
                img.verify()
        except HTTPException:
            raise
        except Image.DecompressionBombError:
            record_security_event("upload_decompression_bomb_rejected", component="upload", outcome="blocked")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image rejected due to decompression bomb protection."
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or invalid image file."
            )

    return detected_format, ext
