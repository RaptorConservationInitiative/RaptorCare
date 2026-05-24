"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

from server.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy Base for models
Base = declarative_base()

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    poolclass=NullPool if settings.DEBUG else None
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        # 👇 DAS FEHLT BEI DIR
        from server import models  # zwingend!

        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        raise

def get_db():
    """Get database session (dependency for FastAPI routes)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
