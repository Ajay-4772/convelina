import os
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CONVELINA API"
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
    # Administrator Configuration
    ADMIN_GMAIL: Optional[str] = "admin.demo@gmail.com"

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
    
    # Resend Email Configuration for OTP Verification
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    EMAIL_OTP_EXPIRY_SECONDS: int = 300
    EMAIL_OTP_RESEND_COOLDOWN_SECONDS: int = 60
    EMAIL_OTP_MAX_ATTEMPTS: int = 5

    # Database Connection Pool Settings
    # Scaled safely for multi-worker deployments (e.g. 4 workers * 20 = 80 < PostgreSQL 100 default)
    DB_POOL_SIZE: int = 8
    DB_MAX_OVERFLOW: int = 12
    DB_POOL_TIMEOUT: int = 20
    DB_PREPARE_THRESHOLD: Optional[int] = None  # None for standard psycopg2; configurable for pooler testing

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://admin.localhost:3000",
    ]

    # Module 6 & 7: Google Gemini LLM & RAG Knowledge Base
    GEMINI_ENABLED: bool = False  # Disabled by default in staging/prototype; enabled when paid key configured
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 15
    GEMINI_MAX_RETRIES: int = 2
    GEMINI_BACKOFF_FACTOR: float = 2.0
    EMBEDDING_MODEL: str = "deterministic-hash-1024"  # Accurate 1024-dim deterministic token-hash projection
    QDRANT_IN_PROCESS: bool = True  # Self-contained in-process/memory mode (₹0, zero dormancy/pause)
    QDRANT_LOCATION: Optional[str] = None  # None defaults to ":memory:" when QDRANT_IN_PROCESS is True
    QDRANT_KNOWLEDGE_COLLECTION: str = "consolith_knowledge"
    QDRANT_FORMS_COLLECTION: str = "consolith_forms"
    RAG_TOP_K: int = 5
    RAG_MIN_RELEVANCE: float = 0.55  # Minimum similarity score floor per project rule
    RAG_MAX_CONTEXT_TOKENS: int = 4000
    RAG_SOURCE_MAX_AGE_DAYS: int = 365

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if self.DEBUG:
                raise ValueError("Security violation: DEBUG must be set to False in production.")
            if self.ENCRYPTION_KEY == "consolith_dev_fernet_secret_key_32_bytes_len=":
                raise ValueError("Security violation: Default development ENCRYPTION_KEY is forbidden in production.")
            if not self.ENCRYPTION_KEY or len(self.ENCRYPTION_KEY) < 32:
                raise ValueError("Security violation: A valid 32-byte Fernet ENCRYPTION_KEY is required in production.")
            try:
                from cryptography.fernet import Fernet
                Fernet(self.ENCRYPTION_KEY.encode())
            except Exception:
                raise ValueError("Security violation: ENCRYPTION_KEY is not a valid url-safe base64-encoded Fernet key.")
            if self.TEST_MODE_ALLOW_SIMULATED_TOKENS:
                raise ValueError("Security violation: TEST_MODE_ALLOW_SIMULATED_TOKENS must be False in production.")
            if "consolith_secure_app_pw" in self.DATABASE_URL or "postgres_dev_password" in self.DATABASE_URL:
                raise ValueError("Security violation: Default development database credentials are forbidden in production.")
            from urllib.parse import urlparse
            parsed_db = urlparse(self.DATABASE_URL)
            if parsed_db.username == "postgres":
                raise ValueError("Security violation: Application runtime must connect via dedicated non-superuser role (e.g. 'consolith_app').")
            if self.STORAGE_RETENTION_POLICY != "delete_after_ocr":
                raise ValueError("Privacy violation: STORAGE_RETENTION_POLICY must be 'delete_after_ocr' in production per Aadhaar Act privacy compliance.")
            if self.GEMINI_ENABLED and not self.GEMINI_API_KEY:
                raise ValueError("Security violation: GEMINI_API_KEY must be configured when GEMINI_ENABLED is True in production.")
            if not self.FIREBASE_PROJECT_ID or self.FIREBASE_PROJECT_ID == "consolith-dev":
                raise ValueError("Security violation: A valid production FIREBASE_PROJECT_ID is required in production.")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("Security violation: Wildcard CORS origin is forbidden in production.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
