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

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://admin.localhost:3000",
    ]

    # Module 6 & 7: Google Gemini LLM & RAG Knowledge Base
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
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
            if self.TEST_MODE_ALLOW_SIMULATED_TOKENS:
                raise ValueError("Security violation: TEST_MODE_ALLOW_SIMULATED_TOKENS must be False in production.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
