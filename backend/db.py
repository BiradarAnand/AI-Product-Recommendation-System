# db.py
import os
import threading
from mysql.connector import pooling

_pool = None
_pool_lock = threading.Lock()

def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pooling.MySQLConnectionPool(
                    pool_name    = "app_pool",
                    pool_size    = 10,         # ✅ FIXED: was 2, now 10
                    pool_reset_session = True,
                    connection_timeout = 30,   # ✅ FIXED: was 10, now 30 (Render is slow)
                    host         = os.environ.get("DB_HOST"),
                    user         = os.environ.get("DB_USER"),
                    password     = os.environ.get("DB_PASSWORD"),
                    database     = os.environ.get("DB_NAME"),
                    port         = int(os.environ.get("DB_PORT", 3305))
                )
                print("[DB] Pool created ✓")
    return _pool

def get_db():
    return _get_pool().get_connection()