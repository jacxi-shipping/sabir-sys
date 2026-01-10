from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
import logging

from egg_farm_system.config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """Manages database connection and sessions with performance optimizations"""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def initialize(cls):
        """Initialize database connection and create tables with performance optimizations"""
        try:
            # SQLite configuration optimizations
            # Use StaticPool for better performance with SQLite file databases
            # NullPool would be used for in-memory databases
            pool_class = StaticPool if 'memory' not in DATABASE_URL else NullPool
            
            cls._engine = create_engine(
                DATABASE_URL,
                echo=False,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20  # 20 second timeout for locked database
                },
                poolclass=pool_class
            )
            
            # Enable performance optimizations for SQLite
            @event.listens_for(cls._engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys=ON")
                # Journal mode for better concurrent access
                cursor.execute("PRAGMA journal_mode=WAL")
                # Synchronous mode for better performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Cache size for better query performance
                cursor.execute("PRAGMA cache_size=10000")
                # Temp store in memory for better performance
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
            
            # Create all tables
            Base.metadata.create_all(bind=cls._engine)
            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls._engine,
                expire_on_commit=False  # Prevent re-fetching on commit
            )
            
            # Run migrations
            from egg_farm_system.database.migrate_sales_table import migrate_sales_table
            migrate_sales_table()
            
            from egg_farm_system.database.migrate_payment_method import migrate_payment_method
            migrate_payment_method()
            
            logger.info("Database initialized successfully with performance optimizations")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @classmethod
    def get_session(cls):
        """Get a new database session"""
        if cls._SessionLocal is None:
            cls.initialize()
        return cls._SessionLocal()
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._engine:
            cls._engine.dispose()
            logger.info("Database connection closed")

# Export Base for use in models
__all__ = ['Base', 'DatabaseManager']
