import io
import os
import re
from typing import Tuple
from fastapi import HTTPException, status
from PIL import Image
import pypdf

from app.config import settings

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

def validate_file_content(content: bytes, filename: str) -> Tuple[str, str]:
    """
    Validates file content: size, magic bytes, and decode integrity.
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

    # 3. Magic bytes inspection
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

    # 4. Deep decoding & corruption validation
    if detected_format == "pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            if len(reader.pages) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF file contains no valid pages."
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or malformed PDF file."
            )
    else:
        # Image validation
        try:
            with Image.open(io.BytesIO(content)) as img:
                img.verify()
                # Ensure dimensions are reasonable
                if img.width <= 0 or img.height <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image has invalid dimensions."
                    )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or invalid image file."
            )

    return detected_format, ext
