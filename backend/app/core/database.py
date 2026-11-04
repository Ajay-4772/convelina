import uuid
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from app.config import settings

connect_args = {}
if settings.DB_PREPARE_THRESHOLD is not None:
    connect_args["prepare_threshold"] = settings.DB_PREPARE_THRESHOLD

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()

def set_rls_context(session: Session, user_id: Optional[uuid.UUID], role: Optional[str]) -> None:
    """
    Sets transaction-local session parameters for PostgreSQL Row-Level Security.
    Uses SET LOCAL so parameters automatically expire upon transaction completion,
    preventing any connection-pooling identity leakage.
    """
    uid_str = str(user_id) if user_id is not None else ""
    role_str = role if role is not None else ""
    
    session.execute(
        text("SELECT set_config('app.current_user_id', :uid, true);"),
        {"uid": uid_str}
    )
    session.execute(
        text("SELECT set_config('app.current_user_role', :role, true);"),
        {"role": role_str}
    )

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions with automatic rollback on exception."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
