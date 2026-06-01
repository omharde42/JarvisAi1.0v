"""
Database Configuration and Session Management
SQLAlchemy setup for all models
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

logger_module = __import__("logging").getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for FastAPI routes to get database session

    Yields:
        Database session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db() -> None:
    """
    Initialize database tables
    Should be called on application startup
    """
    try:
        logger_module.info("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger_module.info("✅ Database initialized successfully")
    except Exception as e:
        logger_module.error(f"❌ Database initialization failed: {str(e)}")
        raise


async def close_db() -> None:
    """
    Close database connection
    Should be called on application shutdown
    """
    try:
        engine.dispose()
        logger_module.info("✅ Database connections closed")
    except Exception as e:
        logger_module.error(f"Error closing database: {str(e)}")
