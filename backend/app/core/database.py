import uuid
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
