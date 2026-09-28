import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Consolith API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database - connects via dedicated non-superuser role
    DATABASE_URL: str = "postgresql://consolith_app:consolith_secure_app_pw@postgres:5432/consolith"
    
    # Qdrant Vector DB
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    
    # Firebase Authentication
    FIREBASE_PROJECT_ID: Optional[str] = "consolith-dev"
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None
    FIREBASE_AUTH_EMULATOR_HOST: Optional[str] = None
    
    # Test Mode / Isolated verification (never enable in production)
    TEST_MODE_ALLOW_SIMULATED_TOKENS: bool = False
    
    # Document Storage & Upload Security (Module 4)
    STORAGE_TEMP_DIR: str = "/tmp/consolith/temp_docs"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/jpeg", "image/png"]
    STORAGE_RETENTION_POLICY: str = "delete_after_ocr"  # "delete_after_ocr" or "retain_temp"
    
    # Fernet at-rest sensitive payload encryption key (derived or configured)
    ENCRYPTION_KEY: Optional[str] = "consolith_dev_fernet_secret_key_32_bytes_len="
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
    ]


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
