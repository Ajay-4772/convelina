import os
import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth

from app.config import settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None
_firebase_initialized: bool = False
_firebase_init_error: Optional[str] = None

def initialize_firebase() -> Optional[firebase_admin.App]:
    global _firebase_app, _firebase_initialized, _firebase_init_error
    
    if _firebase_initialized:
        return _firebase_app

    # Set emulator host if configured
    if settings.FIREBASE_AUTH_EMULATOR_HOST:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.FIREBASE_AUTH_EMULATOR_HOST
        logger.info(f"Using Firebase Auth Emulator at {settings.FIREBASE_AUTH_EMULATOR_HOST}")

    try:
        # Check if already initialized by another worker
        try:
            _firebase_app = firebase_admin.get_app()
            _firebase_initialized = True
            return _firebase_app
        except ValueError:
            pass

        # Option 1: Explicit Service Account JSON file path
        if settings.FIREBASE_SERVICE_ACCOUNT_PATH and os.path.isfile(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            _firebase_app = firebase_admin.initialize_app(cred, {
                "projectId": settings.FIREBASE_PROJECT_ID
            })
            logger.info("Firebase Admin SDK initialized with service account file.")
        
        # Option 2: Default Application Credentials or Project ID (e.g. in cloud or emulator)
        elif settings.FIREBASE_PROJECT_ID:
            # If in emulator mode or cloud environment
            if settings.FIREBASE_AUTH_EMULATOR_HOST:
                _firebase_app = firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
                logger.info("Firebase Admin SDK initialized for emulator environment.")
            else:
                try:
                    cred = credentials.ApplicationDefault()
                    _firebase_app = firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
                    logger.info("Firebase Admin SDK initialized with Application Default Credentials.")
                except Exception as e:
                    _firebase_init_error = (
                        f"Firebase credentials not available. Set FIREBASE_SERVICE_ACCOUNT_PATH or run in emulator: {e}"
                    )
                    logger.warning(_firebase_init_error)
        else:
            _firebase_init_error = "Neither FIREBASE_SERVICE_ACCOUNT_PATH nor FIREBASE_PROJECT_ID configured."
            logger.warning(_firebase_init_error)

        _firebase_initialized = True
        return _firebase_app

    except Exception as e:
        _firebase_init_error = str(e)
        _firebase_initialized = True
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return None

def is_firebase_configured() -> bool:
    initialize_firebase()
    return _firebase_app is not None

def get_firebase_init_error() -> Optional[str]:
    return _firebase_init_error
