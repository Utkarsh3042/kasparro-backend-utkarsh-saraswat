from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
from src.config import get_settings
from src.utils.logger import get_logger
from src.database.models import Base

logger = get_logger(__name__)
settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,  # Disable pooling for development
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    connect_args={
        "options": "-c timezone=utc"
    } if "postgresql" in settings.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        logger.info("🗄️  Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def drop_db():
    """Drop all database tables (use with caution!)"""
    try:
        logger.warning("⚠️  Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Database tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Database drop failed: {e}")
        raise

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Usage:
        with get_db() as db:
            db.query(Cryptocurrency).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Get database session (for dependency injection)
    
    Usage in FastAPI:
        @app.get("/")
        def route(db: Session = Depends(get_db_session)):
            return db.query(Cryptocurrency).all()
    """
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise