import mysql.connector
from mysql.connector import pooling, Error
from contextlib import contextmanager
import logging
import os
logger = logging.getLogger(__name__)

# INCREASED pool size from default to handle concurrent requests
dbconfig = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME"),
}

_pool = None

def init_pool():
    """Initialize connection pool with proper configuration"""
    global _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=20,                    # INCREASED from default (5)
        pool_reset_session=True,         # Reset session for each connection
        autocommit=True,                 # Auto-commit transactions
        use_pure=True,                   # Use pure Python (avoid C extension issues)
        **dbconfig
    )
    logger.info("Connection pool initialized with size 20")

def get_pool():
    """Get or create the connection pool"""
    global _pool
    if _pool is None:
        init_pool()
    return _pool

@contextmanager
def get_db_connection():
    """
    Context manager for database connections - ENSURES proper cleanup
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # ... your code ...
    """
    connection = None
    try:
        connection = get_pool().get_connection()
        yield connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        if connection:
            connection.close()
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()  # ✅ GUARANTEED cleanup

def get_db():
    """Legacy function - kept for backward compatibility"""
    try:
        return get_pool().get_connection()
    except Error as e:
        logger.error(f"Failed to get connection: {e}")
        raise