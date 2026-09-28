import hashlib
import os
import uuid
import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger("consolith.storage")

def ensure_temp_dir() -> str:
    """
    Ensures the temporary storage directory exists and returns its absolute path.
    """
    temp_dir = os.path.abspath(settings.STORAGE_TEMP_DIR)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def compute_sha256(content: bytes) -> str:
    """
    Calculates SHA-256 cryptographic hash of byte content.
    """
    return hashlib.sha256(content).hexdigest()

def save_temp_document(content: bytes, ext: str) -> Tuple[str, str]:
    """
    Saves file bytes to an unpredictable server-side filename in the temporary storage dir.
    Returns (absolute_file_path, sha256_hash).
    """
    temp_dir = ensure_temp_dir()
    unique_filename = f"doc_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(temp_dir, unique_filename)
    
    with open(target_path, "wb") as f:
        f.write(content)
        
    file_hash = compute_sha256(content)
    logger.info("Saved temporary document to disk (sha256=%s...)", file_hash[:12])
    return target_path, file_hash

def delete_temp_document(file_path: str) -> bool:
    """
    Safely deletes a temporary file from disk.
    Ensures path lies strictly within the configured temporary storage directory.
    """
    if not file_path or not os.path.exists(file_path):
        return False
        
    temp_dir = ensure_temp_dir()
    abs_target = os.path.abspath(file_path)
    
    # Path traversal safety check
    if not abs_target.startswith(temp_dir):
        logger.warning("Attempted deletion of file outside temporary storage: %s", abs_target)
        return False
        
    try:
        os.remove(abs_target)
        logger.info("Successfully deleted temporary file: %s", abs_target)
        return True
    except OSError as e:
        logger.error("Failed to delete temporary file %s: %s", abs_target, str(e))
        return False
