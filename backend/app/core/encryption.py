import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from app.config import settings

def _get_fernet_key(raw_key: Optional[str] = None) -> bytes:
    """
    Derives a guaranteed 32-byte url-safe base64-encoded Fernet key.
    """
    secret = raw_key or settings.ENCRYPTION_KEY or "consolith_default_secret_key_dev"
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_data(plaintext: str) -> str:
    """
    Encrypts sensitive text using Fernet.
    """
    if not plaintext:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    encrypted_bytes = f.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_data(ciphertext: str) -> str:
    """
    Decrypts Fernet ciphertext back to plaintext.
    """
    if not ciphertext:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    decrypted_bytes = f.decrypt(ciphertext.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
