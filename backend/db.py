# db.py
# ─────────────────────────────────────────────────────────────────────
# Lazy connection pool — does NOT open any DB connections at import time.
# The pool is created only when the first request calls get_db().
#
# Why lazy?  MySQLConnectionPool pre-opens ALL connections immediately.
# With pool_size=2 × 2 workers = 4 connections at startup — hitting the
# limit of 5 before serving a single request.
#
# With lazy init + pool_size=1:
#   • 0 connections opened at startup
#   • Each worker opens 1 connection on its first request
#   • Max live connections = 1 × 2 workers = 2  (well under the limit of 5)
# ─────────────────────────────────────────────────────────────────────

import os
import threading
from mysql.connector import pooling

_pool      = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:   # double-checked locking
                _pool = pooling.MySQLConnectionPool(
                    pool_name="app_pool",
                    pool_size=1,            # 1 per worker × 2 workers = 2 total ✅
                    pool_reset_session=True,
                    host=os.environ.get("DB_HOST"),
                    user=os.environ.get("DB_USER"),
                    password=os.environ.get("DB_PASSWORD"),
                    database=os.environ.get("DB_NAME"),
                    port=int(os.environ.get("DB_PORT", 3306))
                )
                print("[DB] Connection pool created ✓")
    return _pool


def get_db():
    """Borrow a connection from the pool.
    Always call conn.close() in a finally block to return it."""
    return _get_pool().get_connection()