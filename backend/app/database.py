from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Configure engine based on database type
if "sqlite" in settings.DATABASE_URL:
    # SQLite doesn't support connection pooling, use NullPool
    from sqlalchemy.pool import NullPool
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 10  # 10 second timeout for database operations
        },
        poolclass=NullPool,  # SQLite doesn't need connection pooling
        echo=False
    )
else:
    # For PostgreSQL/MySQL, use connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Max overflow connections
        echo=False  # Set to True for SQL debugging
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

